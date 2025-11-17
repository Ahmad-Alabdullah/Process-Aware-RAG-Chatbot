from __future__ import annotations
from typing import List, Tuple, Dict
import random, statistics
from .db import get_pool


def fetch_per_query_scores(run_id: int, metric: str) -> Dict[int, float]:
    pool = get_pool()
    vals: Dict[int, float] = {}
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            "select query_pk, value from ragrun.scores where run_id=%s and metric=%s",
            (run_id, metric),
        )
        for qpk, v in cur.fetchall():
            vals[int(qpk)] = float(v)
    return vals


def paired_bootstrap(
    run_a: int, run_b: int, metric: str, iters: int = 10000, seed: int = 42
) -> Tuple[float, float, float]:
    ra = fetch_per_query_scores(run_a, metric)
    rb = fetch_per_query_scores(run_b, metric)
    keys = sorted(set(ra.keys()) & set(rb.keys()))
    if not keys:
        raise ValueError("No overlapping queries between runs for metric=" + metric)
    diffs = [rb[k] - ra[k] for k in keys]
    delta_mean = statistics.mean(diffs)
    rnd = random.Random(seed)
    boots = []
    for _ in range(iters):
        sample = [diffs[rnd.randrange(0, len(diffs))] for __ in range(len(diffs))]
        boots.append(statistics.mean(sample))
    boots.sort()
    if delta_mean >= 0:
        p = sum(1 for b in boots if b <= 0.0) / len(boots)
    else:
        p = sum(1 for b in boots if b >= 0.0) / len(boots)
    p_two = min(1.0, 2.0 * p)
    lo = boots[int(0.025 * len(boots))]
    hi = boots[int(0.975 * len(boots)) - 1]
    half = (hi - lo) / 2.0
    return (delta_mean, p_two, half)
