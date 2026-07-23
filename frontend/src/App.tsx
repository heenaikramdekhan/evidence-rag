import { useEffect, useState } from "react";
import { askQuestion, getStats, type HistoryItem, type Stats } from "./api";
import { ChatMessage, type Message } from "./components/ChatMessage";
import { Composer } from "./components/Composer";
import { HistoryPanel } from "./components/HistoryPanel";
import { RetrievalInspector } from "./components/RetrievalInspector";
import { UploadDialog } from "./components/UploadDialog";
import "./App.css";

let counter = 0;
const nextId = () => `m${counter++}`;

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const [stats, setStats] = useState<Stats | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyKey, setHistoryKey] = useState(0);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [inspectOpen, setInspectOpen] = useState(false);

  function refreshStats() {
    getStats().then(setStats).catch(() => setStats(null));
  }

  useEffect(refreshStats, []);

  function loadFromHistory(item: HistoryItem) {
    setMessages([
      { id: nextId(), role: "user", text: item.question },
      {
        id: nextId(),
        role: "assistant",
        text: item.answer,
        citations: item.citations,
        usedContext: item.used_context,
        latencyMs: item.latency_ms ?? undefined,
      },
    ]);
  }

  async function handleSend(question: string) {
    setMessages((m) => [...m, { id: nextId(), role: "user", text: question }]);
    setBusy(true);
    try {
      const resp = await askQuestion(question);
      setMessages((m) => [
        ...m,
        {
          id: nextId(),
          role: "assistant",
          text: resp.answer,
          citations: resp.citations,
          usedContext: resp.used_context,
          latencyMs: resp.latency_ms,
        },
      ]);
      setHistoryKey((k) => k + 1); // new query recorded server-side
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          id: nextId(),
          role: "assistant",
          text: err instanceof Error ? err.message : "Request failed.",
          error: true,
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header className="app__header">
        <div className="app__title">
          <span className="app__logo">◆</span> Evidence-RAG
        </div>
        <div className="app__header-right">
          {stats && (
            <div className="app__stats">
              <span>{stats.chunks} chunks</span>
              <span className="dot" />
              <span>{stats.llm_provider}</span>
            </div>
          )}
          <button className="app__history-btn" onClick={() => setInspectOpen(true)}>
            Inspect
          </button>
          <button className="app__history-btn" onClick={() => setUploadOpen(true)}>
            Upload
          </button>
          <button className="app__history-btn" onClick={() => setHistoryOpen(true)}>
            History
          </button>
        </div>
      </header>

      <main className="app__chat">
        {messages.length === 0 && (
          <div className="empty">
            <h1>Ask your documents anything</h1>
            <p>
              Answers are grounded in your ingested corpus with inline citations —
              and the system refuses when the evidence isn&apos;t there.
            </p>
          </div>
        )}
        {messages.map((m) => (
          <ChatMessage key={m.id} message={m} />
        ))}
        {busy && (
          <div className="msg msg--assistant">
            <div className="msg__avatar">RAG</div>
            <div className="msg__body">
              <div className="msg__bubble typing">
                <span />
                <span />
                <span />
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="app__footer">
        <Composer onSend={handleSend} disabled={busy} />
        <div className="app__hint">Enter to send · Shift+Enter for newline</div>
      </footer>

      <HistoryPanel
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        onSelect={loadFromHistory}
        refreshKey={historyKey}
      />

      <UploadDialog
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onUploaded={refreshStats}
      />

      <RetrievalInspector open={inspectOpen} onClose={() => setInspectOpen(false)} />
    </div>
  );
}
