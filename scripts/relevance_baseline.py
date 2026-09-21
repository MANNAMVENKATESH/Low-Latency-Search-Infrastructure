from elasticsearch import Elasticsearch
import json

ES_URL = "http://localhost:9200"
INDEX_NAME = "products"
JUDGEMENT_FILE = "data/relevance_judgements.json"

es = Elasticsearch(ES_URL)

# Load independent relevance judgements
with open(JUDGEMENT_FILE, "r", encoding="utf-8") as f:
    judgements = json.load(f)

print("=" * 70)
print("CLOUD-30 O2 RELEVANCE BASELINE")
print("=" * 70)

overall_relevant = 0
overall_results = 0

for query, relevant_ids in judgements.items():

    relevant_ids = set(relevant_ids)

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

    hits = response["hits"]["hits"]

    relevant_count = 0

    print()
    print("Query:", query)
    print("-" * 70)

    for i, hit in enumerate(hits, start=1):

        product = hit["_source"]
        product_id = hit["_id"]

        relevant = product_id in relevant_ids

        if relevant:
            relevant_count += 1

        status = "RELEVANT" if relevant else "NOT RELEVANT"

        print(
            f"{i}. {product['title']} "
            f"-> {status}"
        )

    precision = (
        relevant_count / len(hits) * 100
        if hits else 0
    )

    overall_relevant += relevant_count
    overall_results += len(hits)

    print()
    print(f"Relevant Results: {relevant_count}/{len(hits)}")
    print(f"Precision@5: {precision:.2f}%")

overall_precision = (
    overall_relevant / overall_results * 100
    if overall_results else 0
)

print()
print("=" * 70)
print("O2 RELEVANCE BASELINE SUMMARY")
print("=" * 70)
print(f"Total Relevant Results: {overall_relevant}")
print(f"Total Results Evaluated: {overall_results}")
print(f"Overall Precision@5: {overall_precision:.2f}%")
print("=" * 70)