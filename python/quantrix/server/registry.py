"""In-memory dataset registry.

Shared by app.py and routes. Kept in its own module to avoid
circular imports between the app factory and route modules.
"""

from __future__ import annotations

from fastapi import HTTPException

from quantrix.core.dataset import Dataset

_datasets: dict[str, Dataset] = {}
_import_nodes: dict[str, str] = {}
_counter: int = 0


def register_dataset(dataset: Dataset) -> str:
    global _counter
    _counter += 1
    did = str(_counter)
    _datasets[did] = dataset
    return did


def get_dataset(dataset_id: str) -> Dataset:
    ds = _datasets.get(dataset_id)
    if ds is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds


def set_import_node_id(dataset_id: str, node_id: str) -> None:
    _import_nodes[dataset_id] = node_id


def get_import_node_id(dataset_id: str) -> str | None:
    return _import_nodes.get(dataset_id)
