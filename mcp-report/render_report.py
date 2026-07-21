#!/usr/bin/env python3
"""生成 MCP 拓扑巡检报告骨架（结果 JSON → HTML）。"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "mcp-report"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "screenshots").mkdir(exist_ok=True)


def render(data: dict) -> str:
    pages = data.get("pages") or []
    summary = data.get("summary") or {}
    cards = []
    for i, p in enumerate(pages):
        err_n = len(p.get("pageErrors") or []) + len(p.get("consoleErrors") or []) + len(p.get("rejections") or [])
        badge = f'<span class="badge bad">{err_n} 问题</span>' if err_n or not p.get("ok", True) else '<span class="badge ok">通过</span>'
        actions = "".join(f"<li><code>{_esc(a)}</code></li>" for a in (p.get("actions") or [])[:30]) or "<p class='ok'>无点击</p>"
        pe = "".join(f"<li><code>{_esc(x)}</code></li>" for x in (p.get("pageErrors") or [])[:10]) or "<p class='ok'>无</p>"
        ce = "".join(f"<li><code>{_esc(x)}</code></li>" for x in (p.get("consoleErrors") or [])[:10]) or "<p class='ok'>无</p>"
        shot = p.get("screenshot")
        fig = f'<figure><img src="{_esc(shot)}" alt="{_esc(p.get("name"))}" loading="lazy"/></figure>' if shot else ""
        cards.append(f"""
<section class="page-card">
  <header><h2>{_esc(p.get('section'))} {_esc(p.get('name'))} {badge}</h2>
  <p class="meta"><code>{_esc(p.get('path'))}</code> → <code>{_esc(p.get('finalUrl'))}</code></p>
  <p class="meta">耗时 {p.get('ms', 0)}ms · 操作 {(p.get('actions') or []).__len__()}</p></header>
  {fig}
  <div class="grid">
    <div><h3>人为操作</h3><ul>{actions}</ul></div>
    <div><h3>pageerror</h3><ul>{pe}</ul></div>
    <div><h3>console.error</h3><ul>{ce}</ul></div>
  </div>
  <p class="sample">{_esc((p.get('bodyTextSample') or '')[:180])}</p>
</section>""")

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"/><title>MCP 路由拓扑巡检报告</title>
<style>
:root{{--bg:#0f1419;--panel:#1a222c;--text:#e7ecf1;--muted:#8b9aab;--ok:#3dd68c;--bad:#ff6b6b;--accent:#5b9fd4;--border:#2a3542}}
body{{margin:0;font-family:Segoe UI,PingFang SC,Microsoft YaHei,sans-serif;background:linear-gradient(160deg,#0b1016,#15202b);color:var(--text)}}
.wrap{{max-width:1100px;margin:0 auto;padding:32px 20px 64px}}
.summary{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:24px 0}}
.stat{{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:14px}}
.stat .n{{font-size:1.6rem;font-weight:700}}.stat .l{{color:var(--muted);font-size:.85rem}}
.page-card{{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:20px}}
.meta{{color:var(--muted);margin:2px 0;font-size:.9rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}
.badge{{font-size:.75rem;padding:2px 8px;border-radius:999px}}
.badge.ok{{background:rgba(61,214,140,.15);color:var(--ok)}}.badge.bad{{background:rgba(255,107,107,.15);color:var(--bad)}}
.ok{{color:var(--ok)}} code{{font-family:Consolas,monospace;font-size:.85rem}}
figure img{{width:100%;border-radius:8px;border:1px solid var(--border)}}
.sample{{color:var(--muted);font-size:.85rem;white-space:pre-wrap}}
h3{{color:var(--accent);font-size:.95rem}}
</style></head><body><div class="wrap">
<h1>MCP 路由拓扑人工操作巡检</h1>
<p class="meta">依据 docs/route-architecture-topology.md · 账号 {_esc(data.get('account'))} · { _esc(data.get('finishedAt') or datetime.now().isoformat()) }</p>
<div class="summary">
  <div class="stat"><div class="n">{summary.get('pages',0)}</div><div class="l">页面</div></div>
  <div class="stat"><div class="n">{summary.get('actions',0)}</div><div class="l">点击/操作</div></div>
  <div class="stat"><div class="n">{summary.get('withPageErrors',0)}</div><div class="l">含 pageerror</div></div>
  <div class="stat"><div class="n">{summary.get('withConsoleErrors',0)}</div><div class="l">含 console.error</div></div>
  <div class="stat"><div class="n">{summary.get('failed',0)}</div><div class="l">失败页</div></div>
</div>
{''.join(cards)}
</div></body></html>"""


def _esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def main():
    raw = sys.stdin.read() if not sys.argv[1:] else Path(sys.argv[1]).read_text(encoding="utf-8")
    data = json.loads(raw)
    (OUT / "results.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    html = render(data)
    out = OUT / "index.html"
    out.write_text(html, encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
