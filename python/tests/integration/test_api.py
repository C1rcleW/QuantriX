"""Integration tests for the Quantrix HTTP API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from quantrix.server.app import app


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


@pytest.fixture
def csv_content() -> bytes:
    return b"id,score,group\n1,85.5,A\n2,92.0,B\n3,78.3,A\n4,,B\n5,88.1,A\n"


@pytest.fixture
def sav_path(simple_sav_path) -> Path:
    return simple_sav_path


class TestDataImport:
    """POST /api/data/import tests."""

    def test_import_csv(self, client, csv_content):
        response = client.post(
            "/api/data/import",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "dataset_id" in data
        assert data["name"] == "test"
        assert data["n_rows"] == 5
        assert data["n_columns"] == 3
        assert len(data["variables"]) == 3

    def test_import_sav(self, client, sav_path):
        with open(sav_path, "rb") as f:
            response = client.post(
                "/api/data/import",
                files={"file": ("test.sav", f, "application/octet-stream")},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["n_rows"] == 100
        assert data["n_columns"] == 5
        assert data["source_format"] == "sav"

    def test_import_csv_infers_types(self, client, csv_content):
        response = client.post(
            "/api/data/import",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )
        data = response.json()
        types = {v["name"]: v["variable_type"] for v in data["variables"]}
        assert types["score"] == "continuous"
        assert types["group"] == "nominal"

    def test_import_unsupported_format(self, client):
        response = client.post(
            "/api/data/import",
            files={"file": ("data.json", b"{}", "application/json")},
        )
        assert response.status_code == 400

    def test_registry_persistence(self, client, csv_content):
        r1 = client.post(
            "/api/data/import",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )
        dataset_id = r1.json()["dataset_id"]
        r2 = client.get(f"/api/data/{dataset_id}")
        assert r2.status_code == 200
        assert r2.json()["name"] == "test"


class TestGetDataset:
    def test_get_existing(self, client, csv_content):
        r1 = client.post(
            "/api/data/import",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )
        did = r1.json()["dataset_id"]
        r2 = client.get(f"/api/data/{did}")
        assert r2.status_code == 200
        assert r2.json()["n_rows"] == 5

    def test_get_nonexistent(self, client):
        r = client.get("/api/data/nonexistent-id")
        assert r.status_code == 404


class TestGetVariables:
    def test_variables_have_metadata(self, client, csv_content):
        r1 = client.post(
            "/api/data/import",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )
        did = r1.json()["dataset_id"]
        r2 = client.get(f"/api/data/{did}/variables")
        assert r2.status_code == 200
        vars_list = r2.json()["variables"]
        assert len(vars_list) == 3
        score = next(v for v in vars_list if v["name"] == "score")
        assert score["is_continuous"] is True
        assert score["stats"] is not None
        group = next(v for v in vars_list if v["name"] == "group")
        assert group["is_categorical"] is True


class TestGetProfile:
    def test_profile_json(self, client, csv_content):
        r1 = client.post(
            "/api/data/import",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )
        did = r1.json()["dataset_id"]
        r2 = client.get(f"/api/data/{did}/profile?format=json")
        assert r2.status_code == 200
        data = r2.json()
        assert data["n_rows"] == 5
        assert data["n_columns"] == 3
        assert len(data["variable_profiles"]) == 3

    def test_profile_markdown(self, client, csv_content):
        r1 = client.post(
            "/api/data/import",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )
        did = r1.json()["dataset_id"]
        r2 = client.get(f"/api/data/{did}/profile?format=markdown")
        assert r2.status_code == 200
        assert "# Data Profile" in r2.text


class TestGetTable:
    def test_table_pagination(self, client, csv_content):
        r1 = client.post(
            "/api/data/import",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )
        did = r1.json()["dataset_id"]
        r2 = client.get(f"/api/data/{did}/table?offset=0&limit=2")
        assert r2.status_code == 200
        data = r2.json()
        assert data["total_rows"] == 5
        assert len(data["rows"]) == 2
        assert data["columns"] == ["id", "score", "group"]
