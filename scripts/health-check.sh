#!/usr/bin/env bash
# 单机巡检：API / Redis / 磁盘 / Docker 残留容器

set -euo pipefail

ROOT="${NEEPU_ROOT:-/opt/neepu}"
API_URL="${NEPU_HEALTH_URL:-http://127.0.0.1:5000/api/health/ready}"

echo "== NEEPU health check $(date -Is) =="

check_systemd() {
  local unit="$1"
  if systemctl is-active --quiet "${unit}"; then
    echo "[ok] ${unit}"
  else
    echo "[FAIL] ${unit} not active" >&2
    return 1
  fi
}

check_systemd nginx || true
check_systemd neepu-api || true
check_systemd mysql || true

if docker compose -f "${ROOT}/docker-compose.yml" ps --status running 2>/dev/null | grep -q redis; then
  echo "[ok] redis container"
else
  echo "[WARN] redis container not running" >&2
fi

if curl -fsS "${API_URL}" >/dev/null; then
  echo "[ok] ${API_URL}"
else
  echo "[FAIL] ${API_URL}" >&2
fi

df -h / /opt 2>/dev/null || df -h /

RUNNING="$(docker ps -q | wc -l | tr -d ' ')"
echo "[info] running docker containers: ${RUNNING}"
