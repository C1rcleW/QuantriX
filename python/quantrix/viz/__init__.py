"""Chart data generators for statistical visualization.

Each stat method calls the appropriate builder to produce chart-ready JSON
that the frontend renders with Recharts. No image generation happens here --
only structured data arrays.
"""

from __future__ import annotations

import math
from typing import Any


def _compute_kde(values: list[float], n_points: int = 100) -> tuple[list[float], list[float]]:
    """Compute kernel density estimate using Gaussian kernel and Scott's bandwidth."""
    if len(values) < 2:
        return [], []
    n = len(values)
    mean = sum(values) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1)) if n > 1 else 1.0
    bw = std * n ** (-0.2) if std > 0 else 1.0  # Scott's rule (≈ n^(-1/5))
    bw = max(bw, 0.001)

    x_min = min(values) - 3 * bw
    x_max = max(values) + 3 * bw
    step = (x_max - x_min) / (n_points - 1)
    x_grid = [x_min + i * step for i in range(n_points)]
    density = []
    inv_nh = 1.0 / (n * bw)
    for x in x_grid:
        s = sum(math.exp(-0.5 * ((x - v) / bw) ** 2) for v in values)
        density.append(s * inv_nh / math.sqrt(2 * math.pi))
    return x_grid, density


def histogram(values: list[float], title: str, x_label: str, bins: int = 20) -> dict[str, Any]:
    """Build histogram chart data."""
    if not values:
        return {"chart_type": "histogram", "title": title, "x_label": x_label, "data": []}
    x_min, x_max = min(values), max(values)
    if x_min == x_max:
        x_min -= 0.5
        x_max += 0.5
    width = (x_max - x_min) / bins
    bins_edges = [x_min + i * width for i in range(bins + 1)]
    counts = [0] * bins
    for v in values:
        idx = min(int((v - x_min) / width), bins - 1)
        counts[idx] += 1
    data = [{"x": f"{bins_edges[i]:.2f}-{bins_edges[i+1]:.2f}", "count": counts[i]} for i in range(bins)]

    kde_x, kde_y = _compute_kde(values)
    density_data = [{"x": round(kde_x[i], 4), "density": round(kde_y[i], 6)} for i in range(len(kde_x))]

    return {
        "chart_type": "histogram",
        "title": title,
        "x_label": x_label,
        "y_label": "Frequency",
        "data": data,
        "density": density_data,
    }


def bar(
    categories: list[str], values: list[float], title: str, x_label: str = "", y_label: str = ""
) -> dict[str, Any]:
    """Build simple bar chart."""
    data = [{"name": str(c), "value": v} for c, v in zip(categories, values)]
    return {"chart_type": "bar", "title": title, "x_label": x_label, "y_label": y_label, "data": data}


def grouped_bar(
    categories: list[str],
    series: list[dict[str, Any]],
    title: str,
    x_label: str = "",
    y_label: str = "",
) -> dict[str, Any]:
    """Build grouped bar chart. series = [{"name": "Mean", "data": [5.0, 6.0]}, ...]."""
    return {
        "chart_type": "grouped_bar",
        "title": title,
        "x_label": x_label,
        "y_label": y_label,
        "data": categories,
        "series": series,
    }


def scatter(
    x: list[float],
    y: list[float],
    title: str,
    x_label: str = "",
    y_label: str = "",
    line_x: list[float] | None = None,
    line_y: list[float] | None = None,
    ci_upper: list[float] | None = None,
    ci_lower: list[float] | None = None,
) -> dict[str, Any]:
    """Build scatter chart, optionally with regression line and confidence band."""
    points = [{"x": round(x[i], 4), "y": round(y[i], 4)} for i in range(len(x))]
    result: dict[str, Any] = {
        "chart_type": "scatter",
        "title": title,
        "x_label": x_label,
        "y_label": y_label,
        "data": points,
    }
    if line_x is not None and line_y is not None:
        result["line"] = [{"x": round(line_x[i], 4), "y": round(line_y[i], 4)} for i in range(len(line_x))]
        result["chart_type"] = "scatter_with_line"
    if ci_upper is not None and ci_lower is not None:
        n = len(ci_upper)
        result["ci_upper"] = [round(ci_upper[i], 4) for i in range(n)]
        result["ci_lower"] = [round(ci_lower[i], 4) for i in range(n)]
    return result


def box_plot(
    groups: dict[str, list[float]], title: str, x_label: str = "", y_label: str = ""
) -> dict[str, Any]:
    """Build box plot data. groups = {"setosa": [5.1, 4.9, ...], ...}."""
    result_data = []
    for name, vals in groups.items():
        if not vals:
            continue
        sv = sorted(vals)
        n = len(sv)
        q1 = sv[int(n * 0.25)]
        q2 = sv[int(n * 0.50)]
        q3 = sv[int(n * 0.75)]
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = [v for v in sv if v < lower or v > upper]
        whisker_low = next((v for v in sv if v >= lower), sv[0])
        whisker_high = next((v for v in reversed(sv) if v <= upper), sv[-1])
        result_data.append({
            "name": str(name),
            "min": round(sv[0], 4),
            "q1": round(q1, 4),
            "median": round(q2, 4),
            "q3": round(q3, 4),
            "max": round(sv[-1], 4),
            "whisker_low": round(whisker_low, 4),
            "whisker_high": round(whisker_high, 4),
            "outliers": [round(o, 4) for o in outliers],
            "mean": round(sum(vals) / n, 4),
            "sd": round(math.sqrt(sum((v - sum(vals) / n) ** 2 for v in vals) / (n - 1)), 4) if n > 1 else 0,
        })
    return {
        "chart_type": "box",
        "title": title,
        "x_label": x_label,
        "y_label": y_label,
        "data": result_data,
    }
