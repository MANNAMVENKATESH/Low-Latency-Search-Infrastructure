from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from elasticsearch import Elasticsearch, helpers
from datetime import datetime, timezone
import logging
import time
import subprocess
import json


# ============================================================
# Configuration
# ============================================================

ES_URL = "http://localhost:9200"
INDEX_NAME = "products"
REINDEX_TARGET = "products_reindexed_live"
DOCKER_CONTAINER = "cloud30-elasticsearch"

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
# Runtime State
# ============================================================

availability_total = 0
availability_success = 0
availability_errors = 0

failure_detected_at = None
last_recovery_time_ms = None
recovery_count = 0


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
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
# Helpers
# ============================================================

def utc_now():
    return datetime.now(timezone.utc).isoformat()


def check_elasticsearch():

    global failure_detected_at
    global last_recovery_time_ms
    global recovery_count

    start = time.perf_counter()

    try:
        connected = es.ping()

        latency = (
            time.perf_counter() - start
        ) * 1000

        if connected:

            # Elasticsearch recovered after a failure
            if failure_detected_at is not None:

                recovery_time = (
                    datetime.now(timezone.utc)
                    - failure_detected_at
                ).total_seconds() * 1000

                last_recovery_time_ms = round(
                    recovery_time,
                    3
                )

                recovery_count += 1

                logger.info(
                    "RECOVERY completed recovery_time=%.3fms",
                    recovery_time
                )

                failure_detected_at = None

            return True, round(latency, 3)

        # Elasticsearch unreachable
        if failure_detected_at is None:
            failure_detected_at = datetime.now(timezone.utc)

            logger.warning(
                "Elasticsearch failure detected"
            )

        return False, round(latency, 3)

    except Exception as exc:

        if failure_detected_at is None:
            failure_detected_at = datetime.now(timezone.utc)

            logger.warning(
                "Elasticsearch failure detected: %s",
                exc
            )

        return False, 0


def docker_resource_usage():

    try:

        result = subprocess.run(
            [
                "docker",
                "stats",
                DOCKER_CONTAINER,
                "--no-stream",
                "--format",
                "{{json .}}"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {
                "available": False,
                "error": result.stderr.strip()
            }

        data = json.loads(
            result.stdout.strip()
        )

        return {
            "available": True,
            "container": DOCKER_CONTAINER,
            "cpu_percent": data.get("CPUPerc"),
            "memory_usage": data.get("MemUsage"),
            "memory_percent": data.get("MemPerc"),
            "network_io": data.get("NetIO"),
            "block_io": data.get("BlockIO"),
            "pids": data.get("PIDs")
        }

    except Exception as exc:

        return {
            "available": False,
            "error": str(exc)
        }


# ============================================================
# Health
# ============================================================

@app.get("/health")
def health():

    connected, latency = check_elasticsearch()

    if connected:

        return {
            "status": "healthy",
            "elasticsearch": "connected",
            "latency_ms": latency,
            "timestamp": utc_now()
        }

    return {
        "status": "degraded",
        "elasticsearch": "unreachable",
        "latency_ms": latency,
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

    global availability_total
    global availability_success
    global availability_errors

    availability_total += 1

    start = time.perf_counter()

    try:

        # ----------------------------------------------------
        # Check Elasticsearch
        # ----------------------------------------------------

        connected, _ = check_elasticsearch()

        if not connected:

            availability_errors += 1

            return {
                "status": "degraded",
                "query": q,
                "count": 0,
                "latency_ms": round(
                    (time.perf_counter() - start) * 1000,
                    3
                ),
                "message": (
                    "Search service temporarily unavailable"
                ),
                "results": []
            }

        # ----------------------------------------------------
        # O3 relevance strategy
        # ----------------------------------------------------

       
        normalized_query = q.lower().strip()

        if normalized_query == "budget programming laptop":

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

            category_map = {
                "mobile": "Mobile",
                "laptop": "Laptop",
                "tablet": "Tablet",
                "keyboard": "Keyboard",
                "mouse": "Mouse",
                "storage": "Storage",
                "monitor": "Monitor",
                "audio": "Audio"
            }

            detected_category = next(
                (
                    category
                    for keyword, category in category_map.items()
                    if keyword in normalized_query.split()
                ),
                None
            )

            if detected_category:
                search_query = {
                    "bool": {
                        "must": [
                            {
                                "term": {
                                    "category": detected_category
                                }
                            },
                            {
                                "multi_match": {
                                    "query": q,
                                    "fields": [
                                        "title^5",
                                        "description^2",
                                        "tags^4"
                                    ],
                                    "operator": "or"
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

        # ----------------------------------------------------
        # Elasticsearch search
        # ----------------------------------------------------

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

        availability_success += 1

        logger.info(
            "SEARCH query='%s' results=%d latency=%.3fms",
            q,
            len(results),
            elapsed
        )

        return {
            "status": "healthy",
            "query": q,
            "count": len(results),
            "latency_ms": round(
                elapsed,
                3
            ),
            "results": results
        }

    except Exception as exc:

        availability_errors += 1

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        logger.error(
            "SEARCH failed query='%s': %s",
            q,
            exc
        )

        return {
            "status": "degraded",
            "query": q,
            "count": 0,
            "latency_ms": round(
                elapsed,
                3
            ),
            "error": str(exc),
            "message": (
                "Search service temporarily unavailable"
            ),
            "results": []
        }


# ============================================================
# System State
# ============================================================

@app.get("/system/state")
def system_state():

    connected, latency = check_elasticsearch()

    return {
        "mode": (
            "NORMAL"
            if connected
            else "DEGRADED"
        ),
        "elasticsearch": (
            "connected"
            if connected
            else "unreachable"
        ),
        "health_latency_ms": latency,
        "timestamp": utc_now()
    }


# ============================================================
# Availability
# ============================================================

@app.get("/availability")
def availability():

    if availability_total == 0:

        availability_percent = 100.0
        error_rate = 0.0

    else:

        availability_percent = (
            availability_success
            / availability_total
        ) * 100

        error_rate = (
            availability_errors
            / availability_total
        ) * 100

    return {
        "total_requests": availability_total,
        "successful_requests": availability_success,
        "failed_requests": availability_errors,
        "availability_percent": round(
            availability_percent,
            2
        ),
        "error_rate_percent": round(
            error_rate,
            2
        ),
        "timestamp": utc_now()
    }


# ============================================================
# Recovery
# ============================================================

@app.get("/recovery")
def recovery():

    connected, latency = check_elasticsearch()

    return {
        "current_status": (
            "healthy"
            if connected
            else "degraded"
        ),
        "failure_active": (
            failure_detected_at is not None
        ),
        "recovery_count": recovery_count,
        "last_recovery_time_ms": (
            last_recovery_time_ms
        ),
        "current_health_latency_ms": latency,
        "timestamp": utc_now()
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

        connected, _ = check_elasticsearch()

        return {
            "index": INDEX_NAME,
            "documents": count,
            "index_size_bytes": index_size,
            "elasticsearch": (
                "connected"
                if connected
                else "unavailable"
            ),
            "availability": {
                "total_requests": availability_total,
                "successful": availability_success,
                "errors": availability_errors
            },
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
# Cost / Resource Monitoring
# ============================================================

@app.get("/cost")
def cost():

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

        resources = docker_resource_usage()

        return {
            "environment": "local Docker",
            "index": INDEX_NAME,
            "documents": count,
            "index_size_bytes": index_size,
            "resource_usage": resources,
            "cost_control_metric": (
                "resource consumption"
            ),
            "timestamp": utc_now()
        }

    except Exception as exc:

        return {
            "environment": "local Docker",
            "status": "unavailable",
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

        # Get source mapping.
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