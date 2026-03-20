# Tab Memory Agent

> Your browser has a great memory. You don't. This fixes that.

A Chrome extension + AI backend that gives your browser persistent memory — powered by [mem0](https://mem0.ai) and [Cartesia](https://cartesia.ai).

---

---

## The problem

You open 50 tabs researching something. You close them. A week later you're back on the same topic with no memory of what you found, what you compared, or where you left off. Your browser history is a list of URLs with no context — it doesn't know what you were *trying to do*.

Tab Memory Agent fixes this by building a persistent memory layer on top of your browsing. Not just URLs — intent.

---

## Features

### 1. Passive memory capture
The extension silently watches what you browse. Every page you spend 15+ seconds on gets converted into an intent-rich memory and stored in mem0. Not "visited pinecone.io" — *"Spent 10 minutes on Pinecone's vector search docs, likely comparing storage approaches for an ML project."*

### 2. Conversational history
Click the extension icon and ask anything about your browsing history:
- *"What was I researching about vector databases?"*
- *"Should I use Pinecone or Weaviate based on what I've read?"*
- *"What was I working on last Tuesday?"*

It answers from your actual sessions — semantically, not by keyword.

### 3. Voice commands with tab reopening
Click the mic and say *"reopen my tabs about AI memory tools"* — Cartesia responds out loud and the relevant tabs reopen automatically. No typing, no searching, no reconstructing lost context.

### 4. Contextual reminders
When you switch to a tab on a topic you've researched before, the extension surfaces a specific reminder — with one-click buttons to reopen related tabs from past sessions.

### 5. Session restore
When you open Chrome, the popup summarizes what you were working on in your last session and offers to reopen the relevant tabs.

### 6. Idle nudges
Every 30 minutes, checks for unfinished research threads and badges the extension icon as a quiet reminder.

---

## Architecture
```
Chrome Extension (MV3)
    │  onActivated, onRemoved, onUpdated listeners
    │  captures: URL, title, time spent per tab
    ▼
FastAPI Backend
    │  processor.py: tab event → natural language via GPT-4o-mini
    │  "Spent 10 min on Pinecone docs, evaluating vector search for ML project"
    ▼
mem0 Memory Layer
    │  stores intent-rich memories with URL metadata
    │  semantic search retrieves relevant memories on tab switch
    ▼
LLM Agent (GPT-4o)
    │  decides whether to surface a reminder based on topic + intent match
    │  answers conversational queries about browsing history
    │  parses voice command intent (topic, time filter, action)
    ▼
Cartesia Sonic-2
    │  speaks reminders and voice command responses out loud
    ▼
Extension Popup
    chat interface + reopen buttons + session restore view
```

---

## Tech stack

| Component | Tool | Why |
|---|---|---|
| Memory layer | [mem0](https://mem0.ai) | Persistent, semantic, model-agnostic memory |
| Voice | [Cartesia](https://cartesia.ai) Sonic-2 | Sub-100ms TTS latency for natural responses |
| Intent extraction | OpenAI GPT-4o-mini | Fast, cheap tab-to-memory conversion |
| Agent reasoning | OpenAI GPT-4o | Relevance decisions + conversational answers |
| Speech-to-text | Web Speech API | Native Chrome, no extra API needed |
| Backend | FastAPI + Python | Async, lightweight, easy to extend |
| Extension | Chrome MV3 | Background service worker for passive capture |

---

## Why mem0?

Most memory solutions are model-specific or app-specific — your memories in ChatGPT don't transfer anywhere else. mem0 is model-agnostic and portable. This project uses it as the single source of truth for all browsing context, which means the same memory layer could power a voice assistant, a note-taking app, or a research tool — all reading from the same history.

The semantic search quality is what makes the agent work. Searching "vector databases" surfaces memories about Pinecone, Weaviate, and a Hacker News discussion about DB comparisons — none of which use the exact phrase "vector databases" — because mem0 understands intent, not just keywords.

---

## Setup

### Prerequisites
- Python 3.11+
- Chrome browser (personal profile, not managed by an org)
- API keys for [mem0](https://app.mem0.ai), [OpenAI](https://platform.openai.com), and [Cartesia](https://cartesia.ai)

### 1. Clone the repo
```bash
git clone https://github.com/rushjais/tab-memory-agent.git
cd tab-memory-agent
```

### 2. Set up Python environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn openai mem0ai cartesia python-dotenv
```

### 3. Add API keys

Create a `.env` file in the project root:
```
OPENAI_API_KEY=your_key_here
MEM0_API_KEY=your_key_here
CARTESIA_API_KEY=your_key_here
```

Never commit this file — it's already in `.gitignore`.

### 4. Start the backend
```bash
uvicorn backend.main:app --reload --port 8000
```

### 5. Load the Chrome extension

1. Open `chrome://extensions`
2. Enable **Developer mode** (top right toggle)
3. Click **Load unpacked**
4. Select the `extension/` folder

The Tab Memory icon will appear in your toolbar. Browse normally — it starts capturing immediately.

---

## Usage

**Passive capture** happens automatically. Just browse normally for 15+ seconds on any page.

**Chat:** Click the extension icon → type any question about your browsing history → hit enter.

**Voice command:** Click the mic button → say what you need (e.g. *"reopen my research on FastAPI background tasks"*) → tabs reopen and Cartesia confirms out loud.

**Contextual reminder:** Switch tabs — if you've researched that topic before, a reminder appears with reopen buttons.

**Session restore:** Open Chrome fresh → popup shows last session summary with reopen buttons.

---

## Project structure
```
tab-memory-agent/
├── backend/
│   ├── main.py          # FastAPI routes (/tab-event, /check-tab, /chat, /speak, /voice-command, /session-summary, /idle-check)
│   ├── processor.py     # Tab event → natural language memory (GPT-4o-mini)
│   ├── memory.py        # mem0 client — store and search
│   ├── agent.py         # LLM reasoning — relevance decisions
│   └── voice.py         # Cartesia TTS integration
└── extension/
    ├── manifest.json    # Chrome MV3 config
    ├── background.js    # Tab listeners, idle nudge, session startup
    ├── popup.html       # Extension UI shell
    ├── popup.css        # Dark theme styling
    └── popup.js         # Chat, voice command, session restore, reminders
```

---

## API endpoints

| Endpoint | Method | What it does |
|---|---|---|
| `/tab-event` | POST | Stores a tab visit as a memory in mem0 |
| `/check-tab` | POST | Checks if current tab should surface a reminder |
| `/chat` | POST | Answers natural language questions about browsing history |
| `/speak` | POST | Converts text to speech via Cartesia |
| `/voice-command` | POST | Parses voice intent, finds URLs, generates spoken response |
| `/session-summary` | POST | Summarizes last session for restore view |
| `/idle-check` | POST | Returns topics with unfinished research threads |
| `/health` | GET | Health check |
---

## Roadmap

- [ ] Date filtering in voice commands ("what was I reading *yesterday*?")
- [ ] Import from browser history to seed initial memories
- [ ] Multi-device memory sync via mem0's cross-platform layer
- [ ] Proactive email/calendar integration for context-aware reminders
- [ ] Firefox support
--