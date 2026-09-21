from elasticsearch import Elasticsearch
import time
import statistics
import json
import os

ES_URL = "http://localhost:9200"
SOURCE_INDEX = "products"
TARGET_INDEX = "products_reindexed"

es = Elasticsearch(ES_URL)

QUERIES = [
    "laptop for students",
    "budget programming laptop",
    "mobile phone with good camera",
    "affordable gaming laptop",
    "wireless headphones"
]

TRIALS = 30


def create_target_index():
    if es.indices.exists(index=TARGET_INDEX):
        print(f"Deleting existing {TARGET_INDEX}...")
        es.indices.delete(index=TARGET_INDEX)

    print(f"Creating {TARGET_INDEX}...")

    es.indices.create(
        index=TARGET_INDEX,
        mappings={
            "properties": {
                "title": {"type": "text"},
                "description": {"type": "text"},
                "category": {"type": "keyword"},
                "brand": {"type": "keyword"},
                "price": {"type": "float"},
                "rating": {"type": "float"},
                "tags": {"type": "keyword"},
                "location": {"type": "keyword"},
                "updated_at": {"type": "date"}
            }
        }
    )


def reindex_data():
    print("\nReindexing data...")

    response = es.reindex(
        wait_for_completion=True,
        refresh=True,
        body={
            "source": {
                "index": SOURCE_INDEX
            },
            "dest": {
                "index": TARGET_INDEX
            }
        }
    )

    print(f"Documents copied: {response['created']}")


def percentile(values, p):
    values = sorted(values)

    position = (p / 100) * (len(values) - 1)

    lower = int(position)
    upper = min(lower + 1, len(values) - 1)

    if lower == upper:
        return values[lower]

    return values[lower] + (
        values[upper] - values[lower]
    ) * (position - lower)


def benchmark_index(index_name, query):

    # Warm-up request
    es.search(
        index=index_name,
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

    latencies = []
    errors = 0

    for _ in range(TRIALS):

        start = time.perf_counter()

        try:
            es.search(
                index=index_name,
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

            elapsed = (
                time.perf_counter() - start
            ) * 1000

            latencies.append(elapsed)

        except Exception:
            errors += 1

    return {
        "successful": len(latencies),
        "errors": errors,
        "error_rate_percent": (
            errors / TRIALS
        ) * 100,
        "min_ms": min(latencies),
        "average_ms": statistics.mean(latencies),
        "p50_ms": percentile(latencies, 50),
        "p95_ms": percentile(latencies, 95),
        "p99_ms": percentile(latencies, 99),
        "max_ms": max(latencies)
    }


def compare_relevance():

    print("\n" + "=" * 70)
    print("RELEVANCE COMPARISON")
    print("=" * 70)

    with open(
        "data/relevance_judgements.json",
        "r",
        encoding="utf-8"
    ) as f:
        judgements = json.load(f)

    comparison = {}

    for query in QUERIES:

        relevant_ids = set(judgements[query])

        source_response = es.search(
            index=SOURCE_INDEX,
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

        target_response = es.search(
            index=TARGET_INDEX,
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

        source_ids = [
            hit["_id"]
            for hit in source_response["hits"]["hits"]
        ]

        target_ids = [
            hit["_id"]
            for hit in target_response["hits"]["hits"]
        ]

        source_relevant = sum(
            1 for doc_id in source_ids
            if doc_id in relevant_ids
        )

        target_relevant = sum(
            1 for doc_id in target_ids
            if doc_id in relevant_ids
        )

        comparison[query] = {
            "source_relevant": source_relevant,
            "target_relevant": target_relevant,
            "source_p5": source_relevant / 5,
            "target_p5": target_relevant / 5,
            "top5_identical": source_ids == target_ids
        }

        print(f"\nQuery: {query}")
        print(
            f"Original P@5: "
            f"{source_relevant}/5 "
            f"({source_relevant / 5 * 100:.2f}%)"
        )
        print(
            f"Reindexed P@5: "
            f"{target_relevant}/5 "
            f"({target_relevant / 5 * 100:.2f}%)"
        )
        print(
            f"Top-5 identical: "
            f"{source_ids == target_ids}"
        )

    return comparison


def main():

    if not es.ping():
        print("Elasticsearch is not reachable.")
        return

    source_count = es.count(
        index=SOURCE_INDEX
    )["count"]

    print("=" * 70)
    print("CLOUD-30 O3 REINDEX EXPERIMENT")
    print("=" * 70)
    print(f"Source index: {SOURCE_INDEX}")
    print(f"Target index: {TARGET_INDEX}")
    print(f"Source documents: {source_count}")

    create_target_index()

    reindex_data()

    target_count = es.count(
        index=TARGET_INDEX
    )["count"]

    print(f"Target documents: {target_count}")

    print("\n" + "=" * 70)
    print("LATENCY COMPARISON")
    print("=" * 70)

    results = {}

    for query in QUERIES:

        print(f"\nQuery: {query}")
        print("-" * 70)

        source_result = benchmark_index(
            SOURCE_INDEX,
            query
        )

        target_result = benchmark_index(
            TARGET_INDEX,
            query
        )

        results[query] = {
            "original": source_result,
            "reindexed": target_result
        }

        print(
            f"Original  P50: "
            f"{source_result['p50_ms']:.3f} ms | "
            f"P95: {source_result['p95_ms']:.3f} ms | "
            f"P99: {source_result['p99_ms']:.3f} ms"
        )

        print(
            f"Reindexed P50: "
            f"{target_result['p50_ms']:.3f} ms | "
            f"P95: {target_result['p95_ms']:.3f} ms | "
            f"P99: {target_result['p99_ms']:.3f} ms"
        )

    relevance = compare_relevance()

    output = {
        "source_index": SOURCE_INDEX,
        "target_index": TARGET_INDEX,
        "source_documents": source_count,
        "target_documents": target_count,
        "latency": results,
        "relevance": relevance
    }

    os.makedirs("results", exist_ok=True)

    output_file = (
        "results/o3_reindex_results.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            output,
            f,
            indent=2
        )

    print("\n" + "=" * 70)
    print("O3 REINDEX EXPERIMENT COMPLETED")
    print("=" * 70)
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()