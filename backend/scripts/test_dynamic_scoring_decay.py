# -*- coding: utf-8 -*-
"""Smoke: dynamic scoring formula + decay timeline helper shape."""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.services.scoring_service import ScoringService


def test_formula():
    # ret2shell cosine: initial=1000, min=250 (rate 0.25), decay=5
    assert ScoringService.calculate_dynamic_score(1000, 0, 0.25, 5) == 1000
    assert ScoringService.calculate_dynamic_score(1000, 1, 0.25, 5) == 1000
    s5 = ScoringService.calculate_dynamic_score(1000, 5, 0.25, 5)
    assert s5 == 250, s5  # N>=decay → minimum
    s3 = ScoringService.calculate_dynamic_score(1000, 3, 0.25, 5)
    # ratio=(3-1)/(5-1)=0.5 → cos(π/2)=0 → normalized=0.5 → 250+750*0.5=625
    assert s3 == 625, s3
    print("OK formula", s3, s5)


def test_imports():
    assert hasattr(ScoringService, "recalculate_challenge_scores")
    assert hasattr(ScoringService, "build_decay_timeline")
    assert hasattr(ScoringService, "count_accepted_solvers")
    assert hasattr(ScoringService, "calculate_ret2shell_score")
    print("OK methods present")


if __name__ == "__main__":
    test_formula()
    test_imports()
    import py_compile
    for rel in [
        "backend/services/scoring_service.py",
        "backend/route/ctf_api.py",
        "backend/route/challenges.py",
    ]:
        py_compile.compile(str(ROOT / rel), doraise=True)
        print("OK compile", rel)
