# -*- coding: utf-8 -*-
r"""_zf104_retarget4.py —— 定形配方 **42 → 43**（并行任务加了「稳定金属块」那张图纸）

这是本轮**第二次**跟"活体数字"：键数 335→349→**350**、定形配方 42→**43**。
两次都是并行的另一条任务在动同一棵树（先加盔甲键、再加硬质钛合金与稳定金属块配方）。

§4.36 的口径照旧：**改锚点，绝不放宽断言**（仍然写死数字）。

改哪些：
  · `EXPECT_SHAPED = 42` → 43（6 份）
  · `craft == 42` / `shaped == 42` 这类内联断言 → 43
  · 期望文件清单里补上 `stable_metal_block.json`（3 份）
"""
import io
import os
import py_compile
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ZT = r"E:\PotatoST\build\zftools"
fails = []

RULES = {
    "_zf95_verify.py": [(u"EXPECT_SHAPED = 42", u"EXPECT_SHAPED = 43", 1)],
    "_zf96_verify.py": [(u"EXPECT_SHAPED = 42", u"EXPECT_SHAPED = 43", 1)],
    "_zf97_verify.py": [(u"EXPECT_SHAPED = 42", u"EXPECT_SHAPED = 43", 1)],
    "_zf100_verify.py": [(u"EXPECT_SHAPED = 42", u"EXPECT_SHAPED = 43", 1)],
    "_zf101_verify.py": [(u"EXPECT_SHAPED = 42", u"EXPECT_SHAPED = 43", 1)],
    "_zf102_verify.py": [(u"EXPECT_SHAPED = 42", u"EXPECT_SHAPED = 43", 1)],
    "_zf71_verify.py": [(u"check(craft == 42,", u"check(craft == 43,", 1)],
    "_zf100_recipe_guard.py": [(u"shaped == 42)", u"shaped == 43)", 1)],
    "_zf100_recipe_guard.py$2": [(u"改前 38 + ZF100 三件 + ZF101 一件",
                                  u"改前 38 + ZF100 三件 + ZF101 一件 + ZF104 一件（稳定金属块）", 1)],
}
# 期望文件清单：补 stable_metal_block.json
LIST_RULES = [
    (u"'music_disc_jasmine_flower.json']",
     u"'music_disc_jasmine_flower.json', 'stable_metal_block.json']"),
    (u'"music_disc_jasmine_flower.json"]',
     u'"music_disc_jasmine_flower.json", "stable_metal_block.json"]'),
]


def apply(name, rules, label):
    path = os.path.join(ZT, name)
    if not os.path.isfile(path):
        fails.append(u"%s 不存在" % name)
        return
    text = io.open(path, encoding="utf-8").read()
    orig = text
    changed = 0
    for old, new, expect in rules:
        hits = text.count(old)
        if hits != expect:
            fails.append(u"%s：锚点 %r 命中 %d（应为 %d）" % (label, old[:40], hits, expect))
            continue
        text = text.replace(old, new)
        changed += hits
    if text == orig:
        print(u"  [--]   %-26s 无需改动" % label)
        return
    io.open(path, "w", encoding="utf-8", newline=u"").write(text)
    try:
        py_compile.compile(path, doraise=True)
    except Exception as exc:
        fails.append(u"%s：py_compile 失败 %s" % (label, exc))
        io.open(path, "w", encoding="utf-8", newline=u"").write(orig)
        return
    print(u"  [OK]   %-26s 改 %d 处" % (label, changed))


def main():
    print(u"================ 定形配方 42 → 43 ================")
    for key, rules in RULES.items():
        name = key.split(u"$")[0]
        apply(name, rules, name + (u" (含说明)" if u"$" in key else u""))

    print(u"")
    print(u"================ 期望文件清单补 stable_metal_block.json ================")
    for name in sorted(os.listdir(ZT)):
        if not (name.endswith(".py") and name.startswith("_zf") and u"verify" in name):
            continue
        path = os.path.join(ZT, name)
        text = io.open(path, encoding="utf-8").read()
        if u"stable_metal_block.json" in text:
            continue
        rules = [(old, new, text.count(old)) for old, new in LIST_RULES if text.count(old) >= 1]
        if rules:
            apply(name, rules, name + u" (清单)")

    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
