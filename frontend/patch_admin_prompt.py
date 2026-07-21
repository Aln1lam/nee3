# -*- coding: utf-8 -*-
from pathlib import Path
import re

p = Path(__file__).resolve().parent / "src" / "components" / "AdminPanel.vue"
t = p.read_text(encoding="utf-8")
t2, n = re.subn(
    r"<LinuxPrompt[\s\S]*?extra-class=\"matrix-page-prompt\"\s*/>",
    '<p class="matrix-page-prompt">运维中心 · ADMIN</p>',
    t,
    count=1,
)
if n:
    # drop unused import if no longer used
    if "<LinuxPrompt" not in t2:
        t2 = t2.replace("import { LinuxPrompt } from '@/components/shared'\n", "")
        t2 = t2.replace("  components: { LinuxPrompt },\n", "  components: {},\n")
    p.write_text(t2, encoding="utf-8", newline="\n")
    print("ok")
else:
    print("skip")
