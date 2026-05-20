#!/usr/bin/env python3
"""
检查题目的flag模板配置
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app
from backend.server.extensions import db
from backend.server.db_models import CtfChallenge, CtfGame
from backend.services.flag_generator import ContainerFlagService

app = create_app()

with app.app_context():
    print("\n=== 检查题目Flag模板配置 ===\n")
    
    challenges = CtfChallenge.query.filter(CtfChallenge.docker_image.isnot(None)).all()
    
    if not challenges:
        print("❌ 没有找到容器题目")
        sys.exit(1)
    
    for ch in challenges:
        print(f"题目 #{ch.id}: {ch.title}")
        print(f"  Docker镜像: {ch.docker_image}")
        print(f"  Flag模板: {ch.flag_template or '未设置'}")
        print(f"  静态Flag: {ch.flag or '未设置'}")
        
        # 如果有flag_template，测试生成
        if ch.flag_template:
            game = CtfGame.query.get(ch.game_id)
            team_hash_salt = game.team_hash_salt if game else None
            
            try:
                generated = ContainerFlagService.generate_dynamic_flag(
                    flag_template=ch.flag_template,
                    challenge_id=ch.id,
                    user_id=1,
                    game_id=ch.game_id,
                    team_id=1,
                    team_hash_salt=team_hash_salt
                )
                
                has_placeholder = '[' in generated or ']' in generated
                
                print(f"  ✅ 生成的Flag: {generated}")
                if has_placeholder:
                    print(f"  ⚠️  警告：Flag中仍包含占位符！")
                else:
                    print(f"  ✓ Flag生成正常（占位符已替换）")
            except Exception as e:
                print(f"  ❌ 生成失败: {e}")
        else:
            print(f"  ⚠️  警告：未设置flag_template，将使用静态flag")
        
        print()
