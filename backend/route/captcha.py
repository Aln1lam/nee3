"""
图形验证码 API — 登录/注册使用
"""

import random
import string
import uuid

from flask import Blueprint, jsonify, make_response, request
from PIL import Image, ImageDraw

from backend.middleware_refactored import rate_limit
from backend.services.captcha_store import store_captcha, pop_captcha

bp = Blueprint("captcha", __name__, url_prefix="/api/captcha")

_TTL = 300


def _gen_code(length=4):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def _render_image(code):
    w, h = 120, 40
    img = Image.new("RGB", (w, h), (240, 245, 250))
    draw = ImageDraw.Draw(img)
    for _ in range(6):
        draw.line(
            (
                random.randint(0, w),
                random.randint(0, h),
                random.randint(0, w),
                random.randint(0, h),
            ),
            fill=(0, 120, 214, 80),
            width=1,
        )
    for i, ch in enumerate(code):
        x = 12 + i * 24 + random.randint(-2, 2)
        y = random.randint(6, 12)
        draw.text((x, y), ch, fill=(0, 80, 160))
    from io import BytesIO
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def verify_captcha(captcha_id, answer):
    """校验验证码，成功返回 True 并消费 token"""
    if not captcha_id or not answer:
        return False
    entry = pop_captcha(captcha_id)
    if not entry:
        return False
    return entry["code"] == str(answer).strip().upper()


@bp.route("/", methods=["GET"])
@rate_limit(max_requests=30, window_seconds=60, error_message="验证码请求过于频繁")
def get_captcha():
    code = _gen_code()
    captcha_id = str(uuid.uuid4())
    store_captcha(captcha_id, code, ttl=_TTL)
    buf = _render_image(code)
    resp = make_response(buf.read())
    resp.headers["Content-Type"] = "image/png"
    resp.headers["X-Captcha-Id"] = captcha_id
    resp.headers["Access-Control-Expose-Headers"] = "X-Captcha-Id"
    resp.headers["Cache-Control"] = "no-store"
    return resp


@bp.route("/verify", methods=["POST"])
@rate_limit(max_requests=20, window_seconds=60, error_message="验证码校验过于频繁")
def verify():
    data = request.get_json() or {}
    ok = verify_captcha(data.get("captcha_id"), data.get("captcha_answer"))
    return jsonify({"valid": ok})
