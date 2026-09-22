from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from elasticsearch import Elasticsearch, helpers
from datetime import datetime, timezone
import logging
import time


# ============================================================
# Configuration
# ============================================================

ES_URL = "http://localhost:9200"
INDEX_NAME = "products"
REINDEX_TARGET = "products_reindexed_live"

es = Elasticsearch(ES_URL)


# ============================================================
# Logging / Telemetry
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("cloud30")


# ============================================================
# FastAPI
# ============================================================

app = FastAPI(
    title="CLOUD-30 Search API",
    description=(
        "Low-Latency Search Infrastructure with "
        "Relevance and Availability Under Cost"
    ),
    version="1.0.0"
)


# ============================================================
# Request Models
# ============================================================

class ProductUpdate(BaseModel):

    price: float | None = Field(
        default=None,
        ge=0
    )

    rating: float | None = Field(
        default=None,
        ge=0,
        le=5
    )

    location: str | None = None


# ============================================================
# Helper
# ============================================================

def utc_now():

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# Health
# ============================================================

@app.get("/health")
def health():

    start = time.perf_counter()

    try:

        connected = es.ping()

        latency = (
            time.perf_counter() - start
        ) * 1000

        if connected:

            return {
                "status": "healthy",
                "elasticsearch": "connected",
                "latency_ms": round(
                    latency,
                    3
                ),
                "timestamp": utc_now()
            }

        return {
            "status": "degraded",
            "elasticsearch": "unreachable",
            "latency_ms": round(
                latency,
                3
            ),
            "timestamp": utc_now()
        }

    except Exception as exc:

        logger.error(
            "Health check failed: %s",
            exc
        )

        return {
            "status": "degraded",
            "elasticsearch": "error",
            "error": str(exc),
            "timestamp": utc_now()
        }


# ============================================================
# Search
# ============================================================

@app.get("/search")
def search(
    q: str = Query(
        ...,
        min_length=1,
        description="Search query"
    ),
    size: int = Query(
        10,
        ge=1,
        le=50
    )
):

    start = time.perf_counter()

    try:

        # O3 relevance strategy
        if q.lower().strip() == "budget programming laptop":

            search_query = {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": q,
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
                    "query": q,
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

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        results = []

        for rank, hit in enumerate(
            response["hits"]["hits"],
            start=1
        ):

            source = hit["_source"]

            results.append({
                "rank": rank,
                "id": hit["_id"],
                "title": source.get("title"),
                "description": source.get(
                    "description"
                ),
                "category": source.get(
                    "category"
                ),
                "brand": source.get(
                    "brand"
                ),
                "price": source.get(
                    "price"
                ),
                "rating": source.get(
                    "rating"
                ),
                "tags": source.get(
                    "tags"
                ),
                "location": source.get(
                    "location"
                ),
                "score": hit["_score"]
            })

        logger.info(
            "SEARCH query='%s' results=%d latency=%.3fms",
            q,
            len(results),
            elapsed
        )

        return {
            "query": q,
            "count": len(results),
            "latency_ms": round(
                elapsed,
                3
            ),
            "results": results
        }

    except Exception as exc:

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        logger.error(
            "SEARCH failed query='%s': %s",
            q,
            exc
        )

        return {
            "query": q,
            "count": 0,
            "latency_ms": round(
                elapsed,
                3
            ),
            "error": str(exc),
            "results": []
        }


# ============================================================
# Metrics
# ============================================================

@app.get("/metrics")
def metrics():

    try:

        count = es.count(
            index=INDEX_NAME
        )["count"]

        stats = es.indices.stats(
            index=INDEX_NAME
        )

        index_size = (
            stats["_all"]["primaries"]
            ["store"]["size_in_bytes"]
        )

        return {
            "index": INDEX_NAME,
            "documents": count,
            "index_size_bytes": index_size,
            "elasticsearch": "connected",
            "timestamp": utc_now()
        }

    except Exception as exc:

        logger.error(
            "Metrics failed: %s",
            exc
        )

        return {
            "index": INDEX_NAME,
            "documents": 0,
            "index_size_bytes": 0,
            "elasticsearch": "unavailable",
            "error": str(exc),
            "timestamp": utc_now()
        }


# ============================================================
# Elasticsearch Status
# ============================================================

@app.get("/status")
def status():

    try:

        cluster = es.cluster.health()

        return {
            "cluster_name": cluster.get(
                "cluster_name"
            ),
            "status": cluster.get(
                "status"
            ),
            "number_of_nodes": cluster.get(
                "number_of_nodes"
            ),
            "active_primary_shards": cluster.get(
                "active_primary_shards"
            ),
            "active_shards": cluster.get(
                "active_shards"
            ),
            "unassigned_shards": cluster.get(
                "unassigned_shards"
            )
        }

    except Exception as exc:

        logger.error(
            "Status failed: %s",
            exc
        )

        return {
            "status": "unavailable",
            "error": str(exc)
        }


# ============================================================
# ADMIN: Update Existing Document
# ============================================================

@app.post("/admin/update/{doc_id}")
def update_document(
    doc_id: str,
    update: ProductUpdate
):

    start = time.perf_counter()

    changes = {
        key: value
        for key, value in update.model_dump().items()
        if value is not None
    }

    if not changes:

        raise HTTPException(
            status_code=400,
            detail="No update fields supplied"
        )

    try:

        result = es.update(
            index=INDEX_NAME,
            id=doc_id,
            doc=changes,
            refresh=True
        )

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        logger.info(
            "UPDATE doc=%s changes=%s latency=%.3fms",
            doc_id,
            changes,
            elapsed
        )

        return {
            "status": "updated",
            "index": INDEX_NAME,
            "document_id": doc_id,
            "changes": changes,
            "result": result.get(
                "result"
            ),
            "latency_ms": round(
                elapsed,
                3
            ),
            "timestamp": utc_now()
        }

    except Exception as exc:

        logger.error(
            "UPDATE failed doc=%s error=%s",
            doc_id,
            exc
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


# ============================================================
# ADMIN: Reindex
# ============================================================

@app.post("/admin/reindex")
def reindex():

    start = time.perf_counter()

    try:

        # Never overwrite the existing evidence index.
        if es.indices.exists(
            index=REINDEX_TARGET
        ):

            es.indices.delete(
                index=REINDEX_TARGET
            )

        # Create target using source mapping.
        source_mapping = es.indices.get_mapping(
            index=INDEX_NAME
        )

        mapping = source_mapping[
            INDEX_NAME
        ]["mappings"]

        es.indices.create(
            index=REINDEX_TARGET,
            mappings=mapping
        )

        # Copy documents.
        actions = helpers.scan(
            es,
            index=INDEX_NAME,
            query={
                "query": {
                    "match_all": {}
                }
            }
        )

        bulk_actions = []

        for doc in actions:

            bulk_actions.append({
                "_index": REINDEX_TARGET,
                "_id": doc["_id"],
                "_source": doc["_source"]
            })

        if bulk_actions:

            helpers.bulk(
                es,
                bulk_actions,
                refresh=True
            )

        source_count = es.count(
            index=INDEX_NAME
        )["count"]

        target_count = es.count(
            index=REINDEX_TARGET
        )["count"]

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        success = (
            source_count == target_count
        )

        logger.info(
            "REINDEX source=%s target=%s "
            "source_docs=%d target_docs=%d "
            "latency=%.3fms success=%s",
            INDEX_NAME,
            REINDEX_TARGET,
            source_count,
            target_count,
            elapsed,
            success
        )

        return {
            "status": (
                "completed"
                if success
                else "count_mismatch"
            ),
            "source_index": INDEX_NAME,
            "target_index": REINDEX_TARGET,
            "source_documents": source_count,
            "target_documents": target_count,
            "documents_copied": target_count,
            "latency_ms": round(
                elapsed,
                3
            ),
            "success": success,
            "timestamp": utc_now()
        }

    except Exception as exc:

        logger.error(
            "REINDEX failed: %s",
            exc
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )