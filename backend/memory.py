from mem0 import MemoryClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MemoryClient(api_key=os.getenv("MEM0_API_KEY"))

def store_tab_memory(natural_language: str, topic: str, user_id: str = "rushil"):
    client.add(
        [{"role": "user", "content": natural_language}],
        user_id=user_id,
        metadata={"topic": topic, "source": "browser"}
    )
    
def search_tab_memory(query: str, user_id: str = "rushil", limit: int = 5):
    results = client.search(
        query,
        user_id=user_id,
        limit=limit,
        filters={"user_id": user_id}
    )
    print("MEM0 RAW RESULTS:", results)
    # mem0 returns {"results": [...]} 
    if isinstance(results, dict):
        return results.get("results", [])
    return results
