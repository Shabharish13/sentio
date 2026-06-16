import numpy as np
import chromadb
from chromadb.api.types import EmbeddingFunction

from app.rag.store import Chunk, Retriever, build_index, chunk_markdown


class ToyEF(EmbeddingFunction):
    """Deterministic offline embedding (letter-frequency) — no model download."""

    def __init__(self):
        pass

    def __call__(self, input):
        return [
            np.array([float(t.lower().count(c)) for c in "abcdefghijklmnopqrstuvwxyz"],
                     dtype=np.float32)
            for t in input
        ]

    @staticmethod
    def name():
        return "toy"

    def get_config(self):
        return {}

    @staticmethod
    def build_from_config(config):
        return ToyEF()


def test_chunk_markdown_splits_sections_and_prepends_title():
    md = "# Pricing\n\nIntro line.\n\n## Starter\n$18k/yr.\n\n## Growth\n$36k/yr.\n"
    chunks = chunk_markdown(md, "pricing-tiers.md")
    assert len(chunks) >= 2
    assert all(src == "pricing-tiers.md" for _text, src in chunks)
    assert all(text.startswith("[Pricing]") for text, _src in chunks)
    assert any("Starter" in text for text, _src in chunks)


def test_build_index_and_retrieve_returns_scored_chunks(tmp_path):
    (tmp_path / "pricing.md").write_text(
        "# Pricing\n\n## Tiers\nstarter growth enterprise pricing tiers.\n", encoding="utf-8")
    (tmp_path / "security.md").write_text(
        "# Security\n\n## Compliance\nsoc2 gdpr encryption security review.\n", encoding="utf-8")

    retriever = build_index(
        kb_dir=tmp_path, client=chromadb.EphemeralClient(),
        embedding_function=ToyEF(),
    )
    results = retriever.retrieve("[Pricing]\nstarter growth enterprise pricing tiers.", k=2)
    assert results and isinstance(results[0], Chunk)
    assert results[0].source == "pricing.md"
    assert results[0].score > 0.99
    assert len(results) == 2


def test_retrieve_on_empty_collection_returns_empty():
    r = Retriever(chromadb.EphemeralClient().get_or_create_collection(
        "emptycol", embedding_function=ToyEF()))
    assert r.retrieve("anything", k=3) == []
