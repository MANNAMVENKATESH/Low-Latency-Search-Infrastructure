from elasticsearch import Elasticsearch
import time
import statistics

es = Elasticsearch("http://localhost:9200")

INDEX_NAME = "products"

queries = [
    "laptop for students",
    "budget programming laptop",
    "mobile phone with good camera",
    "affordable gaming laptop",
    "wireless headphones"
]

WARMUP_RUNS = 2
MEASURED_RUNS = 10

print("=" * 70)
print("CLOUD-30 O1 BASELINE SEARCH TEST")
print("=" * 70)

all_results = []

for query in queries:

    # Warm-up requests
    for _ in range(WARMUP_RUNS):
        es.search(
            index=INDEX_NAME,
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
    last_response = None

    # Measured requests
    for _ in range(MEASURED_RUNS):

        start = time.perf_counter()

        response = es.search(
            index=INDEX_NAME,
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

        latency = (end - start) * 1000

        latencies.append(latency)
        last_response = response

    average = statistics.mean(latencies)
    minimum = min(latencies)
    maximum = max(latencies)

    sorted_latencies = sorted(latencies)

    p95_index = int(0.95 * len(sorted_latencies)) - 1
    p95 = sorted_latencies[p95_index]

    total_results = last_response["hits"]["total"]["value"]

    all_results.append({
        "query": query,
        "average": average,
        "p95": p95,
        "results": total_results
    })

    print()
    print(f"Query: {query}")
    print(f"Average Latency: {average:.2f} ms")
    print(f"Minimum Latency: {minimum:.2f} ms")
    print(f"Maximum Latency: {maximum:.2f} ms")
    print(f"P95 Latency: {p95:.2f} ms")
    print(f"Results Found: {total_results}")

    print("Top 3 Results:")

    for i, hit in enumerate(
        last_response["hits"]["hits"][:3],
        start=1
    ):
        product = hit["_source"]

        print(
            f"  {i}. {product['title']} "
            f"(Score: {hit['_score']:.2f})"
        )

print()
print("=" * 70)
print("O1 BASELINE SUMMARY")
print("=" * 70)

for result in all_results:

    print(
        f"{result['query']:<35} "
        f"Avg: {result['average']:.2f} ms | "
        f"P95: {result['p95']:.2f} ms"
    )

print("-" * 70)

overall_average = statistics.mean(
    result["average"] for result in all_results
)

overall_p95 = max(
    result["p95"] for result in all_results
)

print(f"Overall Average Latency: {overall_average:.2f} ms")
print(f"Worst Query P95:         {overall_p95:.2f} ms")

print("=" * 70)