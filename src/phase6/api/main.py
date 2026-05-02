"""FastAPI application entry point for Phase 6 Backend API Service."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from phase6.api.routers import health, metadata, recommendations

# Load .env from repo root (two levels up from this file)
_env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="Zomato AI Recommender API",
    description="Backend API for the AI-powered restaurant recommendation system.",
    version="0.1.0",
)

# CORS: allow local frontend dev servers, and read from environment variable
cors_origins_env = os.environ.get("CORS_ORIGINS", "")
if cors_origins_env:
    allow_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
else:
    allow_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _extract_field_from_loc(loc: tuple) -> str | None:
    if len(loc) > 1 and loc[0] == "body":
        return str(loc[1])
    return str(loc[0]) if loc else None


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {
            "field": _extract_field_from_loc(error.get("loc", ())),
            "message": error.get("msg", ""),
            "type": error.get("type", "validation_error"),
        }
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


app.include_router(health.router)
app.include_router(metadata.router)
app.include_router(recommendations.router)


@app.get("/")
def root() -> dict:
    return {"message": "Zomato AI Recommender API", "docs": "/docs"}
