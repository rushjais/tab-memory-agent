from openai import OpenAI
from dotenv import load_dotenv
from backend.memory import search_tab_memory
import os
import json

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_domain(url: str) -> str:
    try:
        return url.split("/")[2].replace("www.", "")
    except:
        return ""

def decide_whether_to_surface(current_tab: dict, user_id: str = "rushil") -> dict:
    current_domain = get_domain(current_tab['url'])
    query = f"{current_tab['title']} {current_domain}"
    memories = search_tab_memory(query, user_id=user_id, limit=7)

    if not memories:
        return {"surface": False}

    scored_memories = []
    for m in memories:
        if isinstance(m, dict):
            text = m.get("memory") or m.get("text") or str(m)
            score = m.get("score", 0)
        else:
            text = str(m)
            score = 0
        if score >= 0.5:
            scored_memories.append((score, text))

    if not scored_memories:
        return {"surface": False}

    scored_memories.sort(reverse=True)
    memory_lines = [f"- {text} (relevance: {score:.2f})" for score, text in scored_memories]
    memory_text = "\n".join(memory_lines)

    prompt = f"""You are a browsing memory assistant. A user just opened a tab.
Your job: decide if any past memory is genuinely relevant to what they're currently looking at, and surface a specific, useful reminder if so.

Current tab:
Title: {current_tab['title']}
URL: {current_tab['url']}
Domain: {current_domain}

Past memories ranked by relevance:
{memory_text}

How to decide:
- Think about whether the current page's topic, company, person, tool, or concept overlaps meaningfully with any memory
- Relevance is about TOPIC and INTENT, not just domain matching
- Example: opening a founder's company page is relevant to a memory about their LinkedIn profile
- Example: opening a Python docs page is relevant to a memory about a FastAPI tutorial
- Example: opening a competitor's site is relevant to a memory about a similar product
- Example: opening a news article about a company is relevant to a memory about that company's product
- Do NOT surface if the connection is superficial or generic (e.g. both are just "tech websites")
- Do NOT surface if no memory is genuinely relevant
- The reminder must be specific and reference actual content from the memory
- Keep the reminder under 15 words
- Write it like a helpful colleague who remembers what you were doing, not a robot

Respond with only valid JSON:
{{"surface": true, "message": "specific reminder under 15 words", "mode": "popup"}}
or
{{"surface": false}}"""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()
    print("AGENT DECISION:", raw)

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"surface": False}