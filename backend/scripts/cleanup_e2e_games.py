# -*- coding: utf-8 -*-
"""Hide leftover E2E / API probe competitions from the public games list.

These scripts create real CtfGame rows (not traffic PCAP files):
  traffic_capture_e2e / sqli_traffic_capture_e2e / container_lifecycle_e2e
  full_competition_e2e / verify_capture_ports_flag / API probes

Usage:
  python backend/scripts/cleanup_e2e_games.py           # dry-run
  python backend/scripts/cleanup_e2e_games.py --apply   # set is_public=False
"""
from __future__ import annotations

import argparse
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.chdir(os.path.join(ROOT, 'backend'))

from backend.app import app  # noqa: E402
from backend.server.db_models import db, CtfGame  # noqa: E402
from backend.server.game_filters import is_ephemeral_test_game  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Persist is_public=False')
    args = parser.parse_args()

    with app.app_context():
        games = CtfGame.query.order_by(CtfGame.id.desc()).all()
        targets = [g for g in games if is_ephemeral_test_game(g) and g.is_public]
        print(f'total={len(games)} public_ephemeral={len(targets)}')
        for g in targets:
            print(f'  hide id={g.id} type={g.game_type} title={g.title!r}')
        if not args.apply:
            print('dry-run only; re-run with --apply to hide')
            return
        for g in targets:
            g.is_public = False
        db.session.commit()
        print(f'updated {len(targets)} rows -> is_public=False')


if __name__ == '__main__':
    main()
