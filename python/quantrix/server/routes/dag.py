"""DAG / provenance routes.

GET    /api/dag           — Get the current DAG
POST   /api/dag/export    — Export DAG as Python/R/SPSS Syntax
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from quantrix.dag.exporters.python import export_python
from quantrix.dag.exporters.r import export_r
from quantrix.dag.exporters.syntax import export_syntax
from quantrix.dag.tracker import get_tracker

router = APIRouter(prefix="/api/dag", tags=["dag"])


class ExportRequest(BaseModel):
    language: str = "python"  # "python", "r", "syntax"
    dataset_name: str = "data"


class ExportResponse(BaseModel):
    language: str
    code: str


@router.get("")
def get_dag() -> dict:
    """Get the current analysis DAG."""
    tracker = get_tracker()
    return tracker.dag.to_dict()


@router.post("/export", response_model=ExportResponse)
def export_dag(request: ExportRequest) -> ExportResponse:
    """Export the current DAG as reproducible code."""
    tracker = get_tracker()
    dag = tracker.dag

    exporters = {
        "python": export_python,
        "r": export_r,
        "syntax": export_syntax,
    }
    exporter = exporters.get(request.language)
    if exporter is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")

    code = exporter(dag, request.dataset_name)
    return ExportResponse(language=request.language, code=code)
