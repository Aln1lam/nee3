#!/usr/bin/env python3
"""
更新题目的动态flag模板
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app
from backend.server.extensions import db
from backend.server.db_models import CtfChallenge

app = create_app()

def update_challenge_flag_template(challenge_id, flag_template):
    """更新指定题目的flag模板"""
    with app.app_context():
        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            print(f"❌ 未找到题目 #{challenge_id}")
            return False
        
        print(f"\n更新题目 #{challenge_id}: {challenge.title}")
        print(f"  旧配置:")
        print(f"    静态Flag: {challenge.flag}")
        print(f"    Flag模板: {challenge.flag_template or '未设置'}")
        
        challenge.flag_template = flag_template
        db.session.commit()
        
        print(f"  新配置:")
        print(f"    Flag模板: {challenge.flag_template}")
        print(f"  ✅ 更新成功！")
        return True

if __name__ == "__main__":
    print("=== 更新动态Flag模板 ===\n")
    
    # 方式1：命令行参数
    if len(sys.argv) >= 3:
        challenge_id = int(sys.argv[1])
        flag_template = sys.argv[2]
        update_challenge_flag_template(challenge_id, flag_template)
    else:
        # 方式2：批量更新所有容器题目
        with app.app_context():
            challenges = CtfChallenge.query.filter(
                CtfChallenge.docker_image.isnot(None)
            ).all()
            
            print("找到以下容器题目：")
            for ch in challenges:
                print(f"  #{ch.id}: {ch.title} - 镜像: {ch.docker_image}")
            
            print("\n请选择更新方式：")
            print("1. 为所有题目设置相同的模板")
            print("2. 逐个设置每个题目的模板")
            print("3. 退出")
            
            choice = input("\n选择 (1/2/3): ").strip()
            
            if choice == "1":
                print("\n常用模板示例：")
                print("  flag{[GUID]} - 使用GUID（每次不同）")
                print("  flag{hello_[TEAM_HASH]} - 使用团队hash（每队不同）")
                print("  flag{[TEAM_HASH]_[GUID]} - 组合使用")
                
                flag_template = input("\n输入模板: ").strip()
                
                for ch in challenges:
                    ch.flag_template = flag_template
                
                db.session.commit()
                print(f"\n✅ 已为 {len(challenges)} 个题目设置模板: {flag_template}")
                
            elif choice == "2":
                for ch in challenges:
                    print(f"\n题目 #{ch.id}: {ch.title}")
                    print(f"  当前: {ch.flag_template or '未设置'}")
                    
                    flag_template = input("  新模板 (留空跳过): ").strip()
                    if flag_template:
                        ch.flag_template = flag_template
                        print(f"  ✓ 已设置")
                
                db.session.commit()
                print("\n✅ 更新完成")
            
            else:
                print("退出")
