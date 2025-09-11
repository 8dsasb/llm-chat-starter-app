import { useMessages } from "@/store/messages";

export const ClearChatButton = () => {
  const clearMessages = useMessages((state) => state.clearMessages);

  const handleClear = () => {
    // Remove session id so backend starts a new one
    localStorage.removeItem("bf_session_id");
    // Clear current messages in UI
    clearMessages();
  };

  return (
    <button
      onClick={handleClear}
      className="px-4 py-2 rounded-md bg-green-500 text-white hover:bg-red-600"
    >
      New Chat
    </button>
  );
};
