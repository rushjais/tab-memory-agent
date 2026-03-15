from openai import OpenAI
from dotenv import load_dotenv
from backend.memory import search_tab_memory
import os
import json

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def decide_whether_to_surface(current_tab: dict, user_id: str = "rushil") -> dict:
    query = f"{current_tab['title']} {current_tab['url']}"
    memories = search_tab_memory(query, user_id=user_id, limit=5)

    if not memories:
        return {"surface": False}

    # Handle both formats mem0 might return
    memory_lines = []
    for m in memories:
        if isinstance(m, dict):
            text = m.get("memory") or m.get("text") or str(m)
        else:
            text = str(m)
        memory_lines.append(f"- {text}")

    memory_text = "\n".join(memory_lines)

    prompt = f"""You are a quiet, helpful browsing memory assistant.
A user just opened a new tab. You have access to their past browsing memories.
Decide if it's worth surfacing a reminder — only do so if it's genuinely useful.

Surface a reminder if:
- The user is returning to a topic they researched 2+ days ago and likely had deep context on
- The reminder would save them meaningful time or help them continue prior work
- The connection is specific, not vague

Do NOT surface if:
- The connection is generic
- You're not confident the memories are actually relevant

Current tab:
Title: {current_tab['title']}
URL: {current_tab['url']}

Past memories:
{memory_text}

Respond with only valid JSON in this exact format:
{{"surface": true, "message": "short reminder under 20 words", "mode": "popup"}}
or
{{"surface": false}}"""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.2
    )

    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"surface": False}
