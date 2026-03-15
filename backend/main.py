from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv

from backend.processor import tab_to_memory, extract_topic
from backend.memory import store_tab_memory
from backend.agent import decide_whether_to_surface
from backend.voice import speak_reminder
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TabEvent(BaseModel):
    url: str
    title: str
    time_spent_seconds: int
    event: str

class QueryEvent(BaseModel):
    url: str
    title: str

@app.post("/tab-event")
async def handle_tab_event(tab: TabEvent):
    # Step 1: convert to natural language memory
    memory_text = tab_to_memory(tab.url, tab.title, tab.time_spent_seconds)

    if not memory_text:
        return {"stored": False, "reason": "tab too brief"}

    # Step 2: extract topic and store in mem0
    topic = extract_topic(tab.url, tab.title)
    store_tab_memory(memory_text, topic)

    return {"stored": True, "memory": memory_text, "topic": topic}


@app.post("/check-tab")
async def check_tab(tab: QueryEvent):
    # Called when user opens a new tab — check if we should surface anything
    decision = decide_whether_to_surface({"url": tab.url, "title": tab.title})

    if not decision.get("surface"):
        return {"surface": False}

    message = decision.get("message", "")

    # If voice mode, generate audio and return it
    if decision.get("mode") == "voice":
        audio = speak_reminder(message)
        return Response(content=audio, media_type="audio/wav")

    return {"surface": True, "message": message, "mode": decision.get("mode", "popup")}
class SpeakRequest(BaseModel):
    message: str

@app.post("/speak")
async def speak(req: SpeakRequest):
    audio = speak_reminder(req.message)
    return Response(content=audio, media_type="audio/wav")


@app.get("/health")
async def health():
    return {"status": "ok"}

class ChatRequest(BaseModel):
    message: str
    user_id: str = "rushil"

@app.post("/chat")
async def chat(req: ChatRequest):
    from backend.memory import search_tab_memory
    from openai import OpenAI
    import os
    
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Search mem0 for relevant memories
    memories = search_tab_memory(req.message, user_id=req.user_id, limit=8)
    
    if not memories:
        return {"reply": "I don't have any memories related to that yet. Browse more and I'll start remembering.", "urls": []}
    
    memory_lines = []
    urls = []
    for m in memories:
        if isinstance(m, dict):
            text = m.get("memory", "")
            score = m.get("score", 0)
            url = m.get("metadata", {}).get("url", "")
            if score >= 0.4 and text:
                memory_lines.append(f"- {text} (score: {score:.2f})")
                if url:
                    urls.append(url)
    
    memory_text = "\n".join(memory_lines)
    
    prompt = f"""You are a personal browsing memory assistant. 
The user is asking about their past browsing history.
Answer specifically based on their memories. Be concise and helpful.
If they ask what they were working on, summarize the themes.
If they ask about a specific topic, tell them exactly what they read.
If relevant URLs exist, mention you can reopen them.
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
    from backend.memory import search_tab_memory
    from openai import OpenAI
    import os
    
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
            url = m.get("metadata", {}).get("url", "")
            if score >= 0.3 and text:
                memory_lines.append(f"- {text}")
                if url:
                    urls.append(url)
    
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
    from backend.memory import search_tab_memory
    
    memories = search_tab_memory("research work project", user_id=user_id, limit=5)
    
    if not memories:
        return {"has_idle": False, "topics": []}
    
    topics = []
    for m in memories:
        if isinstance(m, dict):
            meta = m.get("metadata", {})
            topic = meta.get("topic", "")
            text = m.get("memory", "")
            score = m.get("score", 0)
            if score >= 0.5 and topic and topic not in topics:
                topics.append(topic)
    
    return {
        "has_idle": len(topics) > 0,
        "topics": topics[:3]
    }