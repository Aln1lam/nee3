#!/usr/bin/env python
import sys
sys.path.insert(0, 'e:\\neepu\\backend')
from server.extensions import db
from server.db_models import CtfGame, CtfChallenge, CtfUserInviteCode, CtfDivision, CtfParticipation, CtfParticipatingUser
from app import create_app

app = create_app()
with app.app_context():
    print("=" * 60)
    print("GAME 1 (公开比赛)")
    print("=" * 60)
    game1 = CtfGame.query.get(1)
    if game1:
        print(f"Title: {game1.title}")
        print(f"Is Public: {game1.is_public}")
        
        # 题目数
        challenges = CtfChallenge.query.filter_by(game_id=1, is_enabled=True).count()
        print(f"Challenge Count: {challenges}")
        
        # 参赛人数（参赛用户）
        users = CtfParticipatingUser.query.filter_by(game_id=1).distinct(CtfParticipatingUser.user_id).count()
        print(f"Participating Users: {users}")
        
        # 邀请码数
        invites = CtfUserInviteCode.query.filter_by(game_id=1).count()
        print(f"Invite Codes: {invites}")
    
    print("\n" + "=" * 60)
    print("GAME 2 (非公开比赛)")
    print("=" * 60)
    game2 = CtfGame.query.get(2)
    if game2:
        print(f"Title: {game2.title}")
        print(f"Is Public: {game2.is_public}")
        
        # 题目数
        challenges = CtfChallenge.query.filter_by(game_id=2, is_enabled=True).count()
        print(f"Challenge Count: {challenges}")
        
        # 邀请码数（应该用这个来计算成员数）
        invites = CtfUserInviteCode.query.filter_by(game_id=2).distinct(CtfUserInviteCode.user_id).count()
        print(f"Users with Invite Codes: {invites}")
        
        # 显示具体的邀请码数据
        invites_data = CtfUserInviteCode.query.filter_by(game_id=2).all()
        print(f"Invite codes details:")
        for ic in invites_data:
            print(f"  - user_id={ic.user_id}, division_id={ic.division_id}, code={ic.invite_code_used}")
    
    print("\n" + "=" * 60)
    print("ALL INVITE CODES")
    print("=" * 60)
    all_invites = CtfUserInviteCode.query.all()
    print(f"Total: {len(all_invites)}")
    for ic in all_invites:
        print(f"  - user {ic.user_id}, game {ic.game_id}, division {ic.division_id}")
