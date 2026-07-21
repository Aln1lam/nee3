"""流量包捕获：目录存储 + 数据库记录联调"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from backend.server.extensions import db
from backend.server.db_models import (
    PcapCapture,
    CtfChallenge,
    CtfGameInstance,
    User,
    Team,
)
from backend.server.traffic_capture import get_traffic_manager

logger = logging.getLogger(__name__)


class TrafficCaptureService:
    @staticmethod
    def _resolve_team_id(user_id: int, folder_team_id: Optional[int], instance: Optional[CtfGameInstance]) -> Optional[int]:
        if instance and instance.team_id and Team.query.get(instance.team_id):
            return instance.team_id
        if folder_team_id and Team.query.get(folder_team_id):
            return folder_team_id
        user = User.query.get(user_id)
        if user and user.team_id and Team.query.get(user.team_id):
            return user.team_id
        return None

    @staticmethod
    def _admin_user(user):
        return user and getattr(user, "is_admin", False)

    @staticmethod
    def _resolve_file_path(relative_path: str) -> Path:
        manager = get_traffic_manager()
        full = (manager.base_dir / relative_path).resolve()
        base = manager.base_dir.resolve()
        if not str(full).startswith(str(base)):
            raise ValueError("非法文件路径")
        return full

    @staticmethod
    def sync_game_records(game_id: int) -> None:
        """将 captures/ 目录下的 PCAP 与数据库记录对齐。"""
        manager = get_traffic_manager()
        challenge_ids = [
            c.id for c in CtfChallenge.query.filter_by(game_id=game_id).all()
        ]
        if not challenge_ids:
            return

        records = (
            PcapCapture.query.join(CtfChallenge)
            .filter(CtfChallenge.game_id == game_id)
            .all()
        )
        for rec in records:
            rec.file_path = Path(rec.file_path).as_posix()
            full_path = manager.base_dir / rec.file_path
            if full_path.exists():
                rec.file_size = full_path.stat().st_size
                rec.is_completed = True
            else:
                rec.is_completed = False

        for challenge_id in challenge_ids:
            for item in manager.list_captures(challenge_id=challenge_id):
                rel_path = item.get("path")
                if not rel_path:
                    continue
                rel_path = Path(rel_path).as_posix()
                if PcapCapture.query.filter_by(
                    challenge_id=challenge_id,
                    file_path=rel_path,
                ).first():
                    continue

                user_id = item.get("user_id")
                folder_team_id = item.get("team_id")
                if not user_id:
                    continue

                instance = (
                    CtfGameInstance.query.filter_by(
                        challenge_id=challenge_id,
                        user_id=user_id,
                    )
                    .order_by(CtfGameInstance.started_at.desc())
                    .first()
                )
                if not instance:
                    logger.debug(
                        "Skip orphan PCAP without instance: %s", rel_path
                    )
                    continue

                resolved_team_id = TrafficCaptureService._resolve_team_id(
                    user_id, folder_team_id, instance
                )

                db.session.add(
                    PcapCapture(
                        challenge_id=challenge_id,
                        instance_id=instance.id,
                        team_id=resolved_team_id,
                        user_id=user_id,
                        file_path=rel_path,
                        file_size=item.get("size") or 0,
                        is_completed=True,
                    )
                )

        db.session.commit()

    @classmethod
    def reconcile_consistency(
        cls,
        delete_missing_records: bool = True,
        prune_orphan_files: bool = False,
    ) -> Dict:
        """全库 PCAP 一致性清扫。

        - 缺文件的 DB 记录：默认删除
        - 磁盘有文件但无记录：尽量写入 DB（有实例时）；否则按 prune_orphan_files 决定是否删文件
        """
        manager = get_traffic_manager()
        stats = {
            "missing_records_deleted": 0,
            "orphans_imported": 0,
            "orphan_files_deleted": 0,
            "orphan_files_kept": 0,
            "size_refreshed": 0,
        }

        # 1) DB → 磁盘
        for rec in PcapCapture.query.all():
            try:
                full = manager.base_dir / Path(rec.file_path).as_posix()
            except Exception:
                full = None
            if full is not None and full.exists():
                size = full.stat().st_size
                if rec.file_size != size or not rec.is_completed:
                    rec.file_size = size
                    rec.is_completed = True
                    stats["size_refreshed"] += 1
                continue
            if delete_missing_records:
                db.session.delete(rec)
                stats["missing_records_deleted"] += 1
            else:
                rec.is_completed = False

        db.session.flush()

        # 2) 磁盘 → DB
        known_paths = {
            Path(r.file_path).as_posix()
            for r in PcapCapture.query.all()
        }
        for pcap_file in manager.iter_pcap_files():
            try:
                rel = pcap_file.relative_to(manager.base_dir).as_posix()
            except ValueError:
                continue
            if rel in known_paths:
                continue

            # folder: challenge_{cid}_team_{tid}_user_{uid}
            folder = pcap_file.parent.name
            parts = folder.split("_")
            challenge_id = team_id = user_id = None
            try:
                if "challenge" in parts and "team" in parts and "user" in parts:
                    challenge_id = int(parts[parts.index("challenge") + 1])
                    team_id = int(parts[parts.index("team") + 1])
                    user_id = int(parts[parts.index("user") + 1])
            except (ValueError, IndexError):
                challenge_id = team_id = user_id = None

            imported = False
            if challenge_id and user_id:
                instance = (
                    CtfGameInstance.query.filter_by(
                        challenge_id=challenge_id,
                        user_id=user_id,
                    )
                    .order_by(CtfGameInstance.started_at.desc())
                    .first()
                )
                if instance:
                    resolved_team = cls._resolve_team_id(user_id, team_id, instance)
                    db.session.add(
                        PcapCapture(
                            challenge_id=challenge_id,
                            instance_id=instance.id,
                            team_id=resolved_team,
                            user_id=user_id,
                            file_path=rel,
                            file_size=pcap_file.stat().st_size,
                            is_completed=True,
                        )
                    )
                    known_paths.add(rel)
                    stats["orphans_imported"] += 1
                    imported = True

            if imported:
                continue
            if prune_orphan_files:
                try:
                    pcap_file.unlink()
                    stats["orphan_files_deleted"] += 1
                except Exception as e:
                    logger.warning("Delete orphan PCAP failed %s: %s", rel, e)
            else:
                stats["orphan_files_kept"] += 1

        db.session.commit()
        try:
            q = manager.enforce_disk_quota()
            stats["quota"] = q
        except Exception as e:
            logger.debug("quota after reconcile: %s", e)
        logger.info("PCAP reconcile: %s", stats)
        return stats

    @staticmethod
    def serialize_record(rec: PcapCapture) -> Dict:
        manager = get_traffic_manager()
        challenge = rec.challenge or CtfChallenge.query.get(rec.challenge_id)
        user = rec.user or User.query.get(rec.user_id)
        team = Team.query.get(rec.team_id) if rec.team_id else None
        full_path = manager.base_dir / rec.file_path
        return {
            **rec.to_dict(),
            "game_id": challenge.game_id if challenge else None,
            "challenge_title": challenge.title if challenge else None,
            "user_nickname": (user.nickname or user.username) if user else None,
            "team_name": team.name if team else None,
            "file_exists": full_path.exists(),
            "absolute_path": str(full_path.resolve()) if full_path.exists() else None,
            "storage_dir": str(manager.base_dir.resolve()),
        }

    @classmethod
    def list_game_captures(cls, game_id: int, sync: bool = True) -> Dict:
        if sync:
            cls.sync_game_records(game_id)

        records = (
            PcapCapture.query.join(CtfChallenge)
            .filter(CtfChallenge.game_id == game_id)
            .order_by(PcapCapture.created_at.desc())
            .all()
        )
        manager = get_traffic_manager()
        items = [cls.serialize_record(r) for r in records]
        return {
            "items": items,
            "total": len(items),
            "storage_dir": str(manager.base_dir.resolve()),
        }

    @classmethod
    def get_capture_for_download(
        cls, capture_id: int
    ) -> Tuple[Optional[PcapCapture], Optional[Path], Optional[str]]:
        rec = PcapCapture.query.get(capture_id)
        if not rec:
            return None, None, "记录不存在"
        try:
            full_path = cls._resolve_file_path(rec.file_path)
        except ValueError as e:
            return rec, None, str(e)
        if not full_path.exists():
            return rec, None, "PCAP 文件不存在"
        return rec, full_path, None

    @classmethod
    def delete_capture(cls, capture_id: int) -> Tuple[bool, str]:
        rec = PcapCapture.query.get(capture_id)
        if not rec:
            return False, "记录不存在"
        try:
            full_path = cls._resolve_file_path(rec.file_path)
            if full_path.exists():
                full_path.unlink()
        except ValueError:
            pass
        db.session.delete(rec)
        db.session.commit()
        return True, "已删除"
