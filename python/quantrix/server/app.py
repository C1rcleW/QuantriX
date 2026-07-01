"""FastAPI application — Quantrix backend server."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from quantrix.server.routes.analysis import router as analysis_router
from quantrix.server.routes.chat import router as chat_router
from quantrix.server.routes.dag import router as dag_router
from quantrix.server.routes.data import router as data_router
from quantrix.server.routes.report import router as report_router
from quantrix.server.routes.safety import router as safety_router

app = FastAPI(title="Quantrix", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_router)
app.include_router(analysis_router)
app.include_router(safety_router)
app.include_router(chat_router)
app.include_router(report_router)
app.include_router(dag_router)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
