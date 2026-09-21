from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

if es.ping():
    print("Elasticsearch connection successful!")
else:
    print("Elasticsearch connection failed!")