import json
import statistics
import time

from elasticsearch import Elasticsearch

ES_URL = "http://localhost:9200"
INDEX_NAME = "products"

TRIALS = 30

QUERIES = [
    "laptop for students",
    "budget programming laptop",
    "gaming laptop",
    "wireless headphones",
    "mobile phone",
]


es = Elasticsearch(ES_URL)


def percentile(values, p):
    values = sorted(values)

    if not values:
        return 0

    index = (len(values) - 1) * (p / 100)

    lower = int(index)
    upper = min(lower + 1, len(values) - 1)

    weight = index - lower

    return (
        values[lower]
        + (values[upper] - values[lower]) * weight
    )


def improved_query(query):

    if query == "budget programming laptop":

        return {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": [
                                "title^5",
                                "description^2",
                                "tags^4"
                            ]
                        }
                    }
                ],
                "should": [
                    {
                        "range": {
                            "price": {
                                "lte": 60000,
                                "boost": 4
                            }
                        }
                    }
                ]
            }
        }

    return {
        "multi_match": {
            "query": query,
            "fields": [
                "title^5",
                "description^2",
                "tags^4"
            ]
        }
    }


def run_query(query):

    start = time.perf_counter()

    try:

        response = es.search(
            index=INDEX_NAME,
            size=20,
            query=improved_query(query)
        )

        latency = (
            time.perf_counter() - start
        ) * 1000

        return latency, True

    except Exception as exc:

        print(f"ERROR: {exc}")

        return 0, False


def main():

    if not es.ping():

        raise RuntimeError(
            "Elasticsearch is not reachable"
        )

    print("=" * 70)
    print("CLOUD-30 O3 CANDIDATE LATENCY BENCHMARK")
    print("=" * 70)

    all_latencies = []
    query_results = []

    for query in QUERIES:

        latencies = []
        errors = 0

        print(f"\nQuery: {query}")

        for _ in range(TRIALS):

            latency, success = run_query(query)

            if success:

                latencies.append(latency)
                all_latencies.append(latency)

            else:

                errors += 1

        result = {
            "query": query,
            "trials": TRIALS,
            "successful": len(latencies),
            "errors": errors,
            "p50_ms": percentile(latencies, 50),
            "p95_ms": percentile(latencies, 95),
            "p99_ms": percentile(latencies, 99),
            "max_ms": max(latencies) if latencies else 0,
            "avg_ms": statistics.mean(latencies)
                if latencies else 0
        }

        query_results.append(result)

        print(
            f"  P50: {result['p50_ms']:.3f} ms"
        )
        print(
            f"  P95: {result['p95_ms']:.3f} ms"
        )
        print(
            f"  P99: {result['p99_ms']:.3f} ms"
        )
        print(
            f"  Errors: {errors}"
        )

    overall = {
        "documents": es.count(
            index=INDEX_NAME
        )["count"],

        "total_trials": len(all_latencies),

        "successful": len(all_latencies),

        "errors": (
            len(QUERIES) * TRIALS
            - len(all_latencies)
        ),

        "p50_ms": percentile(
            all_latencies, 50
        ),

        "p95_ms": percentile(
            all_latencies, 95
        ),

        "p99_ms": percentile(
            all_latencies, 99
        ),

        "max_ms": max(all_latencies)
            if all_latencies else 0,

        "avg_ms": statistics.mean(
            all_latencies
        ) if all_latencies else 0
    }

    output = {
        "experiment": "O3 candidate",
        "index": INDEX_NAME,
        "trials_per_query": TRIALS,
        "queries": query_results,
        "overall": overall
    }

    with open(
        "results/o3_candidate_latency.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=2
        )

    print("\n" + "=" * 70)
    print("OVERALL")
    print("=" * 70)

    print(
        f"Documents : {overall['documents']}"
    )

    print(
        f"Trials    : {overall['total_trials']}"
    )

    print(
        f"Successful: {overall['successful']}"
    )

    print(
        f"Errors    : {overall['errors']}"
    )

    print(
        f"P50       : {overall['p50_ms']:.3f} ms"
    )

    print(
        f"P95       : {overall['p95_ms']:.3f} ms"
    )

    print(
        f"P99       : {overall['p99_ms']:.3f} ms"
    )

    print(
        f"Max       : {overall['max_ms']:.3f} ms"
    )

    print(
        f"Average   : {overall['avg_ms']:.3f} ms"
    )

    print("\nSaved:")
    print(
        "results/o3_candidate_latency.json"
    )


if __name__ == "__main__":
    main()