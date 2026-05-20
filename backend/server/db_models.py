from datetime import datetime
from backend.server.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import hmac
import binascii
import uuid


def _verify_scrypt_password(stored_hash, password):
    try:
        method, salt, checksum = stored_hash.split("$", 2)
    except ValueError:
        return False

    if not method.startswith("scrypt:"):
        return False

    try:
        _, n_str, r_str, p_str = method.split(":", 3)
        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt.encode("utf-8"),
            n=int(n_str),
            r=int(r_str),
            p=int(p_str),
            dklen=len(binascii.unhexlify(checksum)),
        )
    except (ValueError, TypeError, binascii.Error, OSError):
        return False

    return hmac.compare_digest(derived, binascii.unhexlify(checksum))


def _check_password_hash_compat(stored_hash, password):
    if stored_hash and stored_hash.startswith("scrypt:"):
        return _verify_scrypt_password(stored_hash, password)
    return check_password_hash(stored_hash, password)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=True)
    full_name = db.Column(db.String(128), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(64), nullable=False)
    avatar = db.Column(db.String(255), nullable=True)
    avatar_resource_id = db.Column(db.Integer, db.ForeignKey("file_resource.id"), nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    email_verified = db.Column(db.Boolean, default=False)
    email_notifications = db.Column(db.Boolean, default=True)
    school = db.Column(db.String(128), nullable=True)
    identity = db.Column(db.String(32), nullable=True)
    phone = db.Column(db.String(20), nullable=True)

    # 关系
    avatar_resource = db.relationship("FileResource", foreign_keys=[avatar_resource_id], lazy=True)

    def set_password(self, pwd):
        self.password_hash = generate_password_hash(pwd, method="pbkdf2:sha256")

    def verify_password(self, pwd):
        return _check_password_hash_compat(self.password_hash, pwd)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'avatar_resource_id': self.avatar_resource_id,
            'team_id': self.team_id,
            'is_admin': bool(self.is_admin),
            'email_verified': bool(self.email_verified),
            'email_notifications': bool(self.email_notifications),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    invite_code = db.Column(db.String(32), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship("User", backref="team", lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'invite_code': self.invite_code,
            'members_count': len(self.users),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class School(db.Model):
    """学校/公司表 - 支持按学校分组"""
    __tablename__ = 'school'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True, nullable=False)
    code = db.Column(db.String(64), nullable=True)  # 学校代码，用于邀请码
    region = db.Column(db.String(64), nullable=True)  # 地区
    category = db.Column(db.String(32), nullable=True)  # university, company, other
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'region': self.region,
            'category': self.category,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class CtfSeason(db.Model):
    """CTF赛季表 - 支持多年运营和配置复用"""
    __tablename__ = 'ctf_season'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    season = db.Column(db.String(32), nullable=False)  # spring, summer, autumn, winter
    description = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    games = db.relationship("CtfGame", backref="season", lazy=True)
    divisions = db.relationship("CtfDivision", backref="season", lazy=True, foreign_keys="CtfDivision.season_id")
    challenges = db.relationship("CtfChallenge", backref="season", lazy=True, foreign_keys="CtfChallenge.season_id")
    categories = db.relationship("CtfChallengeCategory", backref="season", lazy=True, foreign_keys="CtfChallengeCategory.season_id")
    
    def to_dict(self):
        return {
            'id': self.id,
            'year': self.year,
            'season': self.season,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class CtfGame(db.Model):
    __tablename__ = 'ctf_game'
    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey("ctf_season.id"), nullable=True)  # 新增：关联赛季
    title = db.Column(db.String(128), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(32), default="not_started")  # not_started, ongoing, ended, archived
    game_type = db.Column(db.String(32), default="official")  # official, practice, training
    archived_at = db.Column(db.DateTime, nullable=True)  # 归档时间
    team_hash_salt = db.Column(db.String(128), nullable=True)  # 动态flag生成时的salt
    participations = db.relationship("CtfParticipation", backref="game", lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_public': self.is_public,
            'status': self.status,
            'game_type': self.game_type,
            'season_id': self.season_id,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None,
        }




class Email(db.Model):
    __tablename__ = 'email'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    token = db.Column(db.String(128), unique=True, nullable=False)
    token_type = db.Column(db.String(32), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

    user = db.relationship("User", backref=db.backref("email_tokens", lazy=True))

    def is_valid(self):
        return not self.used and datetime.utcnow() < self.expires_at


class RegistratingUser(db.Model):
    __tablename__ = 'registrating_user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(64), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    def is_valid(self):
        return datetime.utcnow() < self.expires_at

    def set_password(self, pwd):
        self.password_hash = generate_password_hash(pwd, method="pbkdf2:sha256")


class ApiToken(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(128), nullable=False)
    token = db.Column(db.String(256), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    revoked = db.Column(db.Boolean, default=False)


class CtfParticipation(db.Model):
    """团队参赛记录 - Team-based participation"""
    __tablename__ = 'ctf_participation'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("ctf_game.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    division_id = db.Column(db.Integer, db.ForeignKey("ctf_division.id"), nullable=True)  # 新增：赛道
    # participation is at team level; individual users are represented in `CtfParticipatingUser`
    status = db.Column(db.String(32), default="pending")  # pending, confirmed, rejected
    token = db.Column(db.String(128), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team = db.relationship("Team", backref="ctf_participations", lazy=True)
    members = db.relationship("CtfParticipatingUser", backref="participation", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'game_id': self.game_id,
            'team_id': self.team_id,
            'division_id': self.division_id,
            'status': self.status,
            'token': self.token,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class CtfParticipatingUser(db.Model):
    """用户参赛记录 - User-Game-Team 关系"""
    __tablename__ = 'ctf_participating_user'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey("ctf_game.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    participation_id = db.Column(db.Integer, db.ForeignKey("ctf_participation.id"), nullable=False)
    division_id = db.Column(db.Integer, db.ForeignKey("ctf_division.id"), nullable=True)  # 新增：赛道（可选）
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", backref="ctf_user_participations", lazy=True)
    game = db.relationship("CtfGame", lazy=True)
    team = db.relationship("Team", lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'game_id': self.game_id,
            'team_id': self.team_id,
            'participation_id': self.participation_id,
            'division_id': self.division_id,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
        }


User.ctf_participations = db.relationship("CtfParticipation", secondary="ctf_participating_user", lazy=True, viewonly=True)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1024), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def completed(self):
        return bool(self.done)

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'user_id': self.user_id,
            'done': bool(self.done),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class FileResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(512), nullable=False)
    path = db.Column(db.String(1024), nullable=False)
    url = db.Column(db.String(1024), nullable=True)
    mime_type = db.Column(db.String(128), nullable=True)
    size = db.Column(db.Integer, nullable=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    # 新增字段：记录文件的用途和关联实体
    purpose = db.Column(db.String(64), nullable=True)  # 'avatar', 'article', 'carousel', 'attachment', etc.
    entity_type = db.Column(db.String(64), nullable=True)  # 'user', 'article', 'carousel_slide', etc.
    entity_id = db.Column(db.Integer, nullable=True)  # 关联实体的ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'url': self.url,
            'mime_type': self.mime_type,
            'size': self.size,
            'uploader_id': self.uploader_id,
            'purpose': self.purpose,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text)
    summary = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(512), nullable=True, default='')
    published_at = db.Column(db.DateTime, nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("file_resource.id"), nullable=True)
    status = db.Column(db.String(32), default="draft")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MainAnnouncement(db.Model):
    __tablename__ = 'main_announcement'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text)
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    creator = db.relationship("User", backref="announcements", lazy=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'is_active': self.is_active,
            'creator_id': self.creator_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
        }


class CarouselSlide(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(1024), nullable=False)
    link_url = db.Column(db.String(1024), nullable=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("file_resource.id"), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image_url': self.image_url,
            'link_url': self.link_url,
            'resource_id': self.resource_id,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
        }


class ArticleAttachment(db.Model):
    """文章附件追踪表 - 记录文章关联的所有文件"""
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("article.id"), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey("file_resource.id"), nullable=False)
    attachment_type = db.Column(db.String(32), default='image')  # 'image', 'document', 'archive'
    sort_order = db.Column(db.Integer, default=0)
    description = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    article = db.relationship("Article", backref="attachments", lazy=True)
    file = db.relationship("FileResource", lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'article_id': self.article_id,
            'file_id': self.file_id,
            'attachment_type': self.attachment_type,
            'sort_order': self.sort_order,
            'description': self.description,
            'file': self.file.to_dict() if self.file else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class CarouselAttachment(db.Model):
    """轮播图附件追踪表 - 记录轮播图关联的所有文件"""
    id = db.Column(db.Integer, primary_key=True)
    carousel_id = db.Column(db.Integer, db.ForeignKey("carousel_slide.id"), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey("file_resource.id"), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    is_thumbnail = db.Column(db.Boolean, default=False)  # 是否为缩略图
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    carousel = db.relationship("CarouselSlide", backref="attachments", lazy=True)
    file = db.relationship("FileResource", lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'carousel_id': self.carousel_id,
            'file_id': self.file_id,
            'sort_order': self.sort_order,
            'is_thumbnail': self.is_thumbnail,
            'file': self.file.to_dict() if self.file else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    actor_name = db.Column(db.String(128), nullable=True)
    action = db.Column(db.String(64), nullable=False)
    target_type = db.Column(db.String(64), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    target_name = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    meta = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='success')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'actor_id': self.actor_id,
            'actor_name': self.actor_name,
            'action': self.action,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'target_name': self.target_name,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'meta': self.meta,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {'id': self.id, 'key': self.key, 'value': self.value}
    
    @classmethod
    def get_all(cls):
        configs = cls.query.all()
        return {c.key: c.value for c in configs}

    @classmethod
    def set(cls, key, value):
        rec = cls.query.filter_by(key=key).first()
        if rec:
            rec.value = value
        else:
            rec = cls(key=key, value=value)
            db.session.add(rec)
        db.session.commit()
        return rec

    @classmethod
    def init_defaults(cls):
        defaults = {
            'site_name': 'NEEPU CTF',
            'allow_registration': 'true',
        }
        for k, v in defaults.items():
            if not cls.query.filter_by(key=k).first():
                db.session.add(cls(key=k, value=v))
        db.session.commit()


# ======================== CTF 相关模型 ========================

class CtfDivision(db.Model):
    """CTF竞赛分组/分赛道"""
    __tablename__ = 'ctf_division'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("ctf_game.id"), nullable=False)
    season_id = db.Column(db.Integer, db.ForeignKey("ctf_season.id"), nullable=True)  # 新增：赛季关联
    name = db.Column(db.String(128), nullable=False)  # 分组名称，如"高级组"、"初级组"
    invite_code = db.Column(db.String(32), unique=True, nullable=True)
    school_scope = db.Column(db.String(128), nullable=True)  # 新增：NULL(全局), "高校", "清华大学"(特定学校)
    is_template = db.Column(db.Boolean, default=False)  # 新增：是否为模板
    description = db.Column(db.String(256), nullable=True)  # 新增：描述
    sort_order = db.Column(db.Integer, default=0)  # 新增：排序
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'game_id': self.game_id,
            'season_id': self.season_id,
            'name': self.name,
            'invite_code': self.invite_code,
            'school_scope': self.school_scope,
            'is_template': self.is_template,
            'description': self.description,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class CtfChallenge(db.Model):
    """游戏/竞赛中的挑战题目"""
    __tablename__ = 'ctf_challenge'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("ctf_game.id"), nullable=False)
    season_id = db.Column(db.Integer, db.ForeignKey("ctf_season.id"), nullable=True)  # 新增：赛季关联
    category_id = db.Column(db.Integer, db.ForeignKey("ctf_challenge_category.id"), nullable=True)  # 新增：分类外键
    source_challenge_id = db.Column(db.Integer, db.ForeignKey("ctf_challenge.id"), nullable=True)  # 新增：复用自哪道题
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(64), nullable=False)  # 如 web, pwn, misc, crypto 等
    original_points = db.Column(db.Integer, default=1000)  # 原始分值
    min_score_rate = db.Column(db.Float, default=0.25)  # 最小分值率
    difficulty = db.Column(db.Float, default=5.0)  # 难度系数
    flag = db.Column(db.String(512), nullable=False, default="flag{testflag}")  # 默认占位符，实际flag自己修改
    flag_template = db.Column(db.String(512), nullable=True)  # 动态flag模板
    is_enabled = db.Column(db.Boolean, default=True)
    is_template = db.Column(db.Boolean, default=False)  # 新增：是否为模板
    is_public = db.Column(db.Boolean, default=False)  # 新增：是否公开题库
    attachment_id = db.Column(db.Integer, db.ForeignKey("file_resource.id"), nullable=True)
    submission_limit = db.Column(db.Integer, default=0)  # 0 表示无限制
    deadline = db.Column(db.DateTime, nullable=True)
    disable_blood_bonus = db.Column(db.Boolean, default=False)  # 是否禁用血液奖励
    enable_traffic_capture = db.Column(db.Boolean, default=False)  # 是否启用流量捕获
    # Docker 容器相关字段
    docker_image = db.Column(db.String(256), nullable=True)  # Docker 镜像名称
    docker_port = db.Column(db.Integer, default=80)  # 容器暴露的端口
    cpu_count = db.Column(db.Integer, default=1)
    memory_limit = db.Column(db.Integer, default=256)  # MB
    storage_limit = db.Column(db.Integer, default=1024)  # MB
    network_mode = db.Column(db.String(32), default="Open")  # Open, Isolated, Custom
    challenge_type = db.Column(db.Integer, default=0)  # 0=StaticAttachment, 1=StaticContainer, 2=DynamicAttachment, 3=DynamicContainer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'game_id': self.game_id,
            'season_id': self.season_id,
            'category_id': self.category_id,
            'source_challenge_id': self.source_challenge_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'original_points': self.original_points,
            'points': self.original_points,
            'min_score_rate': self.min_score_rate,
            'difficulty': self.difficulty,
            'is_enabled': self.is_enabled,
            'is_template': self.is_template,
            'is_public': self.is_public,
            'attachment_id': self.attachment_id,
            'submission_limit': self.submission_limit,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'docker_image': self.docker_image,
            'docker_port': self.docker_port,
            'challenge_type': self.challenge_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'flag': self.flag,
            'disable_blood_bonus': self.disable_blood_bonus,
            'memory_limit': self.memory_limit,
            'cpu_count': self.cpu_count,
            'flag_template': self.flag_template,
        }

    @property
    def points(self):
        return self.original_points


class CtfChallengeSubmission(db.Model):
    """用户提交的答案/flag"""
    __tablename__ = 'ctf_challenge_submission'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("ctf_challenge.id"), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey("ctf_game.id"), nullable=False)
    division_id = db.Column(db.Integer, db.ForeignKey("ctf_division.id"), nullable=True)  # 新增：赛道
    answer = db.Column(db.String(1024), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    points_earned = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, default=0)  # 0=ACCEPTED, 1=WRONG, 2=DUPLICATE, 3=CHEAT
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'team_id': self.team_id,
            'challenge_id': self.challenge_id,
            'game_id': self.game_id,
            'division_id': self.division_id,
            'answer': self.answer,
            'is_correct': self.is_correct,
            'points_earned': self.points_earned,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
        }

    # Relationship backrefs for convenience
    challenge = db.relationship("CtfChallenge", backref=db.backref("ctf_submissions", lazy=True))
    user = db.relationship("User", backref=db.backref("ctf_submissions", lazy=True))


class CtfGameInstance(db.Model):
    """动态题目实例（如Docker容器）"""
    __tablename__ = 'ctf_game_instance'
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("ctf_challenge.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    container_id = db.Column(db.String(256), nullable=True)  # Docker容器ID
    container_image = db.Column(db.String(256), nullable=True)  # Docker镜像名
    port = db.Column(db.Integer, nullable=True)  # 映射的端口
    connection_url = db.Column(db.String(512), nullable=True)  # 容器访问地址
    is_running = db.Column(db.Boolean, default=False)
    tcpdump_pid = db.Column(db.Integer, nullable=True)  # tcpdump 进程 PID
    dynamic_flag = db.Column(db.String(512), nullable=True)  # 为此容器实例生成的动态flag
    started_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'instance_id': self.id,  # 前端期望的字段名
            'challenge_id': self.challenge_id,
            'team_id': self.team_id,
            'user_id': self.user_id,
            'container_id': self.container_id,
            'container_image': self.container_image,
            'port': self.port,
            'connection_url': self.connection_url,
            'is_running': self.is_running,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class CtfChallengeCategory(db.Model):
    """挑战分类"""
    __tablename__ = 'ctf_challenge_category'
    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey("ctf_season.id"), nullable=True)  # 新增：赛季
    game_id = db.Column(db.Integer, db.ForeignKey("ctf_game.id"), nullable=True)  # 新增：比赛（可选）
    name = db.Column(db.String(64), unique=True, nullable=False)  # 如 Web, PWN, Misc, Crypto
    description = db.Column(db.String(256), nullable=True)
    icon = db.Column(db.String(128), nullable=True)
    color = db.Column(db.String(16), nullable=True)  # 颜色代码
    is_template = db.Column(db.Boolean, default=False)  # 新增：是否为模板
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'season_id': self.season_id,
            'game_id': self.game_id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'is_template': self.is_template,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class CtfScoreboard(db.Model):
    """实时排行榜数据 - Team-based scoreboard"""
    __tablename__ = 'ctf_scoreboard'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("ctf_game.id"), nullable=False)
    division_id = db.Column(db.Integer, db.ForeignKey("ctf_division.id"), nullable=True)  # 新增：赛道
    season_id = db.Column(db.Integer, db.ForeignKey("ctf_season.id"), nullable=True)  # 新增：赛季（冗余便于查询）
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)  # 必须有队伍
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    total_points = db.Column(db.Integer, default=0)
    solved_challenges = db.Column(db.Integer, default=0)  # 已解决的题目数
    last_submission_time = db.Column(db.DateTime, nullable=True)  # 最后提交时间，用于排名打破平局
    rank = db.Column(db.Integer, nullable=True)  # 排名
    rank_in_division = db.Column(db.Integer, nullable=True)  # 新增：赛道内排名
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    game = db.relationship("CtfGame", backref="ctf_scoreboards", lazy=True)
    team = db.relationship("Team", backref="ctf_scoreboards", lazy=True)
    user = db.relationship("User", backref="ctf_scoreboards", lazy=True)

    def to_dict(self):
        team_data = self.team.to_dict() if self.team else None
        return {
            'id': self.id,
            'game_id': self.game_id,
            'division_id': self.division_id,
            'season_id': self.season_id,
            'user_id': getattr(self, 'user_id', None),
            'team_id': self.team_id,
            'team': team_data,
            'total_points': self.total_points,
            'solved_challenges': self.solved_challenges,
            'last_submission_time': self.last_submission_time.isoformat() if self.last_submission_time else None,
            'rank': self.rank,
            'rank_in_division': self.rank_in_division,
        }


class CtfSolves(db.Model):
    """首解/二解/三解记录 - 不可变事实源"""
    __tablename__ = 'ctf_solves'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("ctf_game.id"), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey("ctf_challenge.id"), nullable=False)
    division_id = db.Column(db.Integer, db.ForeignKey("ctf_division.id"), nullable=True)  # 新增：赛道
    season_id = db.Column(db.Integer, db.ForeignKey("ctf_season.id"), nullable=True)  # 新增：赛季
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
    blood_level = db.Column(db.Integer, default=0)  # 0=一血, 1=二血, 2=三血
    solved_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'game_id': self.game_id,
            'challenge_id': self.challenge_id,
            'division_id': self.division_id,
            'season_id': self.season_id,
            'user_id': self.user_id,
            'team_id': self.team_id,
            'blood_level': self.blood_level,
            'solved_at': self.solved_at.isoformat() if self.solved_at else None
        }


class CtfCheatInfo(db.Model):
    """作弊检测记录"""
    __tablename__ = 'ctf_cheat_info'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("ctf_game.id"), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey("ctf_challenge_submission.id"), nullable=False)
    source_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    similarity = db.Column(db.Float, default=0.0)
    detection_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'game_id': self.game_id,
            'submission_id': self.submission_id,
            'source_user_id': self.source_user_id,
            'target_user_id': self.target_user_id,
            'similarity': self.similarity,
            'detection_time': self.detection_time.isoformat() if self.detection_time else None
        }


class CtfGameNotice(db.Model):
    """比赛公告"""
    __tablename__ = 'ctf_game_notice'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("ctf_game.id"), nullable=False)
    notice_type = db.Column(db.Integer, default=0)  # 0=普通, 1=一血, 2=二血, 3=三血, 4=新提示, 5=新题目
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'game_id': self.game_id,
            'notice_type': self.notice_type,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CtfChallengeHint(db.Model):
    """题目提示"""
    __tablename__ = 'ctf_challenge_hint'
    
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("ctf_challenge.id"), nullable=False)
    hint_text = db.Column(db.Text, nullable=False)
    penalty_points = db.Column(db.Integer, default=0)  # 查看提示的扣分
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'challenge_id': self.challenge_id,
            'hint_text': self.hint_text,
            'penalty_points': self.penalty_points,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CtfUserHintAccess(db.Model):
    """用户查看的提示记录"""
    __tablename__ = 'ctf_user_hint_access'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    hint_id = db.Column(db.Integer, db.ForeignKey("ctf_challenge_hint.id"), nullable=False)
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'hint_id': self.hint_id,
            'accessed_at': self.accessed_at.isoformat() if self.accessed_at else None
        }


# ======================== 新增：邀请码和统计表 ========================

class CtfUserInviteCode(db.Model):
    """用户邀请码绑定表 - 记录用户用哪个邀请码参加了哪个赛道"""
    __tablename__ = 'ctf_user_invite_code'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey("ctf_game.id"), nullable=False)
    division_id = db.Column(db.Integer, db.ForeignKey("ctf_division.id"), nullable=False)
    invite_code_used = db.Column(db.String(128), nullable=False)  # 用户实际填写的邀请码
    verified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # 验证时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'game_id': self.game_id,
            'division_id': self.division_id,
            'invite_code_used': self.invite_code_used,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class UserSeasonStats(db.Model):
    """用户赛季统计表 - 存储用户在某个赛季的累计成绩"""
    __tablename__ = 'user_season_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    season_id = db.Column(db.Integer, db.ForeignKey("ctf_season.id"), nullable=False)
    
    # 赛季内统计
    total_games_participated = db.Column(db.Integer, default=0)  # 参加的竞赛数
    total_points = db.Column(db.Integer, default=0)  # 赛季总分
    total_challenges_solved = db.Column(db.Integer, default=0)  # 解决的题目总数
    
    # 排名
    season_rank = db.Column(db.Integer, nullable=True)  # 赛季排名
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'season_id': self.season_id,
            'total_games_participated': self.total_games_participated,
            'total_points': self.total_points,
            'total_challenges_solved': self.total_challenges_solved,
            'season_rank': self.season_rank,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class TeamSeasonStats(db.Model):
    """队伍赛季统计表 - 存储队伍在某个赛季的累计成绩"""
    __tablename__ = 'team_season_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    season_id = db.Column(db.Integer, db.ForeignKey("ctf_season.id"), nullable=False)
    
    # 赛季内统计
    total_games_participated = db.Column(db.Integer, default=0)  # 参加的竞赛数
    total_points = db.Column(db.Integer, default=0)  # 赛季总分
    total_challenges_solved = db.Column(db.Integer, default=0)  # 解决的题目总数
    
    # 排名
    season_rank = db.Column(db.Integer, nullable=True)  # 赛季排名
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'season_id': self.season_id,
            'total_games_participated': self.total_games_participated,
            'total_points': self.total_points,
            'total_challenges_solved': self.total_challenges_solved,
            'season_rank': self.season_rank,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class PcapCapture(db.Model):
    """流量包捕获记录 - 保存流量捕获的元数据，参考GZCTF的设计"""
    __tablename__ = 'pcap_capture'
    
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("ctf_challenge.id"), nullable=False)
    instance_id = db.Column(db.Integer, db.ForeignKey("ctf_game_instance.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    # 流量捕获文件的存储路径（相对于 captures 目录或数据库存储）
    # 格式: challenge_{challenge_id}_team_{team_id}_user_{user_id}/{timestamp}.pcap
    file_path = db.Column(db.String(512), nullable=False)
    
    # 文件大小（字节）
    file_size = db.Column(db.Integer, default=0)
    
    # 是否已完成捕获
    is_completed = db.Column(db.Boolean, default=False)
    
    # 创建和更新时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)  # 捕获开始时间
    completed_at = db.Column(db.DateTime, nullable=True)  # 捕获完成时间
    
    # 关系
    challenge = db.relationship("CtfChallenge", backref="pcap_captures", lazy=True)
    instance = db.relationship("CtfGameInstance", backref="pcap_captures", lazy=True)
    team = db.relationship("Team", backref="pcap_captures", lazy=True)
    user = db.relationship("User", backref="pcap_captures", lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'challenge_id': self.challenge_id,
            'instance_id': self.instance_id,
            'team_id': self.team_id,
            'user_id': self.user_id,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

