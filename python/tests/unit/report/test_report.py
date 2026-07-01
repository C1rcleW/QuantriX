"""Tests for the ReportGenerator."""

import pytest

from quantrix.report.generator import (
    Report,
    ReportGenerator,
    ReportSection,
    section_from_interpretation,
)


class TestReportGenerator:
    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    def test_empty_report(self, generator):
        report = generator.create_report("Test Report")
        md = generator.render_markdown(report)
        assert "# Test Report" in md

    def test_report_with_sections(self, generator):
        sections = [
            ReportSection(
                heading="Descriptive Statistics",
                interpretation="The average income was 45,200 (SD = 12,500).",
            ),
            ReportSection(
                heading="t-test",
                subheading="Income by Gender",
                interpretation="Males earned significantly more than females, t(1245) = 3.42, p < .001.",
                safety_notes=["Sample sizes were unequal across groups."],
            ),
        ]
        report = generator.create_report(
            "Income Analysis",
            dataset_info={"name": "CGSS2021", "n_rows": 1247, "n_columns": 5, "source_format": "sav"},
            sections=sections,
        )
        md = generator.render_markdown(report)
        assert "# Income Analysis" in md
        assert "CGSS2021" in md
        assert "1247" in md
        assert "Descriptive Statistics" in md
        assert "t-test" in md
        assert "significantly" in md
        assert "Sample sizes" in md

    def test_table_rendering(self, generator):
        section = ReportSection(
            heading="Group Descriptives",
            interpretation="",
            tables=[{
                "title": "Table 1. Group Means",
                "columns": ["Group", "N", "Mean", "SD"],
                "rows": [
                    ["Male", 600, 49200, 12000],
                    ["Female", 647, 41000, 10500],
                ],
            }],
        )
        report = generator.create_report("Test", sections=[section])
        md = generator.render_markdown(report)
        assert "Table 1" in md
        assert "Male" in md
        assert "49200" in md

    def test_section_factory(self):
        section = section_from_interpretation(
            heading="Test",
            interpretation="Significant result.",
            safety_notes=["Small sample."],
        )
        assert section.heading == "Test"
        assert section.interpretation == "Significant result."
        assert section.safety_notes == ["Small sample."]

    def test_html_output(self, generator):
        report = generator.create_report(
            "HTML Test",
            sections=[ReportSection(heading="Results", interpretation="p < .05")],
        )
        html = generator.render_html(report)
        assert "<h1>HTML Test</h1>" in html
        assert "<h3>Results</h3>" in html
        assert "p < .05" in html


class TestReportAPI:
    """Integration test for the report generation API."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from quantrix.server.app import app
        return TestClient(app)

    def test_generate_report(self, client):
        r = client.post("/api/report/generate", json={
            "title": "API Test Report",
            "format": "apa",
            "sections": [
                {
                    "heading": "Descriptive Statistics",
                    "interpretation": "The sample contained 100 participants.",
                }
            ],
            "dataset_info": {"name": "test.csv", "n_rows": 100, "n_columns": 5},
        })
        assert r.status_code == 200
        data = r.json()
        assert data["title"] == "API Test Report"
        assert data["format"] == "apa"
        assert len(data["markdown"]) > 0
        assert len(data["html"]) > 0
        assert data["section_count"] == 1

    def test_multiple_sections(self, client):
        r = client.post("/api/report/generate", json={
            "title": "Multi-Section",
            "sections": [
                {"heading": "A", "interpretation": "Result A."},
                {"heading": "B", "interpretation": "Result B."},
                {"heading": "C", "interpretation": "Result C."},
                {"heading": "D", "interpretation": "Result D."},
            ],
        })
        assert r.status_code == 200
        assert r.json()["section_count"] == 4
