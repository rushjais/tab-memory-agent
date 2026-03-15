# Tab Memory Agent

A Chrome extension + AI backend that gives your browser a memory. It tracks what you research, remembers why, and surfaces context when you need it — powered by [mem0](https://mem0.ai) and [Cartesia](https://cartesia.ai).
---

## What it does

Most people have 50+ tabs open and no memory of why. Tab Memory Agent solves this by building a persistent memory layer on top of your browsing — not just URLs, but intent.

**4 core features:**

**1. Session restore** — When you open Chrome, the popup summarizes what you were working on last session and offers to reopen relevant tabs.

**2. Conversational memory** — Ask the popup anything: *"what was I researching about vector databases?"* or *"should I use Pinecone or Weaviate?"* — it answers from your actual browsing history.

**3. Idle nudges** — Every 30 minutes, checks if you have unfinished research threads and badges the extension icon.

**4. Contextual reminders** — When you switch to a tab on a topic you've researched before, surfaces a specific reminder with a voice option powered by Cartesia.

---

## How it works
```
Chrome Extension
    │  captures tab events (URL, title, time spent)
    ▼
FastAPI Backend
    │  converts raw tab data → natural language via GPT-4o-mini
    │  "Spent 10 min on Pinecone docs, evaluating vector search for ML project"
    ▼
mem0 Memory Layer
    │  stores intent-rich memories with semantic search
    │  retrieves relevant memories when you revisit topics
    ▼
LLM Agent (GPT-4o)
    │  decides whether to surface a reminder
    │  answers conversational queries about your history
    ▼
Cartesia Sonic-2
    speaks reminders out loud on demand
```

---

## Tech stack

| Layer | Tool |
|---|---|
| Memory | [mem0](https://mem0.ai) |
| Voice | [Cartesia](https://cartesia.ai) Sonic-2 |
| LLM | OpenAI GPT-4o + GPT-4o-mini |
| Backend | FastAPI + Python |
| Extension | Chrome MV3 |

---

## Setup

### 1. Clone and install
```bash
git clone https://github.com/YOUR_USERNAME/tab-memory-agent.git
cd tab-memory-agent
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn openai mem0ai cartesia python-dotenv
```

### 2. Add API keys

Create a `.env` file:
```
OPENAI_API_KEY=your_key
MEM0_API_KEY=your_key
CARTESIA_API_KEY=your_key
```

### 3. Run the backend
```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Load the extension

1. Go to `chrome://extensions`
2. Enable Developer mode
3. Click "Load unpacked" → select the `extension/` folder

---

## Project structure
```
tab-memory-agent/
├── backend/
│   ├── main.py         # FastAPI routes
│   ├── processor.py    # Tab event → natural language memory
│   ├── memory.py       # mem0 client (store + search)
│   ├── agent.py        # LLM decision layer
│   └── voice.py        # Cartesia TTS
└── extension/
    ├── manifest.json
    ├── background.js   # Tab event listeners + idle nudge
    ├── popup.html      # Extension UI
    ├── popup.css
    └── popup.js        # Chat + session restore + reminders
```

---

## Why mem0?

Most memory solutions lock you into one model or one app. mem0 is model-agnostic and portable — the same memory layer works across any LLM, any framework, any surface. This project uses mem0 as the single source of truth for all browsing context, making it trivially easy to query across sessions, models, and use cases.

---

*Built as a demonstration of mem0's memory layer for real-world agentic applications.*