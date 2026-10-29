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

ab_results = {}
all_variant_latencies = {
    "A_full_source": [],
    "B_selected_fields": []
}

ab_results = {}
all_variant_latencies = {
    "A_full_source": [],
    "B_selected_fields": []
}

ab_results = {}
all_variant_latencies = {
    "A_full_source": [],
    "B_selected_fields": []
}

ab_results = {}
all_variant_latencies = {
    "A_full_source": [],
    "B_selected_fields": []
}

for query in queries:
    print()
    print(f"Query: {query}")
    print("-" * 70)

    variants = {
        "A_full_source": {},
        "B_selected_fields": {
            "_source": ["title", "price", "category", "brand", "rating", "tags"]
        }
    }

    latencies = {name: [] for name in variants}
    errors = {name: 0 for name in variants}

    # Warm up both variants before measurement.
    for name, options in variants.items():
        es.search(
            index=INDEX_NAME,
            size=5,
            query={
                "multi_match": {
                    "query": query,
                    "fields": ["title", "description", "tags"]
                }
            },
            **options
        )

    # Alternate A/B order to reduce order bias.
    for trial in range(TRIALS):
        order = list(variants.items())
        if trial % 2:
            order.reverse()

        for name, options in order:
            start_time = time.perf_counter()
            try:
                es.search(
                    index=INDEX_NAME,
                    size=5,
                    query={
                        "multi_match": {
                            "query": query,
                            "fields": ["title", "description", "tags"]
                        }
                    },
                    **options
                )
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                latencies[name].append(elapsed_ms)
                all_variant_latencies[name].append(elapsed_ms)
            except Exception as error:
                errors[name] += 1
                print(f"{name} request error: {error}")

    query_result = {}
    for name in variants:
        values = latencies[name]
        query_result[name] = {
            "successful_requests": len(values),
            "errors": errors[name],
            "average_ms": round(statistics.mean(values), 3) if values else None,
            "p50_ms": round(percentile(values, 50), 3) if values else None,
            "p95_ms": round(percentile(values, 95), 3) if values else None,
            "p99_ms": round(percentile(values, 99), 3) if values else None,
            "max_ms": round(max(values), 3) if values else None
        }

        print(
            f"{name}: success={len(values)}/{TRIALS}, "
            f"errors={errors[name]}, "
            f"avg={query_result[name]['average_ms']} ms, "
            f"P95={query_result[name]['p95_ms']} ms"
        )

    ab_results[query] = query_result
# Save results
output = {
    "benchmark": "CLOUD-30 O5 AC-2 Paired A/B Latency Experiment",
    "timestamp": datetime.now().isoformat(),
    "elasticsearch_url": ES_URL,
    "index": INDEX_NAME,
    "document_count": document_count,
    "trials_per_query_per_variant": TRIALS,
    "method": (
        "Paired A/B test with alternating request order, one warm-up "
        "per variant per query, and 30 measured trials per query."
    ),
    "variants": {}
}

for variant_name in ("A_full_source", "B_selected_fields"):
    values = all_variant_latencies[variant_name]
    variant_queries = {}

    for query, query_result in ab_results.items():
        variant_queries[query] = query_result[variant_name]

    successful = len(values)
    errors = sum(
        item["errors"] for item in variant_queries.values()
    )
    expected = len(queries) * TRIALS

    output["variants"][variant_name] = {
        "source_filter": (
            None if variant_name == "A_full_source"
            else ["title", "price", "category", "brand", "rating", "tags"]
        ),
        "queries": variant_queries,
        "summary": {
            "expected_requests": expected,
            "successful_requests": successful,
            "errors": errors,
            "error_rate_percent": round(errors / expected * 100, 2),
            "minimum_ms": round(min(values), 3) if values else None,
            "average_ms": round(statistics.mean(values), 3) if values else None,
            "p50_ms": round(percentile(values, 50), 3) if values else None,
            "p95_ms": round(percentile(values, 95), 3) if values else None,
            "p99_ms": round(percentile(values, 99), 3) if values else None,
            "maximum_ms": round(max(values), 3) if values else None
        }
    }

output_path = "results/o5/o5_ac2_ab_experiment.json"

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print()
for variant_name in ("A_full_source", "B_selected_fields"):
    print(f"=== {variant_name} OVERALL ===")
    print(json.dumps(output["variants"][variant_name]["summary"], indent=2))

print()
print("Saved A/B results to:")
print(output_path)
print("=" * 70)
