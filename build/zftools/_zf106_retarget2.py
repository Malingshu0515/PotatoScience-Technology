# -*- coding: utf-8 -*-
r"""_zf106_retarget2.py —— 定形配方总数锚点 **43 → 51**（本轮新增 8 张盔甲图纸）

§4.36 口径：改锚点，不放宽断言。
⚠ 上两轮我按"每份 1 处 / 2 处"分两批改，返工过两次 —— 这一遍统一"全替换 + 个数核对"。
"""
import io
import os
import py_compile
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ZT = r"E:\PotatoST\build\zftools"
OLD, NEW = u"43", u"51"
fails = []

# 只改"配方条数"这一个语义位置，所以逐个文件给出精确锚点（避免误伤别的 43）
RULES = [
    ("_zf71_verify.py", u"check(craft == 43,", u"check(craft == 51,"),
    ("_zf100_verify.py", u"EXPECT_SHAPED = 43", u"EXPECT_SHAPED = 51"),
    ("_zf101_verify.py", u"EXPECT_SHAPED = 43", u"EXPECT_SHAPED = 51"),
    ("_zf102_verify.py", u"EXPECT_SHAPED = 43", u"EXPECT_SHAPED = 51"),
    ("_zf95_verify.py", u"EXPECT_SHAPED = 43", u"EXPECT_SHAPED = 51"),
    ("_zf96_verify.py", u"EXPECT_SHAPED = 43", u"EXPECT_SHAPED = 51"),
    ("_zf97_verify.py", u"EXPECT_SHAPED = 43", u"EXPECT_SHAPED = 51"),
    ("_zf100_recipe_guard.py", u"shaped == 43)", u"shaped == 51)"),
    ("_zf100_recipe_guard.py", u"ZF104 一件（稳定金属块）", u"ZF104 一件（稳定金属块）+ ZF106 八件（两套盔甲）"),
]


def main():
    print(u"================ 定形配方 %s → %s ================" % (OLD, NEW))
    by_file = {}
    for name, old, new in RULES:
        by_file.setdefault(name, []).append((old, new))
    for name, rules in sorted(by_file.items()):
        path = os.path.join(ZT, name)
        if not os.path.isfile(path):
            fails.append(u"%s 不存在" % name)
            continue
        text = io.open(path, encoding="utf-8").read()
        orig = text
        changed = 0
        for old, new in rules:
            hits = text.count(old)
            if hits != 1:
                fails.append(u"%s：锚点 %r 命中 %d 次（应为 1）" % (name, old[:44], hits))
                continue
            text = text.replace(old, new)
            changed += hits
        if text == orig:
            print(u"  [--]   %-24s 无改动" % name)
            continue
        io.open(path, "w", encoding="utf-8", newline=u"").write(text)
        try:
            py_compile.compile(path, doraise=True)
        except Exception as exc:
            fails.append(u"%s：py_compile 失败 %s" % (name, exc))
            io.open(path, "w", encoding="utf-8", newline=u"").write(orig)
            print(u"  [FAIL] %-24s 已回滚" % name)
            continue
        print(u"  [OK]   %-24s 改 %d 处" % (name, changed))

    print(u"")
    print(u"================ 复查：活体脚本里还有没有写死 43 的配方断言 ================")
    left = []
    for name in sorted(os.listdir(ZT)):
        if not (name.endswith(u".py") and name.startswith(u"_zf")):
            continue
        if u"retarget" in name:
            continue
        t = io.open(os.path.join(ZT, name), encoding="utf-8").read()
        if re.search(r"(?<![0-9])43(?![0-9])", t) and (u"SHAPED" in t or u"craft" in t or u"shaped" in t):
            left.append(name)
    if left:
        print(u"  [WARN] 仍是 43 且带配方语境的：%s（人工确认是否还有语义位置）" % left)
    else:
        print(u"  [OK]   活体脚本里已无 43 的配方断言")

    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
