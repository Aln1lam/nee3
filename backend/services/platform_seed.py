"""
平台默认内容种子 — Wiki 教程、欢迎公告等
"""

from datetime import datetime


WIKI_ARTICLES = [
    {
        "tag": "wiki:how-to-use",
        "title": "如何使用这个平台？",
        "summary": "NEEPU CTF 终端快速上手指南",
        "content": """# 如何使用 NEEPU CTF 终端

欢迎使用 **NEEPU CTF 终端** — 东北电力大学网络安全竞赛与训练平台。

## 快速开始

1. **注册账号**：访问 `/account/register` 完成注册并验证邮箱
2. **进入训练场**：导航栏「训练」→ 选择练习场开始刷题
3. **参加赛事**：导航栏「赛事」→ 报名并加入队伍
4. **提交 Flag**：在题目页「终端」Tab 底部输入 flag 并回车

## 核心功能

| 模块 | 说明 |
|------|------|
| 知识 | Wiki 教程与 CTF 学习路线 |
| 训练 | 永久开放的练习场，不计分 |
| 赛事 | 正式 CTF 竞赛 |
| 公告 | 平台维护与赛事通知 |

## 在线环境

部分题目需要启动 Docker 容器。点击题目上方「启动」按钮，然后使用顶栏 **环境连接器** 查看连接地址。

TCP 类题目请使用 `netcat` 连接，详见 [netcat 访问教程](/wiki/netcat)。

## 需要帮助？

- 查看 [从零开始的 CTF 之路](/wiki/ctf-roadmap)
- 联系平台管理员或在赛事中使用 🔨 锤子反馈
""",
    },
    {
        "tag": "wiki:ctf-roadmap",
        "title": "从零开始的 CTF 之路",
        "summary": "CTF 学习路线与资源推荐",
        "content": """# 从零开始的 CTF 之路

## 入门阶段

- **Web 安全**：HTTP 协议、SQL 注入、XSS、文件上传
- **密码学**：编码（Base64/Hex）、古典密码、RSA 基础
- **杂项**：隐写、流量分析、基础取证

## 进阶阶段

- **Pwn**：栈溢出、ROP、堆利用
- **Reverse**：IDA/Ghidra 静态分析、动态调试
- **Web 进阶**：SSRF、SSTI、反序列化

## 推荐练习

1. 先在 **训练场** 完成「从此开始」系列题目
2. 参加校内赛事积累经验
3. 组队参加外部 CTF（NewStar、MoeCTF 等）

## 工具清单

```bash
# 常用工具
burpsuite    # Web 抓包
pwntools     # Pwn 利用框架
ghidra       # 逆向分析
wireshark    # 流量分析
nc           # 网络连接
```

坚持练习，生命不息，探索不止。
""",
    },
    {
        "tag": "wiki:connector",
        "title": "连接器使用教程",
        "summary": "动态容器公网地址连接说明",
        "content": """# 容器环境连接说明

部分题目提供 **在线 Docker 环境**，启动后可直接使用 **公网 IP + 端口** 连接，无需额外连接器。

## 启动步骤

1. 进入题目页，切换到「终端」Tab
2. 点击 **启动** 按钮创建容器实例
3. 复制显示的连接地址（如 `1.2.3.4:31337` 或 `http://1.2.3.4:8080`）
4. 也可点击顶栏 **容器实例** 查看所有运行中的环境

## 连接方式

| 题型 | 连接方法 |
|------|----------|
| Web | 浏览器打开 `http://公网IP:端口` |
| Pwn / TCP | `nc 公网IP 端口` |

## 实例管理

- **运行中**：实例正常，可以连接
- **延期**：部分赛事支持延长实例时间
- **销毁**：手动停止并释放容器资源

## 注意事项

- 比赛部署时管理员需配置 `NEPU_CONTAINER_PUBLIC_HOST` 为服务器公网 IP
- 确保防火墙/安全组已放行动态映射端口
- 比赛结束后所有实例将被销毁
""",
    },
    {
        "tag": "wiki:netcat",
        "title": "netcat 访问教程",
        "summary": "使用 nc 连接 TCP 类 CTF 题目",
        "content": """# netcat 访问教程

TCP 类题目（标注 **tcp** 标签）需要通过命令行工具连接，而非浏览器。

## 基本用法

```bash
# 连接题目服务
nc <host> <port>

# 示例
nc localhost 31337
```

## Windows 用户

PowerShell 可使用：

```powershell
# 使用 ncat（Nmap 附带）
ncat localhost 31337

# 或使用 WSL
wsl nc localhost 31337
```

## 常见场景

### 交互式 Shell

```bash
nc host port
# 连接后直接输入命令或 payload
```

### 发送数据

```bash
echo "payload" | nc host port
```

### 接收 Banner

```bash
nc -v host port
```

## 提示

- 连接地址可在题目页「终端」Tab 或环境连接器中复制
- 部分题目需要先启动 Docker 实例才能连接
- 使用 `Ctrl+C` 断开连接
""",
    },
    {
        "tag": "wiki:ics-security",
        "title": "工控安全入门",
        "summary": "SCADA/DCS/PLC 与电力工控 CTF 入门",
        "content": """# 工控安全入门

东北电力大学以 **能源电力** 为办学特色，工控安全是 NEEPU CTF 的重点方向之一。

## 什么是工控系统？

工控系统（ICS）用于监控和控制工业流程，在电力行业中常见形态包括：

| 组件 | 说明 |
|------|------|
| SCADA | 数据采集与监视控制系统 |
| DCS | 分布式控制系统 |
| PLC | 可编程逻辑控制器 |
| RTU | 远程终端单元 |

## CTF 常见考点

- **协议分析**：Modbus TCP/RTU、DNP3、IEC 104 等报文解析
- **固件逆向**：PLC 程序、嵌入式设备固件
- **逻辑漏洞**：越权写线圈、错误的功能码处理
- **网络隔离绕过**：IT/OT 边界、VPN 与跳板

## 实验环境建议

```bash
# 使用 scapy 构造 Modbus 报文
pip install scapy pymodbus

# 流量分析
wireshark   # 过滤 modbus / dnp3
```

## 学习路径

1. 了解 OT 与 IT 网络分区模型（Purdue 模型）
2. 在训练场完成「电力工控安全」分类题目
3. 阅读 [电力信息系统安全](/wiki) 延伸章节

> 提示：真实工控环境操作需授权，本平台题目均在隔离容器中进行。
""",
    },
    {
        "tag": "wiki:power-grid-sec",
        "title": "电力信息系统安全",
        "summary": "电网业务系统与信息安全防护要点",
        "content": """# 电力信息系统安全

## 电力行业背景

东北电力大学位于 **吉林省吉林市**，长期服务于电力、能源行业人才培养。电力信息系统安全涉及发电、输电、变电、配电、用电全链条的信息化与自动化。

## 典型系统

- **EMS** — 能量管理系统
- **WAMS** — 广域测量系统
- **营销/客服系统** — 面向用户的业务平台
- **调度自动化** — 实时性要求极高的控制平面

## 安全威胁模型

| 威胁 | 示例 |
|------|------|
| 外部渗透 | Web 漏洞、弱口令、供应链攻击 |
| 内部误操作 | 误下发遥控指令、配置错误 |
| 协议滥用 | 伪造遥测/遥信、重放攻击 |
| 可用性 | DDoS、勒索软件影响调度可用性 |

## CTF 与实战映射

本平台部分 Web/Pwn 题目场景设定为 **电厂运维门户**、**调度日志审计** 等，帮助你在安全竞赛中理解电力业务语境。

## 合规与标准（了解即可）

- 《电力监控系统安全防护规定》
- 等级保护 2.0 在电力行业的应用
- 工控安全最佳实践（网络分区、堡垒机、审计）

## 延伸阅读

- [工控安全入门](/wiki/ics-security)
- [连接器使用教程](/wiki/connector) — 在线 Docker 环境
- [从零开始的 CTF 之路](/wiki/ctf-roadmap)

生命不息，探索不止 — 守护能源基础设施，从理解开始。
""",
    },
]

WIKI_INTERNAL_LINK_FIXES = (
    ("[netcat 访问教程](/wiki)", "[netcat 访问教程](/wiki/netcat)"),
    ("[从零开始的 CTF 之路](/wiki)", "[从零开始的 CTF 之路](/wiki/ctf-roadmap)"),
    ("[工控安全入门](/wiki)", "[工控安全入门](/wiki/ics-security)"),
    ("[连接器使用教程](/wiki)", "[连接器使用教程](/wiki/connector)"),
    ("[电力信息系统安全](/wiki)", "[电力信息系统安全](/wiki/power-grid-sec)"),
)


def repair_wiki_internal_links():
    """修正已入库 Wiki 正文中指向 /wiki 的占位内链（幂等）。"""
    from backend.server.extensions import db
    from backend.server.db_models import Article

    changed = 0
    for article in Article.query.filter(Article.tags.contains("wiki:")).all():
        content = article.content or ""
        new_content = content
        for old, new in WIKI_INTERNAL_LINK_FIXES:
            new_content = new_content.replace(old, new)
        if new_content != content:
            article.content = new_content
            changed += 1
    if changed:
        db.session.commit()
    return changed


WELCOME_BULLETIN = {
    "title": "欢迎使用 NEEPU CTF 终端",
    "content": """NEEPU CTF 终端已上线运行。

**平台功能：**
- 🏋️ 永久开放训练场，随时刷题
- 🏁 正式 CTF 赛事与积分排行
- 📚 知识库 Wiki 教程
- ⚡ Docker 在线环境支持

如有问题，请查阅 [知识库](/wiki) 或联系管理员。

祝你在网络安全之路上越走越远！
""",
}


def seed_platform_content(app):
    """应用启动时写入默认 Wiki 与公告（幂等）"""
    with app.app_context():
        try:
            from backend.server.extensions import db
            from backend.server.db_models import Article, MainAnnouncement

            for item in WIKI_ARTICLES:
                tag = item["tag"]
                exists = Article.query.filter(
                    Article.tags.contains(tag),
                    Article.status == "published",
                ).first()
                if exists:
                    continue
                article = Article(
                    title=item["title"],
                    content=item["content"],
                    summary=item.get("summary", ""),
                    tags=tag,
                    status="published",
                    published_at=datetime.utcnow(),
                )
                db.session.add(article)
                app.logger.info(f"Seeded wiki article: {item['title']}")

            welcome = MainAnnouncement.query.filter_by(title=WELCOME_BULLETIN["title"]).first()
            if not welcome:
                bulletin = MainAnnouncement(
                    title=WELCOME_BULLETIN["title"],
                    content=WELCOME_BULLETIN["content"],
                    is_active=True,
                    published_at=datetime.utcnow(),
                )
                db.session.add(bulletin)
                app.logger.info("Seeded welcome bulletin")

            repair_wiki_internal_links()
            db.session.commit()
        except Exception as e:
            app.logger.debug(f"Platform seed skipped: {e}")
