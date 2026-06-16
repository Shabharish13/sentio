from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from app.config import REPO_ROOT

KB_DIR = REPO_ROOT / "kb"
DEFAULT_PERSIST_DIR = REPO_ROOT / "backend" / ".chroma"
COLLECTION_NAME = "sentio_kb"


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str
    score: float  # cosine similarity in [0, 1]


def chunk_markdown(text: str, source: str) -> list[tuple[str, str]]:
    """Split a KB markdown file into one chunk per `##` section, each prefixed
    with the document title so a retrieved chunk carries its own context."""
    title_match = re.search(r"(?m)^#\s+(.+)$", text)
    title = title_match.group(1).strip() if title_match else source
    sections = re.split(r"(?m)^##\s+", text)
    chunks: list[tuple[str, str]] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        chunks.append((f"[{title}]\n{section}", source))
    return chunks


def build_index(kb_dir=KB_DIR, *, client=None, embedding_function=None, reset: bool = True) -> "Retriever":
    """Ingest kb/*.md into a Chroma collection (cosine). Production uses the default
    MiniLM embedder; tests inject an ephemeral client + a toy embedding function."""
    client = client or chromadb.PersistentClient(path=str(DEFAULT_PERSIST_DIR))
    ef = embedding_function or DefaultEmbeddingFunction()
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
    collection = client.get_or_create_collection(
        COLLECTION_NAME, embedding_function=ef,
        configuration={"hnsw": {"space": "cosine"}},
    )
    ids, docs, metas = [], [], []
    for md in sorted(Path(kb_dir).glob("*.md")):
        for i, (chunk, source) in enumerate(chunk_markdown(md.read_text(encoding="utf-8"), md.name)):
            ids.append(f"{md.name}:{i}")
            docs.append(chunk)
            metas.append({"source": source})
    if docs:
        collection.add(ids=ids, documents=docs, metadatas=metas)
    return Retriever(collection)


class Retriever:
    def __init__(self, collection) -> None:
        self._collection = collection

    def retrieve(self, query: str, k: int = 4) -> list[Chunk]:
        count = self._collection.count()
        if count == 0:
            return []
        result = self._collection.query(query_texts=[query], n_results=min(k, count))
        docs = result["documents"][0]
        metas = result["metadatas"][0]
        dists = result["distances"][0]
        return [
            Chunk(text=d, source=m.get("source", ""), score=1.0 - float(dist))
            for d, m, dist in zip(docs, metas, dists)
        ]


def get_retriever(persist_dir=DEFAULT_PERSIST_DIR) -> Retriever:
    """Load the persisted production index (default MiniLM embedder)."""
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_collection(COLLECTION_NAME, embedding_function=DefaultEmbeddingFunction())
    return Retriever(collection)
