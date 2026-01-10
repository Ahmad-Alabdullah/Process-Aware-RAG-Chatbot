import logging
import threading
import colorlog
import redis.asyncio as redis
from opensearchpy import OpenSearch
from qdrant_client import QdrantClient
from neo4j import GraphDatabase
from app.core.config import settings

# OpenSearch with connection pool for concurrent requests (default is 10)
_os = OpenSearch(
    settings.OPENSEARCH_URL,
    verify_certs=False,
    maxsize=10,  # Connection pool size per node
    timeout=30,
)
_qd = QdrantClient(url=settings.QDRANT_URL)
_r = None
_r_lock = threading.Lock()
_neo = GraphDatabase.driver(
    settings.NEO4J_URL,
    auth=("neo4j", settings.NEO4J_PASSWORD),
    max_connection_pool_size=10,  # Connection pool for Neo4j
)


def get_opensearch():
    return _os


def get_qdrant():
    return _qd


def get_redis():
    """Thread-safe Redis client initialization."""
    global _r
    if _r is None:
        with _r_lock:
            if _r is None:
                _r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _r


def get_neo4j():
    return _neo


def setup_logging(level: str = "INFO"):
    """Konfiguriert farbiges Logging mit colorlog."""
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s - %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors={},
            style="%",
        )
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
