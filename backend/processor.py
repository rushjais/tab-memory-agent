from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_topic(url: str, title: str) -> str:
    domain = url.split("/")[2] if "//" in url else url
    combined = f"{domain} {title}".lower()

    topics = {
        "github": "software_dev",
        "stackoverflow": "software_dev",
        "arxiv": "research",
        "scholar": "research",
        "techcrunch": "startups",
        "ycombinator": "startups",
        "news.ycombinator": "startups",
        "bloomberg": "finance",
        "wsj": "finance",
        "linkedin": "networking",
        "twitter": "social",
        "x.com": "social",
        "youtube": "video",
        "notion": "productivity",
        "docs.google": "productivity",
    }

    for keyword, topic in topics.items():
        if keyword in combined:
            return topic

    return "general"

def tab_to_memory(url: str, title: str, time_spent_seconds: int) -> str:
    if time_spent_seconds < 15:
        return None

    prompt = f"""Convert this browsing event into a specific, useful memory fact (1 sentence).
Rules:
- Be SPECIFIC about what the page was actually about
- Mention the exact topic, tool, company, or concept
- Include what the user was likely trying to accomplish
- Do NOT be generic — avoid phrases like "researching tech" or "exploring a project"
- Write in past tense, third person

URL: {url}
Page title: {title}
Time spent: {time_spent_seconds} seconds

Good examples:
- "Spent 8 min on mem0's graph memory docs, likely comparing graph vs vector storage approaches."
- "Read TechCrunch article about mem0's $24M Series A — researching AI memory infrastructure funding."
- "Explored mem0ai/mem0 GitHub repo for 10 min, likely reviewing the Python SDK and integration examples."

Bad examples (too generic):
- "User was researching a tech topic."
- "Spent time on a website about AI."

Output only the memory sentence, nothing else."""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=80,
        temperature=0.2
    )

    return response.choices[0].message.content.strip()
