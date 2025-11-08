#Useful commands
##Redis Streams
###Check messages for consumer groups
docker exec -it <redis-container> redis-cli ping
docker exec -it <redis-container> redis-cli XINFO STREAM doc.uploaded
docker exec -it <redis-container> redis-cli XINFO STREAM doc.indexed
docker exec -it <redis-container> redis-cli XINFO STREAM doc.failed
docker exec -it <redis-container> redis-cli XINFO GROUPS doc.uploaded
docker exec -it <redis-container> redis-cli XPENDING doc.uploaded monolith