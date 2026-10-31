"""Golden snapshots for the safety net's current decisions."""

from __future__ import annotations

import pytest

from quantrix.safety.engine import create_default_safety_net
from tests.golden._snapshot import assert_snapshot
from tests.golden.data import make_dataset, make_small_group_dataset

SAFETY_CASES = (
    ("ttest_clean", make_dataset, "independent_ttest", "x", ("g2",)),
    ("anova_clean", make_dataset, "oneway_anova", "x", ("g3",)),
    ("chi_square_clean", make_dataset, "chi_square", "cat", ("g2",)),
    ("regression_warning", make_dataset, "linear_regression", "y", ("x",)),
    ("small_group_error", make_small_group_dataset, "independent_ttest", "score", ("group",)),
)


@pytest.mark.parametrize(
    ("name", "dataset_factory", "method", "dv", "ivs"),
    SAFETY_CASES,
    ids=[case[0] for case in SAFETY_CASES],
)
def test_safety_snapshot(name, dataset_factory, method, dv, ivs) -> None:
    dataset = dataset_factory()
    report = create_default_safety_net().check(
        method,
        dataset.get_variable(dv),
        [dataset.get_variable(variable) for variable in ivs],
        dataset,
    )
    assert_snapshot(report.to_dict(), "safety.json", name)
