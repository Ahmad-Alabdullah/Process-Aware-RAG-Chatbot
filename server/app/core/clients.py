import redis.asyncio as redis
from opensearchpy import OpenSearch
from qdrant_client import QdrantClient
from neo4j import GraphDatabase
from app.core.config import settings

_os = OpenSearch(settings.OPENSEARCH_URL, verify_certs=False)
_qd = QdrantClient(url=settings.QDRANT_URL)
_r = None
_neo = GraphDatabase.driver(settings.NEO4J_URL, auth=("neo4j", settings.NEO4J_PASSWORD))


def get_opensearch():
    return _os


def get_qdrant():
    return _qd


def get_redis():
    global _r
    if _r is None:
        _r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _r


def get_neo4j():
    return _neo
