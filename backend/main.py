from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv

from backend.processor import tab_to_memory, extract_topic
from backend.memory import store_tab_memory
from backend.agent import decide_whether_to_surface
from backend.voice import speak_reminder

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


@app.get("/health")
async def health():
    return {"status": "ok"}
