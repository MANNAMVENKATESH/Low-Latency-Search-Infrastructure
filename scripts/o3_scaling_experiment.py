from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from datetime import datetime, timezone
import random
import time
import statistics
import json
import os

ES_URL = "http://localhost:9200"
INDEX_NAME = "products"

es = Elasticsearch(ES_URL)

QUERIES = [
    "laptop for students",
    "budget programming laptop",
    "mobile phone with good camera",
    "affordable gaming laptop",
    "wireless headphones"
]

random.seed(42)


def generate_document(i):
    categories = {
        "Laptop": ["Dell", "HP", "Lenovo", "ASUS"],
        "Mobile": ["Samsung", "OnePlus", "Xiaomi", "Realme"],
        "Tablet": ["Samsung", "Lenovo", "Xiaomi"],
        "Audio": ["Sony", "JBL", "Boat", "Anker"],
        "Monitor": ["LG", "Samsung", "Acer"],
        "Keyboard": ["Logitech", "HP", "Dell"],
        "Mouse": ["Logitech", "HP", "Dell"],
        "Storage": ["Samsung", "Kingston", "SanDisk"]
    }

    category = random.choice(list(categories.keys()))
    brand = random.choice(categories[category])

    items = {
        "Laptop": "Laptop",
        "Mobile": "Mobile Phone",
        "Tablet": "Tablet",
        "Audio": "Wireless Headphones",
        "Monitor": "Computer Monitor",
        "Keyboard": "Keyboard",
        "Mouse": "Wireless Mouse",
        "Storage": "SSD Storage"
    }

    item = items[category]

    return {
        "_index": INDEX_NAME,
        "_id": f"SCALE{i:05d}",
        "_source": {
            "title": f"{brand} {item} {i}",
            "description": (
                f"{brand} {item} suitable for students, "
                "professionals, programming and everyday use. "
                "Provides reliable performance and good quality."
            ),
            "category": category,
            "brand": brand,
            "price": random.randint(2000, 100000),
            "rating": round(random.uniform(3.0, 5.0), 1),
            "tags": [
                category.lower(),
                brand.lower(),
                item.lower().replace(" ", "_")
            ],
            "location": random.choice([
                "India",
                "Bangalore",
                "Hyderabad",
                "Chennai",
                "Mumbai",
                "Delhi"
            ]),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    }


def add_documents(start_id, end_id):
    documents = [
        generate_document(i)
        for i in range(start_id, end_id + 1)
    ]

    bulk(es, documents)
    es.indices.refresh(index=INDEX_NAME)


def measure_query(query, trials=30):

    # Warm-up
    es.search(
        index=INDEX_NAME,
        size=5,
        query={
            "multi_match": {
                "query": query,
                "fields": ["title", "description", "tags"]
            }
        }
    )

    latencies = []
    errors = 0

    for _ in range(trials):

        start = time.perf_counter()

        try:
            es.search(
                index=INDEX_NAME,
                size=5,
                query={
                    "multi_match": {
                        "query": query,
                        "fields": ["title", "description", "tags"]
                    }
                }
            )

            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)

        except Exception:
            errors += 1

    if not latencies:
        return {
            "successful": 0,
            "errors": errors
        }

    sorted_latencies = sorted(latencies)

    def percentile(values, p):
        index = int((p / 100) * len(values))
        index = min(index, len(values) - 1)
        return values[index]

    return {
        "successful": len(latencies),
        "errors": errors,
        "error_rate_percent": (errors / trials) * 100,
        "min_ms": min(latencies),
        "average_ms": statistics.mean(latencies),
        "p50_ms": percentile(sorted_latencies, 50),
        "p95_ms": percentile(sorted_latencies, 95),
        "p99_ms": percentile(sorted_latencies, 99),
        "max_ms": max(latencies)
    }


def run_condition(document_count):

    print("\n" + "=" * 70)
    print(f"CORPUS SIZE: {document_count} DOCUMENTS")
    print("=" * 70)

    results = {}

    for query in QUERIES:

        result = measure_query(query)

        results[query] = result

        print(f"\nQuery: {query}")
        print("-" * 70)
        print(f"P50: {result['p50_ms']:.3f} ms")
        print(f"P95: {result['p95_ms']:.3f} ms")
        print(f"P99: {result['p99_ms']:.3f} ms")
        print(f"Errors: {result['errors']}")

    return results


if __name__ == "__main__":

    if not es.ping():
        print("Elasticsearch is not reachable.")
        exit(1)

    initial_count = es.count(index=INDEX_NAME)["count"]

    print("=" * 70)
    print("CLOUD-30 O3 SCALING EXPERIMENT")
    print("=" * 70)
    print(f"Starting documents: {initial_count}")

    target_sizes = [1100, 1200, 1500, 2000]

    all_results = {}

    current_count = initial_count

    for target in target_sizes:

        if current_count < target:

            print(
                f"\nAdding {target - current_count} documents "
                f"to reach {target}..."
            )

            add_documents(current_count + 1, target)

            current_count = es.count(index=INDEX_NAME)["count"]

        all_results[str(current_count)] = run_condition(current_count)

    os.makedirs("results", exist_ok=True)

    output_file = "results/o3_scaling_results.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print("\n" + "=" * 70)
    print("O3 SCALING EXPERIMENT COMPLETED")
    print("=" * 70)
    print(f"Final documents: {current_count}")
    print(f"Results saved to: {output_file}")