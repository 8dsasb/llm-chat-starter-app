# LLM Chat App (FastAPI + React)

A modern chat application built with **React (Vite + TypeScript)** and a new **Python FastAPI backend** that streams responses via **Server-Sent Events (SSE)**.  
This project extends the [starter app](https://github.com/brainfish-ai/llm-chat-starter-app).

---

## 📂 Project Structure
```
llm-chat-starter-app/
├── apps/
│   ├── frontend/      # Vite + React + shadcn/ui components
│   ├── backend/       # Original Node backend (not used now)
│   └── backend-py/    # New FastAPI backend with SSE + history
```

---

## ✨ Features
- **Chat with LLMs**
  - Providers: `mock`, `openai`, `openrouter`
  - Streaming responses via SSE
- **Conversation History**
  - Persistent SQLite DB using SQLModel
  - Sessions keyed by `session_id`
  - REST endpoint: `GET /api/history/{session_id}`
- **Session Persistence**
  - `session_id` stored in `localStorage`
  - Conversations survive page refreshes
- **New Chat Button**
  - Clears current messages and session
  - Starts a fresh conversation (like ChatGPT)

---

## 🔧 Prerequisites
- Node.js (v18+)  
- Yarn (v4)  
- Python 3.10+ with `venv`  
- (Optional) OpenRouter or OpenAI API key  

---

## 🚀 Setup Instructions

### 1. Clone & Install
```bash
git clone https://github.com/8dsasb/llm-chat-starter-app.git
cd llm-chat-starter-app
yarn install
```

### 2. Backend Setup
```bash
cd apps/backend-py
python -m venv .venv
.venv\Scripts\activate     # Windows
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
```env
PROVIDER=mock   # mock | openai | openrouter
```

### 3. Start Dev Servers
From the **repo root**:
```bash
yarn dev
```
- Frontend → http://localhost:5173  
- Backend → http://localhost:3000  

---

## 🔌 API Endpoints

- **Health check**  
  `GET /health` → `{ "ok": true, "provider": "mock" }`

- **Chat (SSE)**  
  `POST /api/chat`  
  ```json
  {
    "session_id": "1234", // optional
    "messages": [{ "role": "user", "content": "hello" }]
  }
  ```

- **Conversation history**  
  `GET /api/history/{session_id}` → returns saved messages

---

## 🛠 Enhancement
This fork implements **Conversation History** as the chosen enhancement:
- Messages persisted in SQLite
- Sessions persist across reloads
- “New Chat” button resets session

---

## 🧰 Technologies
- **Frontend:** Vite, React, TypeScript, shadcn/ui  
- **Backend:** FastAPI, Uvicorn, SQLModel (SQLite)  
- **LLM Integration:** Mock, OpenAI, OpenRouter  
- **Monorepo:** Yarn 4 workspaces  

---

## 📜 License
MIT
