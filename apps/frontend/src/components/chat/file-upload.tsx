import React from "react";
import { useMessages } from "@/store/messages";

export const FileUpload = () => {
  const { addMessage } = useMessages();

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.currentTarget.files?.length) return;
    const file = e.currentTarget.files[0];

    const formData = new FormData();
    formData.append("file", file);

    // attach current session id
    const sessionId = localStorage.getItem("bf_session_id");
    if (sessionId) {
      formData.append("session_id", sessionId);
    }

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();

        // if backend generated a new session id, update it
        if (data.session_id) {
          localStorage.setItem("bf_session_id", data.session_id);
        }

        // Push a system message into chat UI
        addMessage({
          role: "system",
          content: `📎 ${data.filename} uploaded and added to context.`,
        });
      } else {
        addMessage({
          role: "system",
          content: `❌ File upload failed: ${file.name}`,
        });
      }
    } catch (err) {
      addMessage({
        role: "system",
        content: `❌ Upload error: ${(err as Error).message}`,
      });
    }
  };
  const handleClearFiles = async () => {
  const sessionId = localStorage.getItem("bf_session_id");
  if (!sessionId) return;

  try {
    const res = await fetch(`/api/upload/clear?session_id=${sessionId}`, {
      method: "DELETE",
    });

    if (res.ok) {
      addMessage({
        role: "system",
        content: "🗑️ All uploaded files removed from context.",
      });
    } else {
      addMessage({
        role: "system",
        content: "❌ Failed to clear uploaded files.",
      });
    }
  } catch (err) {
    addMessage({
      role: "system",
      content: `❌ Error clearing files: ${(err as Error).message}`,
    });
  }
};

  return (
    <div className="p-2 space-x-2">
      <input type="file" onChange={handleUpload} />
      <button
        onClick={handleClearFiles}
        className="bg-red-500 text-white px-3 py-1 rounded"
      >
        Clear Files
      </button>
    </div>
  );
};
