"""Integration tests for the safety check API."""

import pytest
from fastapi.testclient import TestClient

from quantrix.server.app import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def dataset_id(client):
    csv = b"id,income,gender,age\n1,50000,1,25\n2,60000,2,30\n3,45000,1,22\n4,75000,2,35\n5,55000,1,28\n"
    r = client.post(
        "/api/data/import",
        files={"file": ("test.csv", csv, "text/csv")},
    )
    return r.json()["dataset_id"]


class TestSafetyCheck:
    def test_valid_method_passes(self, client, dataset_id):
        r = client.post("/api/safety/check", json={
            "dataset_id": dataset_id,
            "method_name": "independent_ttest",
            "dependent": "income",
            "independents": ["gender"],
        })
        assert r.status_code == 200
        data = r.json()
        assert data["method_name"] == "independent_ttest"
        assert "errors" in data
        assert "warnings" in data
        assert "is_clean" in data

    def test_type_mismatch_errors(self, client, dataset_id):
        """Nominal DV with t-test should error."""
        r = client.post("/api/safety/check", json={
            "dataset_id": dataset_id,
            "method_name": "independent_ttest",
            "dependent": "gender",  # nominal!
            "independents": ["income"],
        })
        data = r.json()
        assert data["has_errors"] is True

    def test_wrong_dataset(self, client):
        r = client.post("/api/safety/check", json={
            "dataset_id": "999",
            "method_name": "ttest",
        })
        assert r.status_code == 404

    def test_info_and_warning_fields(self, client, dataset_id):
        r = client.post("/api/safety/check", json={
            "dataset_id": dataset_id,
            "method_name": "descriptives",
            "dependent": "income",
            "independents": [],
        })
        data = r.json()
        assert "info" in data
