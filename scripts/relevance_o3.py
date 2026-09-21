from elasticsearch import Elasticsearch
import json

ES_URL = "http://localhost:9200"
INDEX_NAME = "products"

es = Elasticsearch(ES_URL)

with open("data/relevance_judgements.json", "r", encoding="utf-8") as f:
    judgements = json.load(f)

queries = list(judgements.keys())

print("=" * 70)
print("CLOUD-30 O3 RELEVANCE AFTER DATA CHANGES")
print("=" * 70)

total_relevant = 0
total_results = 0

for query in queries:

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

    relevant_ids = set(judgements[query])

    hits = response["hits"]["hits"]

    relevant_count = sum(
        1 for hit in hits
        if hit["_id"] in relevant_ids
    )

    precision = relevant_count / len(hits) if hits else 0

    total_relevant += relevant_count
    total_results += len(hits)

    print(f"\nQuery: {query}")
    print("-" * 70)
    print(
        f"{relevant_count}/{len(hits)} relevant, "
        f"P@5 {precision * 100:.2f}%"
    )

overall_precision = (
    total_relevant / total_results
    if total_results
    else 0
)

print("\n" + "=" * 70)
print(
    f"Overall Precision@5: "
    f"{overall_precision * 100:.2f}%"
)
print(f"Total Relevant Results: {total_relevant}")
print(f"Total Results Evaluated: {total_results}")
print("=" * 70)