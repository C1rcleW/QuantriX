"""Interpretation / chat routes.

POST   /api/chat/interpret   — Generate natural-language interpretation of results
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from quantrix.interpreter.engine import ResultInterpreter

router = APIRouter(prefix="/api/chat", tags=["chat"])


class InterpretRequest(BaseModel):
    method_name: str
    statistics: dict
    safety_warnings: list[dict] | None = None


class InterpretResponse(BaseModel):
    method_name: str
    summary: str
    detailed: str
    key_findings: list[str]
    limitations: list[str]


@router.post("/interpret", response_model=InterpretResponse)
def interpret_results(request: InterpretRequest) -> InterpretResponse:
    """Generate a natural-language interpretation of statistical results.

    This is template-based (no LLM), providing consistent,
    statistically accurate interpretations of common analysis methods.
    """
    interpreter = ResultInterpreter()
    result = interpreter.interpret(
        request.method_name,
        request.statistics,
        request.safety_warnings,
    )
    return InterpretResponse(
        method_name=result.method_name,
        summary=result.summary,
        detailed=result.detailed,
        key_findings=result.key_findings,
        limitations=result.limitations,
    )
