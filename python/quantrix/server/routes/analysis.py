"""Analysis plan routes.

POST   /api/analysis/plan    — Submit a research question, get method recommendations
POST   /api/analysis/execute — Execute a statistical analysis
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from quantrix.planner.recommendation import ResearchPlanner
from quantrix.server.registry import get_dataset
from quantrix.stats.registry import execute_analysis

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class PlanRequest(BaseModel):
    dataset_id: str
    question: str


class PlanResponse(BaseModel):
    question: str
    question_type: str
    design: str
    recommendations: list[dict]


@router.post("/plan", response_model=PlanResponse)
def get_analysis_plan(request: PlanRequest) -> PlanResponse:
    """Generate an analysis plan from a research question.

    Returns ranked method recommendations with rationale and assumptions.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    dataset = get_dataset(request.dataset_id)
    planner = ResearchPlanner()
    plan = planner.plan(request.question, dataset)

    return PlanResponse(
        question=plan["question"],
        question_type=plan["question_type"],
        design=plan["design"],
        recommendations=plan["recommendations"],
    )


class ExecuteRequest(BaseModel):
    dataset_id: str
    method_name: str
    dependent: str | None = None
    independents: list[str] = []


@router.post("/execute")
def execute_analysis_route(request: ExecuteRequest) -> dict:
    dataset = get_dataset(request.dataset_id)
    dv = dataset.get_variable(request.dependent) if request.dependent else None
    ivs = [dataset.get_variable(n) for n in request.independents]
    result = execute_analysis(request.method_name, dataset, dv, ivs)
    return result
