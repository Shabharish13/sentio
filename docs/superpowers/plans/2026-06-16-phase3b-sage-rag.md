# Phase 3B — Sage Chat Agent + RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the KB RAG layer (ChromaDB over `kb/*.md`) and the Sage chat agent: retrieval-grounded answers from `sage_agent.md`, with cosine-similarity confidence gating that escalates to a human when the KB can't answer — turning the "dumb greeter" into a grounded assistant.

**Architecture:** New `app/rag/` package wraps a ChromaDB collection (cosine space). Markdown is chunked by section and embedded with ChromaDB's **default** embedding function (`all-MiniLM-L6-v2`, ONNX, local + free, **no torch**) in production; tests inject a tiny deterministic `EmbeddingFunction` + an ephemeral client so the suite stays fast and offline. `app/agents/sage.py` retrieves, gates on the top cosine score (<0.75 → escalate), and otherwise calls `get_llm()` with the `sage_agent.md` prompt populated with the retrieved context.

**Tech Stack:** `chromadb==1.5.9` (verified API), Python stdlib, pytest. Runs from `backend/` via `.venv/Scripts/python.exe`.

**Verified ChromaDB facts (1.5.9):**
- Collection names need 3–512 chars. Cosine via `configuration={"hnsw": {"space": "cosine"}}`.
- A custom embedding function must subclass `chromadb.api.types.EmbeddingFunction` and implement `__init__`, `__call__(self, input) -> list[np.ndarray]`, static `name()`, `get_config()`, static `build_from_config(config)`. A plain callable is rejected.
- `collection.query(query_texts=[q], n_results=n)` returns `{"documents":[[...]], "metadatas":[[...]], "distances":[[...]]}`. Cosine **similarity = 1 - distance**.
- `collection.count()` gives the size.

**Scope note:** Phase 3B delivers grounded answering + escalation (the core "not a dumb chatbot" value) and the RAG store. The full booking/nurture/disqualify **outcome routing + HubSpot hand-off on the chat path** is the chat-orchestration layer (a later, smaller piece, analogous to how the inbound orchestration is Phase 4) — not in this plan. The Sage prompt still drives the conversational qualifying question per turn.

---

## File Structure

```
backend/app/rag/
  __init__.py
  store.py           # chunk_markdown, build_index, Retriever, Chunk, get_retriever
backend/app/agents/
  sage.py            # SageResponse, answer(message, page, llm, retriever)
backend/scripts/
  build_kb_index.py  # one-time: ingest kb/*.md into the persistent Chroma index
backend/tests/
  test_rag_store.py
  test_agent_sage.py
```

---

## Task 1: RAG store (chunking + Chroma index + retriever)

**Files:**
- Modify: `backend/requirements.txt` (add `chromadb==1.5.9`)
- Create: `backend/app/rag/__init__.py`, `backend/app/rag/store.py`
- Modify: `/.gitignore` (ignore the Chroma persist dir)
- Test: `backend/tests/test_rag_store.py`

- [ ] **Step 1: Pin the dependency.** Add `chromadb==1.5.9` to `backend/requirements.txt` (after the `openai==2.41.1` line). It is already installed in the venv.

- [ ] **Step 2: Ignore the persist dir.** Append `backend/.chroma/` to the repo-root `.gitignore` (read it first, then add the line under the Local caches section).

- [ ] **Step 3: Create `backend/app/rag/__init__.py`** (single newline).

- [ ] **Step 4: Write the failing test** `backend/tests/test_rag_store.py`:

```python
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
    # one chunk per section (the preamble counts as a chunk too)
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
    # Query with the exact text of the pricing chunk -> identical embedding -> top, score ~1.
    results = retriever.retrieve("[Pricing]\nstarter growth enterprise pricing tiers.", k=2)
    assert results and isinstance(results[0], Chunk)
    assert results[0].source == "pricing.md"
    assert results[0].score > 0.99
    assert len(results) == 2  # k respected


def test_retrieve_on_empty_collection_returns_empty():
    r = Retriever(chromadb.EphemeralClient().get_or_create_collection(
        "emptycol", embedding_function=ToyEF()))
    assert r.retrieve("anything", k=3) == []
```

- [ ] **Step 5: Run, expect FAIL** (`ModuleNotFoundError: No module named 'app.rag.store'`).

Run: `cd /c/Users/Arunkumar/Documents/Docket-assignment/backend && .venv/Scripts/python.exe -m pytest tests/test_rag_store.py -v`

- [ ] **Step 6: Write `backend/app/rag/store.py`:**

```python
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
```

- [ ] **Step 7: Run, expect PASS (3 passed).**

Run: `.venv/Scripts/python.exe -m pytest tests/test_rag_store.py -v`

- [ ] **Step 8: Commit.**

```bash
git add backend/requirements.txt backend/app/rag backend/tests/test_rag_store.py .gitignore
git commit -m "feat(rag): ChromaDB KB store — section chunking, cosine retrieval, injectable embedder"
```

---

## Task 2: Sage chat agent

**Files:**
- Create: `backend/app/agents/sage.py`
- Test: `backend/tests/test_agent_sage.py`

- [ ] **Step 1: Write the failing test** `backend/tests/test_agent_sage.py`:

```python
from app.agents.sage import ESCALATION_MESSAGE, SageResponse, answer
from app.rag.store import Chunk


class StubLLM:
    def __init__(self, reply):
        self._reply = reply
        self.calls = []

    def complete(self, system, user, max_tokens=1024):
        self.calls.append((system, user))
        return self._reply


class StubRetriever:
    def __init__(self, chunks):
        self._chunks = chunks

    def retrieve(self, query, k=4):
        return list(self._chunks)


def test_grounded_answer_when_confident():
    chunks = [Chunk("[Pricing] Growth is $36k/yr.", "pricing-tiers.md", 0.91),
              Chunk("[Pricing] Starter is $18k/yr.", "pricing-tiers.md", 0.82)]
    llm = StubLLM("Growth is $36k/year. Are you evaluating for your own team, or a broader group?")
    resp = answer("how much is growth?", page="/pricing", llm=llm, retriever=StubRetriever(chunks))
    assert isinstance(resp, SageResponse)
    assert resp.escalated is False
    assert "36k" in resp.reply
    assert resp.sources == ["pricing-tiers.md", "pricing-tiers.md"]
    # the prompt was populated with retrieved context and the page
    system, _user = llm.calls[0]
    assert "Growth is $36k/yr." in system
    assert "/pricing" in system


def test_escalates_when_top_score_below_threshold():
    chunks = [Chunk("vaguely related", "faq-objections.md", 0.40)]
    llm = StubLLM("should not be called")
    resp = answer("do you integrate with SAP S/4HANA?", page="/pricing",
                  llm=llm, retriever=StubRetriever(chunks))
    assert resp.escalated is True
    assert resp.reply == ESCALATION_MESSAGE
    assert resp.sources == []
    assert llm.calls == []  # no LLM call on escalation


def test_escalates_when_no_chunks():
    resp = answer("anything", page="/demo", llm=StubLLM("x"), retriever=StubRetriever([]))
    assert resp.escalated is True
    assert resp.reply == ESCALATION_MESSAGE
```

- [ ] **Step 2: Run, expect FAIL** (`ModuleNotFoundError: No module named 'app.agents.sage'`).

Run: `.venv/Scripts/python.exe -m pytest tests/test_agent_sage.py -v`

- [ ] **Step 3: Write `backend/app/agents/sage.py`:**

```python
from __future__ import annotations

from dataclasses import dataclass

from app.clients.anthropic_client import load_prompt

# Canned escalation line from sage_agent.md's confidence-threshold rule.
ESCALATION_MESSAGE = (
    "That's a great question — I want to make sure you get accurate information. "
    "Let me connect you with our team."
)
CONFIDENCE_THRESHOLD = 0.75


@dataclass(frozen=True)
class SageResponse:
    reply: str
    escalated: bool
    sources: list[str]


def answer(message: str, page: str, llm, retriever,
           threshold: float = CONFIDENCE_THRESHOLD, k: int = 4) -> SageResponse:
    """Grounded chat turn: retrieve KB context, escalate when the top cosine score
    is below threshold (or nothing retrieved), otherwise answer via the Sage prompt."""
    chunks = retriever.retrieve(message, k=k)
    top_score = chunks[0].score if chunks else 0.0
    if not chunks or top_score < threshold:
        return SageResponse(reply=ESCALATION_MESSAGE, escalated=True, sources=[])

    context = "\n\n".join(f"[{c.source}] {c.text}" for c in chunks)
    system = load_prompt("sage_agent.md").replace("{context}", context).replace("{page}", page)
    reply = llm.complete(system, message, max_tokens=400).strip()
    return SageResponse(reply=reply, escalated=False, sources=[c.source for c in chunks])
```

- [ ] **Step 4: Run, expect PASS (3 passed).**

Run: `.venv/Scripts/python.exe -m pytest tests/test_agent_sage.py -v`

- [ ] **Step 5: Commit.**

```bash
git add backend/app/agents/sage.py backend/tests/test_agent_sage.py
git commit -m "feat(agents): Sage chat agent — RAG-grounded answer with confidence-gated escalation"
```

---

## Task 3: KB index build script + verification

**Files:**
- Create: `backend/scripts/__init__.py`, `backend/scripts/build_kb_index.py`
- Test: none new (verification + one live, opt-in check)

- [ ] **Step 1: Create `backend/scripts/__init__.py`** (single newline).

- [ ] **Step 2: Write `backend/scripts/build_kb_index.py`:**

```python
"""One-time: ingest kb/*.md into the persistent Chroma index (downloads the
MiniLM ONNX model on first run). Run from backend/: .venv/Scripts/python.exe -m scripts.build_kb_index"""
from __future__ import annotations

from app.rag.store import build_index


def main() -> None:
    retriever = build_index()  # default kb dir, default MiniLM embedder, persistent
    # sanity: confirm a representative query returns the right doc
    hits = retriever.retrieve("what are the pricing tiers?", k=3)
    print(f"Indexed. Top source for a pricing query: {hits[0].source if hits else 'NONE'}")
    for h in hits:
        print(f"  score={h.score:.3f}  {h.source}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the full unit suite (no model download).**

Run: `cd /c/Users/Arunkumar/Documents/Docket-assignment/backend && .venv/Scripts/python.exe -m pytest -q`
Expected: all prior tests (62) + rag store 3 + sage 3 = **68 passed**. (The default suite must NOT download the MiniLM model — tests inject the toy embedder / stub retriever.) If anything fails, STOP and report BLOCKED.

- [ ] **Step 4: Build the real index live (downloads MiniLM once) and verify retrieval.**

Run: `.venv/Scripts/python.exe -m scripts.build_kb_index`
Expected: prints `Indexed. Top source for a pricing query: pricing-tiers.md` (or `roi-benchmarks.md`/`pricing` related) with cosine scores. This confirms the production embedder + real KB chunks retrieve sensibly. If the model download fails (offline), report DONE_WITH_CONCERNS noting the unit suite is green and only the live index build is blocked.

- [ ] **Step 5: Commit.**

```bash
git add backend/scripts
git commit -m "feat(rag): KB index build script + live retrieval sanity check"
```

---

## Self-Review

- **Spec coverage:** RAG stack (sentence-transformers MiniLM via ChromaDB default embedder + ChromaDB, ingest `kb/*.md`) Task 1 ✓; Sage RAG-grounded chat + cosine<0.75 escalation Task 2 ✓; KB ingestion/build Task 3 ✓.
- **Type/name consistency:** `Chunk(text, source, score)` defined in Task 1, consumed by `Retriever` and by Sage tests (Task 2). `Retriever.retrieve(query, k)` signature matches the `StubRetriever` in Sage tests. `SageResponse(reply, escalated, sources)` consistent. `build_index(kb_dir, *, client, embedding_function, reset)` matches its test calls.
- **Placeholders:** none.
- **Deferred (later, not this plan):** the chat-path **outcome routing** (book/nurture/disqualify) and the post-email-capture enrich→score→research→CRM hand-off — that's the chat-orchestration layer. Sage here delivers grounded answering + escalation; the 5-signal qualification is driven conversationally by the `sage_agent.md` prompt.
- **Fast-suite guarantee:** unit tests inject a toy `EmbeddingFunction` (store) or a stub retriever (Sage), so `pytest` never downloads a model or hits the network. The only model download is the explicit `scripts.build_kb_index` run (Task 3 Step 4).
