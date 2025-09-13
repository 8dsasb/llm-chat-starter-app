from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import health, chat, history

app = FastAPI(title="Brainfish Chat (FastAPI)")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health.router)
app.include_router(chat.router, prefix="/api")
app.include_router(history.router, prefix="/api")
