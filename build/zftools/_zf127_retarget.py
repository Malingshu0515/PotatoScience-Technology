# -*- coding: utf-8 -*-
u"""_zf127_retarget.py —— 活体数字跟平：四语言键数 **476 → 478**（ZF127 银线 +2 键）

口径照 `_zf125_retarget2.py`（那一轮的教训写在它的 docstring 里）：

  · **不再靠手捞**：逐份给出"预期命中次数"（用 Python 精确数出来的），
    命中次数对不上就**停手不改那一份** —— 断言不匹配时最可能是我数错了；
  · 只动 `*_verify.py` / `*_guard.py` / `*_repro.py` / `*_audit.py` 这些**常驻门**；
  · `_zf125_falsify.py` / `_zf126_falsify.py` 里那一处 476 是**历史刀的记录**，不许改
    （改了就是伪造历史）；
  · 改完做残留体检：盘上常驻门里不该再有裸的 `476`。

⚠ 本轮 +2 键的来源：`item.potato_s_t.silver_wire`（银线）与 `item.potato_s_t.silver_wire_spool`
  （银线轴）—— 两个物品各一个名字，四份语言同步加（§4.64 那条"键数是活体数字"）。

跑法：
    python build\\zftools\\_zf127_retarget.py
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ZT = r"E:\PotatoST\build\zftools"
OLD, NEW = u"476", u"478"

# 逐份的预期命中次数（Python 精确数出来的，见本轮 `_zf127_peek476.txt`）
FILES = {
    u"_zf71_verify.py": 2,
    u"_zf73_verify.py": 2,
    u"_zf75_verify.py": 2,
    u"_zf78_verify.py": 2,
    u"_zf79_verify.py": 2,
    u"_zf80_verify.py": 1,
    u"_zf81_verify.py": 2,
    u"_zf82_verify.py": 2,
    u"_zf93_verify.py": 1,
    u"_zf96_verify.py": 1,
    u"_zf97_verify.py": 1,
    u"_zf98_verify.py": 1,
    u"_zf100_verify.py": 1,
    u"_zf101_verify.py": 1,
    u"_zf102_verify.py": 1,
    u"_zf103_verify.py": 2,
    u"_zf107_verify.py": 1,
    u"_zf109_verify.py": 3,
    u"_zf111_verify.py": 1,
    u"_zf112_verify.py": 5,
    u"_zf114_verify.py": 1,
    u"_zf117_verify.py": 6,
    u"_zf118_verify.py": 2,
    u"_zf119_verify.py": 4,
    u"_zf122_verify.py": 1,
    u"_zf125_verify.py": 10,
    u"_zf126_verify.py": 3,
}

# 历史记录，不许动（改了就是伪造历史）
EXEMPT = (u"_zf125_falsify.py", u"_zf126_falsify.py")

notes, fails = [], []


def count(text, num):
    return len(re.findall(r"\b%s\b" % num, text))


def sweep(name, times):
    path = os.path.join(ZT, name)
    if not os.path.exists(path):
        fails.append(u"%s 不在盘上" % name)
        return
    text = io.open(path, encoding="utf-8", newline=u"").read()
    n_old, n_new = count(text, OLD), count(text, NEW)
    if n_old == 0 and n_new >= times:
        notes.append(u"%s：已经是 %s（%d 处）" % (name, NEW, n_new))
        return
    if n_old != times:
        fails.append(u"%s：%s 命中 %d 次（预期 %d）—— 停手" % (name, OLD, n_old, times))
        return
    io.open(path, "w", encoding="utf-8", newline=u"").write(re.sub(r"\b%s\b" % OLD, NEW, text))
    back = io.open(path, encoding="utf-8", newline=u"").read()
    if count(back, OLD):
        fails.append(u"%s：改完还残留 %s" % (name, OLD))
        return
    try:
        compile(back, name, u"exec")      # 语法自检（§4.99：批量改盘之后要自证没改坏）
    except SyntaxError as e:
        fails.append(u"%s：改完语法不过（%s）" % (name, e))
        return
    notes.append(u"%s：%d 处 %s → %s" % (name, times, OLD, NEW))


def main():
    for name in sorted(FILES):
        sweep(name, FILES[name])

    left = []
    for fn in sorted(os.listdir(ZT)):
        if fn in EXEMPT or not fn.endswith(u".py"):
            continue
        if not any(k in fn for k in (u"_verify", u"_guard", u"_repro", u"_audit")):
            continue
        if count(io.open(os.path.join(ZT, fn), encoding="utf-8").read(), OLD):
            left.append(fn)
    if left:
        fails.append(u"这些常驻门里还有裸的 476：%s" % u"、".join(left))
    else:
        notes.append(u"残留体检：常驻门里再没有裸的 476（豁免 %d 份历史刀）" % len(EXEMPT))

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改了 %d 份" % len([n for n in notes if NEW in n and OLD in n]))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
