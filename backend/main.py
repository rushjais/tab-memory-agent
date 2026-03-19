from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from backend.processor import tab_to_memory, extract_topic
from backend.memory import store_tab_memory, search_tab_memory
from backend.agent import decide_whether_to_surface
from backend.voice import speak_reminder
import os
import json

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Reply", "X-Urls"],
)

class TabEvent(BaseModel):
    url: str
    title: str
    time_spent_seconds: int
    event: str

class QueryEvent(BaseModel):
    url: str
    title: str

class SpeakRequest(BaseModel):
    message: str

class ChatRequest(BaseModel):
    message: str
    user_id: str = "rushil"

class VoiceCommandRequest(BaseModel):
    transcript: str
    user_id: str = "rushil"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/tab-event")
async def handle_tab_event(tab: TabEvent):
    memory_text = tab_to_memory(tab.url, tab.title, tab.time_spent_seconds)
    if not memory_text:
        return {"stored": False, "reason": "tab too brief"}
    topic = extract_topic(tab.url, tab.title)
    store_tab_memory(memory_text, topic, tab.url)
    return {"stored": True, "memory": memory_text, "topic": topic}


@app.post("/check-tab")
async def check_tab(tab: QueryEvent):
    decision = decide_whether_to_surface({"url": tab.url, "title": tab.title})

    if not decision.get("surface"):
        return {"surface": False}

    message = decision.get("message", "")

    # Also fetch related URLs from mem0
    memories = search_tab_memory(
        f"{tab.title} {tab.url}",
        user_id="rushil",
        limit=5
    )

    related_urls = []
    for m in memories:
        if isinstance(m, dict):
            score = m.get("score", 0)
            url = m.get("metadata", {}).get("url", "") if m.get("metadata") else ""
            current_domain = tab.url.split("/")[2] if "//" in tab.url else ""
            mem_domain = url.split("/")[2] if "//" in url else ""
            # Only include URLs from different domains (not the same site)
            if score >= 0.5 and url and url not in related_urls and mem_domain != current_domain:
                related_urls.append(url)

    return {
        "surface": True,
        "message": message,
        "mode": decision.get("mode", "popup"),
        "related_urls": related_urls[:3]
    }


@app.post("/speak")
async def speak(req: SpeakRequest):
    audio = speak_reminder(req.message)
    return Response(content=audio, media_type="audio/wav")


@app.post("/chat")
async def chat(req: ChatRequest):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    memories = search_tab_memory(req.message, user_id=req.user_id, limit=8)

    if not memories:
        return {"reply": "I don't have any memories related to that yet. Browse more and I'll start remembering.", "urls": []}

    memory_lines = []
    urls = []
    for m in memories:
        if isinstance(m, dict):
            text = m.get("memory", "")
            score = m.get("score", 0)
            url = m.get("metadata", {}).get("url", "") if m.get("metadata") else ""
            if score >= 0.4 and text:
                memory_lines.append(f"- {text} (score: {score:.2f})")
                if url and url not in urls:
                    urls.append(url)

    if not memory_lines:
        return {"reply": "Nothing relevant found for that topic yet.", "urls": []}

    memory_text = "\n".join(memory_lines)

    prompt = f"""You are a personal browsing memory assistant.
Answer specifically based on the user's browsing memories. Be concise and helpful.
If they ask what they were working on, summarize the themes.
If they ask about a specific topic, tell them exactly what they read.
Keep response under 3 sentences.

User question: {req.message}

Their browsing memories:
{memory_text}"""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.3
    )

    reply = response.choices[0].message.content.strip()
    return {"reply": reply, "urls": urls[:3]}


@app.post("/session-summary")
async def session_summary(user_id: str = "rushil"):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    memories = search_tab_memory("recent browsing research work", user_id=user_id, limit=10)

    if not memories:
        return {"summary": None, "topics": [], "urls": []}

    memory_lines = []
    urls = []
    for m in memories:
        if isinstance(m, dict):
            text = m.get("memory", "")
            score = m.get("score", 0)
            url = m.get("metadata", {}).get("url", "") if m.get("metadata") else ""
            if score >= 0.3 and text:
                memory_lines.append(f"- {text}")
                if url and url not in urls:
                    urls.append(url)

    if not memory_lines:
        return {"summary": None, "topics": [], "urls": []}

    memory_text = "\n".join(memory_lines)

    prompt = f"""Based on these recent browsing memories, give a 1-sentence summary of what the user was working on.
Then list 2-3 topic labels (e.g. "Vector databases", "FastAPI", "AI memory").
Format as JSON: {{"summary": "...", "topics": ["...", "..."]}}
Only output JSON, nothing else.

Memories:
{memory_text}"""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.2
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        parsed = json.loads(raw)
        return {
            "summary": parsed.get("summary"),
            "topics": parsed.get("topics", []),
            "urls": urls[:3]
        }
    except:
        return {"summary": None, "topics": [], "urls": []}


@app.post("/idle-check")
async def idle_check(user_id: str = "rushil"):
    memories = search_tab_memory("research work project", user_id=user_id, limit=5)

    if not memories:
        return {"has_idle": False, "topics": []}

    topics = []
    for m in memories:
        if isinstance(m, dict):
            meta = m.get("metadata", {})
            topic = meta.get("topic", "")
            score = m.get("score", 0)
            if score >= 0.5 and topic and topic not in topics:
                topics.append(topic)

    return {"has_idle": len(topics) > 0, "topics": topics[:3]}


@app.post("/voice-command")
async def voice_command(req: VoiceCommandRequest):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    intent_prompt = f"""Parse this voice command about browsing history into JSON.
Extract: topic (what they want), time_filter (today/yesterday/this week/all), action (reopen/find/summarize)

Examples:
"reopen my tabs about vector databases from yesterday" → {{"topic": "vector databases", "time_filter": "yesterday", "action": "reopen"}}
"what was I reading about AI memory?" → {{"topic": "AI memory", "time_filter": "all", "action": "find"}}

Voice command: "{req.transcript}"
Output only valid JSON, nothing else."""

    intent_response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": intent_prompt}],
        max_tokens=80,
        temperature=0.1
    )

    raw = intent_response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        intent = json.loads(raw)
    except:
        intent = {"topic": req.transcript, "time_filter": "all", "action": "find"}

    memories = search_tab_memory(intent["topic"], user_id=req.user_id, limit=6)

    if not memories:
        reply = f"I couldn't find any memories about {intent['topic']}. Try browsing some pages on that topic first."
        audio = speak_reminder(reply)
        return Response(
            content=audio,
            media_type="audio/wav",
            headers={"X-Reply": reply, "X-Urls": "[]"}
        )

    urls = []
    for m in memories:
        if isinstance(m, dict):
            score = m.get("score", 0)
            url = m.get("metadata", {}).get("url", "") if m.get("metadata") else ""
            if score >= 0.45 and url and url not in urls:
                urls.append(url)

    if intent["action"] == "reopen" and urls:
        count = len(urls)
        domains = [u.split("/")[2].replace("www.", "") for u in urls[:3]]
        reply = f"Found {count} tab{'s' if count > 1 else ''} about {intent['topic']}. Opening {', '.join(domains)} now."
    elif urls:
        domains = [u.split("/")[2].replace("www.", "") for u in urls[:3]]
        reply = f"You were researching {intent['topic']} on {', '.join(domains)}. Want me to reopen them?"
    else:
        reply = f"I have memories about {intent['topic']} but couldn't find the exact URLs. Try the chat for more details."

    audio = speak_reminder(reply)

    return Response(
        content=audio,
        media_type="audio/wav",
        headers={
            "X-Reply": reply,
            "X-Urls": json.dumps(urls[:3])
        }
    )