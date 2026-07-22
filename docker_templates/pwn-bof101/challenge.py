#!/usr/bin/env python3
"""Minimal TCP challenge listener for BOF 101 warmup (keeps container alive)."""
from __future__ import annotations

import socket
import threading
from pathlib import Path

HOST = "0.0.0.0"
PORT = 9999
FLAG = Path("/flag").read_text(encoding="utf-8").strip()


def handle(conn: socket.socket, addr) -> None:
    try:
        conn.sendall(b"Buffer Overflow 101 - send your payload (end with newline):\n")
        data = b""
        while b"\n" not in data and len(data) < 4096:
            chunk = conn.recv(256)
            if not chunk:
                break
            data += chunk
        # Toy overflow: long input unlocks flag (swap for real binary later)
        if len(data) >= 80:
            conn.sendall(("Congrats! %s\n" % FLAG).encode())
        else:
            conn.sendall(b"You said: " + data[:64] + b"\nToo short.\n")
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def main() -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(32)
    print("pwn-bof101 listening on %s:%s" % (HOST, PORT), flush=True)
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
