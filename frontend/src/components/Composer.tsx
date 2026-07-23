import { useRef, useState } from "react";

export function Composer({
  onSend,
  disabled,
}: {
  onSend: (q: string) => void;
  disabled: boolean;
}) {
  const [value, setValue] = useState("");
  const taRef = useRef<HTMLTextAreaElement>(null);

  function submit() {
    const q = value.trim();
    if (!q || disabled) return;
    onSend(q);
    setValue("");
    taRef.current?.focus();
  }

  return (
    <div className="composer">
      <textarea
        ref={taRef}
        className="composer__input"
        placeholder="Ask a question about your documents…"
        value={value}
        rows={1}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
      />
      <button className="composer__send" onClick={submit} disabled={disabled || !value.trim()}>
        {disabled ? "…" : "Ask"}
      </button>
    </div>
  );
}
