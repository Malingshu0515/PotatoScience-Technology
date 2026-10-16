# -*- coding: utf-8 -*-
"""Which of the 19 keys still differ from what the translation table wants?
Prints per-locale remaining work, so a re-run can be verified as a clean no-op."""
import io
import json
import os
import sys

sys.path.insert(0, r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools")
import _rzh_ztrans2 as Z2                                        # noqa: E402

LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
data = {}
for loc in ("zh_cn", "en_us", "ja_jp", "ru_ru", "lzh"):
    data[loc] = json.load(io.open(os.path.join(LANG, loc + ".json"), encoding="utf-8"))

out = []
for loc in ("en_us", "ja_jp", "ru_ru", "lzh"):
    todo = []
    for key, per in sorted(Z2.T.items()):
        want = per.get(loc)
        if want is None:
            continue
        got = data[loc].get(key)
        if got != want:
            todo.append((key, got, want))
    out.append("%-6s 待改 %d / %d" % (loc, len(todo), len(Z2.T)))
    for key, got, want in todo:
        out.append("   %s" % key)
        out.append("     now : %s" % (u"<MISSING>" if got is None else got).replace("\n", "\\n")[:120])
        out.append("     want: %s" % want.replace("\n", "\\n")[:120])
    out.append("")

out.append("=== zh_cn 有没有被我碰过（用户要求不许改）===")
import subprocess
rel = "src/main/resources/assets/potato_s_t/lang/zh_cn.json"
d = subprocess.run([r"C:\Program Files\Git\cmd\git.exe", "diff", "--numstat", "--", rel],
                   cwd=r"E:\PotatoST\PotatoSTneoforge1.21.1", capture_output=True).stdout.decode().strip()
out.append("git diff --numstat zh_cn: %s" % (d or "(empty)"))
out.append("→ 用户自己的 19 处改动应当仍然是 19 增 19 删")

io.open(r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools\_rzh_todo2.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("ok")
