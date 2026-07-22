#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""向指定训练靶场注入标准测试题目（幂等）。

默认目标：
1) GAME_ID 环境变量 / 参数
2) id=11（若存在）
3) game_type=training 且 title='11'
4) 第一个 challenges=0 的 training 靶场
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import create_app
from backend.server.extensions import db
from backend.server.db_models import CtfGame, CtfChallenge

SEED_CHALLENGES = [
    {
        "title": "[Web] Simple SQLi (SQL注入基础)",
        "category": "Web",
        "flag": "flag{sql_injection_basics_neepu}",
        "original_points": 100,
        "difficulty": 2.0,
        "description": (
            "## Simple SQLi\n\n"
            "一道经典的 SQL 注入入门题。\n\n"
            "提示：尝试在登录框或查询参数中构造 `' OR 1=1--`。\n\n"
            "提交 Flag：`flag{sql_injection_basics_neepu}`"
        ),
    },
    {
        "title": "[Crypto] Base64 & Rot13 (古典密码学)",
        "category": "Crypto",
        "flag": "flag{base64_rot13_warmup}",
        "original_points": 100,
        "difficulty": 1.5,
        "description": (
            "## Base64 & Rot13\n\n"
            "密文经过 Base64 与 Rot13 组合处理。\n\n"
            "密文样例：`c3lici1uMzNwLXIwNDE=`（请自行推导完整解法）。\n\n"
            "提交 Flag：`flag{base64_rot13_warmup}`"
        ),
    },
    {
        "title": "[Pwn] Buffer Overflow 101 (栈溢出入门)",
        "category": "Pwn",
        "flag": "flag{stack_bof_101_neepu}",
        "original_points": 200,
        "difficulty": 3.0,
        "description": (
            "## Buffer Overflow 101\n\n"
            "存在明显的栈缓冲区溢出。目标是覆盖返回地址并拿到 shell / 读出 flag。\n\n"
            "本地复现可使用 `pwntools`。\n\n"
            "提交 Flag：`flag{stack_bof_101_neepu}`"
        ),
    },
    {
        "title": "[Reverse] Hello Re (逆向工程初探)",
        "category": "Reverse",
        "flag": "flag{hello_re_neepu}",
        "original_points": 150,
        "difficulty": 2.5,
        "description": (
            "## Hello Re\n\n"
            "分析给出的二进制，找到校验逻辑并还原正确输入。\n\n"
            "推荐工具：IDA / Ghidra / Binary Ninja。\n\n"
            "提交 Flag：`flag{hello_re_neepu}`"
        ),
    },
]


def resolve_game(preferred_id: int | None) -> CtfGame | None:
    if preferred_id:
        g = db.session.get(CtfGame, preferred_id)
        if g:
            return g

    g = db.session.get(CtfGame, 11)
    if g:
        return g

    g = (
        CtfGame.query.filter(
            CtfGame.game_type.in_(["training", "practice"]),
            CtfGame.title == "11",
        )
        .order_by(CtfGame.id.desc())
        .first()
    )
    if g:
        return g

    # fallback: first empty training game
    trainings = (
        CtfGame.query.filter(CtfGame.game_type.in_(["training", "practice"]))
        .order_by(CtfGame.id.asc())
        .all()
    )
    for t in trainings:
        if CtfChallenge.query.filter_by(game_id=t.id).count() == 0:
            return t
    return trainings[0] if trainings else None


def _container_fields(item: dict) -> dict:
    """仅使用种子项显式字段；不按分类强行改题型（以管理端配置为准）。"""
    return {
        "challenge_type": int(item.get("challenge_type") or 0),
        "docker_image": item.get("docker_image"),
        "docker_port": item.get("docker_port"),
    }


def seed(game: CtfGame) -> int:
    created = 0
    updated = 0
    for item in SEED_CHALLENGES:
        fields = _container_fields(item)
        exists = CtfChallenge.query.filter_by(game_id=game.id, title=item["title"]).first()
        if exists:
            # 已存在题目：尊重管理端配置，绝不覆盖 challenge_type
            print(f"  skip exists: {item['title']} (type={exists.challenge_type})")
            continue
        ch = CtfChallenge(
            game_id=game.id,
            title=item["title"],
            category=item["category"],
            description=item["description"],
            flag=item["flag"],
            original_points=item["original_points"],
            difficulty=item["difficulty"],
            challenge_type=fields.get("challenge_type") or 0,
            docker_image=fields.get("docker_image"),
            docker_port=fields.get("docker_port") or 80,
            is_enabled=True,
            disable_blood_bonus=True,
        )
        db.session.add(ch)
        created += 1
        print(f"  + created: [{item['category']}] {item['title']}")
    db.session.commit()
    print(f"  (updated container meta: {updated})")
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed training challenges")
    parser.add_argument("--game-id", type=int, default=None, help="目标比赛/训练场 ID")
    args = parser.parse_args()
    preferred = args.game_id or (int(os.environ["GAME_ID"]) if os.environ.get("GAME_ID") else None)

    app = create_app()
    with app.app_context():
        game = resolve_game(preferred)
        if not game:
            print("ERROR: 未找到可用训练靶场")
            return 1
        print(f"Target game id={game.id} type={game.game_type} status={game.status} title={game.title!r}")
        created = seed(game)
        total = CtfChallenge.query.filter_by(game_id=game.id).count()
        print(f"Done. created={created}, total_challenges={total}")
        try:
            from backend.server.cache_invalidation import invalidate_training_sidebar_cache
            invalidate_training_sidebar_cache()
            print("training sidebar cache invalidated")
        except Exception as exc:
            print(f"cache invalidate skipped: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
