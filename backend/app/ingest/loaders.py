"""Document loaders: turn PDF / Markdown / HTML / text files into plain text.

Kept deliberately dependency-light so the pipeline runs on a CPU laptop with
no heavyweight `unstructured` install. Each loader returns a single string;
chunking happens downstream in ``chunker.py``.
"""
from __future__ import annotations

from pathlib import Path

SUPPORTED_SUFFIXES = {".pdf", ".md", ".markdown", ".html", ".htm", ".txt"}


def load_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def load_markdown(path: Path) -> str:
    from markdown_it import MarkdownIt
    from bs4 import BeautifulSoup

    raw = path.read_text(encoding="utf-8", errors="ignore")
    html = MarkdownIt().render(raw)
    return BeautifulSoup(html, "html.parser").get_text("\n")


def load_html(path: Path) -> str:
    from bs4 import BeautifulSoup

    raw = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text("\n")


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


_LOADERS = {
    ".pdf": load_pdf,
    ".md": load_markdown,
    ".markdown": load_markdown,
    ".html": load_html,
    ".htm": load_html,
    ".txt": load_text,
}


def load_document(path: Path) -> str:
    """Load a single file into normalized plain text."""
    suffix = path.suffix.lower()
    if suffix not in _LOADERS:
        raise ValueError(f"Unsupported file type: {suffix}")
    text = _LOADERS[suffix](path)
    return _normalize(text)


def load_directory(directory: Path) -> dict[str, str]:
    """Load every supported document in a directory. Returns {filename: text}."""
    docs: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            try:
                docs[path.name] = load_document(path)
            except Exception as exc:  # noqa: BLE001 - keep ingesting the rest
                print(f"[loaders] skipping {path.name}: {exc}")
    return docs


def _normalize(text: str) -> str:
    # Collapse runs of blank lines and trailing whitespace; keep paragraph breaks.
    lines = [line.rstrip() for line in text.splitlines()]
    out: list[str] = []
    blank = False
    for line in lines:
        if line.strip():
            out.append(line)
            blank = False
        elif not blank:
            out.append("")
            blank = True
    return "\n".join(out).strip()
