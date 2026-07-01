"""Integration tests for the analysis plan API."""

import pytest
from fastapi.testclient import TestClient

from quantrix.server.app import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def dataset_id(client):
    """Import a CSV and return its dataset_id."""
    csv = b"id,income,gender,education\n1,50000,1,16\n2,60000,2,18\n3,45000,1,14\n4,75000,2,20\n5,55000,1,16\n"
    r = client.post(
        "/api/data/import",
        files={"file": ("test.csv", csv, "text/csv")},
    )
    return r.json()["dataset_id"]


class TestAnalysisPlan:
    def test_basic_plan(self, client, dataset_id):
        r = client.post("/api/analysis/plan", json={
            "dataset_id": dataset_id,
            "question": "Does gender affect income?",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["question_type"] in ("difference", "prediction")
        assert len(data["recommendations"]) >= 1
        rec = data["recommendations"][0]
        assert "method_name" in rec
        assert "rationale" in rec
        assert "assumptions" in rec
        assert "confidence" in rec

    def test_descriptive_plan(self, client, dataset_id):
        r = client.post("/api/analysis/plan", json={
            "dataset_id": dataset_id,
            "question": "Describe the distribution of income.",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["question_type"] == "descriptive"

    def test_empty_question_fails(self, client, dataset_id):
        r = client.post("/api/analysis/plan", json={
            "dataset_id": dataset_id,
            "question": "   ",
        })
        assert r.status_code == 400

    def test_nonexistent_dataset(self, client):
        r = client.post("/api/analysis/plan", json={
            "dataset_id": "999",
            "question": "What predicts income?",
        })
        assert r.status_code == 404

    def test_plan_includes_design(self, client, dataset_id):
        r = client.post("/api/analysis/plan", json={
            "dataset_id": dataset_id,
            "question": "Does gender affect income over time?",
        })
        assert r.status_code == 200
        assert r.json()["design"] == "longitudinal"

    def test_plan_returns_alternative_methods(self, client, dataset_id):
        r = client.post("/api/analysis/plan", json={
            "dataset_id": dataset_id,
            "question": "Is there a difference in income between genders?",
        })
        data = r.json()
        rec = data["recommendations"][0]
        assert "alternative_methods" in rec

    def test_plan_ranks_by_confidence(self, client, dataset_id):
        r = client.post("/api/analysis/plan", json={
            "dataset_id": dataset_id,
            "question": "What affects income?",
        })
        data = r.json()
        if len(data["recommendations"]) >= 2:
            confidences = [rec["confidence"] for rec in data["recommendations"]]
            assert confidences == sorted(confidences, reverse=True)
