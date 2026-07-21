#!/usr/bin/env python3
"""Append page result(s) into results.json. Usage: python _append_page.py path/to/page.json"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PATH = ROOT / "results.json"
ORDER = {"2.1": 1, "2.2": 2, "2.3": 3, "2.4": 4, "2.5": 5}


def load() -> dict:
    if PATH.exists():
        return json.loads(PATH.read_text(encoding="utf-8"))
    return {
        "account": "mcp_20260721160612_a533c373",
        "finishedAt": None,
        "gameIds": ["68"],
        "summary": {},
        "pages": [],
        "notes": [],
    }


def summarize(data: dict) -> None:
    pages = data.get("pages") or []
    data["summary"] = {
        "pages": len(pages),
        "actions": sum(len(p.get("actions") or []) for p in pages),
        "failed": sum(1 for p in pages if not p.get("ok", True)),
        "withPageErrors": sum(1 for p in pages if p.get("pageErrors")),
        "withConsoleErrors": sum(1 for p in pages if p.get("consoleErrors")),
    }


def upsert(data: dict, page: dict) -> None:
    pages = data.setdefault("pages", [])
    key = (page.get("section"), page.get("path"))
    pages[:] = [p for p in pages if (p.get("section"), p.get("path")) != key]
    pages.append(page)
    indexed = list(enumerate(pages))
    indexed.sort(key=lambda t: (ORDER.get(t[1].get("section"), 99), t[0]))
    data["pages"] = [p for _, p in indexed]
    gids = page.get("gameIds")
    if gids:
        data["gameIds"] = list(dict.fromkeys((data.get("gameIds") or []) + list(gids)))


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    raw = src.read_text(encoding="utf-8") if src else sys.stdin.read()
    payload = json.loads(raw)
    data = load()
    items = payload if isinstance(payload, list) else [payload]
    for page in items:
        upsert(data, page)
    summarize(data)
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(data["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
