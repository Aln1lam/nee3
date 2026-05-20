#!/usr/bin/env python3
"""
CTF 竞赛平台初始化脚本
用于初始化数据库表、创建示例数据等
"""

import sys
import os

# 获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# 添加项目根目录到 Python 路径
sys.path.insert(0, project_root)

from backend.app import create_app, app
from backend.server.extensions import db
from backend.server.db_models import (
    CtfChallengeCategory, CtfGame, CtfChallenge, CtfDivision,
    User, Team
)
from datetime import datetime, timedelta

def init_database():
    """初始化数据库"""
    print("正在初始化数据库...")
    with app.app_context():
        db.create_all()
    print("✓ 数据库初始化完成")

def init_challenge_categories():
    """初始化题目分类"""
    print("正在初始化题目分类...")
    
    categories = [
        {
            'name': 'Web',
            'description': 'Web安全相关题目',
            'icon': '🌐',
            'color': '#1890ff'
        },
        {
            'name': 'PWN',
            'description': '二进制漏洞利用题目',
            'icon': '💣',
            'color': '#ff7a45'
        },
        {
            'name': 'Crypto',
            'description': '密码学题目',
            'icon': '🔐',
            'color': '#722ed1'
        },
        {
            'name': 'Misc',
            'description': '杂项题目',
            'icon': '🎲',
            'color': '#faad14'
        },
        {
            'name': 'Reverse',
            'description': '逆向工程题目',
            'icon': '↩️',
            'color': '#f5222d'
        },
        {
            'name': 'Forensics',
            'description': '数字取证题目',
            'icon': '🔍',
            'color': '#13c2c2'
        },
    ]
    
    with app.app_context():
        for cat in categories:
            existing = CtfChallengeCategory.query.filter_by(name=cat['name']).first()
            if not existing:
                new_cat = CtfChallengeCategory(**cat)
                db.session.add(new_cat)
                print(f"  ✓ 创建分类: {cat['name']}")
        db.session.commit()

def create_sample_game():
    """创建示例竞赛"""
    print("正在创建示例竞赛...")
    
    with app.app_context():
        # 检查是否已存在
        existing_game = CtfGame.query.filter_by(title="NEEPU CTF 2024 春季赛").first()
        if existing_game:
            print("  ✓ 示例竞赛已存在，跳过")
            return existing_game.id
        
        # 创建竞赛
        now = datetime.utcnow()
        game = CtfGame(
            title="NEEPU CTF 2024 春季赛",
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=8),
            is_public=True
        )
        db.session.add(game)
        db.session.flush()
        print(f"  ✓ 创建竞赛: {game.title}")
        
        # 创建分组
        divisions = [
            CtfDivision(game_id=game.id, name="高级组", invite_code="NEEPU2024-ADVANCED"),
            CtfDivision(game_id=game.id, name="中级组", invite_code="NEEPU2024-MIDDLE"),
            CtfDivision(game_id=game.id, name="初级组", invite_code="NEEPU2024-BEGINNER"),
        ]
        for div in divisions:
            db.session.add(div)
            print(f"  ✓ 创建分组: {div.name}")
        
        db.session.commit()
        return game.id

def create_sample_challenges(game_id):
    """创建示例题目"""
    print("正在创建示例题目...")
    
    sample_challenges = [
        {
            'title': '签到题',
            'category': 'Misc',
            'description': '欢迎来到NEEPU CTF！这是一道简单的签到题。\n\n告诉我你的CTF账号名称即可获得flag。',
            'points': 10,
            'flag': 'flag{welcome_to_neepu_ctf}',
            'hint': '注意题目描述中的关键词'
        },
        {
            'title': '简单的Web',
            'category': 'Web',
            'description': '访问指定的网址，找到隐藏的flag。\n\n网址: http://challenge.example.com:8080\n\n提示: 检查HTML注释和cookie。',
            'points': 50,
            'flag': 'flag{html_source_code_is_important}',
            'hint': '右键查看源代码'
        },
        {
            'title': 'Base64解码',
            'category': 'Crypto',
            'description': '解码以下Base64字符串：\n\nZmxhZ3tZb3VyX2ZpcnN0X2VuY3J5cHRpb259\n\n然后提交解码结果作为flag。',
            'points': 30,
            'flag': 'flag{Your_first_encryption}',
            'hint': 'Base64是一种编码方式，不是加密方式'
        },
        {
            'title': '简单的Misc',
            'category': 'Misc',
            'description': '找到隐藏的flag。\n\n所有线索都在这道题的题目、描述和提示中。',
            'points': 40,
            'flag': 'flag{read_carefully}',
            'hint': '仔细阅读每一个字符'
        },
        {
            'title': '字符串搜索',
            'category': 'Misc',
            'description': '在给定的文本中找到flag的格式（以flag{开头，以}结尾）。\n\n文本内容（不要在这里搜索）：\n\n这是一个随机的文本内容，其中包含了许多无关的信息。\n\n真正的flag在附件中的一个隐藏的文件里。',
            'points': 20,
            'flag': 'flag{check_attachment}',
            'hint': '下载附件并查看所有文件'
        },
    ]
    
    with app.app_context():
        for i, challenge_data in enumerate(sample_challenges):
            existing = CtfChallenge.query.filter_by(
                game_id=game_id,
                title=challenge_data['title']
            ).first()
            
            if not existing:
                challenge = CtfChallenge(
                    game_id=game_id,
                    **challenge_data,
                    is_enabled=True,
                    submission_limit=0  # 无限制
                )
                db.session.add(challenge)
                print(f"  ✓ 创建题目: {challenge_data['title']} ({challenge_data['points']} pts)")
        
        db.session.commit()

def init_system_config():
    """初始化系统配置"""
    print("正在初始化系统配置...")
    
    from backend.server.db_models import SystemConfig
    
    with app.app_context():
        configs = {
            'site_name': 'NEEPU CTF Platform',
            'allow_registration': 'true',
            'ctf_enabled': 'true',
            'max_team_size': '5',
            'max_containers_per_team': '3',
        }
        
        for key, value in configs.items():
            existing = SystemConfig.query.filter_by(key=key).first()
            if not existing:
                config = SystemConfig(key=key, value=value)
                db.session.add(config)
                print(f"  ✓ 配置: {key} = {value}")
        
        db.session.commit()

def main():
    """主函数"""
    print("=" * 60)
    print("CTF 功能迁移 - 初始化脚本")
    print("=" * 60)
    print()
    
    try:
        # 步骤1: 初始化数据库
        init_database()
        print()
        
        # 步骤2: 初始化题目分类
        init_challenge_categories()
        print()
        
        # 步骤3: 初始化系统配置
        init_system_config()
        print()
        
        # 步骤4: 创建示例竞赛
        game_id = create_sample_game()
        print()
        
        # 步骤5: 创建示例题目
        create_sample_challenges(game_id)
        print()
        
        print("=" * 60)
        print("✓ 初始化完成！")
        print("=" * 60)
        print()
        print("后续步骤：")
        print("1. 启动后端服务: python -m backend.app")
        print("2. 启动前端服务: cd frontend && npm run dev")
        print("3. 访问CTF竞赛: http://localhost:5173/ctf")
        print()
        print("示例竞赛信息:")
        print(f"  - 竞赛名称: NEEPU CTF 2024 春季赛")
        print(f"  - 邀请码: NEEPU2024")
        print(f"  - 分组邀请码:")
        print(f"    * 高级组: NEEPU2024-ADVANCED")
        print(f"    * 中级组: NEEPU2024-MIDDLE")
        print(f"    * 初级组: NEEPU2024-BEGINNER")
        print()
        
    except Exception as e:
        print()
        print("✗ 初始化失败！")
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
