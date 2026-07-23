import { useRef, useState } from "react";
import { uploadFiles, type IngestResponse } from "../api";

const ACCEPT = ".pdf,.md,.markdown,.html,.htm,.txt";

export function UploadDialog({
  open,
  onClose,
  onUploaded,
}: {
  open: boolean;
  onClose: () => void;
  onUploaded: (result: IngestResponse) => void;
}) {
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<IngestResponse | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  if (!open) return null;

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await uploadFiles(files);
      setResult(res);
      onUploaded(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal__scrim" onClick={busy ? undefined : onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__head">
          <span>Add documents</span>
          <button className="modal__close" onClick={onClose} disabled={busy}>
            ×
          </button>
        </div>

        <div
          className={`dropzone ${dragging ? "is-drag" : ""} ${busy ? "is-busy" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            if (!busy) handleFiles(e.dataTransfer.files);
          }}
          onClick={() => !busy && inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            multiple
            accept={ACCEPT}
            hidden
            onChange={(e) => handleFiles(e.target.files)}
          />
          {busy ? (
            <p className="dropzone__hint">Uploading &amp; indexing…</p>
          ) : (
            <>
              <div className="dropzone__icon">⬆</div>
              <p className="dropzone__hint">
                Drag files here or <strong>click to browse</strong>
              </p>
              <p className="dropzone__sub">PDF · Markdown · HTML · TXT</p>
            </>
          )}
        </div>

        {error && <p className="modal__error">{error}</p>}
        {result && (
          <p className="modal__ok">
            Indexed {result.documents} document(s) → {result.chunks} chunk(s).
          </p>
        )}

        <p className="modal__note">
          Uploading re-indexes the whole corpus (replaces the current index).
        </p>
      </div>
    </div>
  );
}
