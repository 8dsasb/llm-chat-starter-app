import json

def sse_line(payload: dict) -> bytes:
    return f"data: {json.dumps(payload)}\n\n".encode("utf-8")
