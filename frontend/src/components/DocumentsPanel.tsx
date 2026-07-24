import { useEffect, useState } from "react";
import { getDocuments, type DocumentsResponse } from "../api";

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

  useEffect(() => {
    if (!open) return;
    getDocuments()
      .then((d) => {
        setData(d);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"));
  }, [open, refreshKey]);

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
              </p>
              {data.documents.map((d) => (
                <div key={d.source} className="doc-item">
                  <span className="doc-item__icon">{iconFor(d.source)}</span>
                  <span className="doc-item__name" title={d.source}>
                    {d.source}
                  </span>
                  <span className="doc-item__chunks">
                    {d.chunks} chunk{d.chunks === 1 ? "" : "s"}
                  </span>
                </div>
              ))}
            </>
          )}
        </div>
      </aside>
    </>
  );
}
