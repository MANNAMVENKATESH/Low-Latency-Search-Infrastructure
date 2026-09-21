from elasticsearch import Elasticsearch

ES_URL = "http://localhost:9200"
INDEX_NAME = "products"

es = Elasticsearch(ES_URL)


def test_elasticsearch_connection():
    assert es.ping(), "Elasticsearch is not reachable"


def test_products_index_exists():
    assert es.indices.exists(index=INDEX_NAME), \
        "Products index does not exist"


def test_search_returns_results():
    response = es.search(
        index=INDEX_NAME,
        size=5,
        query={
            "multi_match": {
                "query": "laptop for students",
                "fields": [
                    "title",
                    "description",
                    "tags"
                ]
            }
        }
    )

    assert len(response["hits"]["hits"]) > 0