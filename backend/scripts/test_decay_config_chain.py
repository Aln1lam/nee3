# -*- coding: utf-8 -*-
"""Verify decay config is read from challenge object (ret2shell cosine)."""
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.services.scoring_service import ScoringService


def test_reads_challenge_fields():
    # decay=2 vs decay=20 — N=5 时小 decay 已贴底，大 decay 仍较高
    ch_fast = SimpleNamespace(original_points=1000, min_score_rate=0.25, difficulty=2.0, id=1, points=1000)
    ch_slow = SimpleNamespace(original_points=1000, min_score_rate=0.25, difficulty=20.0, id=2, points=1000)

    ScoringService.count_accepted_solvers = staticmethod(lambda cid: 5)

    fast = ScoringService.challenge_base_dynamic_score(ch_fast, 5)
    slow = ScoringService.challenge_base_dynamic_score(ch_slow, 5)
    assert fast < slow, (fast, slow)
    # decay=2, N=5 → N>=decay → minimum=250
    assert fast == 250, fast
    print("OK field-driven decay", fast, slow)


def test_fe_payload_forces_numbers():
    text = (ROOT / "frontend/src/components/admin/CtfManagement.vue").read_text(encoding="utf-8")
    assert "payload.min_score_rate = Number" in text
    assert "payload.difficulty = Number" in text
    assert "payload.original_points = Number" in text
    print("OK FE Number() force")


def test_admin_rescore_hook():
    text = (ROOT / "backend/route/challenge_admin.py").read_text(encoding="utf-8")
    assert "scoring_changed" in text
    assert "recalculate_challenge_scores" in text
    print("OK admin rescore hook")


if __name__ == "__main__":
    test_reads_challenge_fields()
    test_fe_payload_forces_numbers()
    test_admin_rescore_hook()
    import py_compile
    for rel in [
        "backend/services/scoring_service.py",
        "backend/route/challenge_admin.py",
        "backend/route/ctf_admin.py",
        "backend/route/ctf_api.py",
        "backend/route/challenges.py",
    ]:
        py_compile.compile(str(ROOT / rel), doraise=True)
    print("ALL_OK")
