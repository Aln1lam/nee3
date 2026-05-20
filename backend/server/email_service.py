"""
邮件服务模块 - 支持注册验证、密码重置、通知推送
使用 SMTP 发送邮件
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime, timedelta
import secrets
import hashlib
from threading import Thread
from flask import current_app, url_for


class EmailService:
    """邮件服务类"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化邮件配置"""
        self.app = app
        # 从配置或环境变量读取 SMTP 设置
        app.config.setdefault('MAIL_SERVER', os.environ.get('MAIL_SERVER', 'smtp.qq.com'))
        app.config.setdefault('MAIL_PORT', int(os.environ.get('MAIL_PORT', 465)))
        app.config.setdefault('MAIL_USE_SSL', os.environ.get('MAIL_USE_SSL', 'true').lower() == 'true')
        app.config.setdefault('MAIL_USERNAME', os.environ.get('MAIL_USERNAME', ''))
        app.config.setdefault('MAIL_PASSWORD', os.environ.get('MAIL_PASSWORD', ''))  # SMTP授权码
        app.config.setdefault('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_DEFAULT_SENDER', ''))
        app.config.setdefault('MAIL_SENDER_NAME', os.environ.get('MAIL_SENDER_NAME', 'NEEPU CTF'))
        app.config.setdefault('FRONTEND_URL', os.environ.get('FRONTEND_URL', 'http://localhost:5173'))
    
    def _send_email_sync(self, to_email, subject, html_content, text_content=None):
        """同步发送邮件"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = f"{current_app.config['MAIL_SENDER_NAME']} <{current_app.config['MAIL_DEFAULT_SENDER']}>"
            msg['To'] = to_email
            
            # 添加纯文本版本（备用）
            if text_content:
                msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            
            # 添加 HTML 版本
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 连接 SMTP 服务器
            if current_app.config['MAIL_USE_SSL']:
                server = smtplib.SMTP_SSL(
                    current_app.config['MAIL_SERVER'],
                    current_app.config['MAIL_PORT']
                )
            else:
                server = smtplib.SMTP(
                    current_app.config['MAIL_SERVER'],
                    current_app.config['MAIL_PORT']
                )
                server.starttls()
            
            server.login(
                current_app.config['MAIL_USERNAME'],
                current_app.config['MAIL_PASSWORD']
            )
            server.sendmail(
                current_app.config['MAIL_DEFAULT_SENDER'],
                [to_email],
                msg.as_string()
            )
            server.quit()
            return True
        except Exception as e:
            current_app.logger.error(f"发送邮件失败: {e}")
            return False
    
    def send_email_async(self, to_email, subject, html_content, text_content=None):
        """异步发送邮件（不阻塞请求）"""
        app = current_app._get_current_object()
        
        def send_async():
            with app.app_context():
                self._send_email_sync(to_email, subject, html_content, text_content)
        
        thread = Thread(target=send_async)
        thread.start()

    def send_email(self, to_email, subject, html_body, text_body=None, async_send=True):
        """兼容接口：同步或异步发送邮件。管理端调用使用 `send_email`。"""
        # 平台管理接口使用的参数名是 html_body/text_body
        if async_send:
            return self.send_email_async(to_email, subject, html_body, text_body)
        else:
            return self._send_email_sync(to_email, subject, html_body, text_body)
    
    def send_verification_email(self, to_email, token, nickname):
        """发送注册验证邮件"""
        frontend_url = current_app.config['FRONTEND_URL']
        verify_url = f"{frontend_url}/verify-email?token={token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 28px; font-weight: bold; color: #00c48c; }}
                .content {{ color: #333; line-height: 1.8; }}
                .btn {{ display: inline-block; background: #00c48c; color: white !important; padding: 14px 32px; border-radius: 8px; text-decoration: none; margin: 20px 0; font-weight: 600; }}
                .btn:hover {{ background: #00a86b; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #888; font-size: 12px; text-align: center; }}
                .code {{ background: #f8f9fa; padding: 15px; border-radius: 8px; font-family: monospace; word-break: break-all; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🏁 NEEPU CTF</div>
                </div>
                <div class="content">
                    <h2>欢迎加入 NEEPU CTF！</h2>
                    <p>你好 <strong>{nickname}</strong>，</p>
                    <p>感谢你注册 NEEPU CTF 平台！请点击下方按钮验证你的邮箱地址：</p>
                    <p style="text-align: center;">
                        <a href="{verify_url}" class="btn">验证邮箱</a>
                    </p>
                    <p>或者复制以下链接到浏览器：</p>
                    <div class="code">{verify_url}</div>
                    <p>此链接将在 <strong>24小时</strong> 后失效。</p>
                    <p>如果你没有注册 NEEPU CTF 账号，请忽略此邮件。</p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿直接回复</p>
                    <p>© {datetime.now().year} NEEPU CTF Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
欢迎加入 NEEPU CTF！

你好 {nickname}，

感谢你注册 NEEPU CTF 平台！请访问以下链接验证你的邮箱：
{verify_url}

此链接将在 24小时 后失效。

如果你没有注册 NEEPU CTF 账号，请忽略此邮件。

© {datetime.now().year} NEEPU CTF Team
        """
        
        self.send_email_async(to_email, '【NEEPU CTF】邮箱验证', html_content, text_content)
    
    def send_password_reset_email(self, to_email, token, nickname):
        """发送密码重置邮件"""
        frontend_url = current_app.config['FRONTEND_URL']
        reset_url = f"{frontend_url}/reset-password?token={token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 28px; font-weight: bold; color: #00c48c; }}
                .content {{ color: #333; line-height: 1.8; }}
                .btn {{ display: inline-block; background: #ff6b6b; color: white !important; padding: 14px 32px; border-radius: 8px; text-decoration: none; margin: 20px 0; font-weight: 600; }}
                .btn:hover {{ background: #ee5a5a; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #888; font-size: 12px; text-align: center; }}
                .code {{ background: #f8f9fa; padding: 15px; border-radius: 8px; font-family: monospace; word-break: break-all; margin: 15px 0; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffc107; padding: 12px; border-radius: 6px; color: #856404; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🏁 NEEPU CTF</div>
                </div>
                <div class="content">
                    <h2>重置你的密码</h2>
                    <p>你好 <strong>{nickname}</strong>，</p>
                    <p>我们收到了重置你账号密码的请求。点击下方按钮设置新密码：</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="btn">重置密码</a>
                    </p>
                    <p>或者复制以下链接到浏览器：</p>
                    <div class="code">{reset_url}</div>
                    <p>此链接将在 <strong>1小时</strong> 后失效。</p>
                    <div class="warning">
                        ⚠️ 如果你没有请求重置密码，请忽略此邮件，你的账号是安全的。
                    </div>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿直接回复</p>
                    <p>© {datetime.now().year} NEEPU CTF Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
重置你的密码

你好 {nickname}，

我们收到了重置你账号密码的请求。请访问以下链接设置新密码：
{reset_url}

此链接将在 1小时 后失效。

如果你没有请求重置密码，请忽略此邮件。

© {datetime.now().year} NEEPU CTF Team
        """
        
        self.send_email_async(to_email, '【NEEPU CTF】密码重置', html_content, text_content)
    
    def send_notification_email(self, to_email, nickname, title, content, action_url=None, action_text=None):
        """发送通知邮件（通用）"""
        frontend_url = current_app.config['FRONTEND_URL']
        
        action_html = ''
        if action_url and action_text:
            action_html = f'<p style="text-align: center;"><a href="{action_url}" class="btn">{action_text}</a></p>'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 28px; font-weight: bold; color: #00c48c; }}
                .content {{ color: #333; line-height: 1.8; }}
                .btn {{ display: inline-block; background: #4c6ef5; color: white !important; padding: 14px 32px; border-radius: 8px; text-decoration: none; margin: 20px 0; font-weight: 600; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #888; font-size: 12px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🏁 NEEPU CTF</div>
                </div>
                <div class="content">
                    <h2>{title}</h2>
                    <p>你好 <strong>{nickname}</strong>，</p>
                    <div>{content}</div>
                    {action_html}
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿直接回复</p>
                    <p><a href="{frontend_url}/settings">管理邮件通知设置</a></p>
                    <p>© {datetime.now().year} NEEPU CTF Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.send_email_async(to_email, f'【NEEPU CTF】{title}', html_content)
    
    def send_game_reminder(self, to_email, nickname, game_title, start_time):
        """发送比赛开始提醒"""
        frontend_url = current_app.config['FRONTEND_URL']
        
        self.send_notification_email(
            to_email,
            nickname,
            f'比赛即将开始：{game_title}',
            f'''
            <p>你报名的比赛 <strong>{game_title}</strong> 即将开始！</p>
            <p>⏰ 开始时间：<strong>{start_time.strftime('%Y年%m月%d日 %H:%M')}</strong></p>
            <p>请提前做好准备，祝你取得好成绩！</p>
            ''',
            f'{frontend_url}/games',
            '查看比赛详情'
        )
    
    def send_announcement_notification(self, to_email, nickname, announcement_title, announcement_content):
        """发送公告通知"""
        frontend_url = current_app.config['FRONTEND_URL']
        
        # 截取公告内容前200字
        preview = announcement_content[:200] + '...' if len(announcement_content) > 200 else announcement_content
        
        self.send_notification_email(
            to_email,
            nickname,
            f'新公告：{announcement_title}',
            f'''
            <p>平台发布了新公告：</p>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #00c48c;">
                <strong>{announcement_title}</strong>
                <p style="color: #666; margin-top: 10px;">{preview}</p>
            </div>
            ''',
            frontend_url,
            '查看完整公告'
        )


# 创建全局邮件服务实例
email_service = EmailService()


def generate_token():
    """生成安全的随机token"""
    return secrets.token_urlsafe(32)
