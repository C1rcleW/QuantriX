"""Golden snapshots for Markdown/HTML report rendering."""

from __future__ import annotations

from quantrix.report.generator import ReportGenerator, ReportSection
from tests.golden._snapshot import assert_text_snapshot


def test_report_render_snapshots() -> None:
    section = ReportSection(
        heading="Independent Samples t-test",
        subheading="score by group",
        interpretation=(
            "The difference in score between groups of group was "
            "p = 0.814, which is not statistically significant."
        ),
        tables=[
            {
                "title": "Table 1. Group descriptives",
                "columns": ["Group", "N", "Mean", "SD"],
                "rows": [["A", 4, 86.25, 6.24], ["B", 4, 85.0, 8.04]],
                "notes": "Deterministic synthetic data.",
            }
        ],
        safety_notes=["Total sample size is below the recommended minimum."],
    )
    generator = ReportGenerator()
    report = generator.create_report(
        "QuantriX Golden Report",
        dataset_info={
            "name": "golden",
            "n_rows": 24,
            "n_columns": 6,
            "source_format": "csv",
        },
        sections=[section],
    )
    report.generated_at = "2026-01-01T00:00:00"

    assert_text_snapshot(generator.render_markdown(report), "report.json", "markdown")
    assert_text_snapshot(generator.render_html(report), "report.json", "html")
