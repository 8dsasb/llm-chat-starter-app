import { Chat } from "@/components/chat/chat";

const App = () => {
  return (
    <div className="flex flex-col h-screen">
      <header className="border-b bg-background flex items-center justify-center h-14 w-full flex-none">
        <h1 className="text-lg font-semibold">
          Brainfish Chat{" "}
          <span className="text-sm text-muted-foreground">v1.0</span>
        </h1>
      </header>
      <main className="flex-1 min-h-0">
        <Chat />
      </main>
    </div>
  );
};

export default App;
