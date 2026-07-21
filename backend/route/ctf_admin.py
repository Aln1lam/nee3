"""
CTF 管理员接口 (/api/admin)

路由约定（与 frontend/src/services/admin/ctf.js 对齐）：
- 题目 CRUD、附件：/api/admin/challenges/games/*
- 作弊检测、首解：/api/admin/cheat-*、/api/admin/first-solves
- 比赛写操作 / 统计 / 导出 / 分组 / 流量：/api/competitions/admin/*
- 比赛只读列表：/api/competitions/

已下线（410）：
- /api/admin/games*（CRUD + stats + export-scoreboard）
"""

from flask import Blueprint, request, jsonify, send_file, current_app, g
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
import os
import mimetypes

from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.server.db_models import (
    db, CtfGame, CtfChallenge, CtfChallengeSubmission, CtfCheatInfo,
    CtfSolves, User, Team, CtfDivision, FileResource, CtfGameInstance,
    CtfScoreboard, CtfParticipatingUser, CtfParticipation, CtfHammerMessage
)
from backend.services.scoring_service import (
    ScoringService, CheatDetectionService, PermissionService,
    FlagValidationService, FlagTemplateService
)

ctf_admin_bp = Blueprint('ctf_admin', __name__, url_prefix='/api/admin')

_LEGACY_GAMES_PREFIX = '/api/admin/games'
_LEGACY_API_GAMES_PREFIX = '/api/games'


def register_legacy_games_deprecation(app):
    """App 级 after_request，确保含 JWT 401 在内的所有响应都带上 Deprecation 头"""

    @app.after_request
    def mark_legacy_games_deprecated(response):
        path = request.path or ''
        if path == _LEGACY_GAMES_PREFIX or path.startswith(_LEGACY_GAMES_PREFIX + '/'):
            response.headers['Deprecation'] = 'true'
            response.headers['Link'] = '</api/competitions/admin/>; rel="successor-version"'
            response.headers['X-Deprecated-Endpoint'] = '/api/competitions/admin/*'
        elif path == _LEGACY_API_GAMES_PREFIX or path.startswith(_LEGACY_API_GAMES_PREFIX + '/'):
            response.headers['Deprecation'] = 'true'
            response.headers['Link'] = '</api/competitions/>; rel="successor-version"'
            response.headers['X-Deprecated-Endpoint'] = '/api/competitions/*|/api/ctf/*|/api/challenges/*'
        return response

# 初始化服务
scoring_service = ScoringService()
cheat_service = CheatDetectionService()
permission_service = PermissionService()
flag_service = FlagValidationService()
flag_template_service = FlagTemplateService()

# 管理员权限检查（基于 JWT Cookie，与 admin.py 一致）
def admin_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            uid = get_jwt_identity()
            if not uid:
                return jsonify({'status': 'error', 'message': '需要管理员权限', 'msg': 'forbidden'}), 403
            user = User.query.get(int(uid))
            if not user or not user.is_admin:
                return jsonify({'status': 'error', 'message': '需要管理员权限', 'msg': 'forbidden'}), 403
            g.user = user
        except Exception:
            return jsonify({'status': 'error', 'message': '需要管理员权限', 'msg': 'forbidden'}), 403
        return f(*args, **kwargs)
    return decorated_function


def staff_required(f):
    """管理员或协管（moderator）可读/审核类接口"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            uid = get_jwt_identity()
            if not uid:
                return jsonify({'status': 'error', 'message': '需要登录', 'msg': 'forbidden'}), 403
            user = User.query.get(int(uid))
            if not user or not (user.is_admin or getattr(user, 'is_moderator', False)):
                return jsonify({'status': 'error', 'message': '需要管理员或协管权限', 'msg': 'forbidden'}), 403
            g.user = user
        except Exception:
            return jsonify({'status': 'error', 'message': '需要管理员或协管权限', 'msg': 'forbidden'}), 403
        return f(*args, **kwargs)
    return decorated_function


# ==================== 竞赛管理（CRUD 410；stats/export/challenges 子路径仍保留） ====================

def _admin_games_crud_gone():
    body = {
        'code': 410,
        'status': 'gone',
        'msg': 'Gone: use /api/competitions/admin/* for game CRUD',
        'successor': '/api/competitions/admin/*',
    }
    resp = jsonify(body)
    resp.status_code = 410
    resp.headers['Deprecation'] = 'true'
    resp.headers['Link'] = '</api/competitions/admin/>; rel="successor-version"'
    return resp


@ctf_admin_bp.route('/games', methods=['GET'])
@admin_required
def list_games():
    """已下线：管理列表请用 GET /api/competitions/"""
    return _admin_games_crud_gone()


@ctf_admin_bp.route('/games', methods=['POST'])
@admin_required
def create_game():
    return _admin_games_crud_gone()


@ctf_admin_bp.route('/games/<int:game_id>', methods=['PUT'])
@admin_required
def update_game(game_id):
    return _admin_games_crud_gone()


@ctf_admin_bp.route('/games/<int:game_id>', methods=['DELETE'])
@admin_required
def delete_game(game_id):
    return _admin_games_crud_gone()


@ctf_admin_bp.route('/games/<int:game_id>/archive', methods=['POST'])
@admin_required
def archive_game(game_id):
    return _admin_games_crud_gone()

# ==================== 题目管理 ====================

def allowed_file(filename):
    """检查文件是否被允许"""
    ALLOWED_EXTENSIONS = {'zip', 'tar', 'gz', 'rar', 'py', 'c', 'cpp', 'txt', 'pdf', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@ctf_admin_bp.route('/games/<int:game_id>/challenges', methods=['GET'])
@admin_required
def list_challenges(game_id):
    """获取竞赛下的所有题目"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = CtfChallenge.query.filter_by(game_id=game_id)
    total = query.count()
    items = query.paginate(page=page, per_page=per_page).items
    
    return jsonify({
        'status': 'success',
        'data': {
            'items': [{
                'id': c.id,
                'game_id': c.game_id,
                'title': c.title,
                'category': c.category,
                'original_points': c.original_points,
                'difficulty': c.difficulty,
                'challenge_type': c.challenge_type,
                'solved_count': CtfChallengeSubmission.query.filter_by(challenge_id=c.id, status='correct').count(),
                'attachment_id': c.attachment_id
            } for c in items],
            'total': total,
            'page': page,
            'per_page': per_page
        }
    })

@ctf_admin_bp.route('/games/<int:game_id>/challenges', methods=['POST'])
@admin_required
def create_challenge(game_id):
    """创建新题目（含附件上传）"""
    game = CtfGame.query.get_or_404(game_id)
    
    # 获取表单数据
    title = request.form.get('title')
    category = request.form.get('category')
    original_points = int(request.form.get('original_points', 1000))
    min_score_rate = float(request.form.get('min_score_rate', 0.25))
    difficulty = float(request.form.get('difficulty', 5.0))
    flag = request.form.get('flag')
    flag_template = request.form.get('flag_template')
    description = request.form.get('description', '')
    challenge_type = int(request.form.get('challenge_type', 0))
    submission_limit = int(request.form.get('submission_limit', 0))
    disable_blood_bonus = request.form.get('disable_blood_bonus', 'false').lower() == 'true'
    
    # 创建题目
    challenge = CtfChallenge(
        game_id=game_id,
        title=title,
        category=category,
        original_points=original_points,
        min_score_rate=min_score_rate,
        difficulty=difficulty,
        flag=flag,
        flag_template=flag_template,
        description=description,
        challenge_type=challenge_type,
        submission_limit=submission_limit,
        disable_blood_bonus=disable_blood_bonus
    )
    
    # 处理容器配置
    if challenge_type in [1, 3]:
        challenge.docker_image = request.form.get('docker_image')
        challenge.docker_port = int(request.form.get('docker_port', 80))
        challenge.memory_limit = int(request.form.get('memory_limit', 256))
        challenge.cpu_count = int(request.form.get('cpu_count', 1))
    
    db.session.add(challenge)
    db.session.flush()
    
    # 处理附件上传
    if 'attachment' in request.files and challenge_type in [0, 2]:
        file = request.files['attachment']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            
            # 创建上传目录
            upload_dir = os.path.join(current_app.root_path, 'static/uploads/challenges')
            os.makedirs(upload_dir, exist_ok=True)
            
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            
            # 创建文件资源记录
            file_resource = FileResource(
                original_name=file.filename,
                stored_name=filename,
                file_size=os.path.getsize(filepath),
                file_type=mimetypes.guess_type(filepath)[0] or 'application/octet-stream',
                uploader_id=None,  # 从 g.user.id 获取
                challenge_id=challenge.id
            )
            db.session.add(file_resource)
            challenge.attachment_id = file_resource.id
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '题目已创建',
        'data': {'id': challenge.id}
    }), 201

@ctf_admin_bp.route('/challenges/<int:challenge_id>', methods=['PUT'])
@admin_required
def update_challenge(challenge_id):
    """更新题目"""
    challenge = CtfChallenge.query.get_or_404(challenge_id)
    
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    # 更新基本字段
    for field in ['title', 'category', 'description', 'flag', 'flag_template']:
        if field in data:
            setattr(challenge, field, data[field])
    
    # 更新数值字段
    for field in ['original_points', 'difficulty', 'min_score_rate', 'challenge_type', 'submission_limit']:
        if field in data:
            setattr(challenge, field, type(getattr(challenge, field))(data[field]))
    
    if 'disable_blood_bonus' in data:
        challenge.disable_blood_bonus = data['disable_blood_bonus']
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '题目已更新'
    })

@ctf_admin_bp.route('/challenges/<int:challenge_id>', methods=['DELETE'])
@admin_required
def delete_challenge(challenge_id):
    """删除题目"""
    challenge = CtfChallenge.query.get_or_404(challenge_id)
    db.session.delete(challenge)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '题目已删除'
    })

# ==================== 题目附件管理 ====================

@ctf_admin_bp.route('/challenges/<int:challenge_id>/attachments', methods=['GET'])
@admin_required
def list_attachments(challenge_id):
    """获取题目的所有附件"""
    challenge = CtfChallenge.query.get_or_404(challenge_id)
    
    attachments = FileResource.query.filter_by(challenge_id=challenge_id).all()
    
    return jsonify({
        'status': 'success',
        'data': [{
            'id': a.id,
            'name': a.original_name,
            'size': a.file_size,
            'type': a.file_type,
            'upload_time': a.upload_time.isoformat(),
            'download_url': f'/api/admin/attachments/{a.id}/download'
        } for a in attachments]
    })

@ctf_admin_bp.route('/challenges/<int:challenge_id>/attachments', methods=['POST'])
@admin_required
def upload_attachment(challenge_id):
    """上传题目附件"""
    challenge = CtfChallenge.query.get_or_404(challenge_id)
    
    if 'file' not in request.files:
        return {'status': 'error', 'message': '未找到文件'}, 400
    
    file = request.files['file']
    if not file or not file.filename:
        return {'status': 'error', 'message': '无效的文件'}, 400
    
    if not allowed_file(file.filename):
        return {'status': 'error', 'message': '不支持的文件格式'}, 400
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
    filename = timestamp + filename
    
    upload_dir = os.path.join(current_app.root_path, 'static/uploads/challenges')
    os.makedirs(upload_dir, exist_ok=True)
    
    filepath = os.path.join(upload_dir, filename)
    raw = file.read()
    if not raw:
        return {'status': 'error', 'message': '空文件'}, 400
    if len(raw) > 20 * 1024 * 1024:
        return {'status': 'error', 'message': '文件过大（上限 20MB）'}, 400
    if filename.lower().endswith('.zip'):
        from backend.services.zip_safety import ZipSafetyError, validate_zip_bytes
        try:
            validate_zip_bytes(raw)
        except ZipSafetyError as e:
            return {'status': 'error', 'message': f'ZIP 不安全: {e}'}, 400
    with open(filepath, 'wb') as fh:
        fh.write(raw)
    
    file_resource = FileResource(
        original_name=file.filename,
        stored_name=filename,
        file_size=os.path.getsize(filepath),
        file_type=mimetypes.guess_type(filepath)[0] or 'application/octet-stream',
        challenge_id=challenge_id
    )
    
    db.session.add(file_resource)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '附件已上传',
        'data': {'id': file_resource.id}
    }), 201

@ctf_admin_bp.route('/attachments/<int:attachment_id>/download', methods=['GET'])
@admin_required
def download_attachment(attachment_id):
    """下载题目附件"""
    file_resource = FileResource.query.get_or_404(attachment_id)
    
    filepath = os.path.join(
        current_app.root_path,
        'static/uploads/challenges',
        file_resource.stored_name
    )
    
    if not os.path.exists(filepath):
        return {'status': 'error', 'message': '文件不存在'}, 404
    
    return send_file(
        filepath,
        download_name=file_resource.original_name,
        as_attachment=True
    )

@ctf_admin_bp.route('/attachments/<int:attachment_id>', methods=['DELETE'])
@admin_required
def delete_attachment(attachment_id):
    """删除附件"""
    file_resource = FileResource.query.get_or_404(attachment_id)
    
    filepath = os.path.join(
        current_app.root_path,
        'static/uploads/challenges',
        file_resource.stored_name
    )
    
    if os.path.exists(filepath):
        os.remove(filepath)
    
    db.session.delete(file_resource)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '附件已删除'
    })

# ==================== 作弊检测管理 ====================

@ctf_admin_bp.route('/cheat-detection', methods=['GET'])
@staff_required
def list_cheat_records():
    """获取作弊检测记录"""
    game_id = request.args.get('game_id', type=int)
    status = (request.args.get('status') or '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = CtfCheatInfo.query
    if game_id:
        query = query.filter_by(game_id=game_id)
    if status in ('pending', 'confirmed', 'dismissed'):
        query = query.filter_by(status=status)

    total = query.count()
    items = query.order_by(CtfCheatInfo.detection_time.desc()).paginate(
        page=page, per_page=per_page
    ).items

    out = []
    for c in items:
        row = c.to_dict()
        src = User.query.get(c.source_user_id)
        tgt = User.query.get(c.target_user_id)
        row['source_user_name'] = (src.nickname or src.username) if src else f'用户#{c.source_user_id}'
        row['target_user_name'] = (tgt.nickname or tgt.username) if tgt else f'用户#{c.target_user_id}'
        row['status'] = c.status or 'pending'
        row['cheat_type'] = 'similar_flag' if (c.similarity or 0) > 0 else 'flag_origin'
        row['cheat_reason'] = f'相似度 {(c.similarity or 0) * 100:.1f}%'
        out.append(row)

    return jsonify({
        'status': 'success',
        'code': 200,
        'data': {
            'items': out,
            'total': total,
            'page': page,
            'per_page': per_page
        }
    })


def _review_cheat(record_id, new_status, default_msg):
    record = CtfCheatInfo.query.get_or_404(record_id)
    data = request.get_json(silent=True) or {}
    note = data.get('admin_note')
    if note is not None:
        record.admin_note = str(note).strip() or None
    if new_status:
        record.status = new_status
    record.reviewed_at = datetime.utcnow()
    try:
        record.reviewed_by = int(get_jwt_identity())
    except Exception:
        record.reviewed_by = None
    db.session.commit()
    return jsonify({
        'status': 'success',
        'code': 200,
        'msg': default_msg,
        'data': record.to_dict(),
    })


@ctf_admin_bp.route('/cheat-detection/<int:record_id>', methods=['GET'])
@ctf_admin_bp.route('/cheat-records/<int:record_id>', methods=['GET'])
@staff_required
def get_cheat_record(record_id):
    """获取单条作弊检测详情"""
    c = CtfCheatInfo.query.get_or_404(record_id)
    row = c.to_dict()
    src = User.query.get(c.source_user_id)
    tgt = User.query.get(c.target_user_id)
    row['source_user_name'] = (src.nickname or src.username) if src else f'用户#{c.source_user_id}'
    row['target_user_name'] = (tgt.nickname or tgt.username) if tgt else f'用户#{c.target_user_id}'
    row['status'] = c.status or 'pending'
    row['cheat_type'] = 'similar_flag' if (c.similarity or 0) > 0 else 'flag_origin'
    row['cheat_reason'] = f'相似度 {(c.similarity or 0) * 100:.1f}%'
    return jsonify({'status': 'success', 'code': 200, 'data': row})


@ctf_admin_bp.route('/cheat-records/<int:record_id>/review', methods=['POST'])
@admin_required
def review_cheat_record(record_id):
    """写入审核备注（保持/回到 pending）"""
    return _review_cheat(record_id, 'pending', '已更新审核备注')


@ctf_admin_bp.route('/cheat-records/<int:record_id>/confirm', methods=['POST'])
@admin_required
def confirm_cheat_record(record_id):
    """确认作弊"""
    return _review_cheat(record_id, 'confirmed', '已确认作弊')


@ctf_admin_bp.route('/cheat-records/<int:record_id>/dismiss', methods=['POST'])
@admin_required
def dismiss_cheat_record(record_id):
    """解除作弊标记"""
    return _review_cheat(record_id, 'dismissed', '已驳回标记')


# ==================== 首解管理 ====================

@ctf_admin_bp.route('/first-solves', methods=['GET'])
@staff_required
def list_first_solves():
    """获取首解记录"""
    game_id = request.args.get('game_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = CtfSolves.query
    
    if game_id:
        query = query.join(CtfChallenge).filter(CtfChallenge.game_id == game_id)
    
    total = query.count()
    items = query.order_by(CtfSolves.solved_at.asc()).paginate(
        page=page, per_page=per_page
    ).items

    user_ids = {f.user_id for f in items if f.user_id}
    team_ids = {f.team_id for f in items if f.team_id}
    challenge_ids = {f.challenge_id for f in items if f.challenge_id}
    users = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}
    teams = {t.id: t for t in Team.query.filter(Team.id.in_(team_ids)).all()} if team_ids else {}
    challenges = {c.id: c for c in CtfChallenge.query.filter(CtfChallenge.id.in_(challenge_ids)).all()} if challenge_ids else {}

    def serialize_first_solve(f):
        user = users.get(f.user_id)
        team = teams.get(f.team_id)
        challenge = challenges.get(f.challenge_id)
        return {
            'id': f.id,
            'challenge_id': f.challenge_id,
            'user_id': f.user_id,
            'user_name': (user.nickname or user.username) if user else None,
            'team_id': f.team_id,
            'team_name': team.name if team else None,
            'blood_level': f.blood_level,
            'solved_at': f.solved_at.isoformat(),
            'challenge_title': challenge.title if challenge else '未知',
        }

    return jsonify({
        'status': 'success',
        'data': {
            'items': [serialize_first_solve(f) for f in items],
            'total': total,
            'page': page,
            'per_page': per_page
        }
    })



@ctf_admin_bp.route('/hammer-messages', methods=['GET'])
@staff_required
def list_hammer_messages():
    """管理端聚合锤子消息（按时间倒序）"""
    game_id = request.args.get('game_id', type=int)
    challenge_id = request.args.get('challenge_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int) or 50, 200)

    query = CtfHammerMessage.query
    if game_id:
        query = query.filter_by(game_id=game_id)
    if challenge_id:
        query = query.filter_by(challenge_id=challenge_id)

    total = query.count()
    rows = query.order_by(CtfHammerMessage.created_at.desc()).paginate(
        page=page, per_page=per_page
    ).items

    challenge_ids = {r.challenge_id for r in rows}
    challenges = {
        c.id: c for c in CtfChallenge.query.filter(CtfChallenge.id.in_(challenge_ids)).all()
    } if challenge_ids else {}

    items = []
    for r in rows:
        row = r.to_dict()
        ch = challenges.get(r.challenge_id)
        row['challenge_title'] = ch.title if ch else f'题目#{r.challenge_id}'
        items.append(row)

    return jsonify({
        'status': 'success',
        'code': 200,
        'data': {'items': items, 'total': total, 'page': page, 'per_page': per_page},
    })

# ==================== 排行榜和统计（已迁 competitions/admin） ====================

@ctf_admin_bp.route('/games/<int:game_id>/stats', methods=['GET'])
@staff_required
def game_statistics(game_id):
    """410：请用 GET /api/competitions/admin/<id>/stats"""
    body = {
        'code': 410,
        'status': 'gone',
        'msg': f'Gone: use /api/competitions/admin/{game_id}/stats',
        'successor': f'/api/competitions/admin/{game_id}/stats',
    }
    resp = jsonify(body)
    resp.status_code = 410
    resp.headers['Deprecation'] = 'true'
    resp.headers['Link'] = f'</api/competitions/admin/{game_id}/stats>; rel="successor-version"'
    return resp


# ==================== 批量操作 ====================

@ctf_admin_bp.route('/challenges/batch-delete', methods=['POST'])
@admin_required
def batch_delete_challenges():
    """批量删除题目"""
    data = request.get_json() or {}
    challenge_ids = data.get('ids', [])
    CtfChallenge.query.filter(CtfChallenge.id.in_(challenge_ids)).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({'status': 'success', 'code': 200, 'message': f'已删除 {len(challenge_ids)} 道题目'})


@ctf_admin_bp.route('/cheats/batch-confirm', methods=['POST'])
@admin_required
def batch_confirm_cheats():
    """批量确认作弊"""
    data = request.get_json() or {}
    cheat_ids = data.get('ids', [])
    if not cheat_ids:
        return jsonify({'code': 400, 'msg': '未提供记录 ID'}), 400
    now = datetime.utcnow()
    reviewer = None
    try:
        reviewer = int(get_jwt_identity())
    except Exception:
        pass
    updated = CtfCheatInfo.query.filter(CtfCheatInfo.id.in_(cheat_ids)).update(
        {'status': 'confirmed', 'reviewed_at': now, 'reviewed_by': reviewer},
        synchronize_session=False,
    )
    db.session.commit()
    return jsonify({
        'status': 'success',
        'code': 200,
        'message': f'已确认 {updated} 条作弊记录',
        'msg': f'已确认 {updated} 条作弊记录',
    })


# ==================== 数据导出（已迁 competitions/admin） ====================

@ctf_admin_bp.route('/games/<int:game_id>/export-scoreboard', methods=['GET'])
@staff_required
def export_scoreboard(game_id):
    """410：请用 GET /api/competitions/admin/<id>/export-scoreboard"""
    body = {
        'code': 410,
        'status': 'gone',
        'msg': f'Gone: use /api/competitions/admin/{game_id}/export-scoreboard',
        'successor': f'/api/competitions/admin/{game_id}/export-scoreboard',
    }
    resp = jsonify(body)
    resp.status_code = 410
    resp.headers['Deprecation'] = 'true'
    resp.headers['Link'] = f'</api/competitions/admin/{game_id}/export-scoreboard>; rel="successor-version"'
    return resp


# ==================== 赛季 ====================

@ctf_admin_bp.route("/seasons", methods=["GET"])
@staff_required
def list_seasons():
    from backend.server.db_models import CtfSeason
    rows = CtfSeason.query.order_by(CtfSeason.year.desc(), CtfSeason.id.desc()).all()
    return jsonify({"code": 200, "status": "success", "data": [r.to_dict() for r in rows]})


@ctf_admin_bp.route("/seasons", methods=["POST"])
@admin_required
def create_season():
    from backend.server.db_models import CtfSeason
    data = request.get_json(silent=True) or {}
    year = data.get("year")
    season = (data.get("season") or "").strip()
    if not year or not season:
        return jsonify({"code": 400, "msg": "year 与 season 必填"}), 400
    row = CtfSeason(year=int(year), season=season, description=(data.get("description") or None))
    db.session.add(row)
    db.session.commit()
    return jsonify({"code": 200, "msg": "已创建", "data": row.to_dict()})


@ctf_admin_bp.route("/seasons/<int:season_id>", methods=["PUT"])
@admin_required
def update_season(season_id):
    from backend.server.db_models import CtfSeason
    row = CtfSeason.query.get_or_404(season_id)
    data = request.get_json(silent=True) or {}
    if "year" in data:
        row.year = int(data["year"])
    if "season" in data:
        row.season = str(data["season"]).strip()
    if "description" in data:
        row.description = data.get("description") or None
    db.session.commit()
    return jsonify({"code": 200, "msg": "已更新", "data": row.to_dict()})


@ctf_admin_bp.route("/seasons/<int:season_id>", methods=["DELETE"])
@admin_required
def delete_season(season_id):
    from backend.server.db_models import CtfSeason
    row = CtfSeason.query.get_or_404(season_id)
    db.session.delete(row)
    db.session.commit()
    return jsonify({"code": 200, "msg": "已删除"})


@ctf_admin_bp.route("/users/<int:user_id>/moderator", methods=["POST"])
@admin_required
def set_moderator(user_id):
    data = request.get_json(silent=True) or {}
    enabled = bool(data.get("is_moderator", True))
    u = User.query.get_or_404(user_id)
    u.is_moderator = enabled
    db.session.commit()
    return jsonify({"code": 200, "msg": "已更新", "data": {"id": u.id, "is_moderator": bool(u.is_moderator)}})
