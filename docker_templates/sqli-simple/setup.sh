#!/bin/sh
set -e

MARKER=/var/lib/mysql/.sqli_simple_ready
if [ -f "$MARKER" ]; then
  exit 0
fi

for _ in $(seq 1 30); do
  if mysqladmin ping -uroot -proot --silent 2>/dev/null; then
    break
  fi
  sleep 1
done

mysql -uroot -proot <<'SQL'
CREATE DATABASE IF NOT EXISTS sqli;
USE sqli;
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(64) NOT NULL,
  password VARCHAR(64) NOT NULL
);
CREATE TABLE IF NOT EXISTS secrets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  note VARCHAR(255) NOT NULL
);
TRUNCATE TABLE users;
TRUNCATE TABLE secrets;
INSERT INTO users (username, password) VALUES
  ('admin', 'admin123'),
  ('guest', 'guest');
INSERT INTO secrets (note) VALUES ('flag{testflag}');
SQL

touch "$MARKER"
