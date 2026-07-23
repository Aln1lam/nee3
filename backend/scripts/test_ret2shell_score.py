# -*- coding: utf-8 -*-
"""核验 ret2shell 余弦衰减公式与 Snapshot Replay。"""
from __future__ import annotations

import math
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.services.scoring_service import ScoringService


def ref_ret2shell(initial, minimum, decay, n):
    if n < 1:
        return initial
    if n >= decay:
        return minimum
    ratio = (n - 1) / (decay - 1)
    return int(round(minimum + (initial - minimum) * (math.cos(ratio * math.pi) + 1) / 2))


def main() -> int:
    # score-picker 对照：max=1000 min=200 decay=10
    for n in range(0, 12):
        got = ScoringService.calculate_ret2shell_score(1000, 200, 10, n)
        expect = ref_ret2shell(1000, 200, 10, n)
        assert got == expect, (n, got, expect)
        print(f"N={n:2d} score={got}")

    # 平台字段映射：original=1000 rate=0.2 difficulty=10 → min=200 decay=10
    s1 = ScoringService.calculate_dynamic_score(1000, 1, 0.2, 10)
    s5 = ScoringService.calculate_dynamic_score(1000, 5, 0.2, 10)
    s10 = ScoringService.calculate_dynamic_score(1000, 10, 0.2, 10)
    assert s1 == 1000, s1
    assert s10 == 200, s10
    assert s5 < s1 and s5 > s10, (s1, s5, s10)
    print(f"mapped: N1={s1} N5={s5} N10={s10}")

    assert hasattr(ScoringService, "generate_gzctf_style_timeline")
    assert hasattr(ScoringService, "get_timeline_cached")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
