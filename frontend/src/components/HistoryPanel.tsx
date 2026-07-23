import { useEffect, useState } from "react";
import { clearHistory, getHistory, type HistoryItem } from "../api";

export function HistoryPanel({
  open,
  onClose,
  onSelect,
  refreshKey,
}: {
  open: boolean;
  onClose: () => void;
  onSelect: (item: HistoryItem) => void;
  refreshKey: number; // bump to reload after a new query
}) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    getHistory()
      .then((h) => {
        setItems(h);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"));
  }, [open, refreshKey]);

  async function handleClear() {
    if (!confirm("Delete all query history?")) return;
    await clearHistory();
    setItems([]);
  }

  return (
    <>
      <div
        className={`drawer__scrim ${open ? "is-open" : ""}`}
        onClick={onClose}
      />
      <aside className={`drawer ${open ? "is-open" : ""}`}>
        <div className="drawer__head">
          <span>History</span>
          <div className="drawer__actions">
            {items.length > 0 && (
              <button className="drawer__clear" onClick={handleClear}>
                Clear
              </button>
            )}
            <button className="drawer__close" onClick={onClose} aria-label="Close">
              ×
            </button>
          </div>
        </div>

        <div className="drawer__body">
          {error && <p className="drawer__empty">{error}</p>}
          {!error && items.length === 0 && (
            <p className="drawer__empty">No queries yet.</p>
          )}
          {items.map((item) => (
            <button
              key={item.id}
              className="history-item"
              onClick={() => {
                onSelect(item);
                onClose();
              }}
            >
              <span className="history-item__q">{item.question}</span>
              <span className="history-item__meta">
                {item.used_context ? "answered" : "refused"} ·{" "}
                {new Date(item.created_at).toLocaleString()}
              </span>
            </button>
          ))}
        </div>
      </aside>
    </>
  );
}
