# Useful commands

## Redis Streams

### Check messages for consumer groups

docker exec -it <redis-container> redis-cli ping

docker exec -it <redis-container> redis-cli XINFO STREAM doc.uploaded

docker exec -it <redis-container> redis-cli XINFO STREAM doc.indexed

docker exec -it <redis-container> redis-cli XINFO STREAM doc.failed

docker exec -it <redis-container> redis-cli XINFO GROUPS doc.uploaded

docker exec -it <redis-container> redis-cli XPENDING doc.uploaded monolith

## Opean Search
### Check index

curl -s http://localhost:PORT/_cat/indices?v

### Check mappings

curl -s http://localhost:PORT/chunks/_mappings

### Check documents

curl -s http://localhost:PORT/chunks/_search \
  -H 'Content-Type: application/json' \
  -d '{"size": 1, "_source": ["document_id","text","meta"], "query":{"match_all":{}}}'

## Qdrant
### Check collections

curl -s http://localhost:PORT/collections

### Check chunks

curl -s http://localhost:PORT/collections/chunks
