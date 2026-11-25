#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
root=${TODO_ROOT:-/opt/todo}
# shellcheck disable=SC1091
[[ ! -f "$root/backup.env" ]] || source "$root/backup.env"
compose=${COMPOSE_FILE:-$root/compose.yml}
# A persistent timer may fire immediately after VM boot, before the explicit
# start workflow has started containers that were gracefully stopped earlier.
docker compose -f "$compose" up -d --pull never --wait --wait-timeout 300 mongo >/dev/null
mkdir -p "$root/backups"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
archive="$root/backups/todo-$stamp.archive.gz"
mongo() {
  docker compose -f "$compose" exec -T mongo mongosh --quiet --eval "const fs=require('fs'); db.getSiblingDB('admin').auth('administrator',fs.readFileSync('/run/secrets/mongo_root_password','utf8').trim()); $1"
}
locked=0
unlock() { if [[ "$locked" == 1 ]]; then mongo 'db.adminCommand({fsyncUnlock:1});' >/dev/null; fi; }
trap unlock EXIT
mongo 'db.adminCommand({fsync:1,lock:true});' >/dev/null
locked=1
expected=$(mongo "print(JSON.stringify(db.getSiblingDB('todo-app').todos.find({}, {_id:1,text:1,completed:1}).sort({_id:1}).toArray()))" | sha256sum | cut -d' ' -f1)
docker compose -f "$compose" exec -T mongo mongodump --config=/run/secrets/mongo_tools_config --host=127.0.0.1 --username=administrator --authenticationDatabase=admin --db=todo-app --archive --gzip > "$archive" 2>/dev/null
unlock
locked=0
TODO_ROOT="$root" COMPOSE_FILE="$compose" bash "$(dirname "$0")/restore-isolated.sh" "$archive" "$expected"
archive_sha=$(sha256sum "$archive" | cut -d' ' -f1)
printf '{"validated":true,"archive_sha256":"%s","data_sha256":"%s","created_utc":"%s"}\n' "$archive_sha" "$expected" "$stamp" > "$archive.json"
if [[ -n "${BACKUP_BUCKET:-}" ]]; then
  python3 "$(dirname "$0")/gcs.py" upload "$BACKUP_BUCKET" "todo/$(basename "$archive")" "$archive"
  python3 "$(dirname "$0")/gcs.py" upload "$BACKUP_BUCKET" "todo/$(basename "$archive").json" "$archive.json"
fi
# Remove only old, validated local archives after this backup has recovered
# successfully (and, when configured, both uploads have completed).
while IFS= read -r -d '' manifest; do
  old_archive=${manifest%.json}
  if [[ -f "$old_archive" ]] && python3 -c 'import json,sys; assert json.load(open(sys.argv[1])).get("validated") is True' "$manifest"; then
    rm -- "$old_archive" "$manifest"
  fi
done < <(find "$root/backups" -maxdepth 1 -type f -name 'todo-????????T??????Z.archive.gz.json' -mtime +7 -print0)
echo '{"event":"backup_validated","retention_days":7}'
