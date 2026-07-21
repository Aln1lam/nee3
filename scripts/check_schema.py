"""Check and fix missing DB columns."""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.app import create_app
from backend.server.extensions import db

app = create_app()

MISSING_COLUMNS = [
    ("ctf_game", "description", "ALTER TABLE ctf_game ADD COLUMN description TEXT NULL"),
    ("ctf_game", "game_type", "ALTER TABLE ctf_game ADD COLUMN game_type VARCHAR(32) DEFAULT 'official'"),
    ("ctf_game", "archived_at", "ALTER TABLE ctf_game ADD COLUMN archived_at DATETIME NULL"),
    ("ctf_game", "season_id", "ALTER TABLE ctf_game ADD COLUMN season_id INT NULL"),
    ("ctf_game", "status", "ALTER TABLE ctf_game ADD COLUMN status VARCHAR(32) DEFAULT 'not_started'"),
    ("ctf_game", "is_public", "ALTER TABLE ctf_game ADD COLUMN is_public TINYINT(1) DEFAULT 1"),
]

with app.app_context():
    rows = db.session.execute(
        text(
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ctf_game' "
            "ORDER BY ORDINAL_POSITION"
        )
    ).fetchall()
    existing = {r[0] for r in rows}
    print("ctf_game columns:", sorted(existing))

    for table, column, alter_sql in MISSING_COLUMNS:
        if column in existing:
            print(f"OK: {table}.{column}")
            continue
        print(f"ADD: {table}.{column}")
        db.session.execute(text(alter_sql))
    db.session.commit()
    print("Schema sync done.")
