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

    # Search using both title and domain for better recall
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
Your job: find the single most relevant past memory and surface it as a specific reminder.

Current tab:
Title: {current_tab['title']}
URL: {current_tab['url']}
Domain: {current_domain}

Past memories ranked by relevance:
{memory_text}

Rules:
- Pick the memory that most directly matches the CURRENT domain or topic
- "pinecone.io" matches memories about Pinecone or vector databases
- "github.com" matches memories about coding or specific repos
- "mem0.ai" matches memories about mem0 or AI memory
- If the top memory mentions a completely different product/site, return surface false
- Reminder must be specific, under 15 words, reference actual content from memory
- Do NOT use generic phrases like "continue exploring" or "check updates"

Good reminder examples:
- "You researched Pinecone vector search docs — were you comparing to Weaviate?"
- "You spent 10 min on Pinecone docs earlier — pick up where you left off."

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

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"surface": False}