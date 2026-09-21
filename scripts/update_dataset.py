from elasticsearch import Elasticsearch
from datetime import datetime, timezone
import random
import time

ES_URL = "http://localhost:9200"
INDEX_NAME = "products"

es = Elasticsearch(ES_URL)

random.seed(42)


def add_documents():
    print("\n[1] Adding 100 new documents...")

    documents = []

    for i in range(1001, 1101):
        doc = {
            "title": f"Student Laptop {i}",
            "description": (
                "Lightweight laptop suitable for students, "
                "college work, programming and everyday use."
            ),
            "category": "Laptop",
            "brand": random.choice(["Dell", "HP", "Lenovo", "ASUS"]),
            "price": random.randint(30000, 60000),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "tags": ["laptop", "student", "programming"],
            "location": random.choice(
                ["India", "Bangalore", "Hyderabad", "Chennai", "Mumbai", "Delhi"]
            ),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        documents.append({
            "_index": INDEX_NAME,
            "_id": f"P{i:04d}",
            "_source": doc
        })

    from elasticsearch.helpers import bulk

    bulk(es, documents)
    es.indices.refresh(index=INDEX_NAME)

    print("Added 100 documents.")


def update_documents():
    print("\n[2] Updating 100 existing documents...")

    for i in range(1, 101):
        doc_id = f"P{i:04d}"

        es.update(
            index=INDEX_NAME,
            id=doc_id,
            doc={
                "description": (
                    "Updated product information. "
                    "Suitable for students and programming."
                ),
                "tags": ["laptop", "student", "programming", "updated"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        )

    es.indices.refresh(index=INDEX_NAME)

    print("Updated 100 documents.")


def delete_documents():
    print("\n[3] Deleting 50 documents...")

    for i in range(151, 201):
        doc_id = f"P{i:04d}"

        try:
            es.delete(
                index=INDEX_NAME,
                id=doc_id
            )
        except Exception:
            pass

    es.indices.refresh(index=INDEX_NAME)

    print("Deleted 50 documents.")


def show_index_stats():
    stats = es.count(index=INDEX_NAME)

    print("\nCurrent document count:")
    print(stats["count"])


if __name__ == "__main__":

    if not es.ping():
        print("Elasticsearch is not reachable.")
        exit(1)

    print("=" * 70)
    print("CLOUD-30 O3 CONTROLLED DATA CHANGE")
    print("=" * 70)

    show_index_stats()

    add_documents()

    time.sleep(2)

    update_documents()

    time.sleep(2)

    delete_documents()

    show_index_stats()

    print("\nO3 data changes completed.")