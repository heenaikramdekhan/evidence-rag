import { useEffect, useState } from "react";
import {
  getDocumentChunks,
  getDocuments,
  type Chunk,
  type DocumentsResponse,
} from "../api";

// Pick a small glyph per file type so the list scans quickly.
function iconFor(source: string): string {
  const ext = source.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return "📄";
  if (ext === "md" || ext === "markdown") return "📝";
  if (ext === "html" || ext === "htm") return "🌐";
  return "📃";
}

export function DocumentsPanel({
  open,
  onClose,
  refreshKey,
}: {
  open: boolean;
  onClose: () => void;
  refreshKey: number; // bump to reload after an upload / re-ingest
}) {
  const [data, setData] = useState<DocumentsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [chunks, setChunks] = useState<Record<string, Chunk[]>>({});
  const [loading, setLoading] = useState<string | null>(null);
  const [viewError, setViewError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    getDocuments()
      .then((d) => {
        setData(d);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"));
  }, [open, refreshKey]);

  // A fresh ingest can rename/replace files — drop any cached chunk views.
  useEffect(() => {
    setChunks({});
    setExpanded(null);
  }, [refreshKey]);

  async function toggle(source: string) {
    if (expanded === source) {
      setExpanded(null);
      return;
    }
    setExpanded(source);
    setViewError(null);
    if (chunks[source]) return; // already fetched
    setLoading(source);
    try {
      const res = await getDocumentChunks(source);
      setChunks((c) => ({ ...c, [source]: res.chunks }));
    } catch (e) {
      setViewError(e instanceof Error ? e.message : "Failed to load document");
      setExpanded(null);
    } finally {
      setLoading(null);
    }
  }

  return (
    <>
      <div className={`drawer__scrim ${open ? "is-open" : ""}`} onClick={onClose} />
      <aside className={`drawer ${open ? "is-open" : ""}`}>
        <div className="drawer__head">
          <span>Documents</span>
          <button className="drawer__close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <div className="drawer__body">
          {error && <p className="drawer__empty">{error}</p>}
          {!error && data && data.documents.length === 0 && (
            <p className="drawer__empty">
              No documents yet. Use <strong>Upload</strong> to add PDF, Markdown,
              HTML or TXT files.
            </p>
          )}
          {!error && data && data.documents.length > 0 && (
            <>
              <p className="doc-summary">
                {data.total_documents} document(s) · {data.total_chunks} chunk(s)
                {" · click to view"}
              </p>
              {data.documents.map((d) => {
                const isOpen = expanded === d.source;
                return (
                  <div key={d.source} className="doc">
                    <button
                      className={`doc-item ${isOpen ? "is-open" : ""}`}
                      onClick={() => toggle(d.source)}
                      aria-expanded={isOpen}
                    >
                      <span className="doc-item__icon">{iconFor(d.source)}</span>
                      <span className="doc-item__name" title={d.source}>
                        {d.source}
                      </span>
                      <span className="doc-item__chunks">
                        {d.chunks} chunk{d.chunks === 1 ? "" : "s"}
                      </span>
                      <span className="doc-item__caret">{isOpen ? "▾" : "▸"}</span>
                    </button>

                    {isOpen && (
                      <div className="doc-view">
                        {loading === d.source && (
                          <p className="doc-view__hint">Loading…</p>
                        )}
                        {viewError && (
                          <p className="doc-view__hint">{viewError}</p>
                        )}
                        {chunks[d.source]?.map((c) => (
                          <div key={c.id} className="doc-chunk">
                            <span className="doc-chunk__label">
                              chunk {c.chunk_index}
                            </span>
                            <p className="doc-chunk__text">{c.text}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </>
          )}
        </div>
      </aside>
    </>
  );
}
