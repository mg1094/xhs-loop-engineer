# XHS Loop Engineer

> Xiaohongshu content automation — A Loop Engineering hands-on project

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Loop-Engineering-orange.svg" alt="Loop Engineering">
  <img src="https://img.shields.io/badge/uv-package%20manager-purple.svg" alt="uv">
</p>

---

## 🎯 One-liner

Automate your Xiaohongshu content pipeline — topic discovery → content generation → quality verification → Obsidian archiving — using Loop Engineering.

## 🧠 What is Loop Engineering?

> **Stop being the person who prompts the agent. Design the system that does it for you.**

Loop Engineering sits one floor above prompt engineering. Instead of chatting with an AI for every article, you build a system that:

1. Wakes up on a schedule
2. Finds trending topics
3. Generates content in your voice
4. Verifies quality against your style guide
5. Saves to your Obsidian vault
6. Sends you a notification

You review and publish. The loop handles the rest.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                  Outer Loop                      │
│                                                  │
│  Trigger (daily 8 AM / manual)                   │
│         ↓                                        │
│  ┌──────────────────────────────────────────┐    │
│  │ Agent 1: Topic Finder                     │    │
│  │ Reads Obsidian topic pool + dashboard     │    │
│  │ Output: 3 candidate topics                │    │
│  └──────────────┬───────────────────────────┘    │
│                 ↓                                 │
│          ⚡ Human checkpoint (pick one)            │
│                 ↓                                 │
│  ┌──────────────────────────────────────────┐    │
│  │ Agent 2: Content Writer                   │    │
│  │ Style-driven content generation           │    │
│  │ Output: body + title + tags               │    │
│  └──────────────┬───────────────────────────┘    │
│                 ↓                                 │
│  ┌──────────────────────────────────────────┐    │
│  │ Agent 3: Quality Checker                  │    │
│  │ Forbidden words / structure / tags        │    │
│  │ Output: pass / needs revision             │    │
│  └──────────────┬───────────────────────────┘    │
│                 ↓                                 │
│  ┌──────────────────────────────────────────┐    │
│  │ Agent 4: Archiver + Notifier              │    │
│  │ Saves to Obsidian → Desktop notification  │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  verifyCompletion: Ready to publish?             │
│    No → Inject feedback → Agent 2 retries        │
│    Yes → Archive + End loop                      │
└─────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
xhs-loop-engineer/
├── loop.py                    # Main loop controller
├── agents/
│   ├── topic_finder.py        # Agent 1: Topic discovery
│   ├── content_writer.py      # Agent 2: Content generation
│   ├── quality_checker.py     # Agent 3: Quality verification
│   └── archiver.py            # Agent 4: Archive + notify
├── config/
│   ├── style.yaml             # Style guide (persona, forbidden words, structure)
│   └── schedule.yaml          # Schedule config (frequency, Obsidian paths)
├── prompts/
│   ├── topic_finder.md        # Topic discovery prompt template
│   ├── content_writer.md      # Content generation prompt template
│   └── quality_checker.md     # Quality verification prompt template
├── state/
│   └── loop_state.json        # Persistent loop state
├── output/                    # Generated content output
├── pyproject.toml             # Project metadata + dependencies (uv)
├── requirements.txt           # pip-compatible fallback
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended package manager)
- Node.js 18+ (only for the Web UI)
- [Obsidian](https://obsidian.md/) vault at `~/Documents/Obsidian Vault`
- macOS (for desktop notifications) or Linux

### Option A — Web UI (recommended)

```bash
git clone git@github.com:mg1094/xhs-loop-engineer.git
cd xhs-loop-engineer

# Backend
uv sync
# Frontend
cd frontend && npm install && cd ..

# Start both
./start.sh
```

Open <http://localhost:5173>.

### Option B — CLI only

```bash
git clone git@github.com:mg1094/xhs-loop-engineer.git
cd xhs-loop-engineer
uv sync
source .venv/bin/activate
python loop.py
```

## 📋 Your Daily Workflow

```
8:00 AM → Run python loop.py
         → Agent 1 shows 3 candidate topics
         → You pick one
         → Agent 2 generates content
         → Agent 3 verifies quality
         → Agent 4 saves to Obsidian + desktop notification
         → You open Obsidian, review, copy to Xiaohongshu
         → Publish
         → Done
```

## 🔧 Configuration

### style.yaml

Defines your content persona:

- `forbidden_words` — Words that must never appear
- `preferred_words` — Tone and vocabulary preferences
- `structure` — Article structure template
- `article_types` — Separate rules for beginner posts vs deep-tech posts

### schedule.yaml

Defines your workflow:

- `frequency` — How often to publish
- `obsidian.vault_path` — Path to your Obsidian vault
- `notification` — Desktop notification settings

## 🛠️ Built With

**Backend:** Python 3.10+, [uv](https://github.com/astral-sh/uv), FastAPI, Pydantic
**Frontend:** Vue 3, Vite, Tailwind CSS, Pinia, Vue Router
**Storage:** [Obsidian](https://obsidian.md/) vault (local Markdown)

## 🌐 Languages

[简体中文](README_CN.md)

## 📄 License

MIT © [mg1094](https://github.com/mg1094)
