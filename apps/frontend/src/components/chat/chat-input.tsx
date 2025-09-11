import { Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useMessages } from "@/store/messages";

interface ChatInputProps {
  onTypingChange: (isTyping: boolean) => void;
}

const SESSION_KEY = "bf_session_id";

function getSessionId(): string {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    const gen =
      (globalThis.crypto?.randomUUID?.() as string | undefined) ??
      Math.random().toString(36).slice(2) + Date.now().toString(36);
    id = gen;
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

export const ChatInput = ({ onTypingChange }: ChatInputProps) => {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { messages, addMessage, updateLastMessage } = useMessages();
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when loading state changes to false
  useEffect(() => {
    if (!isLoading) {
      inputRef.current?.focus();
    }
    onTypingChange(isLoading);
  }, [isLoading, onTypingChange]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || isLoading) return;

    // Add user message
    addMessage({
      role: "user",
      content: input,
    });

    // Add empty assistant message that will be streamed
    addMessage({
      role: "assistant",
      content: "",
    });

    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: getSessionId(),
          messages: [...messages, { role: "user", content: input }],
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No reader available");

      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.content) {
                updateLastMessage(data.content);
              }
            } catch (e) {
              console.error("Error parsing SSE data:", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Error:", error);
      updateLastMessage("Sorry, there was an error processing your request.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex w-full items-center space-x-3 bg-muted rounded-lg p-4"
    >
      <Input
        ref={inputRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type your message..."
        className="flex-1 px-4 py-6 text-base"
        disabled={isLoading}
      />
      <Button type="submit" className="size-12" disabled={isLoading}>
        <Send className="h-4 w-4" />
      </Button>
    </form>
  );
};
