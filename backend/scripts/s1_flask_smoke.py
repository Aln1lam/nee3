# -*- coding: utf-8 -*-
"""Flask test-client checks for S1 P0 routes (no Docker)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

# Prefer sqlite for smoke if configured; otherwise use app defaults
from backend.app import app
from backend.services.sensitive_words import assert_clean_team_name

client = app.test_client()

# dynamic packages list without JWT -> 401/422 from jwt
r = client.get("/api/admin/dynamic-packages/challenges/1/packages")
assert r.status_code in (401, 422), r.status_code

# route exists (not 404)
assert r.status_code != 404

# sensitive words unit
ok, _ = assert_clean_team_name("HelloTeam")
assert ok
ok, msg = assert_clean_team_name("admin官方")
assert not ok and msg

# container alias blueprint registered
rules = {str(x) for x in app.url_map.iter_rules()}
assert any("/api/challenges/<int:challenge_id>/start-container" in r or "start-container" in r for r in rules)
assert any("dynamic-packages" in r for r in rules)
assert any("container-status" in r for r in rules)

print("FLASK_SMOKE_OK", "status_without_jwt=", r.status_code)
