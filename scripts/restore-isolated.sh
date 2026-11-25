#!/usr/bin/env bash
set -Eeuo pipefail
root=${TODO_ROOT:-/opt/todo}
compose=${COMPOSE_FILE:-$root/compose.yml}
archive=${1:?archive required}
expected=${2:?expected canonical data SHA-256 required}
image=${MONGO_IMAGE:-mongo:8.0}
[[ -f "$archive" && "$expected" =~ ^[a-f0-9]{64}$ ]] || exit 2
name="todo-restore-$(date +%s)-$RANDOM"
running=$(docker compose -f "$compose" ps --status running -q mongo)
cleanup() {
  if [[ "$name" == todo-restore-* ]]; then
    docker rm -f "$name" >/dev/null 2>&1 || true
    docker volume rm "$name" >/dev/null 2>&1 || true
  fi
  if [[ -n "$running" ]]; then docker compose -f "$compose" start mongo >/dev/null; fi
}
trap cleanup EXIT
# Sequential restore avoids two Mongo working sets exhausting an e2-micro.
# The production data volume is never mounted by this isolated container.
docker compose -f "$compose" stop mongo >/dev/null
docker volume create "$name" >/dev/null
docker run -d --name "$name" --network none --memory 384m --mount "type=volume,source=$name,target=/data/db" --entrypoint mongod "$image" --bind_ip 127.0.0.1 --wiredTigerCacheSizeGB 0.256 >/dev/null
ready=0
for _ in {1..45}; do
  if docker exec "$name" bash -c 'exec 3<>/dev/tcp/127.0.0.1/27017' >/dev/null 2>&1; then ready=1; break; fi
  sleep 1
done
[[ "$ready" == 1 ]] || { echo 'restore_database_start_failed'; exit 1; }

docker exec -i "$name" mongorestore --host=127.0.0.1 --archive --gzip --nsInclude='todo-app.*' < "$archive" >/dev/null 2>&1
actual=$(docker exec "$name" timeout --kill-after=10s 120s mongosh 'mongodb://127.0.0.1:27017/admin?serverSelectionTimeoutMS=10000&connectTimeoutMS=10000' --quiet --norc --eval "print(JSON.stringify(db.getSiblingDB('todo-app').todos.find({}, {_id:1,text:1,completed:1}).sort({_id:1}).toArray()))" | sha256sum | cut -d' ' -f1)
[[ "$actual" == "$expected" ]] || { echo 'restore_validation_failed'; exit 1; }
printf '{"event":"isolated_restore_validated","data_sha256":"%s","production_overwritten":false}\n' "$actual"
