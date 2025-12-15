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

## Useful commands for evaluation runner

### 1. DB initialisieren
python -m app.eval.runner initdb

### 2. Pre-Flight Check
python -m app.eval.scripts.check

### 3. Dataset laden
python -m app.eval.runner load-dataset demo datasets/demo_queries.jsonl datasets/demo_qrels_1800.jsonl

### 4. Answers laden
python -m app.eval.runner load-answers demo datasets/demo_answers.jsonl

### 5. Baseline ausführen
python -m app.eval.runner run configs/baseline.yaml

### 5.1. OFAT ausführen
python -m app.eval.runner study configs/study_ofat.yaml

### 5.2. GSO ausführen
python -m app.eval.runner study configs/study_gso.yaml 

### 6. Scores berechnen
python -m app.eval.runner score BASELINE
