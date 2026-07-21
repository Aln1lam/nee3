# -*- coding: utf-8 -*-
from pathlib import Path

for name in ("ForgotPassword.vue", "ResetPassword.vue", "VerifyEmail.vue"):
    p = Path(__file__).resolve().parent / "src" / "components" / name
    t = p.read_text(encoding="utf-8")
    t2 = t.replace("<h1 class=\"auth-aux-title\">", "          <h1 class=\"auth-aux-title\">")
    # avoid double indent
    t2 = t2.replace("                    <h1", "          <h1")
    if t2 != t:
        p.write_text(t2, encoding="utf-8", newline="\n")
        print("fixed", name)
    else:
        print("skip", name)
