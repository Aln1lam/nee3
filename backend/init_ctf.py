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
    CtfChallengeHint, MainAnnouncement,
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
        existing_game = CtfGame.query.filter_by(title="NEEPU CTF 2025 春季赛").first()
        if existing_game:
            print("  ✓ 示例竞赛已存在，跳过")
            return existing_game.id
        
        # 创建竞赛 — 进行中状态便于直接体验
        now = datetime.utcnow()
        game = CtfGame(
            title="NEEPU CTF 2025 春季赛",
            description=(
                "东北电力大学 **NEEPU CTF 2025 春季赛** 正式开启！\n\n"
                "涵盖 Web 安全、密码学、二进制、逆向、杂项等方向。\n"
                "以队伍形式参赛，实时积分板追踪排名。\n\n"
                "> 新手请先完成练习场「从此开始」分类题目。"
            ),
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=14),
            is_public=True,
            game_type="official",
            status="ongoing",
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
            'title': '从此开始',
            'category': '从此开始',
            'description': '欢迎来到 NEEPU CTF！这是一道简单的签到题。\n\n提交 flag{welcome_to_neepu_ctf} 即可获得分数。',
            'points': 10,
            'flag': 'flag{welcome_to_neepu_ctf}',
            'hint': '注意题目描述中的关键词'
        },
        {
            'title': '简单的Web',
            'category': 'Web安全与渗透测试',
            'description': '访问指定的网址，找到隐藏的 flag。\n\n提示: 检查 HTML 注释和 cookie。',
            'points': 50,
            'flag': 'flag{html_source_code_is_important}',
            'hint': '右键查看源代码'
        },
        {
            'title': 'Base64解码',
            'category': '密码学',
            'description': '解码以下 Base64 字符串：\n\nZmxhZ3tZb3VyX2ZpcnN0X2VuY3J5cHRpb259\n\n然后提交解码结果作为 flag。',
            'points': 30,
            'flag': 'flag{Your_first_encryption}',
            'hint': 'Base64 是一种编码方式，不是加密方式'
        },
        {
            'title': '安全杂项入门',
            'category': '安全杂项',
            'description': '找到隐藏的 flag。\n\n所有线索都在这道题的题目、描述和提示中。',
            'points': 40,
            'flag': 'flag{read_carefully}',
            'hint': '仔细阅读每一个字符'
        },
        {
            'title': '字符串搜索',
            'category': '安全杂项',
            'description': '在给定的文本中找到 flag 格式（以 flag{ 开头，以 } 结尾）。\n\n真正的 flag 在附件中的一个隐藏的文件里。',
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
                payload = {**challenge_data}
                points = payload.pop('points', 100)
                hint_text = payload.pop('hint', None)
                challenge = CtfChallenge(
                    game_id=game_id,
                    original_points=points,
                    **payload,
                    is_enabled=True,
                    submission_limit=0  # 无限制
                )
                db.session.add(challenge)
                db.session.flush()
                if hint_text:
                    db.session.add(CtfChallengeHint(
                        challenge_id=challenge.id,
                        hint_text=hint_text,
                        penalty_points=0,
                    ))
                print(f"  ✓ 创建题目: {challenge_data['title']} ({points} pts)")
        
        db.session.commit()

def init_system_config():
    """初始化系统配置"""
    print("正在初始化系统配置...")
    
    from backend.server.db_models import SystemConfig
    
    with app.app_context():
        configs = {
            'site_name': 'NEEPU CTF 终端',
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

def create_training_playground():
    """创建练习场示例数据"""
    print("正在创建练习场...")

    with app.app_context():
        existing = CtfGame.query.filter_by(title="NEEPU 练习场").first()
        if existing:
            print("  ✓ 练习场已存在，跳过")
            return existing.id

        now = datetime.utcnow()
        game = CtfGame(
            title="NEEPU 练习场",
            start_time=now - timedelta(days=365),
            end_time=now + timedelta(days=3650),
            is_public=True,
            status="ongoing",
            game_type="training",
        )
        db.session.add(game)
        db.session.flush()
        print(f"  ✓ 创建练习场: {game.title}")

        training_challenges = [
            {
                "title": "从此开始",
                "category": "从此开始",
                "description": (
                    "欢迎来到 NEEPU 练习场！\n\n"
                    "这是一道入门题。提交 flag{welcome_to_neepu_training} 即可完成。\n\n"
                    "- 无时间限制\n"
                    "- 无限重试\n"
                    "- 不计入正式赛事积分"
                ),
                "points": 10,
                "flag": "flag{welcome_to_neepu_training}",
            },
            {
                "title": "SQL 注入入门",
                "category": "Web安全与渗透测试",
                "description": "学习基础的 SQL 注入原理。\n\n提示：尝试 `' OR 1=1 --`",
                "points": 50,
                "flag": "flag{sql_injection_101}",
            },
            {
                "title": "Base64 解码",
                "category": "密码学",
                "description": "解码：ZmxhZ3t5b3VyX2ZpcnN0X2NyeXB0b30=",
                "points": 30,
                "flag": "flag{your_first_crypto}",
            },
            {
                "title": "栈溢出初探",
                "category": "二进制漏洞审计",
                "description": "了解栈溢出的基本概念与利用思路。",
                "points": 80,
                "flag": "flag{stack_overflow_intro}",
                "hints": [
                    "栈溢出发生在函数返回地址被覆盖时",
                    "尝试找到 buffer 大小与返回地址的偏移",
                ],
            },
            {
                "title": "逆向 Hello",
                "category": "逆向工程",
                "description": "分析给定的二进制程序，找到隐藏的 flag。\n\n提示：strings 命令是你的好朋友。",
                "points": 60,
                "flag": "flag{reverse_hello_world}",
                "hints": ["使用 strings 或 IDA 查看字符串表"],
            },
            {
                "title": "安全杂项入门",
                "category": "安全杂项",
                "description": "在以下文本中找到 flag 格式（flag{...}）：\n\nNEEPU{not_flag} flag{misc_is_fun} CTF{also_not}",
                "points": 20,
                "flag": "flag{misc_is_fun}",
            },
        ]

        hint_map = {}
        for ch in training_challenges:
            hints = ch.pop("hints", [])
            challenge = CtfChallenge(
                game_id=game.id,
                title=ch["title"],
                category=ch["category"],
                description=ch["description"],
                original_points=ch["points"],
                flag=ch["flag"],
                is_enabled=True,
                submission_limit=0,
            )
            db.session.add(challenge)
            db.session.flush()
            hint_map[challenge.id] = hints
            print(f"  ✓ 创建练习题目: {ch['title']}")

        for challenge_id, hints in hint_map.items():
            for idx, text in enumerate(hints):
                db.session.add(CtfChallengeHint(
                    challenge_id=challenge_id,
                    hint_text=text,
                    penalty_points=0 if idx == 0 else 5 * idx,
                ))

        db.session.commit()
        return game.id


def init_sample_bulletins():
    """初始化示例公告"""
    print("正在初始化公告...")

    samples = [
        {
            "title": "NEEPU CTF 终端平台上线",
            "content": (
                "欢迎使用 **NEEPU CTF 终端**！\n\n"
                "- 训练场永久开放，无时间限制\n"
                "- 在线环境请通过顶栏「环境连接器」管理\n"
                "- TCP 类题目请使用 netcat 连接\n\n"
                "祝各位黑客学习愉快！"
            ),
        },
        {
            "title": "练习场维护通知",
            "content": (
                "NEEPU CTF 终端预计将在低峰时段进行例行维护。\n\n"
                "维护期间容器实例可能短暂不可用，请提前保存进度。"
            ),
        },
    ]

    with app.app_context():
        for item in samples:
            existing = MainAnnouncement.query.filter_by(title=item["title"]).first()
            if existing:
                continue
            row = MainAnnouncement(
                title=item["title"],
                content=item["content"],
                is_active=True,
                published_at=datetime.utcnow(),
            )
            db.session.add(row)
            print(f"  ✓ 创建公告: {item['title']}")
        db.session.commit()


def init_wiki_articles():
    """初始化知识库 Wiki 文章"""
    print("正在初始化 Wiki 文章...")

    from backend.server.db_models import Article

    articles = [
        {
            "title": "如何使用这个平台？",
            "slug": "how-to-use",
            "summary": "NEEPU CTF 终端快速上手指南",
            "content": (
                "# 如何使用 NEEPU CTF 终端\n\n"
                "欢迎使用 **NEEPU CTF 终端**！本平台提供训练、赛事、知识库等完整 CTF 体验。\n\n"
                "## 快速开始\n\n"
                "1. 注册账号并验证邮箱\n"
                "2. 进入 **训练** 选择练习场做题\n"
                "3. 参加 **赛事** 与队伍一起夺旗\n"
                "4. 查阅 **知识库** 学习技巧\n\n"
                "## 在线环境\n\n"
                "带容器类型的题目需点击「启动」按钮，并通过顶栏 **环境连接器** 管理实例。\n\n"
                "## Flag 提交\n\n"
                "在题目页底部输入 flag，支持 `Ctrl+Shift+V` 粘贴后回车提交。"
            ),
        },
        {
            "title": "从零开始的CTF之路",
            "slug": "ctf-roadmap",
            "summary": "CTF 学习路线与资源推荐",
            "content": (
                "# 从零开始的 CTF 之路\n\n"
                "## 入门阶段\n\n"
                "- 了解 Web、Crypto、Misc、Reverse、Pwn 五大方向\n"
                "- 完成练习场「从此开始」分类题目\n\n"
                "## 进阶阶段\n\n"
                "- 参加校内赛与公开赛事\n"
                "- 阅读 Writeup 并复现思路\n\n"
                "## 推荐资源\n\n"
                "- 本平台训练场永久开放\n"
                "- [CTF Wiki](https://ctf-wiki.org/)"
            ),
        },
        {
            "title": "连接器使用教程",
            "slug": "connector",
            "summary": "动态容器公网地址连接说明",
            "content": (
                "# 容器环境连接说明\n\n"
                "部分题目提供 **在线容器环境**，启动后直接连接 **公网 IP:端口**。\n\n"
                "## 步骤\n\n"
                "1. 在题目页点击 **启动** 创建实例\n"
                "2. 复制连接地址（Web 题加 http:// 前缀）\n"
                "3. TCP 题使用 `nc 公网IP 端口` 连接\n"
                "4. 顶栏 **容器实例** 可查看/销毁运行中的环境\n\n"
                "> 管理员需在服务器配置 `NEPU_CONTAINER_PUBLIC_HOST` 为公网 IP。"
            ),
        },
        {
            "title": "netcat 访问教程",
            "slug": "netcat",
            "summary": "TCP 类题目的 netcat 连接方法",
            "content": (
                "# netcat 访问教程\n\n"
                "Pwn / 部分 Misc 题目通过 **TCP 服务** 提供交互 shell。\n\n"
                "## Linux / macOS\n\n"
                "```bash\n"
                "nc host port\n"
                "```\n\n"
                "## Windows\n\n"
                "可使用 WSL、ncat 或 pwntools 连接：\n\n"
                "```bash\n"
                "ncat host port\n"
                "```\n\n"
                "连接成功后即可与远程程序交互，按题目要求获取 flag。"
            ),
        },
    ]

    with app.app_context():
        for item in articles:
            tag = f"wiki:{item['slug']}"
            existing = Article.query.filter(Article.tags.contains(tag)).first()
            if existing:
                continue
            row = Article(
                title=item["title"],
                summary=item["summary"],
                content=item["content"],
                tags=f"wiki,{tag},知识库",
                status="published",
                published_at=datetime.utcnow(),
            )
            db.session.add(row)
            print(f"  ✓ 创建 Wiki: {item['title']}")
        db.session.commit()


def create_extra_games():
    """创建更多示例赛事供赛事列表展示"""
    print("正在创建额外赛事...")

    extras = [
        {
            "title": "Mini L-CTF 2026",
            "description": "轻量级校内夺旗赛，适合新手入门。",
            "offset_start": 14,
            "offset_end": 21,
            "status": "not_started",
        },
        {
            "title": "NewYear CTF 2026",
            "description": "新年特别赛，涵盖全方向题目。",
            "offset_start": 30,
            "offset_end": 37,
            "status": "not_started",
        },
        {
            "title": "MoeCTF 2025",
            "description": "年度大型网络安全竞赛。",
            "offset_start": -14,
            "offset_end": -7,
            "status": "archived",
        },
        {
            "title": "NewStar CTF 2025（托管）",
            "description": "托管赛事 — 面向新生的入门 CTF。",
            "offset_start": -30,
            "offset_end": -20,
            "status": "archived",
            "is_hosted": True,
        },
        {
            "title": "校内新生赛 2025",
            "description": "面向新生的校内网络安全竞赛。",
            "offset_start": -3,
            "offset_end": 4,
            "status": "ongoing",
        },
    ]

    with app.app_context():
        now = datetime.utcnow()
        for item in extras:
            existing = CtfGame.query.filter_by(title=item["title"]).first()
            if existing:
                continue
            game = CtfGame(
                title=item["title"],
                description=item.get("description", ""),
                start_time=now + timedelta(days=item["offset_start"]),
                end_time=now + timedelta(days=item["offset_end"]),
                is_public=True,
                game_type="official",
                status=item.get("status", "not_started"),
            )
            db.session.add(game)
            print(f"  ✓ 创建赛事: {item['title']}")
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

        # 步骤6: 创建练习场
        create_training_playground()
        print()

        # 步骤7: 初始化公告
        init_sample_bulletins()
        print()

        # 步骤8: 初始化 Wiki
        init_wiki_articles()
        print()

        # 步骤9: 额外赛事
        create_extra_games()
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
        print(f"  - 竞赛名称: NEEPU CTF 2025 春季赛")
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
