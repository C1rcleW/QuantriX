"""Data import and exploration routes.

POST   /api/data/import      — Upload file, return Dataset with metadata
GET    /api/data/{id}        — Get dataset summary
GET    /api/data/{id}/variables — Get variable metadata list
GET    /api/data/{id}/profile  — Get data profile (json or markdown)
GET    /api/data/{id}/table   — Get paginated data table
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from quantrix.dag.tracker import get_tracker
from quantrix.data.inference.missing_detector import MissingDetector
from quantrix.data.inference.type_detector import TypeDetector
from quantrix.data.profile import ProfileGenerator
from quantrix.data.readers.csv import CsvReader
from quantrix.data.readers.sav import SpssReader
from quantrix.server.registry import get_dataset, register_dataset, set_import_node_id

router = APIRouter(prefix="/api/data", tags=["data"])

# ── Reader registry ──

_READERS: dict[str, SpssReader | CsvReader] = {
    ".sav": SpssReader(),
    ".zsav": SpssReader(),
    ".csv": CsvReader(),
    ".tsv": CsvReader(),
    ".txt": CsvReader(),
}


def _get_reader(extension: str) -> SpssReader | CsvReader:
    ext = extension.lower()
    reader = _READERS.get(ext)
    if reader is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {ext}",
        )
    return reader


# ── POST /api/data/import ──


@router.post("/import")
async def import_file(
    file: UploadFile = File(description="Data file to import"),  # noqa: B008
) -> dict:
    """Upload a data file and return parsed Dataset metadata."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix
    reader = _get_reader(suffix)

    original_name = Path(file.filename).stem
    content = await file.read()
    with tempfile.NamedTemporaryFile(
        prefix=f"{original_name}_", suffix=suffix, delete=False
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        dataset = reader.read(tmp_path)
        dataset.name = original_name
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse {file.filename}: {e}") from e
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    # Run inference pipeline
    if dataset.data is not None:
        TypeDetector().refine(dataset.variables, dataset.data)
        MissingDetector().analyze(dataset.variables, dataset.data)

    dataset_id = register_dataset(dataset)

    tracker = get_tracker()
    node_id = tracker.record_import(dataset, file.filename)
    set_import_node_id(dataset_id, node_id)

    return {
        "dataset_id": dataset_id,
        "name": dataset.name,
        "source_format": dataset.source_format,
        "n_rows": dataset.n_rows,
        "n_columns": dataset.n_columns,
        "variables": [
            {
                "name": v.name,
                "label": v.label,
                "display_name": v.display_name,
                "variable_type": v.variable_type.value,
                "n_valid": v.n_valid,
                "missing_count": v.missing_count,
                "missing_percentage": round(v.missing_percentage, 1),
                "n_unique": v.n_unique,
            }
            for v in dataset.variables
        ],
    }


# ── GET /api/data/{dataset_id} ──


@router.get("/{dataset_id}")
def get_dataset_summary(dataset_id: str) -> dict:
    ds = get_dataset(dataset_id)
    return {
        "dataset_id": dataset_id,
        "name": ds.name,
        "source_format": ds.source_format,
        "n_rows": ds.n_rows,
        "n_columns": ds.n_columns,
        "variable_count": len(ds.variables),
    }


# ── GET /api/data/{dataset_id}/variables ──


@router.get("/{dataset_id}/variables")
def get_variables(dataset_id: str) -> dict:
    ds = get_dataset(dataset_id)
    return {
        "dataset_id": dataset_id,
        "variables": [
            {
                "name": v.name,
                "label": v.label,
                "display_name": v.display_name,
                "variable_type": v.variable_type.value,
                "measure_level": v.measure_level.value,
                "n_valid": v.n_valid,
                "missing_count": v.missing_count,
                "missing_percentage": round(v.missing_percentage, 1),
                "missing_pattern": v.missing_pattern.value,
                "n_unique": v.n_unique,
                "is_complete": v.is_complete,
                "is_categorical": v.is_categorical,
                "is_continuous": v.is_continuous,
                "value_labels": [
                    {"value": vl.value, "label": vl.label} for vl in v.value_labels[:20]
                ],
                "has_more_labels": len(v.value_labels) > 20,
                "stats": (
                    {
                        "min": v.min_value,
                        "max": v.max_value,
                        "mean": v.mean,
                        "std_dev": v.std_dev,
                    }
                    if v.is_continuous
                    else None
                ),
            }
            for v in ds.variables
        ],
    }


# ── GET /api/data/{dataset_id}/profile ──


@router.get("/{dataset_id}/profile")
def get_profile(
    dataset_id: str,
    format: str = Query(default="json"),
) -> dict | str:
    ds = get_dataset(dataset_id)
    generator = ProfileGenerator()
    profile = generator.generate(ds)

    if format == "markdown":
        return profile.to_markdown()

    return {
        "dataset_id": dataset_id,
        "dataset_name": profile.dataset_name,
        "n_rows": profile.n_rows,
        "n_columns": profile.n_columns,
        "total_missing_cells": profile.total_missing_cells,
        "overall_missing_rate": profile.overall_missing_rate,
        "n_complete_cases": profile.n_complete_cases,
        "n_incomplete_cases": profile.n_incomplete_cases,
        "quality_flags": {
            "has_high_missing": profile.has_high_missing,
            "has_constant_variables": profile.has_constant_variables,
        },
        "variable_profiles": [
            {
                "name": vp.name,
                "display_name": vp.display_name,
                "variable_type": vp.variable_type,
                "completeness_pct": vp.completeness_pct,
                "n_valid": vp.n_valid,
                "n_unique": vp.n_unique,
                "quality_note": vp.quality_note,
            }
            for vp in profile.variable_profiles
        ],
    }


# ── GET /api/data/{dataset_id}/table ──


@router.get("/{dataset_id}/table")
def get_table(
    dataset_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict:
    ds = get_dataset(dataset_id)
    df = ds.data
    if df is None:
        raise HTTPException(status_code=404, detail="No data loaded")

    total = df.height
    slice_df = df.slice(offset, limit)
    rows = slice_df.rows()
    columns = df.columns

    return {
        "dataset_id": dataset_id,
        "total_rows": total,
        "offset": offset,
        "limit": limit,
        "columns": columns,
        "rows": [[str(v) if v is not None else None for v in row] for row in rows],
    }
