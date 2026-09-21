import json
from elasticsearch import Elasticsearch

ES_URL = "http://localhost:9200"
INDEX_NAME = "products"

es = Elasticsearch(ES_URL)

# Independent relevance rules.
# These rules do NOT use Elasticsearch scores.
JUDGEMENTS = {
    "laptop for students": {
        "category": "Laptop",
        "max_price": 70000,
        "required_keywords": ["student"],
    },

    "budget programming laptop": {
        "category": "Laptop",
        "max_price": 60000,
        "required_keywords": ["programming"],
    },

    "gaming laptop": {
        "category": "Laptop",
        "required_keywords": ["gaming"],
    },

    "wireless headphones": {
        "category": "Audio",
        "required_keywords": ["wireless", "headphones"],
    },

    "mobile phone": {
        "category": "Mobile",
    },
}


def is_relevant(doc, rule):
    source = doc["_source"]

    # Category condition
    if "category" in rule:
        if source.get("category") != rule["category"]:
            return False

    # Price condition
    if "max_price" in rule:
        price = source.get("price")
        if price is None or price > rule["max_price"]:
            return False

    # Keyword condition
    if "required_keywords" in rule:
        text = " ".join([
            str(source.get("title", "")),
            str(source.get("description", "")),
            " ".join(source.get("tags", [])),
        ]).lower()

        for keyword in rule["required_keywords"]:
            if keyword.lower() not in text:
                return False

    return True


def evaluate_query(query, rule, size=20):

    response = es.search(
        index=INDEX_NAME,
        size=size,
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

    relevant = 0

    print("\n" + "=" * 70)
    print(f"QUERY: {query}")
    print("=" * 70)

    for rank, hit in enumerate(hits, start=1):

        doc = hit
        correct = is_relevant(doc, rule)

        if correct:
            relevant += 1

        print(
            f"{rank:2}. "
            f"{doc['_source'].get('title')} | "
            f"Category={doc['_source'].get('category')} | "
            f"Price={doc['_source'].get('price')} | "
            f"Relevant={int(correct)}"
        )

    precision = relevant / len(hits) if hits else 0

    print(f"\nRelevant results: {relevant}/{len(hits)}")
    print(f"P@{len(hits)}: {precision * 100:.2f}%")

    return {
        "query": query,
        "retrieved": len(hits),
        "relevant": relevant,
        "precision": precision
    }


def main():

    if not es.ping():
        raise RuntimeError("Elasticsearch is not reachable")

    results = []

    for query, rule in JUDGEMENTS.items():
        result = evaluate_query(query, rule)
        results.append(result)

    overall_precision = (
        sum(r["relevant"] for r in results)
        / sum(r["retrieved"] for r in results)
    )

    output = {
        "index": INDEX_NAME,
        "documents": es.count(index=INDEX_NAME)["count"],
        "evaluation": results,
        "overall_precision": overall_precision
    }

    with open(
        "results/o3_relevance_reference.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(output, f, indent=2)

    print("\n" + "=" * 70)
    print("O3 RELEVANCE REFERENCE")
    print("=" * 70)

    print(
        f"Overall P@20: "
        f"{overall_precision * 100:.2f}%"
    )

    print("\nSaved:")
    print("results/o3_relevance_reference.json")


if __name__ == "__main__":
    main()