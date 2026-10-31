"""Stage 0 guardrail: every registered method has a complete built-in surface."""

from __future__ import annotations

from quantrix.interpreter.template_registry import get as get_template
from quantrix.safety.rules.type_match import _METHOD_DV_TYPES, _METHOD_IV_TYPES
from quantrix.stats.registry import get_registry
from tests.golden.data import METHOD_CASES

NO_IV_METHODS = {"descriptives", "frequencies"}


def test_registered_methods_have_template_type_rules_and_golden_cases() -> None:
    registry = get_registry()

    missing_templates = sorted(
        name for name in registry if get_template(name) is None
    )
    missing_dv_types = sorted(
        name for name in registry if name not in _METHOD_DV_TYPES
    )
    missing_iv_types = sorted(
        name
        for name in registry
        if name not in NO_IV_METHODS and name not in _METHOD_IV_TYPES
    )
    missing_golden_cases = sorted(
        set(registry) - {case.method for case in METHOD_CASES}
    )

    assert not missing_templates, f"Missing templates: {missing_templates}"
    assert not missing_dv_types, f"Missing DV type rules: {missing_dv_types}"
    assert not missing_iv_types, f"Missing IV type rules: {missing_iv_types}"
    assert not missing_golden_cases, (
        f"Missing golden cases: {missing_golden_cases}"
    )


def test_registered_method_metadata_is_consistent() -> None:
    for name, method in get_registry().items():
        assert method.method_name == name
        assert method.method_family
