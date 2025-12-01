from typing import Dict, List, Any, Set


def gating_recall(
    predicted: Dict[str, List[str]],
    expected: Dict[str, List[str]],
) -> Dict[str, float]:
    """
    Berechnet Recall für Gating-Elemente (Lanes, Nodes, Tasks).

    Returns:
        Dict mit lane_recall, node_recall, task_recall, avg_recall
    """
    results = {}

    for key in ["lane_ids", "node_ids", "task_names"]:
        pred_key = key.replace("expected_", "")
        pred_set: Set[str] = set(predicted.get(pred_key, []))
        gold_set: Set[str] = set(expected.get(f"expected_{key}", []))

        if not gold_set:
            results[f"{key}_recall"] = 1.0  # Keine Erwartung = perfekt
        else:
            overlap = len(pred_set & gold_set)
            results[f"{key}_recall"] = overlap / len(gold_set)

    # Durchschnitt
    recalls = [v for k, v in results.items() if k.endswith("_recall")]
    results["avg_gating_recall"] = sum(recalls) / len(recalls) if recalls else 0.0

    return results


def gating_precision(
    predicted: Dict[str, List[str]],
    expected: Dict[str, List[str]],
) -> Dict[str, float]:
    """
    Berechnet Precision für Gating-Elemente.
    Misst, ob der Gating-Hint zu viele irrelevante Elemente enthält.
    """
    results = {}

    for key in ["lane_ids", "node_ids", "task_names"]:
        pred_key = key.replace("expected_", "")
        pred_set: Set[str] = set(predicted.get(pred_key, []))
        gold_set: Set[str] = set(expected.get(f"expected_{key}", []))

        if not pred_set:
            results[f"{key}_precision"] = 1.0 if not gold_set else 0.0
        else:
            overlap = len(pred_set & gold_set)
            results[f"{key}_precision"] = overlap / len(pred_set)

    precisions = [v for k, v in results.items() if k.endswith("_precision")]
    results["avg_gating_precision"] = (
        sum(precisions) / len(precisions) if precisions else 0.0
    )

    return results
