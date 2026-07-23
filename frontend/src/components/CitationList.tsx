import { useState } from "react";
import type { Citation } from "../api";

export function CitationList({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) return null;
  return (
    <div className="citations">
      <div className="citations__label">Sources</div>
      <ol className="citations__list">
        {citations.map((c, i) => (
          <CitationItem key={c.id} index={i + 1} citation={c} />
        ))}
      </ol>
    </div>
  );
}

function CitationItem({ index, citation }: { index: number; citation: Citation }) {
  const [open, setOpen] = useState(false);
  const score = citation.score != null ? citation.score.toFixed(2) : null;
  return (
    <li className="citation">
      <button className="citation__head" onClick={() => setOpen((o) => !o)}>
        <span className="citation__badge">{index}</span>
        <span className="citation__source">
          {citation.source}
          <span className="citation__chunk"> · chunk {citation.chunk_index}</span>
        </span>
        {score && <span className="citation__score">{score}</span>}
        <span className="citation__toggle">{open ? "−" : "+"}</span>
      </button>
      {open && <p className="citation__text">{citation.text}</p>}
    </li>
  );
}
