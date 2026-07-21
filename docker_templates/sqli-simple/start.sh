#!/bin/sh
set -e

/flag.sh

mkdir -p /run/mysqld
chown mysql:mysql /run/mysqld 2>/dev/null || true
mysqld --user=mysql &
MYSQL_PID=$!

for _ in $(seq 1 40); do
  if mysqladmin ping -uroot -proot --silent 2>/dev/null; then
    break
  fi
  sleep 1
done

/setup.sh
php-fpm &
exec nginx
