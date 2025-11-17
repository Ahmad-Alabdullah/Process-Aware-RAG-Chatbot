from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple
from .db import get_pool, upsert_aggregate
import statistics, pathlib


def mean_ci(xs: List[float], z: float = 1.96) -> Tuple[float, float, float]:
    if not xs:
        return (0.0, 0.0, 0.0)
    m = statistics.mean(xs)
    if len(xs) < 2:
        return (m, m, m)
    sd = statistics.stdev(xs)
    half = z * sd / (len(xs) ** 0.5)
    return (m, m - half, m + half)


def aggregate_and_store(
    run_id: int, metrics: List[str], out_dir: Optional[str] = None
) -> str:
    pool = get_pool()
    by_metric: Dict[str, List[float]] = {m: [] for m in metrics}
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            "select metric, value from ragrun.scores where run_id=%s", (run_id,)
        )
        for metric, value in cur.fetchall():
            if metric in by_metric:
                by_metric[metric].append(float(value))
    for m in metrics:
        vals = by_metric.get(m, [])
        mean, lo, hi = mean_ci(vals) if vals else (0.0, 0.0, 0.0)
        upsert_aggregate(run_id, m, mean, len(vals), (lo, hi))
    lines = [
        f"# Aggregated Metrics for run_id={run_id}",
        "",
        "| Metric | Mean | 95% CI | N |",
        "|---|---:|---:|---:|",
    ]
    for m in metrics:
        vals = by_metric.get(m, [])
        mean, lo, hi = mean_ci(vals) if vals else (0.0, 0.0, 0.0)
        lines.append(f"| {m} | {mean:.4f} | [{lo:.4f}, {hi:.4f}] | {len(vals)} |")
    out_dirp = pathlib.Path(out_dir or "reports")
    out_dirp.mkdir(parents=True, exist_ok=True)
    path = out_dirp / f"run_{run_id}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
