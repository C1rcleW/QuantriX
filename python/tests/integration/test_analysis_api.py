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
        r = client.post(
            "/api/analysis/plan",
            json={
                "dataset_id": dataset_id,
                "question": "Does gender affect income?",
            },
        )
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
        r = client.post(
            "/api/analysis/plan",
            json={
                "dataset_id": dataset_id,
                "question": "Describe the distribution of income.",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["question_type"] == "descriptive"

    def test_empty_question_fails(self, client, dataset_id):
        r = client.post(
            "/api/analysis/plan",
            json={
                "dataset_id": dataset_id,
                "question": "   ",
            },
        )
        assert r.status_code == 400

    def test_nonexistent_dataset(self, client):
        r = client.post(
            "/api/analysis/plan",
            json={
                "dataset_id": "999",
                "question": "What predicts income?",
            },
        )
        assert r.status_code == 404

    def test_plan_includes_design(self, client, dataset_id):
        r = client.post(
            "/api/analysis/plan",
            json={
                "dataset_id": dataset_id,
                "question": "Does gender affect income over time?",
            },
        )
        assert r.status_code == 200
        assert r.json()["design"] == "longitudinal"

    def test_plan_explains_unimplemented_nominal_prediction(self, client, dataset_id):
        r = client.post(
            "/api/analysis/plan-structured",
            json={
                "dataset_id": dataset_id,
                "goal": "predict",
                "dependent": "gender",
                "independents": ["income"],
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["recommendations"] == []
        assert any("not implemented" in note.lower() for note in data["notes"])

    def test_plan_returns_alternative_methods(self, client, dataset_id):
        r = client.post(
            "/api/analysis/plan",
            json={
                "dataset_id": dataset_id,
                "question": "Is there a difference in income by gender?",
            },
        )
        data = r.json()
        rec = data["recommendations"][0]
        assert "alternative_methods" in rec

    def test_plan_ranks_by_confidence(self, client, dataset_id):
        r = client.post(
            "/api/analysis/plan",
            json={
                "dataset_id": dataset_id,
                "question": "What affects income?",
            },
        )
        data = r.json()
        if len(data["recommendations"]) >= 2:
            confidences = [rec["confidence"] for rec in data["recommendations"]]
            assert confidences == sorted(confidences, reverse=True)


class TestAnalysisExecute:
    @pytest.fixture
    def balanced_dataset_id(self, client):
        csv = (
            b"score,group\n"
            b"1,A\n2,A\n3,A\n4,A\n"
            b"5,B\n6,B\n7,B\n8,B\n"
        )
        r = client.post(
            "/api/data/import",
            files={"file": ("balanced.csv", csv, "text/csv")},
        )
        return r.json()["dataset_id"]

    def test_execute_ttest(self, client, balanced_dataset_id):
        r = client.post(
            "/api/analysis/execute",
            json={
                "dataset_id": balanced_dataset_id,
                "method_name": "independent_ttest",
                "dependent": "score",
                "independents": ["group"],
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["errors"] == []
        assert "t_stat" in data["statistics"]
        assert len(data["charts"]) >= 1

    def test_execute_descriptives(self, client, dataset_id):
        r = client.post(
            "/api/analysis/execute",
            json={
                "dataset_id": dataset_id,
                "method_name": "descriptives",
                "dependent": "income",
                "independents": [],
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["errors"] == []
        assert "mean" in data["statistics"]

    def test_execute_blocks_on_safety_error(self, client):
        csv = b"score,group\n1,A\n2,B\n3,B\n4,B\n5,B\n"
        imported = client.post(
            "/api/data/import",
            files={"file": ("tiny.csv", csv, "text/csv")},
        ).json()
        r = client.post(
            "/api/analysis/execute",
            json={
                "dataset_id": imported["dataset_id"],
                "method_name": "independent_ttest",
                "dependent": "score",
                "independents": ["group"],
            },
        )
        assert r.status_code == 409
        assert "safety" in r.json()["detail"].lower()
