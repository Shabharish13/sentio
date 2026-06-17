import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

logger = logging.getLogger(__name__)


def _ensure_kb_index() -> None:
    """Verify the Chroma collection is accessible; rebuild if missing or invalid.

    The index is rebuilt by build_kb_index.py and persisted to .chroma/. If
    a rebuild ran in a separate process while the server was up, the server's
    lru_cache-d retriever would hold a stale reference. Checking at startup
    ensures the collection is valid before requests arrive.
    """
    from app.rag.store import DEFAULT_PERSIST_DIR, build_index, get_retriever
    try:
        r = get_retriever(DEFAULT_PERSIST_DIR)
        count = r._collection.count()
        if count == 0:
            raise ValueError("empty collection")
        logger.info("KB index OK — %d chunks loaded", count)
    except Exception:
        logger.warning("KB index missing or stale — rebuilding now")
        build_index()
        logger.info("KB index rebuilt")


@asynccontextmanager
async def lifespan(application: FastAPI):
    _ensure_kb_index()
    yield


app = FastAPI(title="Sentio Agent Backend", lifespan=lifespan)

# The Next.js dev server and common local hosts. Tighten for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
