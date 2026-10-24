"""Load markdown documents and split them into section-level chunks with metadata."""
import re
from dataclasses import dataclass
from pathlib import Path

INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior) instructions",
    r"disregard (the )?(system|above)",
    r"you are now",
]


@dataclass
class Chunk:
    chunk_id: str   # "<doc_id>#<section-slug>"
    doc_id: str
    section: str
    text: str       # includes doc header context so names/dates are searchable
    flagged: bool = False


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def load_chunks(corpus_dir: str | Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(Path(corpus_dir).glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        lines = raw.splitlines()
        title = lines[0].lstrip("# ").strip() if lines else path.stem
        m = re.search(r"Document ID:\s*([A-Z0-9\-]+)", raw)
        doc_id = m.group(1) if m else path.stem
        header = next((l for l in lines if l.startswith("Document ID:")), "")
        parts = re.split(r"^## ", raw, flags=re.M)
        for part in parts[1:]:
            heading, _, body = part.partition("\n")
            text = f"{title} | {header}\nSection: {heading.strip()}\n{body.strip()}"
            flagged = any(re.search(p, body, re.I) for p in INJECTION_PATTERNS)
            chunks.append(Chunk(f"{doc_id}#{_slug(heading)}", doc_id, heading.strip(), text, flagged))
    return chunks
