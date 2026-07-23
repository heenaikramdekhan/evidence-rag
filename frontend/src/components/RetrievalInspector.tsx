import { useState } from "react";
import { retrieveChunks, type Chunk } from "../api";

export function RetrievalInspector({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [query, setQuery] = useState("");
  const [chunks, setChunks] = useState<Chunk[] | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    const q = query.trim();
    if (!q || busy) return;
    setBusy(true);
    setError(null);
    try {
      const res = await retrieveChunks(q);
      setChunks(res.chunks);
      setLatency(res.latency_ms);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Retrieval failed");
      setChunks(null);
    } finally {
      setBusy(false);
    }
  }

  // Normalize scores to 0..1 for the relative bars (cross-encoder scores can be
  // negative, so we scale against the min/max of the current result set).
  const scores = (chunks ?? []).map((c) => c.score ?? 0);
  const min = Math.min(...scores, 0);
  const max = Math.max(...scores, 1);
  const norm = (s: number | null) =>
    max === min ? 1 : ((s ?? 0) - min) / (max - min);

  return (
    <>
      <div className={`drawer__scrim ${open ? "is-open" : ""}`} onClick={onClose} />
      <aside className={`drawer drawer--wide ${open ? "is-open" : ""}`}>
        <div className="drawer__head">
          <span>Retrieval inspector</span>
          <button className="drawer__close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <div className="inspector__search">
          <input
            className="inspector__input"
            placeholder="Query to inspect (no LLM call)…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && run()}
          />
          <button className="inspector__btn" onClick={run} disabled={busy || !query.trim()}>
            {busy ? "…" : "Retrieve"}
          </button>
        </div>

        <div className="drawer__body">
          {error && <p className="drawer__empty">{error}</p>}
          {!error && chunks == null && (
            <p className="drawer__empty">
              Enter a query to see the ranked chunks and their rerank scores.
            </p>
          )}
          {!error && chunks != null && (
            <>
              <p className="inspector__meta">
                {chunks.length} chunk(s) · {Math.round(latency ?? 0)} ms · hybrid + rerank
              </p>
              {chunks.length === 0 && <p className="drawer__empty">No matches.</p>}
              {chunks.map((c, i) => (
                <div key={c.id} className="rchunk">
                  <div className="rchunk__head">
                    <span className="rchunk__rank">{i + 1}</span>
                    <span className="rchunk__source">
                      {c.source}
                      <span className="rchunk__idx"> · chunk {c.chunk_index}</span>
                    </span>
                    <span className="rchunk__score">
                      {c.score != null ? c.score.toFixed(3) : "—"}
                    </span>
                  </div>
                  <div className="rchunk__bar">
                    <div
                      className="rchunk__bar-fill"
                      style={{ width: `${Math.round(norm(c.score) * 100)}%` }}
                    />
                  </div>
                  <p className="rchunk__text">{c.text}</p>
                </div>
              ))}
            </>
          )}
        </div>
      </aside>
    </>
  );
}
