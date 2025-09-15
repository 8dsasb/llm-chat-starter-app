from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import health, chat, history
from routes import upload
from db import init_db

app = FastAPI(title="Brainfish Chat (FastAPI)")
init_db() 
app.include_router(upload.router, prefix="/api")

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
