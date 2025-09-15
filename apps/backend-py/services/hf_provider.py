import os
import httpx
from typing import List, Dict, AsyncGenerator

# Load Hugging Face credentials and model
HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("HF_MODEL", "google/flan-t5-base")  # default to a free model

print("Using Hugging Face model:", HF_MODEL)

async def call_hf(messages: List[Dict[str, str]]) -> str:
    """
    Send conversation messages to Hugging Face Inference API
    and return a generated response. Works with any text-generation or summarization model.
    """
    if not HF_API_KEY:
        raise ValueError("HF_API_KEY is missing")

    # Build a simple prompt from conversation
    prompt = ""
    for m in messages:
        prompt += f"{m.role.capitalize()}: {m.content}\n"
    prompt += "Assistant:"

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 512, "temperature": 0.7},
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"https://api-inference.huggingface.co/models/{HF_MODEL}",
            headers=headers,
            json=payload,
        )

    if resp.status_code != 200:
        raise RuntimeError(f"Hugging Face API error {resp.status_code}: {resp.text}")

    result = resp.json()

    # Case 1: generative models
    if isinstance(result, list) and len(result) > 0 and "generated_text" in result[0]:
        return result[0]["generated_text"].replace(prompt, "").strip()

    # Case 2: summarization models
    if isinstance(result, list) and len(result) > 0 and "summary_text" in result[0]:
        return result[0]["summary_text"].strip()
    
    # Debug fallback
    print("HF raw response:", result)

    return str(result)

async def stream_hf(messages: List[Dict[str, str]], session_id: str, session) -> AsyncGenerator[str, None]:
    """
    Fake streaming for Hugging Face models (API only returns full responses).
    Breaks the full response into chunks to mimic SSE.
    """
    text = await call_hf(messages)

    # Yield in small chunks to simulate streaming tokens
    for i in range(0, len(text), 50):
        yield f"data: {text[i:i+50]}\n\n"
    yield "data: [DONE]\n\n"

async def summarize_text(text: str, max_tokens: int = 300) -> str:
    """
    Summarize large file content using Hugging Face model.
    Falls back to the model defined in HF_MODEL.
    """
    if not HF_API_KEY:
        raise ValueError("HF_API_KEY is missing")

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": f"Summarize the following text:\n\n{text}",
        "parameters": {"max_new_tokens": max_tokens},
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"https://api-inference.huggingface.co/models/{HF_MODEL}",
            headers=headers,
            json=payload,
        )

    if resp.status_code != 200:
        raise RuntimeError(f"Hugging Face API error {resp.status_code}: {resp.text}")

    result = resp.json()

    if isinstance(result, list) and len(result) > 0:
        if "generated_text" in result[0]:
            return result[0]["generated_text"].strip()
        if "summary_text" in result[0]:
            return result[0]["summary_text"].strip()

    return str(result)
