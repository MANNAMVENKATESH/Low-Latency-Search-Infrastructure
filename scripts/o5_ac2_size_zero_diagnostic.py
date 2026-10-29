from elasticsearch import Elasticsearch
import time
import statistics
import json
from datetime import datetime

es = Elasticsearch("http://localhost:9200")
queries = [
    "laptop for students",
    "budget programming laptop",
    "mobile phone with good camera",
    "affordable gaming laptop",
    "wireless headphones"
]
TRIALS = 30

def percentile(values, p):
    values = sorted(values)
    position = (len(values) - 1) * p / 100
    low = int(position)
    high = min(low + 1, len(values) - 1)
    weight = position - low
    return values[low] * (1 - weight) + values[high] * weight

if not es.ping():
    raise RuntimeError("Elasticsearch is not reachable")

results = {}

for query in queries:
    # Warm up
    es.search(
        index="products",
        size=0,
        query={"multi_match": {
            "query": query,
            "fields": ["title", "description", "tags"]
        }}
    )

    timings = []
    for _ in range(TRIALS):
        start = time.perf_counter()
        es.search(
            index="products",
            size=0,
            query={"multi_match": {
                "query": query,
                "fields": ["title", "description", "tags"]
            }}
        )
        timings.append((time.perf_counter() - start) * 1000)

    results[query] = {
        "average_ms": round(statistics.mean(timings), 3),
        "p50_ms": round(percentile(timings, 50), 3),
        "p95_ms": round(percentile(timings, 95), 3),
        "p99_ms": round(percentile(timings, 99), 3),
        "max_ms": round(max(timings), 3)
    }
    print(query, json.dumps(results[query]))

output = {
    "benchmark": "CLOUD-30 O5 AC-2 size-zero diagnostic",
    "timestamp": datetime.now().isoformat(),
    "index": "products",
    "trials_per_query": TRIALS,
    "note": "Diagnostic only; size=0 does not return search hits.",
    "queries": results
}

path = "results/o5/o5_ac2_size_zero_diagnostic.json"
with open(path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("\nSaved to:", path)
