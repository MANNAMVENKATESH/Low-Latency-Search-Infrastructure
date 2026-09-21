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


def search_improved(query, size=20):

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

    elif query == "laptop for students":

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
        size=size,
        query=search_query
    )

    return response["hits"]["hits"]


def main():

    if not es.ping():
        raise RuntimeError("Elasticsearch is not reachable")

    results = []

    for query in QUERIES:

        hits = search_improved(query)

        print("\n" + "=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)

        for rank, hit in enumerate(hits, start=1):

            source = hit["_source"]

            print(
                f"{rank:2}. "
                f"{source.get('title')} | "
                f"Price={source.get('price')} | "
                f"Score={hit['_score']:.3f}"
            )

        results.append({
            "query": query,
            "results": [
                {
                    "rank": rank,
                    "doc_id": hit["_id"],
                    "title": hit["_source"].get("title"),
                    "price": hit["_source"].get("price"),
                    "score": hit["_score"]
                }
                for rank, hit in enumerate(hits, start=1)
            ]
        })

    with open(
        "results/o3_improved_relevance.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print("O3 IMPROVED SEARCH COMPLETE")
    print("=" * 70)

    print("Saved:")
    print("results/o3_improved_relevance.json")


if __name__ == "__main__":
    main()