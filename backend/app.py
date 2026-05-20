from flask import Flask, jsonify, request
import os
from flask_cors import CORS
import requests
from backend.server import config
from backend.server import extensions
from backend.server.email_service import email_service
from backend.server.traffic_capture import TrafficCaptureManager
from backend.middleware_refactored import init_all_middleware
from backend.services.redis_service import initialize_redis
from backend.services.scheduler import scheduler
from backend.route.auth import bp as auth_bp
from backend.route.teams import bp as teams_bp
from backend.route.games import bp as games_bp
from backend.route.tokens import bp as tokens_bp
from backend.route.admin import bp as admin_bp
from backend.route.articles import bp as articles_bp
from backend.route.uploads import bp as uploads_bp
from backend.route.resources import bp as resources_bp
from backend.route.todos import bp as todos_bp
from backend.route.platform_admin import bp as platform_admin_bp
from backend.route.challenges import bp as challenges_bp
from backend.route.competitions import bp as competitions_bp
from backend.route.ctf_api import bp as ctf_bp
from backend.route.ctf_admin import ctf_admin_bp
from backend.route.file_management import bp as file_management_bp
from backend.route.attachments import bp as attachments_bp
from backend.route.container_challenges import bp as container_bp
from backend.route.container_challenges import _is_port_listening, _start_capture_proxy_thread


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
        JWT_SECRET_KEY=config.settings.JWT_SECRET_KEY,
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
    email_service.init_app(app)

    # ======================== 初始化 Redis ========================
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = int(os.environ.get('REDIS_PORT', 6379))
    redis_db = int(os.environ.get('REDIS_DB', 0))
    redis_enabled = os.environ.get('REDIS_ENABLED', 'false').lower() in ('true', '1', 'yes')
    
    if redis_enabled:
        try:
            initialize_redis(host=redis_host, port=redis_port, db=redis_db)
            app.logger.info(f"Redis initialized: {redis_host}:{redis_port}/{redis_db}")
        except Exception as e:
            app.logger.warning(f"Redis initialization failed: {e}, continuing without Redis cache")
    else:
        app.logger.info("Redis disabled via environment variable (REDIS_ENABLED=false)")
    
    # ======================== 初始化中间件 ========================
    init_all_middleware(app, enable_compression=False)

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
                        team_id INT NOT NULL,
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
    app.register_blueprint(todos_bp)
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
    
    # CTF 完整功能 API
    app.register_blueprint(ctf_bp)
    
    # Docker容器管理
    app.register_blueprint(container_bp, url_prefix="/api/container")

    # 简单模式：启动时自动建表，用于验证数据库连接
    with app.app_context():
        extensions.db.create_all()

    # 恢复后端重启前的容器代理线程（daemon 线程会随进程重启丢失）
    def _recover_container_proxies():
        try:
            from backend.server.db_models import CtfGameInstance, User
            running_instances = CtfGameInstance.query.filter_by(is_running=True).all()
            recovered = 0
            skipped = 0

            for inst in running_instances:
                if not inst.port:
                    skipped += 1
                    continue

                proxy_port = inst.tcpdump_pid if (inst.tcpdump_pid and inst.tcpdump_pid > 10000) else (inst.port + 10000)

                if _is_port_listening("127.0.0.1", proxy_port):
                    skipped += 1
                    continue

                user = User.query.get(inst.user_id)
                team_id = user.team_id if (user and user.team_id) else inst.user_id

                _start_capture_proxy_thread(
                    app=app,
                    challenge_id=inst.challenge_id,
                    instance_id=inst.id,
                    team_id=team_id,
                    user_id=inst.user_id,
                    container_port=inst.port,
                    proxy_port=proxy_port,
                )

                inst.connection_url = f"http://localhost:{proxy_port}"
                inst.tcpdump_pid = proxy_port
                recovered += 1

            if recovered:
                extensions.db.session.commit()

            app.logger.info(f"Container proxy recovery done: recovered={recovered}, skipped={skipped}, total={len(running_instances)}")
        except Exception as e:
            app.logger.warning(f"Container proxy recovery failed: {e}")

    with app.app_context():
        _recover_container_proxies()
    
    # ======================== 初始化任务调度器 ========================
    scheduler.init_app(app)

    return app


def external_events_proxy():
    """代理获取国内外赛事数据，避免前端CORS问题"""
    region = request.args.get('region', 'both')  # cn, global, both
    url_cn = 'https://raw.githubusercontent.com/ProbiusOfficial/Hello-CTFtime/main/CN.json'
    url_global = 'https://raw.githubusercontent.com/ProbiusOfficial/Hello-CTFtime/main/Global.json'
    
    def fetch_json(url):
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            Flask.current_app.logger.warning(f"Failed to fetch {url}: {e}")
        return None
    
    result = {}
    if region in ('cn', 'both'):
        cn_data = fetch_json(url_cn)
        # CN.json 格式: {success: true, data: {result: [...]}}
        if isinstance(cn_data, dict) and cn_data.get('data'):
            result['cn'] = cn_data.get('data', {}).get('result', [])
        elif isinstance(cn_data, list):
            result['cn'] = cn_data
        else:
            result['cn'] = []
    
    if region in ('global', 'both'):
        global_data = fetch_json(url_global)
        # Global.json 是直接的数组
        if isinstance(global_data, list):
            result['global'] = global_data
        else:
            result['global'] = []
    
    return jsonify({'success': True, 'data': result})


app = create_app()
app.route('/api/external/events')(external_events_proxy)


if __name__ == "__main__":
    # 容器代理依赖后台线程；开启 reloader 会导致进程重启并丢失线程
    app.run(debug=config.settings.DEBUG, use_reloader=False)