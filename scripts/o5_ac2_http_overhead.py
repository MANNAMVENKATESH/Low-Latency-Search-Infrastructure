import time
import statistics
import urllib.request
from elasticsearch import Elasticsearch

URL = "http://localhost:9200"
TRIALS = 30

es = Elasticsearch(URL)

def direct_http():
    with urllib.request.urlopen(URL, timeout=10) as response:
        response.read()

def python_client():
    es.info()

if not es.ping():
    raise RuntimeError("Elasticsearch is not reachable")

def measure(fn):
    values = []
    for _ in range(TRIALS):
        start = time.perf_counter()
        fn()
        values.append((time.perf_counter() - start) * 1000)

    values.sort()
    return {
        "average_ms": round(statistics.mean(values), 3),
        "p50_ms": round(statistics.median(values), 3),
        "p95_ms": round(values[int((len(values) - 1) * 0.95)], 3),
        "max_ms": round(max(values), 3)
    }

# Warm up both request paths
direct_http()
python_client()

print("Direct HTTP GET /:", measure(direct_http))
print("Elasticsearch Python client info():", measure(python_client))
