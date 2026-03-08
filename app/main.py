"""FastAPI entrypoint for LetterGuard AI."""

from fastapi import FastAPI

from app.api.routes import router as api_router

app = FastAPI(title="LetterGuard AI")

app.include_router(api_router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "app": "LetterGuard AI"}


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "letterguard-ai"}
