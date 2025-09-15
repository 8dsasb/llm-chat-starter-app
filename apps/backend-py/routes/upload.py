from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from uuid import uuid4
import PyPDF2
import docx
from db import get_session
from services import providers
from models.chat_history import ChatHistory
from models.file_context import FileContext   # ✅ new model
from sqlmodel import delete
from services.hf_provider import summarize_text  # ✅ Hugging Face summarizer

router = APIRouter()

UPLOAD_RAW_THRESHOLD = 2000  # chars

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), session_id: str | None = None):
    try:
        content = ""
        if file.filename.endswith(".txt"):
            content = (await file.read()).decode("utf-8")
        elif file.filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(file.file)
            for page in reader.pages:
                content += page.extract_text() or ""
        elif file.filename.endswith(".docx"):
            doc = docx.Document(file.file)
            content = "\n".join([p.text for p in doc.paragraphs])
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # generate session id if not provided
        sid = session_id or str(uuid4())

        processed_text = content
        # summarise if content is too large
        if len(content) > UPLOAD_RAW_THRESHOLD:
            try:
                processed_text = await summarize_text(content, max_tokens=500)
                meta_msg = f"📎 {file.filename} uploaded — summarised and added to context."
            except Exception as e:
                # fallback: store truncated content if summarisation fails
                processed_text = content[:UPLOAD_RAW_THRESHOLD]
                meta_msg = f"📎 {file.filename} uploaded (partial content stored, summarisation failed). Error: {str(e)}"
        else:
            meta_msg = f"📎 {file.filename} uploaded and added to context."

        with get_session() as session:
            # save clean metadata message to chat history
            providers.save_history(session, sid, role="system", content=meta_msg)

            # save file text (full or summary) into FileContext
            file_entry = FileContext(session_id=sid, filename=file.filename, content=processed_text)
            session.add(file_entry)
            session.commit()

        return {
            "session_id": sid,
            "filename": file.filename,
            "status": "saved"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@router.delete("/upload/clear")
async def clear_uploaded_files(session_id: str = Query(...)):
    try:
        with get_session() as session:
            # clear system messages about files
            session.exec(
                delete(ChatHistory).where(
                    (ChatHistory.session_id == session_id) &
                    (ChatHistory.role == "system") &
                    (ChatHistory.content.like("📎%"))
                )
            )
            # clear stored file contexts
            session.exec(
                delete(FileContext).where(FileContext.session_id == session_id)
            )
            session.commit()
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear files: {str(e)}")
