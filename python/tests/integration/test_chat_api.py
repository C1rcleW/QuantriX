"""Integration tests for the interpretation API."""

import pytest
from fastapi.testclient import TestClient

from quantrix.server.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestInterpretAPI:
    def test_interpret_ttest(self, client):
        r = client.post(
            "/api/chat/interpret",
            json={
                "method_name": "independent_ttest",
                "statistics": {
                    "dv_label": "Income",
                    "iv_label": "Gender",
                    "group_labels": ["Male", "Female"],
                    "means": [49200, 41000],
                    "sds": [12000, 10500],
                    "ns": [600, 647],
                    "sig_text": "p < .001, statistically significant",
                    "effect_size_text": "Cohen's d = 0.38, a small effect size",
                },
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["method_name"] == "independent_ttest"
        assert len(data["summary"]) > 0
        assert len(data["detailed"]) > 0
        assert "key_findings" in data
        assert "limitations" in data

    def test_interpret_correlation(self, client):
        r = client.post(
            "/api/chat/interpret",
            json={
                "method_name": "pearson_correlation",
                "statistics": {
                    "dv_label": "Income",
                    "iv_label": "Education (years)",
                    "r": 0.45,
                    "df": 1245,
                    "n": 1247,
                    "p_value": 0.001,
                },
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert "correlation" in data["summary"].lower()

    def test_interpret_with_warnings(self, client):
        r = client.post(
            "/api/chat/interpret",
            json={
                "method_name": "independent_ttest",
                "statistics": {
                    "dv_label": "Score",
                    "iv_label": "Group",
                    "group_labels": ["A", "B"],
                    "means": [85, 78],
                    "sds": [10, 9],
                    "ns": [30, 30],
                    "sig_text": "p = .045",
                    "effect_size_text": "",
                },
                "safety_warnings": [
                    {"severity": "warning", "message": "Small sample size."},
                ],
            },
        )
        data = r.json()
        assert len(data["limitations"]) >= 1

    def test_interpret_descriptive(self, client):
        r = client.post(
            "/api/chat/interpret",
            json={
                "method_name": "descriptive_statistics",
                "statistics": {
                    "dv_label": "Age",
                    "n": 100,
                    "n_valid": 95,
                    "missing_count": 5,
                    "missing_pct": 5.0,
                    "mean": 35.2,
                    "std_dev": 10.5,
                    "min_val": 18.0,
                    "max_val": 65.0,
                    "skewness_text": "",
                },
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert "35.2" in data["detailed"]
