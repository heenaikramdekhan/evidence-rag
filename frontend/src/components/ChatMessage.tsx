import type { Citation } from "../api";
import { CitationList } from "./CitationList";

export interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
  usedContext?: boolean;
  latencyMs?: number;
  error?: boolean;
}

export function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className={`msg ${isUser ? "msg--user" : "msg--assistant"}`}>
      <div className="msg__avatar">{isUser ? "You" : "RAG"}</div>
      <div className="msg__body">
        <div className={`msg__bubble ${message.error ? "msg__bubble--error" : ""}`}>
          {renderWithCitations(message.text)}
        </div>
        {!isUser && message.citations && (
          <CitationList citations={message.citations} />
        )}
        {!isUser && message.latencyMs != null && (
          <div className="msg__meta">
            {message.usedContext === false ? "refused · " : ""}
            {Math.round(message.latencyMs)} ms
          </div>
        )}
      </div>
    </div>
  );
}

// Highlight inline [n] citation markers produced by the model.
function renderWithCitations(text: string) {
  const parts = text.split(/(\[\d+\])/g);
  return parts.map((part, i) =>
    /^\[\d+\]$/.test(part) ? (
      <sup key={i} className="cite-marker">
        {part}
      </sup>
    ) : (
      <span key={i}>{part}</span>
    ),
  );
}
