"""日志与 API 响应中的 Flag 脱敏。"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional


_FLAG_BRACE = re.compile(r"flag\{[^}]{0,512}\}", re.IGNORECASE)
_FLAG_ENV = re.compile(r"(FLAG\s*=\s*)([^\s|;]+)", re.IGNORECASE)


def redact_flag_text(text: Optional[str]) -> str:
    if not text:
        return ""
    out = _FLAG_BRACE.sub("flag{[REDACTED]}", str(text))
    out = _FLAG_ENV.sub(r"\1[REDACTED]", out)
    return out


def sanitize_submission_dict(
    data: Dict[str, Any],
    *,
    include_answer: bool = False,
    include_client_ip: bool = False,
) -> Dict[str, Any]:
    """提交记录对外序列化：默认去掉 answer / client_ip。"""
    if not data:
        return data
    out = dict(data)
    if not include_answer:
        out.pop("answer", None)
        out.pop("flag", None)
    if not include_client_ip:
        out.pop("client_ip", None)
    out.pop("correct_dedupe_key", None)
    return out


def sanitize_log_lines(lines: list[str]) -> list[str]:
    return [redact_flag_text(line) for line in lines]
