from flask import Flask, jsonify, request
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from flask_cors import CORS
import requests
from backend.server import config
from backend.server import extensions
from backend.server.email_service import email_service
from backend.server.traffic_capture import TrafficCaptureManager
from backend.middleware_refactored import init_all_middleware, configure_redis_backend
from backend.services.redis_service import initialize_redis, get_redis
from backend.services.scheduler import scheduler
from backend.route.auth import bp as auth_bp
from backend.route.teams import bp as teams_bp
from backend.route.games import bp as games_bp
from backend.route.tokens import bp as tokens_bp
from backend.route.admin import bp as admin_bp
from backend.route.articles import bp as articles_bp
from backend.route.uploads import bp as uploads_bp
from backend.route.resources import bp as resources_bp
from backend.route.platform_admin import bp as platform_admin_bp
from backend.route.challenges import bp as challenges_bp
from datetime import timedelta
from backend.route.competitions import bp as competitions_bp
from backend.route.ctf_api import bp as ctf_bp
from backend.route.ctf_admin import ctf_admin_bp, register_legacy_games_deprecation
from backend.route.file_management import bp as file_management_bp
from backend.route.attachments import bp as attachments_bp
from backend.route.container_challenges import bp as container_bp
from backend.route.platform import bp as platform_bp
from backend.route.captcha import bp as captcha_bp
from backend.route.health import bp as health_bp


def create_app():
    # static_folder 用于提供静态文件（CSS, JS, images 等）
    app = Flask(__name__, static_folder="static", static_url_path="/static")

    # Allow configuring one or more frontend origins (comma-separated),
    # fallback to the default Vite port 5173. This accepts multiple origins
    # like "http://localhost:5173,http://localhost:5174" for dev setups.
    raw_origins = config.settings.FRONTEND_URL
    if ',' in raw_origins:
        origins = [o.strip() for o in raw_origins.split(',') if o.strip()]
    else:
        origins = raw_origins
    CORS(app, resources={r"/api/*": {"origins": origins}, r"/uploads/*": {"origins": origins}}, supports_credentials=True)
    
    # 打印数据库连接信息（调试用）
    print(f"[DEBUG] 数据库URI: {config.settings.SQLALCHEMY_DATABASE_URI}")
    
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=config.settings.SQLALCHEMY_DATABASE_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=config.settings.SQLALCHEMY_TRACK_MODIFICATIONS,
        SQLALCHEMY_ENGINE_OPTIONS=config.settings.SQLALCHEMY_ENGINE_OPTIONS,
        JWT_SECRET_KEY=config.settings.JWT_SECRET_KEY,
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=config.settings.JWT_ACCESS_TOKEN_EXPIRES_HOURS),
        JWT_TOKEN_LOCATION=['cookies'],
        JWT_ACCESS_COOKIE_NAME='neepu_token',
        JWT_ACCESS_COOKIE_PATH='/',
        JWT_COOKIE_SECURE=not config.settings.DEBUG,
        JWT_COOKIE_SAMESITE='Lax' if config.settings.DEBUG else 'None',
        JWT_COOKIE_CSRF_PROTECT=config.settings.JWT_COOKIE_CSRF_PROTECT,
        JWT_CSRF_IN_COOKIES=True,
        JWT_CSRF_CHECK_FORM=False,
        DEBUG=config.settings.DEBUG,
        MAIL_SERVER=config.settings.MAIL_SERVER,
        MAIL_PORT=config.settings.MAIL_PORT,
        MAIL_USE_SSL=config.settings.MAIL_USE_SSL,
        MAIL_USERNAME=config.settings.MAIL_USERNAME,
        MAIL_PASSWORD=config.settings.MAIL_PASSWORD,
        MAIL_DEFAULT_SENDER=config.settings.MAIL_DEFAULT_SENDER,
        MAIL_SENDER_NAME=config.settings.MAIL_SENDER_NAME,
        FRONTEND_URL=config.settings.FRONTEND_URL,
    )

    extensions.db.init_app(app)
    extensions.jwt.init_app(app)

    from backend.server.cache_hooks import register_cache_hooks
    register_cache_hooks()

    email_service.init_app(app)

    # ======================== 初始化 Redis ========================
    if config.settings.REDIS_ENABLED:
        try:
            initialize_redis(
                host=config.settings.REDIS_HOST,
                port=config.settings.REDIS_PORT,
                db=config.settings.REDIS_DB,
                password=config.settings.REDIS_PASSWORD,
            )
            rs = get_redis()
            if rs and rs.is_available():
                configure_redis_backend(rs.redis)
                app.logger.info('Rate limiting: Redis backend active')
                app.logger.info(
                    f"Redis initialized: {config.settings.REDIS_HOST}:"
                    f"{config.settings.REDIS_PORT}/{config.settings.REDIS_DB}"
                )
                try:
                    from backend.services.cache_aside import warm_public_cache
                    warm_public_cache(app)
                except Exception as warm_exc:
                    app.logger.warning(f"Cache pre-warm failed: {warm_exc}")
            else:
                _redis_fallback_msg = (
                    "Redis enabled but connection failed; "
                    "in-memory rate limiting is per-process and unsafe under multi-worker"
                )
                if not config.settings.DEBUG:
                    app.logger.critical(_redis_fallback_msg)
                    require_redis = os.environ.get("NEPU_REQUIRE_REDIS", "1").lower() in (
                        "1", "true", "yes",
                    )
                    if require_redis:
                        raise RuntimeError(
                            "Production requires Redis for shared rate limits "
                            "(set NEPU_REQUIRE_REDIS=0 to override; not recommended)"
                        )
                else:
                    app.logger.warning(_redis_fallback_msg)
        except RuntimeError:
            raise
        except Exception as e:
            if not config.settings.DEBUG and os.environ.get("NEPU_REQUIRE_REDIS", "1").lower() in (
                "1", "true", "yes",
            ):
                app.logger.critical(f"Redis initialization failed in production: {e}")
                raise RuntimeError(f"Production requires Redis: {e}") from e
            app.logger.warning(f"Redis initialization failed: {e}, continuing without Redis")
    else:
        if not config.settings.DEBUG:
            app.logger.critical(
                "REDIS_ENABLED=false in non-DEBUG mode: Flag rate limits are per-worker only"
            )
        app.logger.info('Rate limiting: in-memory backend (set REDIS_ENABLED=true for multi-worker)')

    # ======================== 初始化中间件 ========================
    init_all_middleware(
        app,
        enable_compression=config.settings.ENABLE_COMPRESSION,
        security_policy=config.settings.SECURITY_POLICY,
    )

    @app.before_request
    def enforce_maintenance_mode():
        """维护模式下仅管理员可访问 API（保留登录与平台信息接口）"""
        from flask import jsonify
        from backend.services.maintenance_service import (
            get_maintenance_state,
            is_exempt_path,
            current_user_is_admin,
        )

        path = request.path or ""
        if not path.startswith("/api/"):
            return None

        enabled, message = get_maintenance_state()
        if not enabled:
            return None
        if is_exempt_path(path):
            return None
        if current_user_is_admin():
            return None

        return jsonify({
            "code": 503,
            "msg": message,
            "maintenance": True,
        }), 503

    @app.before_request
    def block_public_uploads():
        """禁止直接访问 /static/uploads/，统一走受控下载接口"""
        if request.path.startswith('/static/uploads/'):
            return jsonify({'msg': 'forbidden'}), 403

    if not config.settings.DEBUG and not os.environ.get('NEPU_JWT_SECRET'):
        raise RuntimeError(
            '生产环境必须设置 NEPU_JWT_SECRET（建议 openssl rand -hex 32）'
        )
    jwt_secret = config.settings.JWT_SECRET_KEY or ''
    if len(jwt_secret) < 32:
        msg = f'NEPU_JWT_SECRET 长度不足 32（当前 {len(jwt_secret)}），存在伪造风险'
        if config.settings.DEBUG:
            app.logger.warning(msg)
        else:
            raise RuntimeError(msg)
    weak_markers = ('change-me', 'dev-only', 'insecure', 'production-requires')
    if any(m in jwt_secret for m in weak_markers):
        app.logger.warning('检测到弱 JWT 密钥模式，上线前请更换为强随机密钥')
    if 'change-me' in (config.settings.SQLALCHEMY_DATABASE_URI or ''):
        app.logger.warning('数据库连接串仍含 change-me 占位口令，请更换')

    # 更可靠的启动时 schema 同步：先查询 information_schema 判断列是否存在，再按需执行 ALTER
    from sqlalchemy import text
    def _ensure_columns():
        checks = [
            ("announcement", "published_at", "ALTER TABLE announcement ADD COLUMN published_at DATETIME NULL"),
            ("carousel_slide", "resource_id", "ALTER TABLE carousel_slide ADD COLUMN resource_id INT NULL"),
            ("carousel_slide", "sort_order", "ALTER TABLE carousel_slide ADD COLUMN sort_order INT NULL"),
            ("article", "summary", "ALTER TABLE article ADD COLUMN summary TEXT NULL"),
            ("article", "published_at", "ALTER TABLE article ADD COLUMN published_at DATETIME NULL"),
            ("article", "tags", "ALTER TABLE article ADD COLUMN tags VARCHAR(512) NULL"),
            ("user", "full_name", "ALTER TABLE `user` ADD COLUMN full_name VARCHAR(128) NULL"),
            ("todo", "user_id", "ALTER TABLE todo ADD COLUMN user_id INT NULL"),
            ("todo", "done", "ALTER TABLE todo ADD COLUMN done TINYINT(1) DEFAULT 0"),
            ("todo", "text", "ALTER TABLE todo ADD COLUMN text VARCHAR(1024) NULL"),
            ("file_resource", "url", "ALTER TABLE file_resource ADD COLUMN url VARCHAR(1024) NULL"),
            ("file_resource", "path", "ALTER TABLE file_resource ADD COLUMN path VARCHAR(1024) NULL"),
            ("game_challenge", "original_points", "ALTER TABLE game_challenge ADD COLUMN original_points INT DEFAULT 1000"),
            ("game_challenge", "min_score_rate", "ALTER TABLE game_challenge ADD COLUMN min_score_rate FLOAT DEFAULT 0.25"),
            ("game_challenge", "difficulty", "ALTER TABLE game_challenge ADD COLUMN difficulty FLOAT DEFAULT 5.0"),
            ("game_challenge", "flag", "ALTER TABLE game_challenge ADD COLUMN flag VARCHAR(512) NULL"),
            ("game_challenge", "flag_template", "ALTER TABLE game_challenge ADD COLUMN flag_template VARCHAR(512) NULL"),
            ("game_challenge", "is_enabled", "ALTER TABLE game_challenge ADD COLUMN is_enabled TINYINT(1) DEFAULT 1"),
            ("game_challenge", "attachment_id", "ALTER TABLE game_challenge ADD COLUMN attachment_id INT NULL"),
            ("game_challenge", "submission_limit", "ALTER TABLE game_challenge ADD COLUMN submission_limit INT DEFAULT 0"),
            ("game_challenge", "deadline", "ALTER TABLE game_challenge ADD COLUMN deadline DATETIME NULL"),
            ("game_challenge", "docker_image", "ALTER TABLE game_challenge ADD COLUMN docker_image VARCHAR(256) NULL"),
            ("game_challenge", "docker_port", "ALTER TABLE game_challenge ADD COLUMN docker_port INT DEFAULT 80"),
            ("game_challenge", "challenge_type", "ALTER TABLE game_challenge ADD COLUMN challenge_type INT DEFAULT 0"),
            ("game_challenge", "disable_blood_bonus", "ALTER TABLE game_challenge ADD COLUMN disable_blood_bonus TINYINT(1) DEFAULT 0"),
            ("game_challenge", "enable_traffic_capture", "ALTER TABLE game_challenge ADD COLUMN enable_traffic_capture TINYINT(1) DEFAULT 0"),
            ("game_challenge", "cpu_count", "ALTER TABLE game_challenge ADD COLUMN cpu_count INT DEFAULT 1"),
            ("game_challenge", "memory_limit", "ALTER TABLE game_challenge ADD COLUMN memory_limit INT DEFAULT 256"),
            ("game_challenge", "storage_limit", "ALTER TABLE game_challenge ADD COLUMN storage_limit INT DEFAULT 1024"),
            ("game_challenge", "network_mode", "ALTER TABLE game_challenge ADD COLUMN network_mode VARCHAR(32) DEFAULT 'Open'"),
            ("challenge_submission", "status", "ALTER TABLE challenge_submission ADD COLUMN status INT DEFAULT 0"),
            ("challenge_submission", "points_earned", "ALTER TABLE challenge_submission ADD COLUMN points_earned INT DEFAULT 0"),
            ("challenge_submission", "answer", "ALTER TABLE challenge_submission ADD COLUMN answer VARCHAR(1024) NULL"),
            ("challenge_submission", "submitted_at", "ALTER TABLE challenge_submission ADD COLUMN submitted_at DATETIME NULL"),
            ("participation", "status", "ALTER TABLE participation ADD COLUMN status VARCHAR(32) DEFAULT 'pending'"),
            ("participation", "token", "ALTER TABLE participation ADD COLUMN token VARCHAR(128) NOT NULL"),
            ("participation", "joined_at", "ALTER TABLE participation ADD COLUMN joined_at DATETIME NULL"),
            ("participation", "updated_at", "ALTER TABLE participation ADD COLUMN updated_at DATETIME NULL"),
            ("ctf_game_instance", "dynamic_flag", "ALTER TABLE ctf_game_instance ADD COLUMN dynamic_flag VARCHAR(512) NULL"),
            ("ctf_game", "team_hash_salt", "ALTER TABLE ctf_game ADD COLUMN team_hash_salt VARCHAR(128) NULL"),
            ("ctf_game", "description", "ALTER TABLE ctf_game ADD COLUMN description TEXT NULL"),
            ("ctf_game", "game_type", "ALTER TABLE ctf_game ADD COLUMN game_type VARCHAR(32) DEFAULT 'official'"),
            ("ctf_game", "archived_at", "ALTER TABLE ctf_game ADD COLUMN archived_at DATETIME NULL"),
            ("ctf_game", "season_id", "ALTER TABLE ctf_game ADD COLUMN season_id INT NULL"),
            ("ctf_game", "status", "ALTER TABLE ctf_game ADD COLUMN status VARCHAR(32) DEFAULT 'not_started'"),
            ("ctf_game", "is_public", "ALTER TABLE ctf_game ADD COLUMN is_public TINYINT(1) DEFAULT 1"),
            ("ctf_game", "summary", "ALTER TABLE ctf_game ADD COLUMN summary VARCHAR(512) NULL"),
            ("ctf_game", "poster_url", "ALTER TABLE ctf_game ADD COLUMN poster_url VARCHAR(1024) NULL"),
            ("ctf_game", "enable_traffic_capture", "ALTER TABLE ctf_game ADD COLUMN enable_traffic_capture TINYINT(1) DEFAULT 0"),
            ("ctf_challenge_submission", "client_ip", "ALTER TABLE ctf_challenge_submission ADD COLUMN client_ip VARCHAR(64) NULL"),
            ("ctf_challenge_submission", "duration_ms", "ALTER TABLE ctf_challenge_submission ADD COLUMN duration_ms INT NULL"),
            ("ctf_challenge_submission", "correct_dedupe_key", "ALTER TABLE ctf_challenge_submission ADD COLUMN correct_dedupe_key VARCHAR(64) NULL"),
            ("ctf_cheat_info", "status", "ALTER TABLE ctf_cheat_info ADD COLUMN status VARCHAR(32) DEFAULT 'pending'"),
            ("ctf_cheat_info", "admin_note", "ALTER TABLE ctf_cheat_info ADD COLUMN admin_note TEXT NULL"),
            ("ctf_cheat_info", "reviewed_at", "ALTER TABLE ctf_cheat_info ADD COLUMN reviewed_at DATETIME NULL"),
            ("ctf_cheat_info", "reviewed_by", "ALTER TABLE ctf_cheat_info ADD COLUMN reviewed_by INT NULL"),
            ("user", "is_moderator", "ALTER TABLE `user` ADD COLUMN is_moderator TINYINT(1) DEFAULT 0"),
        ]
        
        # 检查是否需要创建 pcap_capture 表
        def _check_pcap_capture_table():
            try:
                q = text("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pcap_capture'")
                res = extensions.db.session.execute(q).scalar()
                table_exists = bool(res and int(res) > 0)
                
                if not table_exists:
                    app.logger.info("Creating pcap_capture table")
                    create_sql = """
                    CREATE TABLE pcap_capture (
                        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        challenge_id INT NOT NULL,
                        instance_id INT NOT NULL,
                        team_id INT NULL,
                        user_id INT NOT NULL,
                        file_path VARCHAR(512) NOT NULL,
                        file_size INT DEFAULT 0,
                        is_completed TINYINT(1) DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        started_at DATETIME NULL,
                        completed_at DATETIME NULL,
                        FOREIGN KEY (challenge_id) REFERENCES ctf_challenge(id),
                        FOREIGN KEY (instance_id) REFERENCES ctf_game_instance(id),
                        FOREIGN KEY (team_id) REFERENCES team(id),
                        FOREIGN KEY (user_id) REFERENCES user(id),
                        INDEX idx_challenge_team_user (challenge_id, team_id, user_id),
                        INDEX idx_instance (instance_id)
                    )
                    """
                    extensions.db.session.execute(text(create_sql))
                    extensions.db.session.commit()
            except Exception as e:
                app.logger.debug(f"pcap_capture table check/creation error: {e}")
        
        # 在主检查之前先检查 pcap_capture 表
        _check_pcap_capture_table()

        def _relax_pcap_team_id_nullable():
            try:
                q = text(
                    "SELECT IS_NULLABLE FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pcap_capture' "
                    "AND COLUMN_NAME = 'team_id'"
                )
                row = extensions.db.session.execute(q).fetchone()
                if row and row[0] == 'NO':
                    extensions.db.session.execute(
                        text("ALTER TABLE pcap_capture MODIFY team_id INT NULL")
                    )
                    extensions.db.session.commit()
            except Exception as e:
                app.logger.debug(f"pcap_capture team_id nullable migration: {e}")

        _relax_pcap_team_id_nullable()

        def _relax_participation_team_id_nullable():
            alters = [
                ("ctf_participation", "team_id"),
                ("ctf_participating_user", "team_id"),
                ("ctf_scoreboard", "team_id"),
            ]
            try:
                for table, col in alters:
                    q = text(
                        "SELECT IS_NULLABLE FROM information_schema.COLUMNS "
                        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c"
                    )
                    row = extensions.db.session.execute(q, {"t": table, "c": col}).fetchone()
                    if row and row[0] == "NO":
                        extensions.db.session.execute(
                            text(f"ALTER TABLE {table} MODIFY {col} INT NULL")
                        )
                extensions.db.session.commit()
            except Exception as e:
                app.logger.debug(f"participation team_id nullable migration: {e}")

        _relax_participation_team_id_nullable()

        def _ensure_dynamic_package_table():
            try:
                q = text(
                    "SELECT COUNT(*) FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ctf_dynamic_package'"
                )
                exists = bool(extensions.db.session.execute(q).scalar())
                if not exists:
                    app.logger.info("Creating ctf_dynamic_package table")
                    extensions.db.session.execute(text("""
                    CREATE TABLE ctf_dynamic_package (
                        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        challenge_id INT NOT NULL,
                        variant_id INT DEFAULT 0,
                        filename VARCHAR(512) NOT NULL,
                        storage_key VARCHAR(1024) NOT NULL,
                        file_hash VARCHAR(128) NULL,
                        file_size INT DEFAULT 0,
                        is_active TINYINT(1) DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_dyn_pkg_challenge (challenge_id),
                        FOREIGN KEY (challenge_id) REFERENCES ctf_challenge(id)
                    )
                    """))
                    extensions.db.session.commit()
            except Exception as e:
                app.logger.debug(f"ctf_dynamic_package table: {e}")

        _ensure_dynamic_package_table()

        for table, column, alter_sql in checks:
            try:
                q = text("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table AND COLUMN_NAME = :column")
                res = extensions.db.session.execute(q, {"table": table, "column": column}).scalar()
                exists = bool(res and int(res) > 0)
                if not exists:
                    app.logger.info(f"Adding missing column {table}.{column}")
                    extensions.db.session.execute(text(alter_sql))
                    extensions.db.session.commit()
            except Exception as e:
                app.logger.debug(f"Schema sync ignored/failed for: {table}.{column} -> {e}")

        def _ensure_blood_unique_index():
            """清理重复一血后加 UNIQUE(challenge_id, blood_level)。"""
            try:
                q = text(
                    "SELECT COUNT(*) FROM information_schema.STATISTICS "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ctf_solves' "
                    "AND INDEX_NAME = 'uq_ctf_solves_challenge_blood'"
                )
                exists = bool(extensions.db.session.execute(q).scalar())
                if exists:
                    return
                # 保留每题每 blood_level 最小 id
                extensions.db.session.execute(text("""
                    DELETE s FROM ctf_solves s
                    INNER JOIN ctf_solves s2
                      ON s.challenge_id = s2.challenge_id
                     AND s.blood_level = s2.blood_level
                     AND s.id > s2.id
                """))
                extensions.db.session.execute(text(
                    "CREATE UNIQUE INDEX uq_ctf_solves_challenge_blood "
                    "ON ctf_solves (challenge_id, blood_level)"
                ))
                extensions.db.session.commit()
                app.logger.info("Created unique index uq_ctf_solves_challenge_blood")
            except Exception as e:
                extensions.db.session.rollback()
                app.logger.warning(f"blood unique index ensure failed: {e}")

        _ensure_blood_unique_index()

        def _ensure_correct_submit_unique():
            """正确提交去重：UNIQUE(correct_dedupe_key)，NULL 允许多条错误提交。"""
            try:
                q = text(
                    "SELECT COUNT(*) FROM information_schema.STATISTICS "
                    "WHERE TABLE_SCHEMA = DATABASE() "
                    "AND TABLE_NAME = 'ctf_challenge_submission' "
                    "AND INDEX_NAME = 'uq_ctf_correct_dedupe_key'"
                )
                exists = bool(extensions.db.session.execute(q).scalar())
                if exists:
                    return
                # 回填已有正确提交的去重键，再删重复（保留最小 id）
                extensions.db.session.execute(text("""
                    UPDATE ctf_challenge_submission
                    SET correct_dedupe_key = CONCAT(
                        'c', challenge_id, ':',
                        IF(team_id IS NOT NULL, CONCAT('t', team_id), CONCAT('u', user_id))
                    )
                    WHERE is_correct = 1 AND (correct_dedupe_key IS NULL OR correct_dedupe_key = '')
                """))
                extensions.db.session.execute(text("""
                    DELETE s FROM ctf_challenge_submission s
                    INNER JOIN ctf_challenge_submission s2
                      ON s.correct_dedupe_key = s2.correct_dedupe_key
                     AND s.correct_dedupe_key IS NOT NULL
                     AND s.id > s2.id
                """))
                extensions.db.session.execute(text(
                    "CREATE UNIQUE INDEX uq_ctf_correct_dedupe_key "
                    "ON ctf_challenge_submission (correct_dedupe_key)"
                ))
                extensions.db.session.commit()
                app.logger.info("Created unique index uq_ctf_correct_dedupe_key")
            except Exception as e:
                extensions.db.session.rollback()
                app.logger.warning(f"correct submit unique index ensure failed: {e}")

        _ensure_correct_submit_unique()

    try:
        with app.app_context():
            _ensure_columns()
    except Exception:
        app.logger.debug('Schema sync skipped')

    # JWT error handlers
    @extensions.jwt.invalid_token_loader
    def _invalid_token_callback(reason):
        return jsonify({'msg': 'invalid token', 'reason': reason}), 401

    @extensions.jwt.unauthorized_loader
    def _missing_token_callback(reason):
        return jsonify({'msg': 'missing token', 'reason': reason}), 401

    @extensions.jwt.expired_token_loader
    def _expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'msg': 'token expired'}), 401

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(teams_bp, url_prefix="/api/teams")
    app.register_blueprint(games_bp, url_prefix="/api/games")
    app.register_blueprint(tokens_bp, url_prefix="/api/tokens")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(articles_bp, url_prefix="/api/articles")
    app.register_blueprint(uploads_bp, url_prefix="/api/uploads")
    app.register_blueprint(resources_bp, url_prefix="/api/resources")
    app.register_blueprint(platform_admin_bp)
    app.register_blueprint(challenges_bp, url_prefix="/api/challenges")
    app.register_blueprint(competitions_bp, url_prefix="/api/competitions")
    app.register_blueprint(file_management_bp, url_prefix="/api/admin/platform")
    app.register_blueprint(attachments_bp)
    
    # CTF 题目管理（仅管理员）
    from backend.route.challenge_admin import bp as challenge_admin_bp
    app.register_blueprint(challenge_admin_bp, url_prefix="/api/admin/challenges")
    
    # CTF 管理员接口 - 竞赛、题目、作弊检测管理
    app.register_blueprint(ctf_admin_bp)
    register_legacy_games_deprecation(app)
    
    # CTF 完整功能 API
    app.register_blueprint(ctf_bp)
    
    # Docker容器管理（兼容别名；主路径见 /api/challenges/...）
    app.register_blueprint(container_bp, url_prefix="/api/container")

    # 动态附件包（stub，避免管理端 404）
    from backend.route.dynamic_packages import bp as dynamic_packages_bp
    app.register_blueprint(dynamic_packages_bp, url_prefix="/api/admin/dynamic-packages")

    # 平台公开信息
    app.register_blueprint(platform_bp)
    app.register_blueprint(captcha_bp)
    app.register_blueprint(health_bp)

    # 简单模式：启动时自动建表，用于验证数据库连接
    with app.app_context():
        extensions.db.create_all()
        try:
            from backend.services.team_service import repair_orphan_participations
            n = repair_orphan_participations()
            if n:
                app.logger.info(f"Cleaned {n} orphan participations (team_id=NULL)")
        except Exception as e:
            app.logger.debug(f"Orphan participation cleanup skipped: {e}")

    # ======================== 初始化任务调度器 ========================
    scheduler.init_app(app)

    # 写入默认 Wiki 教程与欢迎公告（幂等）
    try:
        from backend.services.platform_seed import seed_platform_content
        seed_platform_content(app)
    except Exception as e:
        app.logger.debug(f"Platform content seed skipped: {e}")

    try:
        from backend.services.platform_config_service import seed_platform_config_defaults
        seed_platform_config_defaults(app)
    except Exception as e:
        app.logger.debug(f"Platform config seed skipped: {e}")

    return app


def external_events_proxy():
    """代理获取国内外赛事数据，避免前端CORS问题"""
    region = request.args.get('region', 'both')
    cache_key = f"external_events:{region}"

    rs = get_redis()
    if rs and rs.is_available():
        cached = rs.get_json(cache_key)
        if cached:
            resp = jsonify(cached)
            resp.headers["X-Cache"] = "HIT"
            return resp

    url_cn = 'https://raw.githubusercontent.com/ProbiusOfficial/Hello-CTFtime/main/CN.json'
    url_global = 'https://raw.githubusercontent.com/ProbiusOfficial/Hello-CTFtime/main/Global.json'

    def fetch_json(url):
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            from flask import current_app
            current_app.logger.warning(f"Failed to fetch {url}: {e}")
        return None

    result = {}
    if region in ('cn', 'both'):
        cn_data = fetch_json(url_cn)
        if isinstance(cn_data, dict) and cn_data.get('data'):
            result['cn'] = cn_data.get('data', {}).get('result', [])
        elif isinstance(cn_data, list):
            result['cn'] = cn_data
        else:
            result['cn'] = []

    if region in ('global', 'both'):
        global_data = fetch_json(url_global)
        if isinstance(global_data, list):
            result['global'] = global_data
        else:
            result['global'] = []

    payload = {'success': True, 'data': result}
    if rs and rs.is_available():
        rs.set_json(cache_key, payload, expiration=1800)

    resp = jsonify(payload)
    resp.headers["X-Cache"] = "MISS"
    return resp


app = create_app()

from backend.middleware_refactored import rate_limit

app.route('/api/external/events')(rate_limit(max_requests=20, window_seconds=60)(external_events_proxy))


if __name__ == "__main__":
    # 容器代理依赖后台线程；开启 reloader 会导致进程重启并丢失线程
    app.run(debug=config.settings.DEBUG, use_reloader=False)