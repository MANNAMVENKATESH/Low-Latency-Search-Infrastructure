from elasticsearch import Elasticsearch
import time

es = Elasticsearch("http://localhost:9200")

query = "laptop for students"

start_time = time.perf_counter()

response = es.search(
    index="products",
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

end_time = time.perf_counter()

latency_ms = (end_time - start_time) * 1000

print("\nSearch Query:", query)
print("Latency:", round(latency_ms, 2), "ms")
print("Results Found:", response["hits"]["total"]["value"])

print("\nSearch Results:")

for i, hit in enumerate(response["hits"]["hits"], start=1):
    product = hit["_source"]

    print(
        f"{i}. {product['title']} "
        f"(Score: {round(hit['_score'], 2)})"
    )