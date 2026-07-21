#!/usr/bin/env bash
# NEEPU CTF 单机备份：MySQL + 上传目录 + 流量包
# 建议 cron：0 3 * * 0 /opt/neepu/scripts/backup.sh >> /var/log/neepu-backup.log 2>&1

set -euo pipefail

ROOT="${NEPU_ROOT:-/opt/neepu}"
BACKUP_ROOT="${NEPU_BACKUP_ROOT:-/var/backups/neepu}"
DATE_TAG="$(date +%F_%H%M)"
RETAIN_DAYS="${NEPU_BACKUP_RETAIN_DAYS:-28}"

ENV_FILE="${ROOT}/backend/.env"
if [[ -f "${ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  set -a
  source <(grep -E '^NEPU_DATABASE_URL=' "${ENV_FILE}" | sed 's/^/export /')
  set +a
fi

DB_URL="${NEPU_DATABASE_URL:-mysql+pymysql://neepu_user@127.0.0.1:3306/neepu}"

# 从 SQLAlchemy URL 解析 mysql 连接参数（仅支持 mysql+pymysql）
if [[ "${DB_URL}" =~ mysql\+pymysql://([^:@/]+):?([^@/]*)@([^:/]+):?([0-9]*)/([^?]+) ]]; then
  DB_USER="${BASH_REMATCH[1]}"
  DB_PASS="${BASH_REMATCH[2]}"
  DB_HOST="${BASH_REMATCH[3]:-127.0.0.1}"
  DB_PORT="${BASH_REMATCH[4]:-3306}"
  DB_NAME="${BASH_REMATCH[5]}"
else
  echo "[backup] 无法解析 NEPU_DATABASE_URL: ${DB_URL}" >&2
  exit 1
fi

mkdir -p "${BACKUP_ROOT}/mysql" "${BACKUP_ROOT}/uploads" "${BACKUP_ROOT}/captures"

MYSQL_DUMP="${BACKUP_ROOT}/mysql/${DB_NAME}_${DATE_TAG}.sql.gz"
UPLOADS_ARCHIVE="${BACKUP_ROOT}/uploads/uploads_${DATE_TAG}.tar.gz"
CAPTURES_ARCHIVE="${BACKUP_ROOT}/captures/captures_${DATE_TAG}.tar.gz"

echo "[backup] ${DATE_TAG} start"

export MYSQL_PWD="${DB_PASS}"
mysqldump -h "${DB_HOST}" -P "${DB_PORT}" -u "${DB_USER}" \
  --single-transaction --routines --triggers "${DB_NAME}" \
  | gzip -9 > "${MYSQL_DUMP}"
unset MYSQL_PWD

if [[ -d "${ROOT}/backend/static/uploads" ]]; then
  tar -czf "${UPLOADS_ARCHIVE}" -C "${ROOT}/backend/static" uploads
fi

if [[ -d "${ROOT}/backend/captures" ]]; then
  tar -czf "${CAPTURES_ARCHIVE}" -C "${ROOT}/backend" captures
fi

find "${BACKUP_ROOT}/mysql" -type f -name '*.sql.gz' -mtime +"${RETAIN_DAYS}" -delete
find "${BACKUP_ROOT}/uploads" -type f -name '*.tar.gz' -mtime +"${RETAIN_DAYS}" -delete
find "${BACKUP_ROOT}/captures" -type f -name '*.tar.gz' -mtime +"${RETAIN_DAYS}" -delete

echo "[backup] done"
echo "  mysql:   ${MYSQL_DUMP}"
echo "  uploads: ${UPLOADS_ARCHIVE}"
echo "  captures:${CAPTURES_ARCHIVE}"
