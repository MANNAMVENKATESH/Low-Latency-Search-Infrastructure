from elasticsearch import Elasticsearch
import json

ES_URL = "http://localhost:9200"
INDEX_NAME = "products"

es = Elasticsearch(ES_URL)

queries = {
    "laptop for students": {
        "category": "Laptop",
        "keywords": ["student", "college", "lightweight"]
    },
    "budget programming laptop": {
        "category": "Laptop",
        "keywords": ["programming"],
        "max_price": 60000
    },
    "mobile phone with good camera": {
        "category": "Mobile",
        "keywords": ["camera"]
    },
    "affordable gaming laptop": {
        "category": "Laptop",
        "keywords": ["gaming"],
        "max_price": 80000
    },
    "wireless headphones": {
        "category": "Audio",
        "keywords": ["wireless", "headphones"]
    }
}


def is_relevant(product, criteria):
    category = product["category"].lower()
    title = product["title"].lower()
    description = product["description"].lower()
    tags = " ".join(product.get("tags", [])).lower()

    text = f"{title} {description} {tags}"

    if category != criteria["category"].lower():
        return False

    # At least one relevant keyword must appear
    if not any(keyword in text for keyword in criteria["keywords"]):
        return False

    # Optional price condition
    if "max_price" in criteria:
        if product["price"] > criteria["max_price"]:
            return False

    return True


judgements = {}

response = es.search(
    index=INDEX_NAME,
    size=1000,
    query={"match_all": {}}
)

for query, criteria in queries.items():

    relevant_ids = []

    for hit in response["hits"]["hits"]:
        product = hit["_source"]

        if is_relevant(product, criteria):
            relevant_ids.append(hit["_id"])

    judgements[query] = relevant_ids


with open(
    "data/relevance_judgements.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(judgements, f, indent=2)


print("=" * 60)
print("RELEVANCE JUDGEMENTS CREATED")
print("=" * 60)

for query, ids in judgements.items():
    print(f"{query}: {len(ids)} relevant documents")

print()
print("Saved to: data/relevance_judgements.json")
print("=" * 60)