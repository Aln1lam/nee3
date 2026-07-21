# -*- coding: utf-8 -*-
"""Smoke checks for S1 P0 backend pieces (no Docker required)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.services.sensitive_words import assert_clean_team_name, find_sensitive_hit
from backend.services.scheduler import scheduler

ok, err = assert_clean_team_name("正常队名")
assert ok, err
ok, err = assert_clean_team_name("fuck team")
assert not ok, "should reject"
assert find_sensitive_hit("官方战队") == "官方"

# scheduler has cleanup job registered after init — check method exists
assert hasattr(scheduler, "_cleanup_expired_containers")
assert hasattr(scheduler, "_register_container_cleanup")

from backend.route import dynamic_packages
assert dynamic_packages.bp.name == "dynamic_packages"

print("SMOKE_OK sensitive_words + scheduler hooks + dynamic_packages bp")
