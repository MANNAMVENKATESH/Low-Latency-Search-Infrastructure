from elasticsearch import Elasticsearch
import csv
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

TOP_K = 20


def main():

    if not es.ping():
        print("Elasticsearch is not reachable.")
        return

    os.makedirs("data", exist_ok=True)

    output_file = "data/o3_manual_judgements.csv"

    rows = []

    print("=" * 70)
    print("CLOUD-30 O3 MANUAL RELEVANCE JUDGEMENT GENERATOR")
    print("=" * 70)

    for query in QUERIES:

        print(f"\nQuery: {query}")

        response = es.search(
            index=INDEX_NAME,
            size=TOP_K,
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

        for rank, hit in enumerate(
            response["hits"]["hits"],
            start=1
        ):

            source = hit["_source"]

            rows.append({
                "query": query,
                "rank": rank,
                "doc_id": hit["_id"],
                "title": source.get("title", ""),
                "description": source.get("description", ""),
                "category": source.get("category", ""),
                "brand": source.get("brand", ""),
                "price": source.get("price", ""),
                "rating": source.get("rating", ""),
                "tags": ", ".join(source.get("tags", [])),
                "relevant": ""
            })

            print(
                f"{rank:2}. "
                f"{hit['_id']} | "
                f"{source.get('title', '')}"
            )

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        fieldnames = [
            "query",
            "rank",
            "doc_id",
            "title",
            "description",
            "category",
            "brand",
            "price",
            "rating",
            "tags",
            "relevant"
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    print("\n" + "=" * 70)
    print("JUDGEMENT FILE CREATED")
    print("=" * 70)
    print(f"Queries: {len(QUERIES)}")
    print(f"Documents per query: {TOP_K}")
    print(f"Total judgements: {len(rows)}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()