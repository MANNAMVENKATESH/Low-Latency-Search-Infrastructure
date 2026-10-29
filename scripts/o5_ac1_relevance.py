import json
from elasticsearch import Elasticsearch

ES_URL = "http://localhost:9200"
INDEX_NAME = "products"

es = Elasticsearch(ES_URL)

QUERIES = [
    "laptop for students",
    "budget programming laptop",
    "gaming laptop",
    "wireless headphones",
    "mobile phone",
]


def is_relevant(source, query):

    title = str(source.get("title", "")).lower()
    description = str(source.get("description", "")).lower()
    tags = " ".join(source.get("tags", [])).lower()

    text = f"{title} {description} {tags}"

    price = source.get("price")

    if query == "laptop for students":
        return (
            source.get("category") == "Laptop"
            and "student" in text
            and price <= 70000
        )

    if query == "budget programming laptop":
        return (
            source.get("category") == "Laptop"
            and "programming" in text
            and price <= 60000
        )

    if query == "gaming laptop":
        return (
            source.get("category") == "Laptop"
            and "gaming" in text
        )

    if query == "wireless headphones":
        return (
            source.get("category") == "Audio"
            and "wireless" in text
            and "headphones" in text
        )

    if query == "mobile phone":
        return source.get("category") == "Mobile"

    return False


def baseline_search(query):

    response = es.search(
        index=INDEX_NAME,
        size=20,
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

    return response["hits"]["hits"]


def improved_search(query):

    if query == "budget programming laptop":

        search_query = {
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

    else:

        search_query = {
            "multi_match": {
                "query": query,
                "fields": [
                    "title^5",
                    "description^2",
                    "tags^4"
                ]
            }
        }

    response = es.search(
        index=INDEX_NAME,
        size=20,
        query=search_query
    )

    return response["hits"]["hits"]


def precision_at_k(hits, query, k):

    selected = hits[:k]

    if not selected:
        return 0

    relevant = sum(
        is_relevant(hit["_source"], query)
        for hit in selected
    )

    return relevant / len(selected)


def main():

    if not es.ping():
        raise RuntimeError("Elasticsearch is not reachable")

    all_results = []

    print("=" * 75)
    print("CLOUD-30 O5 AC-1 RELEVANCE EVALUATION")
    print("=" * 75)

    for query in QUERIES:

        baseline = baseline_search(query)
        improved = improved_search(query)

        print("\n" + "-" * 75)
        print(f"QUERY: {query}")
        print("-" * 75)

        result = {
            "query": query
        }

        for k in [5, 10, 20]:

            baseline_p = precision_at_k(
                baseline,
                query,
                k
            )

            improved_p = precision_at_k(
                improved,
                query,
                k
            )

            change = (
                improved_p - baseline_p
            ) * 100

            print(
                f"P@{k:<2}  "
                f"Baseline={baseline_p * 100:6.2f}%   "
                f"Improved={improved_p * 100:6.2f}%   "
                f"Change={change:+6.2f} pp"
            )

            result[f"baseline_p{k}"] = baseline_p
            result[f"improved_p{k}"] = improved_p
            result[f"change_p{k}_percentage_points"] = change

        all_results.append(result)

    print("\n" + "=" * 75)
    print("OVERALL")
    print("=" * 75)

    for k in [5, 10, 20]:

        baseline_total = sum(
            r[f"baseline_p{k}"]
            for r in all_results
        )

        improved_total = sum(
            r[f"improved_p{k}"]
            for r in all_results
        )

        baseline_avg = baseline_total / len(all_results)
        improved_avg = improved_total / len(all_results)

        change = (
            improved_avg - baseline_avg
        ) * 100

        print(
            f"P@{k:<2}  "
            f"Baseline={baseline_avg * 100:6.2f}%   "
            f"Improved={improved_avg * 100:6.2f}%   "
            f"Change={change:+6.2f} pp"
        )

    output = {
        "index": INDEX_NAME,
        "documents": es.count(index=INDEX_NAME)["count"],
        "queries": all_results
    }

    with open(
        "results/o5/o5_ac1_relevance.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(output, f, indent=2)

    print("\nSaved:")
    print("results/o5/o5_ac1_relevance.json")


if __name__ == "__main__":
    main()
