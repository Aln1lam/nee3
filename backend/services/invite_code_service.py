"""
邀请码验证服务
"""
from typing import Optional, Tuple
from datetime import datetime
from backend.server.extensions import db
from backend.server.db_models import (
    CtfDivision, CtfUserInviteCode, User, CtfGame
)

class InviteCodeService:
    """邀请码验证和管理服务"""
    
    @staticmethod
    def verify_invite_code(
        user: User,
        game_id: int,
        invite_code: str
    ) -> Tuple[bool, Optional[CtfDivision], str]:
        """
        验证邀请码
        
        Args:
            user: 用户对象
            game_id: 竞赛 ID
            invite_code: 邀请码
        
        Returns:
            (是否有效, Division对象, 消息)
        """
        # 1. 查找对应的 Division
        division = CtfDivision.query.filter_by(
            game_id=game_id,
            invite_code=invite_code
        ).first()
        
        if not division:
            return False, None, "邀请码无效"
        
        # 2. 检查学校范围限制
        if division.school_scope:
            if division.school_scope == "高校":
                # 高校赛道，只有学生可以参加
                if not user.identity or user.identity not in ["student", "teacher"]:
                    return False, None, "此赛道仅限高校用户参加"
            elif division.school_scope != user.school:
                # 特定学校赛道
                return False, None, f"此赛道仅限 {division.school_scope} 用户参加"
        
        # 3. 检查是否已经使用过此邀请码
        existing = CtfUserInviteCode.query.filter_by(
            user_id=user.id,
            game_id=game_id,
            division_id=division.id
        ).first()
        
        if existing:
            return True, division, "已使用过此邀请码"
        
        return True, division, "邀请码验证通过"
    
    @staticmethod
    def record_invite_code_usage(
        user_id: int,
        game_id: int,
        division_id: int,
        invite_code: str
    ):
        """
        记录用户使用邀请码
        
        Args:
            user_id: 用户 ID
            game_id: 竞赛 ID
            division_id: 赛道 ID
            invite_code: 使用的邀请码
        """
        record = CtfUserInviteCode(
            user_id=user_id,
            game_id=game_id,
            division_id=division_id,
            invite_code_used=invite_code,
            verified_at=datetime.utcnow()
        )
        db.session.add(record)
        db.session.commit()
    
    @staticmethod
    def get_user_divisions(user_id: int, game_id: int):
        """
        获取用户在某个竞赛中参加的所有赛道
        
        Args:
            user_id: 用户 ID
            game_id: 竞赛 ID
        
        Returns:
            Division 列表
        """
        records = CtfUserInviteCode.query.filter_by(
            user_id=user_id,
            game_id=game_id
        ).all()
        
        return [CtfDivision.query.get(r.division_id) for r in records]
    
    @staticmethod
    def generate_invite_code(
        game_id: int,
        division_name: str,
        school_name: Optional[str] = None
    ) -> str:
        """
        生成邀请码
        
        Args:
            game_id: 竞赛 ID
            division_name: 赛道名称
            school_name: 学校名称（可选）
        
        Returns:
            邀请码字符串
        """
        import hashlib
        
        # 基础格式: ctf_{game_id}_{division}
        base = f"ctf_{game_id}_{division_name.lower().replace(' ', '_')}"
        
        # 如果有学校，添加学校代码
        if school_name:
            school_code = school_name[:2]  # 取学校名前两个字
            base += f"_{school_code}"
        
        # 添加短哈希确保唯一性
        hash_input = f"{base}_{datetime.utcnow().timestamp()}"
        short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:6]
        
        return f"{base}_{short_hash}"
    
    @staticmethod
    def create_division_with_invite_code(
        game_id: int,
        name: str,
        school_scope: Optional[str] = None,
        description: Optional[str] = None,
        sort_order: int = 0
    ) -> CtfDivision:
        """
        创建赛道并自动生成邀请码
        
        Args:
            game_id: 竞赛 ID
            name: 赛道名称
            school_scope: 学校范围限制
            description: 描述
            sort_order: 排序
        
        Returns:
            创建的 Division 对象
        """
        # 生成邀请码
        invite_code = InviteCodeService.generate_invite_code(
            game_id, name, school_scope
        )
        
        # 创建 Division
        division = CtfDivision(
            game_id=game_id,
            name=name,
            invite_code=invite_code,
            school_scope=school_scope,
            description=description,
            sort_order=sort_order
        )
        
        db.session.add(division)
        db.session.commit()
        
        return division
