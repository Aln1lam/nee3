#!/usr/bin/env python3
import urllib.request
import requests

BASE = "http://127.0.0.1:5000"
s = requests.Session()
s.post(f"{BASE}/api/auth/login", json={"account": "neepu_admin", "password": "NeepuAdmin2025!"})
r = s.post(f"{BASE}/api/container/start/209", timeout=90)
print("start", r.status_code, r.text[:300])
data = r.json().get("data") or {}
port = data.get("port")
url = data.get("connection_url") or (f"http://127.0.0.1:{port}" if port else None)
print("url", url)
if not url:
    raise SystemExit(1)
for path in ["/", "/index.html", "/index.php"]:
    u = url.rstrip("/") + path
    try:
        resp = urllib.request.urlopen(u, timeout=8)
        body = resp.read().decode("utf-8", "replace")
        print(f"\n--- {path} len={len(body)} ---")
        print(body)
    except Exception as e:
        print(path, "ERR", e)
