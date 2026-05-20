from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import secrets

from backend.server import extensions
from backend.server.db_models import User, ApiToken

bp = Blueprint("tokens", __name__)


def require_admin():
    uid = get_jwt_identity()
    if not uid:
        return None
    user = User.query.get(int(uid))
    return user if user and user.is_admin else None


@bp.post("/")
@jwt_required()
def create_token():
    user = require_admin()
    if not user:
        return {"msg": "admin required"}, 403

    data = request.get_json() or {}
    name = data.get("name") or "api-token"
    expires_in = data.get("expires_in")

    token_value = secrets.token_urlsafe(32)
    token = ApiToken(name=name, token=token_value, creator_id=user.id, created_at=datetime.utcnow())
    if isinstance(expires_in, int) and expires_in > 0:
        token.expires_at = token.created_at + timedelta(days=expires_in)

    extensions.db.session.add(token)
    extensions.db.session.commit()

    return {"token": token_value, "id": token.id}


@bp.get("/")
@jwt_required()
def list_tokens():
    user = require_admin()
    if not user:
        return {"msg": "admin required"}, 403

    tokens = ApiToken.query.all()
    items = [
        {
            "id": t.id,
            "name": t.name,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "expires_at": t.expires_at.isoformat() if t.expires_at else None,
            "creator_id": t.creator_id,
            "revoked": t.revoked,
        }
        for t in tokens
    ]
    return {"items": items}


@bp.post("/<string:tid>/restore")
@jwt_required()
def restore_token(tid):
    user = require_admin()
    if not user:
        return {"msg": "admin required"}, 403

    token = ApiToken.query.get(tid)
    if not token:
        return {"msg": "not found"}, 404

    token.revoked = False
    extensions.db.session.commit()
    return {"msg": "restored"}


@bp.delete("/<string:tid>")
@jwt_required()
def revoke_or_delete_token(tid):
    user = require_admin()
    if not user:
        return {"msg": "admin required"}, 403

    delete = request.args.get("delete", "false").lower() == "true"
    token = ApiToken.query.get(tid)
    if not token:
        return {"msg": "not found"}, 404

    if delete:
        extensions.db.session.delete(token)
    else:
        token.revoked = True

    extensions.db.session.commit()
    return {"msg": "ok"}
