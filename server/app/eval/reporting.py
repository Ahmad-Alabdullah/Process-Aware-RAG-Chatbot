"""
Erweitertes Reporting-System für RAG Evaluation.

Features:
- Markdown export
- Baseline-Vergleich mit Δ und Signifikanz
- Metrik-Gruppierung (Retrieval, Generation, Faithfulness, H2)
- Confidence Intervals
- Best/Worst Query Analyse
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from datetime import datetime
import statistics
import yaml
import csv

from app.core.clients import get_logger

from .db import get_pool, upsert_aggregate
from .stats import paired_bootstrap


logger = get_logger(__name__)

# ============================================================
# METRIK-KATEGORIEN
# ============================================================

METRIC_GROUPS = {
    "retrieval": {
        "name": "Retrieval-Metriken",
        "metrics": [
            "recall@3",
            "recall@5",
            "recall@10",
            "mrr@3",
            "mrr@5",
            "mrr@10",
            "ndcg@3",
            "ndcg@5",
            "ndcg@10",
        ],
        "primary": "recall@5",
        "higher_is_better": True,
    },
    "generation": {
        "name": "Generation-Metriken",
        "metrics": [
            "semantic_sim",
            "rouge_l_recall",
            "content_f1",
            "bertscore_f1",
        ],
        "primary": "semantic_sim",
        "higher_is_better": True,
    },
    "faithfulness": {
        "name": "Faithfulness-Metriken",
        "metrics": [
            "citation_recall",
            "citation_precision",
            "factual_consistency_score",
            "factual_consistency_normalized",
        ],
        "primary": "factual_consistency_normalized",
        "higher_is_better": True,
    },
    "h2_gating": {
        "name": "H2 Gating-Metriken",
        "metrics": [
            "h2_error_rate",
            "h2_structure_violation_rate",
            "h2_hallucination_rate",
            "h2_hint_adherence",
            "h2_knowledge_score",
            "h2_context_respected",
            "h2_integration_score",
            "h2_scope_violation_rate",
            "gating_avg_gating_recall",
            "gating_avg_gating_precision",
        ],
        "primary": "h2_error_rate",
        "higher_is_better": False,  # Niedriger = besser
    },
}


def mean_ci(xs: List[float], z: float = 1.96) -> Tuple[float, float, float]:
    """Berechnet Mittelwert und 95% Konfidenzintervall."""
    if not xs:
        return 0.0, 0.0, 0.0
    m = statistics.mean(xs)
    if len(xs) < 2:
        return m, m, m
    se = statistics.stdev(xs) / (len(xs) ** 0.5)
    return m, m - z * se, m + z * se


def _format_delta(delta: float, higher_is_better: bool = True) -> str:
    """Formatiert Delta mit Pfeil und Farbe."""
    if abs(delta) < 0.001:
        return "≈0"

    if higher_is_better:
        arrow = "↑" if delta > 0 else "↓"
        sign = "+" if delta > 0 else ""
    else:
        arrow = "↓" if delta < 0 else "↑"  # Für Fehlerraten ist niedriger besser
        sign = "" if delta < 0 else "+"

    return f"{arrow} {sign}{delta:.4f}"


def _significance_marker(p_value: float) -> str:
    """Gibt Signifikanz-Marker zurück."""
    if p_value < 0.001:
        return "***"
    elif p_value < 0.01:
        return "**"
    elif p_value < 0.05:
        return "*"
    else:
        return ""


# ============================================================
# EINZELNER RUN REPORT
# ============================================================


def aggregate_and_store(
    run_id: int,
    metrics: List[str],
    out_dir: Optional[str] = None,
    baseline_run_id: Optional[int] = None,
) -> str:
    """
    Aggregiert Metriken und erstellt Report.

    Args:
        run_id: ID des Runs
        metrics: Liste der zu aggregierenden Metriken
        out_dir: Ausgabeverzeichnis
        baseline_run_id: Optional - ID der Baseline für Vergleich
    """
    pool = get_pool()

    # Run-Info laden
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT run_name, config_json, created_at FROM ragrun.eval_runs WHERE id = %s",
            (run_id,),
        )
        row = cur.fetchone()
        run_name = row[0] if row else f"run_{run_id}"
        config = row[1] if row else {}
        created_at = row[2] if row else datetime.now()

    # Metriken laden
    by_metric: Dict[str, List[float]] = {m: [] for m in metrics}
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT metric, value FROM ragrun.eval_scores WHERE run_id = %s", (run_id,)
        )
        for metric, value in cur.fetchall():
            if metric in by_metric:
                by_metric[metric].append(float(value))

    # Baseline-Daten laden (falls vorhanden)
    baseline_metrics: Dict[str, Tuple[float, float, float]] = {}
    if baseline_run_id:
        with pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT metric, value FROM ragrun.eval_scores WHERE run_id = %s",
                (baseline_run_id,),
            )
            baseline_by_metric: Dict[str, List[float]] = {}
            for metric, value in cur.fetchall():
                if metric not in baseline_by_metric:
                    baseline_by_metric[metric] = []
                baseline_by_metric[metric].append(float(value))

            for m, vals in baseline_by_metric.items():
                baseline_metrics[m] = mean_ci(vals)

    # Aggregieren und speichern
    aggregates: Dict[str, Dict[str, Any]] = {}
    for m in metrics:
        vals = by_metric.get(m, [])
        mean, lo, hi = mean_ci(vals) if vals else (0.0, 0.0, 0.0)
        upsert_aggregate(run_id, m, mean, len(vals), (lo, hi))

        aggregates[m] = {
            "mean": mean,
            "ci_low": lo,
            "ci_high": hi,
            "n": len(vals),
        }

        # Delta zur Baseline
        if m in baseline_metrics:
            baseline_mean = baseline_metrics[m][0]
            aggregates[m]["baseline_mean"] = baseline_mean
            aggregates[m]["delta"] = mean - baseline_mean

    # Output-Verzeichnis
    out_path = Path(out_dir or "reports")
    out_path.mkdir(parents=True, exist_ok=True)

    # Markdown Report
    md_path = _write_markdown_report(
        out_path, run_id, run_name, created_at, config, aggregates, baseline_run_id
    )

    return str(md_path)


def _write_markdown_report(
    out_path: Path,
    run_id: int,
    run_name: str,
    created_at: datetime,
    config: Dict[str, Any],
    aggregates: Dict[str, Dict[str, Any]],
    baseline_run_id: Optional[int],
) -> Path:
    """Schreibt ausführlichen Markdown-Report."""

    lines = [
        f"# Evaluation Report: {run_name}",
        "",
        f"**Run ID:** {run_id}",
        f"**Erstellt:** {created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Dataset:** {config.get('dataset', 'unknown')}",
    ]

    if baseline_run_id:
        lines.append(f"**Baseline:** run_id={baseline_run_id}")

    lines.extend(["", "---", ""])

    # Konfiguration
    lines.extend(
        [
            "## Konfiguration",
            "",
            "```yaml",
        ]
    )

    # Wichtigste Config-Parameter
    qa_payload = config.get("qa_payload", {})
    factors = config.get("factors", {})

    lines.extend(
        [
            f"model: {qa_payload.get('model', 'unknown')}",
            f"top_k: {qa_payload.get('top_k', 5)}",
            f"use_rerank: {qa_payload.get('use_rerank', False)}",
            f"prompt_style: {qa_payload.get('prompt_style', 'baseline')}",
            f"retrieval_mode: {factors.get('retrieval', {}).get('mode', 'hybrid')}",
            f"rrf_k: {factors.get('retrieval', {}).get('rrf_k', 60)}",
            "```",
            "",
        ]
    )

    # Metriken nach Gruppen
    for group_key, group_info in METRIC_GROUPS.items():
        group_metrics = [m for m in group_info["metrics"] if m in aggregates]

        if not group_metrics:
            continue

        lines.extend(
            [
                f"## {group_info['name']}",
                "",
            ]
        )

        # Tabellen-Header
        if baseline_run_id:
            lines.extend(
                [
                    "| Metrik | Mean | 95% CI | N | Baseline | Δ |",
                    "|--------|-----:|--------|--:|--------:|---:|",
                ]
            )
        else:
            lines.extend(
                [
                    "| Metrik | Mean | 95% CI | N |",
                    "|--------|-----:|--------|--:|",
                ]
            )

        higher_is_better = group_info.get("higher_is_better", True)

        for m in group_metrics:
            agg = aggregates[m]
            mean = agg["mean"]
            ci = f"[{agg['ci_low']:.4f}, {agg['ci_high']:.4f}]"
            n = agg["n"]

            # Primary metric hervorheben
            prefix = "**" if m == group_info.get("primary") else ""
            suffix = "**" if m == group_info.get("primary") else ""

            if baseline_run_id and "delta" in agg:
                baseline = agg["baseline_mean"]
                delta = _format_delta(agg["delta"], higher_is_better)
                lines.append(
                    f"| {prefix}{m}{suffix} | {mean:.4f} | {ci} | {n} | {baseline:.4f} | {delta} |"
                )
            else:
                lines.append(f"| {prefix}{m}{suffix} | {mean:.4f} | {ci} | {n} |")

        lines.append("")

    # Footer
    lines.extend(
        [
            "---",
            "",
            f"*Report generiert am {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        ]
    )

    md_path = out_path / f"run_{run_id}_{run_name}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    return md_path


# ============================================================
# STUDY COMPARISON REPORT (OFAT vs Baseline)
# ============================================================


def generate_study_report(
    study_name: str,
    baseline_run_name: str,
    variant_run_names: List[str],
    primary_metrics: List[str] = None,
    out_dir: Optional[str] = None,
    significance_iters: int = 2000,
) -> str:
    """
    Generiert Vergleichsreport für eine Study (OFAT, GSO, etc.).

    Args:
        study_name: Name der Study
        baseline_run_name: Name des Baseline-Runs
        variant_run_names: Namen der Varianten-Runs
        primary_metrics: Primäre Metriken für Vergleich
        out_dir: Ausgabeverzeichnis
        significance_iters: Iterationen für Bootstrap-Test
    """
    if primary_metrics is None:
        primary_metrics = ["recall@5", "factual_consistency_normalized", "semantic_sim"]

    pool = get_pool()
    out_path = Path(out_dir or "reports")
    out_path.mkdir(parents=True, exist_ok=True)

    # Baseline-Daten laden
    baseline_data = _load_run_data(pool, baseline_run_name)
    if not baseline_data:
        raise ValueError(f"Baseline '{baseline_run_name}' nicht gefunden")

    # Varianten-Daten laden
    variants_data = []
    for name in variant_run_names:
        data = _load_run_data(pool, name)
        if data:
            variants_data.append(data)

    # Report generieren
    lines = [
        f"# Study Report: {study_name}",
        "",
        f"**Baseline:** {baseline_run_name}",
        f"**Varianten:** {len(variants_data)}",
        f"**Primäre Metriken:** {', '.join(primary_metrics)}",
        "",
        "---",
        "",
    ]

    # Übersichtstabelle
    lines.extend(
        [
            "## Übersicht: Primäre Metriken",
            "",
            "| Variante | " + " | ".join(primary_metrics) + " |",
            "|----------|" + "|".join(["---:" for _ in primary_metrics]) + "|",
        ]
    )

    # Baseline-Zeile
    baseline_cells = []
    for m in primary_metrics:
        val = baseline_data["aggregates"].get(m, {}).get("mean", 0)
        baseline_cells.append(f"{val:.4f}")
    lines.append(
        f"| **{baseline_run_name}** (Baseline) | " + " | ".join(baseline_cells) + " |"
    )

    # Varianten-Zeilen
    for var in variants_data:
        cells = []
        for m in primary_metrics:
            var_val = var["aggregates"].get(m, {}).get("mean", 0)
            base_val = baseline_data["aggregates"].get(m, {}).get("mean", 0)
            delta = var_val - base_val

            # Signifikanz berechnen
            try:
                _, p_val, _ = paired_bootstrap(
                    baseline_data["run_id"], var["run_id"], m, iters=significance_iters
                )
                sig = _significance_marker(p_val)
            except Exception:
                sig = ""

            higher_is_better = _get_higher_is_better(m)
            delta_str = _format_delta(delta, higher_is_better)
            cells.append(f"{var_val:.4f} ({delta_str}{sig})")

        lines.append(f"| {var['run_name']} | " + " | ".join(cells) + " |")

    lines.extend(
        [
            "",
            "*Signifikanz: *** p<0.001, ** p<0.01, * p<0.05*",
            "",
        ]
    )

    # Ranking nach primärer Metrik
    primary = primary_metrics[0]
    lines.extend(
        [
            f"## Ranking nach {primary}",
            "",
        ]
    )

    all_runs = [baseline_data] + variants_data
    sorted_runs = sorted(
        all_runs,
        key=lambda x: x["aggregates"].get(primary, {}).get("mean", 0),
        reverse=_get_higher_is_better(primary),
    )

    for i, run in enumerate(sorted_runs, 1):
        val = run["aggregates"].get(primary, {}).get("mean", 0)
        is_baseline = run["run_name"] == baseline_run_name
        marker = " (Baseline)" if is_baseline else ""
        lines.append(f"{i}. **{run['run_name']}**{marker}: {val:.4f}")

    lines.extend(["", "---", ""])

    # Detaillierte Vergleiche pro Variante
    lines.extend(
        [
            "## Detailvergleiche",
            "",
        ]
    )

    for var in variants_data:
        lines.extend(
            [
                f"### {var['run_name']}",
                "",
                "| Metrik | Baseline | Variante | Δ | Sig |",
                "|--------|--------:|--------:|---:|:---:|",
            ]
        )

        for m in primary_metrics + ["recall@3", "recall@10", "citation_recall"]:
            base_val = baseline_data["aggregates"].get(m, {}).get("mean", 0)
            var_val = var["aggregates"].get(m, {}).get("mean", 0)
            delta = var_val - base_val

            try:
                _, p_val, _ = paired_bootstrap(
                    baseline_data["run_id"], var["run_id"], m, iters=significance_iters
                )
                sig = _significance_marker(p_val)
            except Exception:
                sig = ""

            higher_is_better = _get_higher_is_better(m)
            delta_str = _format_delta(delta, higher_is_better)

            lines.append(
                f"| {m} | {base_val:.4f} | {var_val:.4f} | {delta_str} | {sig} |"
            )

        lines.extend(["", ""])

    # Footer
    lines.extend(
        [
            "---",
            "",
            f"*Report generiert am {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        ]
    )

    # Schreiben
    md_path = out_path / f"study_{study_name}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    # YAML für maschinelle Verarbeitung
    yaml_data = {
        "study_name": study_name,
        "baseline": baseline_run_name,
        "variants": [v["run_name"] for v in variants_data],
        "rankings": {},
    }

    for m in primary_metrics:
        sorted_by_m = sorted(
            all_runs,
            key=lambda x: x["aggregates"].get(m, {}).get("mean", 0),
            reverse=_get_higher_is_better(m),
        )
        yaml_data["rankings"][m] = [
            {"name": r["run_name"], "value": r["aggregates"].get(m, {}).get("mean", 0)}
            for r in sorted_by_m
        ]

    yaml_path = out_path / f"study_{study_name}.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)

    return str(md_path)


def _load_run_data(pool, run_name: str) -> Optional[Dict[str, Any]]:
    """Lädt alle Daten für einen Run."""
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, config_json FROM ragrun.eval_runs WHERE run_name = %s",
            (run_name,),
        )
        row = cur.fetchone()
        if not row:
            return None

        run_id, config = row

        # Aggregierte Metriken laden
        cur.execute(
            "SELECT metric, mean_val, n, ci_json FROM ragrun.aggregates WHERE run_id = %s",
            (run_id,),
        )

        aggregates = {}
        for metric, mean_val, n, ci_json in cur.fetchall():
            aggregates[metric] = {
                "mean": float(mean_val),
                "n": n,
                "ci": ci_json,
            }

        return {
            "run_id": run_id,
            "run_name": run_name,
            "config": config,
            "aggregates": aggregates,
        }


def _get_higher_is_better(metric: str) -> bool:
    """Bestimmt ob höhere Werte besser sind."""
    lower_is_better = [
        "h2_error_rate",
        "h2_structure_violation_rate",
        "h2_hallucination_rate",
        "h2_scope_violation_rate",
        "output_violation_rate",
        "output_hallucination_rate",
    ]
    return metric not in lower_is_better


# def generate_comparison_table(
#     baseline_run_name: str,
#     variant_run_names: List[str],
#     metrics: List[str] = None,
# ) -> str:
#     """
#     Generiert eine Vergleichstabelle für Konsole/Log.

#     Beispiel-Output:
#     ┌──────────────────────┬──────────┬──────────┬──────────┐
#     │ Metrik               │ BASELINE │ OFAT_k8  │ Δ        │
#     ├──────────────────────┼──────────┼──────────┼──────────┤
#     │ recall@5             │ 0.7234   │ 0.7654   │ ↑+0.0420 │
#     │ factual_consistency  │ 0.7123   │ 0.7234   │ ↑+0.0111 │
#     └──────────────────────┴──────────┴──────────┴──────────┘
#     """
#     if metrics is None:
#         metrics = ["recall@5", "factual_consistency_normalized", "semantic_sim"]

#     pool = get_pool()

#     # Daten laden
#     baseline_data = _load_run_data(pool, baseline_run_name)
#     if not baseline_data:
#         return f"Baseline '{baseline_run_name}' nicht gefunden"

#     lines = []
#     header = f"| {'Metrik':<30} | {baseline_run_name:<12} |"
#     separator = f"|{'-'*32}|{'-'*14}|"

#     for var_name in variant_run_names:
#         header += f" {var_name:<12} | {'Δ':<10} |"
#         separator += f"{'-'*14}|{'-'*12}|"

#     lines.append(separator)
#     lines.append(header)
#     lines.append(separator)

#     for m in metrics:
#         base_val = baseline_data["aggregates"].get(m, {}).get("mean", 0)
#         row = f"| {m:<30} | {base_val:>12.4f} |"

#         for var_name in variant_run_names:
#             var_data = _load_run_data(pool, var_name)
#             if var_data:
#                 var_val = var_data["aggregates"].get(m, {}).get("mean", 0)
#                 delta = var_val - base_val
#                 higher_is_better = _get_higher_is_better(m)
#                 delta_str = _format_delta(delta, higher_is_better)
#                 row += f" {var_val:>12.4f} | {delta_str:<10} |"
#             else:
#                 row += f" {'N/A':>12} | {'N/A':<10} |"

#         lines.append(row)

#     lines.append(separator)

#     return "\n".join(lines)
