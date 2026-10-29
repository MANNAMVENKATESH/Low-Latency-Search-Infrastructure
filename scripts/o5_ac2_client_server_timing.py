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
    lo = int(position)
    hi = min(lo + 1, len(values) - 1)
    weight = position - lo
    return values[lo] * (1 - weight) + values[hi] * weight

results = {}

for query in queries:
    es.search(
        index="products",
        size=5,
        query={"multi_match": {
            "query": query,
            "fields": ["title", "description", "tags"]
        }}
    )

    client_ms = []
    server_ms = []

    for _ in range(TRIALS):
        start = time.perf_counter()
        response = es.search(
            index="products",
            size=5,
            query={"multi_match": {
                "query": query,
                "fields": ["title", "description", "tags"]
            }}
        )
        client_ms.append((time.perf_counter() - start) * 1000)
        server_ms.append(float(response["took"]))

    results[query] = {
        "client_average_ms": round(statistics.mean(client_ms), 3),
        "client_p95_ms": round(percentile(client_ms, 95), 3),
        "server_took_average_ms": round(statistics.mean(server_ms), 3),
        "server_took_p95_ms": round(percentile(server_ms, 95), 3)
    }
    print(query, json.dumps(results[query]))

output = {
    "benchmark": "CLOUD-30 O5 AC-2 Client vs Server Timing Diagnostic",
    "timestamp": datetime.now().isoformat(),
    "index": "products",
    "trials_per_query": TRIALS,
    "queries": results
}

path = "results/o5/o5_ac2_client_server_timing.json"
with open(path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("\nSaved to:", path)
