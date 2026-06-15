from fastapi import FastAPI

app = FastAPI(title="Sentio Agent Backend")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
