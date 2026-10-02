# -*- coding: utf-8 -*-
"""_zf134_patchapply.py —— 把 `mainCoord` 从第 1 刀的禁令里挪走（留给第 2 刀处理）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf134_apply.py"

OLD = '''    code = strip_comments(s)
    for dead in ("alongX", "mainCoord", "int main =", "wave.sign"):
        assert dead not in code, "代码里还残留：%s（%d 次）" % (dead, code.count(dead))'''

NEW = '''    code = strip_comments(s)
    # ⚠ 残留的 mainCoord 方法体 + 旧类收尾的 } 由 _zf134_apply2.py 吃掉（见那个脚本的注释）。
    #   这一刀只保证"这一刀该管的"都干净，跨刀的尾巴交给下一刀 —— 否则一刀永远过不去。
    for dead in ("alongX", "int main =", "wave.sign"):
        assert dead not in code, "代码里还残留：%s（%d 次）" % (dead, code.count(dead))'''

s = io.open(P, encoding="utf-8").read()
n = s.count(OLD)
assert n == 1, "锚点 %d 次" % n
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(OLD, NEW, 1))
print("[OK] 已调整第 1 刀的禁令")
