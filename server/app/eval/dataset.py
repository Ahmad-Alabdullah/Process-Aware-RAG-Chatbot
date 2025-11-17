from __future__ import annotations
import json
from typing import Iterable, Dict, Any, List, Optional
from .db import upsert_query, insert_qrels


def load_queries(dataset_name: str, path: str) -> Dict[str, int]:
    id_map: Dict[str, int] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            qid = obj["query_id"]
            text = obj["text"]
            p = obj.get("process_name")
            pid = obj.get("process_id")
            roles = obj.get("roles")
            qpk = upsert_query(dataset_name, qid, text, p, pid, roles)
            id_map[qid] = qpk
    return id_map


def load_qrels(dataset_name: str, qid_to_pk: Dict[str, int], path: str) -> None:
    buf: Dict[int, List[tuple[str, int]]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            qpk = qid_to_pk[obj["query_id"]]
            buf.setdefault(qpk, []).append(
                (obj["chunk_id"], int(obj.get("relevance", 1)))
            )
    for qpk, qrels in buf.items():
        insert_qrels(qpk, qrels)


def load_answers_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            yield obj["query_id"], obj.get("answers", []), obj.get("explanation")
