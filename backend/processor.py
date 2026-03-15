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

    prompt = f"""Convert this browsing event into a concise memory fact (1-2 sentences max).
Focus on what the user was likely trying to DO or LEARN, not just what page they visited.
Be specific. Write in third person past tense.

URL: {url}
Page title: {title}
Time spent: {time_spent_seconds} seconds

Examples of good output:
- "Spent 5 minutes reading about mem0's graph memory architecture, likely evaluating it for a project."
- "Quickly scanned a GitHub repo for a Python FastAPI boilerplate, probably looking for starter code."
- "Read a TechCrunch article about Cartesia's Series A funding for about 8 minutes."

Output only the memory sentence, nothing else."""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.3
    )

    return response.choices[0].message.content.strip()
