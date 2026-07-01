"""Core abstractions for the Quantrix platform.

This package defines the foundational types, protocols, and data models
that all other modules depend on. It has zero external dependencies beyond
the Python standard library and Pydantic.
"""

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import MissingDefinition, ValueLabel, VariableMetadata
from quantrix.core.protocol import (
    ReaderProtocol,
    SafetyRuleProtocol,
    StatMethodProtocol,
    WriterProtocol,
)
from quantrix.core.provenance import ProvenanceEdge, ProvenanceNode
from quantrix.core.types import MeasureLevel, MissingPattern, VariableType

__all__ = [
    # types
    "VariableType",
    "MeasureLevel",
    "MissingPattern",
    # metadata
    "VariableMetadata",
    "ValueLabel",
    "MissingDefinition",
    # dataset
    "Dataset",
    # protocol
    "ReaderProtocol",
    "WriterProtocol",
    "StatMethodProtocol",
    "SafetyRuleProtocol",
    # provenance
    "ProvenanceNode",
    "ProvenanceEdge",
]
