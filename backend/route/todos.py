from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.server.extensions import db
from backend.server.db_models import Todo, User
from backend.server.audit_log import log_create, log_view, log_update, log_delete

bp = Blueprint("todos", __name__, url_prefix="/api/todos")


@bp.route("", methods=["GET"])
@jwt_required()
def get_todos():
    """Get all todos for current user."""
    user_id = int(get_jwt_identity())
    todos = Todo.query.filter_by(user_id=user_id).order_by(Todo.created_at.desc()).all()
    try:
        log_view('todo', None, 'todo_list', meta={'count': len(todos)})
    except Exception:
        pass
    return jsonify([t.to_dict() for t in todos])


@bp.route("", methods=["POST"])
@jwt_required()
def create_todo():
    """Create a new todo."""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    text = data.get("text", "").strip()
    
    if not text:
        return jsonify({"error": "待办内容不能为空"}), 400
    
    todo = Todo(user_id=user_id, text=text, done=False)
    db.session.add(todo)
    db.session.commit()
    try:
        log_create('todo', todo.id, todo.text)
    except Exception:
        pass
    
    return jsonify(todo.to_dict()), 201


@bp.route("/<int:todo_id>", methods=["PATCH"])
@jwt_required()
def update_todo(todo_id):
    """Update todo (toggle done status or edit text)."""
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    if not todo:
        return jsonify({"error": "待办不存在"}), 404
    
    data = request.get_json()
    
    if "done" in data:
        todo.done = bool(data["done"])
    
    if "text" in data:
        text = data["text"].strip()
        if text:
            todo.text = text
    
    db.session.commit()
    try:
        log_update('todo', todo.id, todo.text)
    except Exception:
        pass
    return jsonify(todo.to_dict())


@bp.route("/<int:todo_id>", methods=["DELETE"])
@jwt_required()
def delete_todo(todo_id):
    """Delete a todo."""
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    if not todo:
        return jsonify({"error": "待办不存在"}), 404
    
    db.session.delete(todo)
    db.session.commit()
    try:
        log_delete('todo', todo.id, todo.text)
    except Exception:
        pass

    return jsonify({"success": True})
