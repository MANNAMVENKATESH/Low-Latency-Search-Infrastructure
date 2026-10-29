from elasticsearch import Elasticsearch
import time
import json
import statistics
from datetime import datetime

ES_URL = "http://localhost:9200"
INDEX_NAME = "products"

es = Elasticsearch(ES_URL)

queries = [
    "laptop for students",
    "budget programming laptop",
    "mobile phone with good camera",
    "affordable gaming laptop",
    "wireless headphones"
]

TRIALS = 30


def percentile(values, p):
    """
    Calculate percentile using linear interpolation.
    """
    if not values:
        return 0

    values = sorted(values)

    position = (len(values) - 1) * (p / 100)

    lower = int(position)
    upper = min(lower + 1, len(values) - 1)

    weight = position - lower

    return values[lower] + (
        values[upper] - values[lower]
    ) * weight


print("=" * 70)
print("CLOUD-30 O5 AC-2 LATENCY VALIDATION")
print("=" * 70)

# Check Elasticsearch
if not es.ping():
    raise RuntimeError("Elasticsearch is not reachable")

print(f"Elasticsearch: {ES_URL}")
print(f"Index: {INDEX_NAME}")
print(f"Trials per query: {TRIALS}")

# Get document count
count_response = es.count(index=INDEX_NAME)
document_count = count_response["count"]

print(f"Documents: {document_count}")

all_latencies = []
total_requests = 0
total_errors = 0

results = {}

for query in queries:

    print()
    print(f"Query: {query}")
    print("-" * 70)

    latencies = []
    errors = 0

    # Warm-up request
    es.search(
        index=INDEX_NAME,
        size=5,
        query={
            "multi_match": {
                "query": query,
                "fields": [
                    "title",
                    "description",
                    "tags"
                ]
            }
        }
    )

    # Measured requests
    for _ in range(TRIALS):

        start = time.perf_counter()

        try:

            response = es.search(
                index=INDEX_NAME,
                size=5,
                query={
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "title",
                            "description",
                            "tags"
                        ]
                    }
                }
            )

            end = time.perf_counter()

            latency_ms = (end - start) * 1000

            latencies.append(latency_ms)

        except Exception as error:

            errors += 1
            total_errors += 1

            print(f"Request error: {error}")

    total_requests += TRIALS

    all_latencies.extend(latencies)

    if latencies:

        p50 = percentile(latencies, 50)
        p95 = percentile(latencies, 95)
        p99 = percentile(latencies, 99)

        minimum = min(latencies)
        maximum = max(latencies)
        average = statistics.mean(latencies)

    else:

        p50 = 0
        p95 = 0
        p99 = 0
        minimum = 0
        maximum = 0
        average = 0

    error_rate = (
        errors / TRIALS * 100
        if TRIALS
        else 0
    )

    results[query] = {
        "trials": TRIALS,
        "successful_requests": len(latencies),
        "errors": errors,
        "error_rate_percent": round(error_rate, 2),
        "min_ms": round(minimum, 3),
        "average_ms": round(average, 3),
        "p50_ms": round(p50, 3),
        "p95_ms": round(p95, 3),
        "p99_ms": round(p99, 3),
        "max_ms": round(maximum, 3)
    }

    print(f"Successful requests: {len(latencies)}/{TRIALS}")
    print(f"Error rate: {error_rate:.2f}%")
    print(f"Min: {minimum:.3f} ms")
    print(f"Average: {average:.3f} ms")
    print(f"P50: {p50:.3f} ms")
    print(f"P95: {p95:.3f} ms")
    print(f"P99: {p99:.3f} ms")
    print(f"Max: {maximum:.3f} ms")


# Overall statistics
print()
print("=" * 70)
print("O5 AC-2 LATENCY SUMMARY")
print("=" * 70)

if all_latencies:

    overall_p50 = percentile(all_latencies, 50)
    overall_p95 = percentile(all_latencies, 95)
    overall_p99 = percentile(all_latencies, 99)

    overall_average = statistics.mean(all_latencies)
    overall_min = min(all_latencies)
    overall_max = max(all_latencies)

else:

    overall_p50 = 0
    overall_p95 = 0
    overall_p99 = 0
    overall_average = 0
    overall_min = 0
    overall_max = 0

overall_error_rate = (
    total_errors / total_requests * 100
    if total_requests
    else 0
)

print(f"Total requests: {total_requests}")
print(f"Successful requests: {total_requests - total_errors}")
print(f"Errors: {total_errors}")
print(f"Overall error rate: {overall_error_rate:.2f}%")
print(f"Overall minimum: {overall_min:.3f} ms")
print(f"Overall average: {overall_average:.3f} ms")
print(f"Overall P50: {overall_p50:.3f} ms")
print(f"Overall P95: {overall_p95:.3f} ms")
print(f"Overall P99: {overall_p99:.3f} ms")
print(f"Overall maximum: {overall_max:.3f} ms")

# Save results
output = {
    "benchmark": "CLOUD-30 O2 Latency Baseline",
    "timestamp": datetime.now().isoformat(),
    "elasticsearch_url": ES_URL,
    "index": INDEX_NAME,
    "document_count": document_count,
    "trials_per_query": TRIALS,
    "total_requests": total_requests,
    "total_errors": total_errors,
    "overall_error_rate_percent": round(
        overall_error_rate, 2
    ),
    "overall": {
        "min_ms": round(overall_min, 3),
        "average_ms": round(overall_average, 3),
        "p50_ms": round(overall_p50, 3),
        "p95_ms": round(overall_p95, 3),
        "p99_ms": round(overall_p99, 3),
        "max_ms": round(overall_max, 3)
    },
    "queries": results
}

with open(
    "results/o5/o5_ac2_latency_after_config.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(output, f, indent=2)

print()
print("Saved to:")
print("o5_ac2_latency.json")

print("=" * 70)

