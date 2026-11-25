#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
root=${TODO_ROOT:-/opt/todo}
cd "$root"
compose=${COMPOSE_FILE:-$root/compose.yml}
wait_seconds=${TODO_DEPLOY_WAIT_SECONDS:-120}
[[ "$wait_seconds" =~ ^[0-9]+$ ]] || exit 2
ready() {
  curl --fail --silent --show-error --retry 10 --retry-delay 1 --retry-max-time 30 --retry-all-errors --max-time 5 http://127.0.0.1:8080/health/ready >/dev/null
}
if [[ ${1:-} == rollback ]]; then
  [[ -s release.previous.env ]] || { echo 'No previous release'; exit 2; }
  cp release.env release.failed.env
  cp release.previous.env release.env
  docker compose --env-file release.env -f "$compose" up -d --wait --wait-timeout "$wait_seconds"
  ready
  echo '{"event":"rolled_back"}'
  exit
fi
frontend=${1:?frontend image required}; backend=${2:?backend image required}; version=${3:?version required}
[[ "$frontend" =~ ^[a-zA-Z0-9./:@_-]+$ && "$backend" =~ ^[a-zA-Z0-9./:@_-]+$ && "$version" =~ ^[a-zA-Z0-9._-]+$ ]] || exit 2
printf 'FRONTEND_IMAGE=%s\nBACKEND_IMAGE=%s\nAPP_VERSION=%s\n' "$frontend" "$backend" "$version" > release.next.env
if [[ -f release.env ]] && cmp -s release.env release.next.env; then
  docker compose --env-file release.env -f "$compose" up -d --wait --wait-timeout "$wait_seconds" >/dev/null
  ready
  rm release.next.env
  echo '{"event":"unchanged"}'
  exit
fi
if [[ -f release.env ]]; then cp release.env release.previous.env; fi
mv release.next.env release.env
if ! docker compose --env-file release.env -f "$compose" up -d --pull never --wait --wait-timeout "$wait_seconds" || ! ready; then
  if [[ -s release.previous.env ]]; then
    cp release.previous.env release.env
    docker compose --env-file release.env -f "$compose" up -d --wait --wait-timeout "$wait_seconds"
    ready
  fi
  echo 'Deployment failed; previous release restored when available' >&2
  exit 1
fi
echo '{"event":"deployed"}'
