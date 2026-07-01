"""Report generation routes.

POST   /api/report/generate   — Generate an academic report
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from quantrix.report.generator import (
    Report,
    ReportGenerator,
    ReportSection,
    section_from_interpretation,
)

router = APIRouter(prefix="/api/report", tags=["report"])


class SectionInput(BaseModel):
    heading: str = ""
    subheading: str = ""
    interpretation: str = ""
    tables: list[dict] = []
    safety_notes: list[str] = []


class ReportRequest(BaseModel):
    title: str = "Quantrix Analysis Report"
    dataset_id: str | None = None
    format: str = "apa"
    sections: list[SectionInput] = []
    dataset_info: dict | None = None


class ReportResponse(BaseModel):
    title: str
    format: str
    markdown: str
    html: str
    section_count: int


@router.post("/generate", response_model=ReportResponse)
def generate_report(request: ReportRequest) -> ReportResponse:
    """Generate an academic report from analysis sections.

    Returns Markdown (for preview) and HTML (for viewing).
    """
    sections = [
        ReportSection(
            heading=s.heading,
            subheading=s.subheading,
            interpretation=s.interpretation,
            tables=s.tables,
            safety_notes=s.safety_notes,
        )
        for s in request.sections
    ]

    gen = ReportGenerator()
    report = gen.create_report(
        title=request.title,
        dataset_info=request.dataset_info or {},
        sections=sections,
        fmt=request.format,
    )

    md = gen.render_markdown(report)
    html = gen.render_html(report)

    return ReportResponse(
        title=report.title,
        format=report.format,
        markdown=md,
        html=html,
        section_count=len(report.sections),
    )
