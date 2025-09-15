# LLM Chat App (FastAPI + React)

A modern chat application built with **React (Vite + TypeScript)** and a new **Python FastAPI backend** that streams responses via **Server-Sent Events (SSE)**.  
This project extends the [starter app](https://github.com/brainfish-ai/llm-chat-starter-app).

## Project Structure
llm-chat-starter-app/

├── apps/

│   ├── frontend/      # Vite + React + shadcn/ui components

│   ├── backend/       # Original Node backend (removed, not used now)

│   └── backend-py/    # New FastAPI backend with SSE + history + file upload

## Features
- Chat with LLMs
  - Providers: mock, hf, openai, openrouter
  - Streaming responses via SSE
- Conversation History
  - Persistent SQLite DB using SQLModel
  - Sessions keyed by session_id
  - REST endpoint: GET /api/history/{session_id}
- File Upload Context
  - Upload files, extract/summarize content
  - Stored in DB and injected into chat as system context
- Session Persistence
  - session_id stored in localStorage
  - Conversations survive page refreshes
- New Chat Button
  - Clears current messages and session
  - Starts a fresh conversation (like ChatGPT)
- Logging
  - Logs active provider and model at startup
  - Per-request logging for OpenRouter model

## Prerequisites
- Node.js (v18+)
- Yarn (v4)
- Python 3.10+ with venv
- SQLite (default)
- Hugging Face or OpenRouter API key (if using those providers)

## Setup Instructions

### 1. Clone & Install
git clone https://github.com/8dsasb/llm-chat-starter-app.git
cd llm-chat-starter-app
yarn install

### 2. Backend Setup
cd apps/backend-py
python -m venv .venv
.venv\Scripts\activate     # Windows
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env

Edit .env (choose one provider):
PROVIDER=mock

# Hugging Face
HF_API_KEY=hf_xxxxxxxxxxxxx
HF_MODEL=facebook/bart-large-cnn

# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxx

# OpenRouter
OPENROUTER_API_KEY=or_xxxxxxxxxxxxx
OPENROUTER_MODEL=deepseek/deepseek-chat-v3.1:free

# Database
DB_URL=sqlite:///./chat_history.db

### 3. Start Dev Servers
From the repo root:
yarn dev

- Frontend → http://localhost:5173  
- Backend → http://localhost:8000  

## API Endpoints

- Health check  
  GET /health → { "ok": true, "provider": "mock" }

- Chat (SSE)  
  POST /api/chat  
  { "session_id": "1234", "messages": [{ "role": "user", "content": "hello" }] }

- Conversation history  
  GET /api/history/{session_id} → returns saved messages

- File upload  
  POST /api/upload → saves file text/summary to DB for the session

## Enhancement
This fork implements Conversation History + File Upload Context as the chosen enhancements:
- Messages and file context persisted in SQLite
- Sessions persist across reloads
- “New Chat” button resets session

## Technologies
- Frontend: Vite, React, TypeScript, shadcn/ui
- Backend: Python, FastAPI, Uvicorn, SQLModel (SQLite)
- LLM Integration: Mock, Hugging Face, OpenAI, OpenRouter
- Monorepo: Yarn 4 workspaces

## Notes
- Hugging Face free models are limited or require payment before API access.
- OpenRouter free models (like DeepSeek) may hit rate limits (429). Retry logic may be required.
- Only FastAPI backend (apps/backend-py) is supported; the Node backend has been removed.

## License
MIT
