"""Safety check routes.

POST   /api/safety/check   — Run safety rules for a method + variables
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from quantrix.safety.engine import create_default_safety_net
from quantrix.server.registry import get_dataset

router = APIRouter(prefix="/api/safety", tags=["safety"])


class SafetyCheckRequest(BaseModel):
    dataset_id: str
    method_name: str
    dependent: str | None = None
    independents: list[str] = []


@router.post("/check")
def run_safety_check(request: SafetyCheckRequest) -> dict:
    """Run all safety rules for a proposed analysis.

    Returns errors, warnings, and info messages.
    """
    dataset = get_dataset(request.dataset_id)

    # Resolve variables
    dv = dataset.get_variable(request.dependent) if request.dependent else None
    ivs = [dataset.get_variable(name) for name in request.independents]

    net = create_default_safety_net()
    report = net.check(request.method_name, dv, ivs, dataset)

    return report.to_dict()
