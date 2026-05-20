"""
CTF 管理员接口
- 题目管理（含附件上传）
- 作弊检测管理
- 竞赛管理
- 首解记录
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
import os
import mimetypes

from backend.server.db_models import (
    db, CtfGame, CtfChallenge, CtfChallengeSubmission, CtfCheatInfo,
    CtfSolves, User, CtfDivision, FileResource, CtfGameInstance
)
from backend.services.scoring_service import (
    ScoringService, CheatDetectionService, PermissionService,
    FlagValidationService, FlagTemplateService
)

ctf_admin_bp = Blueprint('ctf_admin', __name__, url_prefix='/api/admin')

# 初始化服务
scoring_service = ScoringService()
cheat_service = CheatDetectionService()
permission_service = PermissionService()
flag_service = FlagValidationService()
flag_template_service = FlagTemplateService()

# 管理员权限检查
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import g
        if not hasattr(g, 'user') or not g.user.is_admin:
            return {'status': 'error', 'message': '需要管理员权限'}, 403
        return f(*args, **kwargs)
    return decorated_function

# ==================== 竞赛管理 ====================

@ctf_admin_bp.route('/games', methods=['GET'])
@admin_required
def list_games():
    """获取所有竞赛列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = CtfGame.query
    total = query.count()
    items = query.paginate(page=page, per_page=per_page).items
    
    return jsonify({
        'status': 'success',
        'data': {
            'items': [{
                'id': g.id,
                'title': g.title,
                'start_time': g.start_time.isoformat(),
                'end_time': g.end_time.isoformat(),
                'is_public': g.is_public,
                'participation_count': CtfGameInstance.query.filter_by(game_id=g.id).count(),
                'challenge_count': CtfChallenge.query.filter_by(game_id=g.id).count()
            } for g in items],
            'total': total,
            'page': page,
            'per_page': per_page
        }
    })

@ctf_admin_bp.route('/games', methods=['POST'])
@admin_required
def create_game():
    """创建新竞赛"""
    data = request.get_json()
    
    game = CtfGame(
        title=data.get('title'),
        start_time=datetime.fromisoformat(data.get('start_time')),
        end_time=datetime.fromisoformat(data.get('end_time')),
        is_public=data.get('is_public', False),
        description=data.get('description', '')
    )
    
    db.session.add(game)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '竞赛已创建',
        'data': {'id': game.id}
    }), 201

@ctf_admin_bp.route('/games/<int:game_id>', methods=['PUT'])
@admin_required
def update_game(game_id):
    """更新竞赛信息"""
    game = CtfGame.query.get_or_404(game_id)
    data = request.get_json()
    
    if 'title' in data:
        game.title = data['title']
    if 'start_time' in data:
        game.start_time = datetime.fromisoformat(data['start_time'])
    if 'end_time' in data:
        game.end_time = datetime.fromisoformat(data['end_time'])
    if 'is_public' in data:
        game.is_public = data['is_public']
    if 'description' in data:
        game.description = data['description']
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '竞赛已更新'
    })

@ctf_admin_bp.route('/games/<int:game_id>', methods=['DELETE'])
@admin_required
def delete_game(game_id):
    """删除竞赛"""
    game = CtfGame.query.get_or_404(game_id)
    db.session.delete(game)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '竞赛已删除'
    })

@ctf_admin_bp.route('/games/<int:game_id>/archive', methods=['POST'])
@admin_required
def archive_game(game_id):
    """归档竞赛"""
    from datetime import datetime
    game = CtfGame.query.get_or_404(game_id)
    
    if game.archived_at is not None:
        return jsonify({
            'status': 'error',
            'msg': '该竞赛已经是归档状态'
        }), 400
    
    game.archived_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'msg': '竞赛已归档'
    })

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
    for field in ['title', 'category', 'description', 'flag']:
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
    file.save(filepath)
    
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
@admin_required
def list_cheat_records():
    """获取作弊检测记录"""
    game_id = request.args.get('game_id', type=int)
    status = request.args.get('status', 'pending')  # pending, reviewed, confirmed, dismissed
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = CtfCheatInfo.query
    
    if game_id:
        # 需要通过提交来关联竞赛
        query = query.join(CtfChallengeSubmission).join(CtfChallenge).filter(
            CtfChallenge.game_id == game_id
        )
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    total = query.count()
    items = query.order_by(CtfCheatInfo.detection_time.desc()).paginate(
        page=page, per_page=per_page
    ).items
    
    return jsonify({
        'status': 'success',
        'data': {
            'items': [{
                'id': c.id,
                'source_user_id': c.source_user_id,
                'target_user_id': c.target_user_id,
                'submission_id': c.submission_id,
                'similarity': c.similarity,
                'detection_time': c.detection_time.isoformat(),
                'status': c.status,
                'notes': c.notes
            } for c in items],
            'total': total,
            'page': page,
            'per_page': per_page
        }
    })

@ctf_admin_bp.route('/cheat-records/<int:record_id>/review', methods=['POST'])
@admin_required
def review_cheat_record(record_id):
    """人工审核作弊记录"""
    record = CtfCheatInfo.query.get_or_404(record_id)
    record.status = 'reviewed'
    record.notes = request.json.get('notes', record.notes)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '已标记为待审核'
    })

@ctf_admin_bp.route('/cheat-records/<int:record_id>/confirm', methods=['POST'])
@admin_required
def confirm_cheat_record(record_id):
    """确认作弊"""
    record = CtfCheatInfo.query.get_or_404(record_id)
    record.status = 'confirmed'
    db.session.commit()
    
    # 这里可以添加对作弊用户的处理，如禁赛等
    # TODO: 实现用户处罚逻辑
    
    return jsonify({
        'status': 'success',
        'message': '已确认作弊'
    })

@ctf_admin_bp.route('/cheat-records/<int:record_id>/dismiss', methods=['POST'])
@admin_required
def dismiss_cheat_record(record_id):
    """解除作弊标记"""
    record = CtfCheatInfo.query.get_or_404(record_id)
    record.status = 'dismissed'
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '已解除标记'
    })

# ==================== 首解管理 ====================

@ctf_admin_bp.route('/first-solves', methods=['GET'])
@admin_required
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
    
    return jsonify({
        'status': 'success',
        'data': {
            'items': [{
                'id': f.id,
                'challenge_id': f.challenge_id,
                'user_id': f.user_id,
                'blood_level': f.blood_level,
                'solved_at': f.solved_at.isoformat(),
                'challenge_title': CtfChallenge.query.get(f.challenge_id).title if f.challenge_id else '未知'
            } for f in items],
            'total': total,
            'page': page,
            'per_page': per_page
        }
    })

# ==================== 排行榜和统计 ====================

@ctf_admin_bp.route('/games/<int:game_id>/stats', methods=['GET'])
@admin_required
def game_statistics(game_id):
    """获取竞赛统计信息"""
    game = CtfGame.query.get_or_404(game_id)
    
    # 参赛队伍数
    participation_count = CtfGameInstance.query.filter_by(game_id=game_id).count()
    
    # 题目数
    challenge_count = CtfChallenge.query.filter_by(game_id=game_id).count()
    
    # 总提交数
    total_submissions = CtfChallengeSubmission.query.filter(
        CtfChallengeSubmission.challenge_id.in_(
            db.session.query(CtfChallenge.id).filter_by(game_id=game_id)
        )
    ).count()
    
    # 正确提交数
    correct_submissions = CtfChallengeSubmission.query.filter(
        CtfChallengeSubmission.challenge_id.in_(
            db.session.query(CtfChallenge.id).filter_by(game_id=game_id)
        ),
        CtfChallengeSubmission.status == 'correct'
    ).count()
    
    # 作弊记录数
    cheat_count = CtfCheatInfo.query.filter(
        CtfCheatInfo.submission_id.in_(
            db.session.query(CtfChallengeSubmission.id).filter(
                CtfChallengeSubmission.challenge_id.in_(
                    db.session.query(CtfChallenge.id).filter_by(game_id=game_id)
                )
            )
        ),
        CtfCheatInfo.status == 'confirmed'
    ).count()
    
    return jsonify({
        'status': 'success',
        'data': {
            'game': {
                'id': game.id,
                'title': game.title,
                'start_time': game.start_time.isoformat(),
                'end_time': game.end_time.isoformat()
            },
            'statistics': {
                'participation_count': participation_count,
                'challenge_count': challenge_count,
                'total_submissions': total_submissions,
                'correct_submissions': correct_submissions,
                'cheat_count': cheat_count,
                'correct_rate': (correct_submissions / total_submissions * 100) if total_submissions > 0 else 0
            }
        }
    })

# ==================== 批量操作 ====================

@ctf_admin_bp.route('/challenges/batch-delete', methods=['POST'])
@admin_required
def batch_delete_challenges():
    """批量删除题目"""
    data = request.get_json()
    challenge_ids = data.get('ids', [])
    
    CtfChallenge.query.filter(CtfChallenge.id.in_(challenge_ids)).delete()
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'已删除 {len(challenge_ids)} 道题目'
    })

@ctf_admin_bp.route('/cheats/batch-confirm', methods=['POST'])
@admin_required
def batch_confirm_cheats():
    """批量确认作弊"""
    data = request.get_json()
    cheat_ids = data.get('ids', [])
    
    CtfCheatInfo.query.filter(CtfCheatInfo.id.in_(cheat_ids)).update({'status': 'confirmed'})
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'已确认 {len(cheat_ids)} 条作弊记录'
    })

# ==================== 数据导出 ====================

@ctf_admin_bp.route('/games/<int:game_id>/export-scoreboard', methods=['GET'])
@admin_required
def export_scoreboard(game_id):
    """导出排行榜数据"""
    import csv
    from io import StringIO
    
    # 获取排行榜数据
    # TODO: 使用 ScoringService 获取实际排行榜
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['排名', '用户ID', '总分', '解题数', '最后提交时间'])
    
    # 写入数据行
    # ...
    
    return output.getvalue(), 200, {
        'Content-Disposition': f'attachment; filename="scoreboard_{game_id}.csv"',
        'Content-Type': 'text/csv'
    }

if __name__ == '__main__':
    pass
