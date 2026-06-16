"""One-time: ingest kb/*.md into the persistent Chroma index (downloads the
MiniLM ONNX model on first run). Run from backend/: .venv/Scripts/python.exe -m scripts.build_kb_index"""
from __future__ import annotations

from app.rag.store import build_index


def main() -> None:
    retriever = build_index()  # default kb dir, default MiniLM embedder, persistent
    hits = retriever.retrieve("what are the pricing tiers?", k=3)
    print(f"Indexed. Top source for a pricing query: {hits[0].source if hits else 'NONE'}")
    for h in hits:
        print(f"  score={h.score:.3f}  {h.source}")


if __name__ == "__main__":
    main()
