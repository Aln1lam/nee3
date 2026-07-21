# -*- coding: utf-8 -*-
from pathlib import Path
import re

SRC = Path(__file__).resolve().parent / "src" / "components"
for name, eyebrow in [
    ("ForgotPassword.vue", "找回密码 · AUTH"),
    ("ResetPassword.vue", "重置密码 · AUTH"),
    ("VerifyEmail.vue", "邮箱验证 · AUTH"),
]:
    p = SRC / name
    text = p.read_text(encoding="utf-8")
    text2, n = re.subn(
        r"[ \t]*<LinuxPrompt\b[^>]*/?>\s*",
        f'          <p class="matrix-page-prompt">{eyebrow}</p>\n',
        text,
        count=1,
    )
    if not n:
        print("fail", name)
        continue
    text2 = text2.replace("import { LinuxPrompt } from '@/components/shared'\n", "")
    text2 = text2.replace("components: { LinuxPrompt },", "components: {},")
    text2 = text2.replace("components: { LinuxPrompt, NSpin },", "components: { NSpin },")
    p.write_text(text2, encoding="utf-8", newline="\n")
    print("ok", name)
