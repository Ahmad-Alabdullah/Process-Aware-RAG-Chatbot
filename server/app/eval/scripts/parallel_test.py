"""
Parallelitäts-Test für QA-Endpoint

Simuliert mehrere gleichzeitige Nutzer und misst:
- Durchschnittliche Latenz
- Throughput (Requests/Sekunde)
- Erfolgsrate

Usage:
    python -m app.eval.scripts.parallel_test --users 2 --queries 5
"""

import asyncio
import time
import argparse
import statistics
from typing import List, Dict, Any
import httpx

# Standard-Queries für Tests
TEST_QUERIES = [
    {"query": "Wie beantrage ich Bildungszeit?", "process_name": "Weiterbildungsangebot"},
    {"query": "Welche Unterlagen brauche ich für eine Dienstreise?", "process_name": "Dienstreiseantrag"},
    {"query": "Wie funktioniert mobiles Arbeiten?", "process_name": "Mobiles Arbeiten"},
    {"query": "Was muss ich bei Elternzeit beachten?", "process_name": "Mutterschutz und Elternzeit"},
    {"query": "Wie melde ich eine Nebentätigkeit an?", "process_name": "Nebentätigkeit"},
]

QA_URL = "http://localhost:8000/api/qa/ask?os_index=chunks_semantic_qwen3&qdrant_collection=chunks_semantic_qwen3&embedding_backend=ollama&embedding_model=qwen3-embedding:4b"


async def send_query(client: httpx.AsyncClient, query_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """Sendet eine Query und misst die Latenz."""
    payload = {
        "query": query_data["query"],
        "process_name": query_data["process_name"],
        "top_k": 5,
        "use_rerank": False,
        "use_hyde": False,
        "prompt_style": "cot",
        "debug_return": False,
    }
    
    start = time.perf_counter()
    try:
        resp = await client.post(QA_URL, json=payload, timeout=120.0)
        elapsed = time.perf_counter() - start
        
        if resp.status_code == 200:
            return {
                "success": True,
                "latency": elapsed,
                "user_id": user_id,
                "query": query_data["query"][:50],
            }
        else:
            return {
                "success": False,
                "latency": elapsed,
                "user_id": user_id,
                "error": f"HTTP {resp.status_code}",
            }
    except Exception as e:
        elapsed = time.perf_counter() - start
        return {
            "success": False,
            "latency": elapsed,
            "user_id": user_id,
            "error": str(e),
        }


async def simulate_user(client: httpx.AsyncClient, user_id: int, queries: List[Dict], results: List) -> None:
    """Simuliert einen einzelnen Nutzer der Queries sendet."""
    for query_data in queries:
        result = await send_query(client, query_data, user_id)
        results.append(result)
        print(f"  User {user_id}: {result['latency']:.2f}s - {'✓' if result['success'] else '✗'}")


async def run_parallel_test(num_users: int, queries_per_user: int) -> Dict[str, Any]:
    """Führt den Parallelitäts-Test durch."""
    print(f"\n{'='*60}")
    print(f"Parallelitäts-Test: {num_users} User, {queries_per_user} Queries/User")
    print(f"{'='*60}\n")
    
    # Queries für jeden User vorbereiten
    user_queries = [
        TEST_QUERIES[:queries_per_user] for _ in range(num_users)
    ]
    
    results: List[Dict[str, Any]] = []
    
    async with httpx.AsyncClient() as client:
        start_time = time.perf_counter()
        
        # Alle User parallel starten
        await asyncio.gather(*[
            simulate_user(client, i + 1, user_queries[i], results)
            for i in range(num_users)
        ])
        
        total_time = time.perf_counter() - start_time
    
    # Auswertung
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    if successful:
        latencies = [r["latency"] for r in successful]
        stats = {
            "total_requests": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) * 100,
            "total_time": total_time,
            "throughput": len(successful) / total_time,
            "avg_latency": statistics.mean(latencies),
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "p50_latency": statistics.median(latencies),
            "p95_latency": sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0],
        }
    else:
        stats = {
            "total_requests": len(results),
            "successful": 0,
            "failed": len(failed),
            "success_rate": 0,
            "error": "All requests failed",
        }
    
    return stats


def print_results(stats: Dict[str, Any]) -> None:
    """Gibt die Testergebnisse aus."""
    print(f"\n{'='*60}")
    print("ERGEBNISSE")
    print(f"{'='*60}")
    print(f"Requests gesamt:    {stats['total_requests']}")
    print(f"Erfolgreich:        {stats['successful']}")
    print(f"Fehlgeschlagen:     {stats['failed']}")
    print(f"Erfolgsrate:        {stats['success_rate']:.1f}%")
    print(f"{'='*60}")
    
    if stats.get("avg_latency"):
        print(f"Gesamtzeit:         {stats['total_time']:.2f}s")
        print(f"Throughput:         {stats['throughput']:.2f} req/s")
        print(f"{'='*60}")
        print(f"Latenz (Avg):       {stats['avg_latency']:.2f}s")
        print(f"Latenz (Min):       {stats['min_latency']:.2f}s")
        print(f"Latenz (Max):       {stats['max_latency']:.2f}s")
        print(f"Latenz (P50):       {stats['p50_latency']:.2f}s")
        print(f"Latenz (P95):       {stats['p95_latency']:.2f}s")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Parallelitäts-Test für QA-Endpoint")
    parser.add_argument("--users", type=int, default=2, help="Anzahl simulierter Nutzer")
    parser.add_argument("--queries", type=int, default=3, help="Queries pro Nutzer")
    args = parser.parse_args()
    
    stats = asyncio.run(run_parallel_test(args.users, args.queries))
    print_results(stats)


if __name__ == "__main__":
    main()
