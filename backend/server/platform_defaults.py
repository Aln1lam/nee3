"""平台默认 UI 配置（代码 fallback，运营配置以 SystemConfig 为准）"""

from datetime import datetime


def build_default_info() -> dict:
    return {
        "name": "NEEPU CTF 终端",
        "subtitle": "能源电力 · 网络安全",
        "tagline_link": "/wiki",
        "brand_desc": "东北电力大学 · 网络安全竞赛 · 训练 · 实战",
        "nav": [
            {"label": "首页", "path": "/home", "code": "HOM"},
            {"label": "知识", "path": "/wiki", "code": "DOC"},
            {"label": "训练", "path": "/training", "code": "TRN"},
            {"label": "赛事", "path": "/games", "code": "CTF"},
            {"label": "公告", "path": "/bulletin", "code": "BUL"},
        ],
        "footer": {
            "org_name": "东北电力大学",
            "org_url": "https://www.neepu.edu.cn/",
            "copyright_years": f"2022-{datetime.now().year}",
            "icp": None,
            "icp_url": "https://beian.miit.gov.cn/",
        },
        "loading_tips": [
            "正在巡检 SCADA 节点...",
            "正在同步电网拓扑...",
            "正在解析 Modbus 报文...",
            "正在校验继电保护定值...",
            "正在枚举 DCS 端口...",
            "正在分析继电保护日志...",
            "正在检测 OT/IT 边界流量...",
            "正在加载 NEEPU 练习场...",
        ],
        "training_categories": [
            {
                "group": "训练",
                "items": [
                    {"slug": "ics", "title": "电力工控安全", "icon": "⚡"},
                    {"slug": "web", "title": "Web 安全审计", "icon": "🌐"},
                    {"slug": "crypto", "title": "密码技术能力提升", "icon": "🔐"},
                    {"slug": "misc", "title": "安全杂项", "icon": "🎲"},
                    {"slug": "pwn", "title": "二进制漏洞审计", "icon": "💣"},
                    {"slug": "reverse", "title": "逆向工程", "icon": "↩️"},
                ],
            },
            {
                "group": "归档赛事",
                "items": [],
            },
        ],
        "challenge_categories": [
            "电力工控安全",
            "安全杂项",
            "从此开始",
            "二进制漏洞审计",
            "密码学",
            "逆向工程",
            "Web安全与渗透测试",
        ],
        "highlight_banner": None,
        "maintenance": False,
        "zen_game": None,
        "oauth_providers": [],
        "training_welcome": (
            "欢迎来到 NEEPU 练习场！\n\n"
            "- 无时间限制、无限重试、不计分\n"
            "- 提示自动解锁、题解已开放\n"
            "- 禁止直接抄题，请独立思考\n"
            "- 🔨 锤子反馈在训练场不可用\n\n"
            "本平台由东北电力大学维护，题目涵盖 Web 渗透、工控协议、"
            "密码学与二进制漏洞等方向，部分场景模拟电厂运维、"
            "调度系统等电力业务环境，欢迎结合专业背景进行安全演练。"
        ),
    }


DEFAULT_INFO = build_default_info()
