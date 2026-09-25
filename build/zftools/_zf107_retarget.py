# -*- coding: utf-8 -*-
u"""_zf107_retarget.py —— ZF107：把往轮校验器里的"活体数字"从 350 键改到 398 键

规则（§4.53 + ZF100 那次的教训）：
  · **写前重读**：每一份都在"要写的那一刻"重新从盘上读一遍，绝不用计划阶段的缓存文本；
  · 每条替换都用正则、要求**正好命中 1 次**，命中 0 次或 ≥2 次就报错退出（不猜）；
  · 写前把改完的文本 `compile()` 一遍，语法不过就不落盘；
  · 只改"键数"这一件事，别的一律不动。

另外补账：ZF107 的改前件（`zf107_pre`）当初漏抄了 5 份本轮也要改的校验器
（`_zf81/_zf82/_zf93/_zf96/_zf98_verify.py`）—— 本脚本在**动它们之前**先补抄进备份，
并写 `_补说明.txt` 记下来（照 ZF100 的先例）。
"""
import hashlib
import io
import os
import re
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, r"build\zftools")
BK = r"C:\PotatoST救援\zf107_pre\build\zftools"

OLD, NEW = u"350", u"398"
NOTE = u"… + ZF107 成就 48 键"

# (文件, [(正则, 替换文本, 说明), …])
PLAN = [
    (u"_zf71_verify.py", [
        (r"set\(keys\.values\(\)\) == \{350\}", u"set(keys.values()) == {398}", u"集合里的旧键数"),
        (r'u"350 keys each"', u'u"398 keys each"', u"英文公告里的键数串"),
    ]),
    (u"_zf73_verify.py", [
        (r'u"B11 四语言各 350 键[^"]*"', u'u"B11 四语言各 398 键（… + ZF107 成就 48）"', u"标题文案"),
        (r"all\(v == 350 for v in counts\.values\(\)\)", u"all(v == 398 for v in counts.values())", u"断言值"),
    ]),
    (u"_zf75_verify.py", [
        (r'u"C2 四语言各 350 键[^"]*"', u'u"C2 四语言各 398 键（ZF104 起；ZF107 +48）"', u"标题文案"),
        (r"all\(v == 350 for v in counts\.values\(\)\)", u"all(v == 398 for v in counts.values())", u"断言值"),
    ]),
    (u"_zf78_verify.py", [
        (r'u"四份语言键数一致且 = 350[^"]*"', u'u"四份语言键数一致且 = 398（ZF107 成就 +48）"', u"标题文案"),
        (r"list\(counts\.values\(\)\)\[0\] == 350", u"list(counts.values())[0] == 398", u"断言值"),
    ]),
    (u"_zf79_verify.py", [
        (r'u"四份语言键数一致且 = 350[^"]*"', u'u"四份语言键数一致且 = 398（ZF107 成就 +48）"', u"标题文案"),
        (r"list\(counts\.values\(\)\)\[0\] == 350", u"list(counts.values())[0] == 398", u"断言值"),
    ]),
    (u"_zf80_verify.py", [(r"EXPECT_KEYS = 350[^\n]*", u"EXPECT_KEYS = 398           # " + NOTE, u"常量")]),
    (u"_zf81_verify.py", [(r'u"语言键数（ZF104 起 350）", 350,',
                           u'u"语言键数（ZF107 起 398）", 398,', u"标题 + 断言")]),
    (u"_zf82_verify.py", [
        (r"EXPECT_KEYS = 350[^\n]*", u"EXPECT_KEYS = 398           # " + NOTE, u"常量"),
        (r'and u"350 keys each" in ann\)', u'and u"398 keys each" in ann)', u"公告里的键数串"),
    ]),
    (u"_zf93_verify.py", [(r"EXPECT_KEYS = 350[^\n]*", u"EXPECT_KEYS = 398           # " + NOTE, u"常量")]),
    (u"_zf96_verify.py", [(r"EXPECT_KEYS = 350[^\n]*", u"EXPECT_KEYS = 398           # " + NOTE, u"常量")]),
    (u"_zf97_verify.py", [(r"EXPECT_KEYS = 350[^\n]*", u"EXPECT_KEYS = 398           # " + NOTE, u"常量")]),
    (u"_zf98_verify.py", [(r"EXPECT_KEYS = 350[^\n]*", u"EXPECT_KEYS = 398           # " + NOTE, u"常量")]),
    (u"_zf100_verify.py", [(r"EXPECT_KEYS = 350[^\n]*", u"EXPECT_KEYS = 398           # " + NOTE, u"常量")]),
    (u"_zf101_verify.py", [(r"EXPECT_KEYS = 350[^\n]*", u"EXPECT_KEYS = 398           # " + NOTE, u"常量")]),
    (u"_zf102_verify.py", [(r"EXPECT_KEYS = 350[^\n]*", u"EXPECT_KEYS = 398           # " + NOTE, u"常量")]),
    (u"_zf103_verify.py", [
        (r"len\(table\) == 350", u"len(table) == 398", u"断言值"),
        (r'u"%s：总键数 350[^"]*"', u'u"%s：总键数 398（… + ZF107 成就 48）"', u"标题文案"),
    ]),
]

# 补抄进改前件的 5 份（ZF107 备份漏的）
LATE_BACKUP = [u"_zf81_verify.py", u"_zf82_verify.py", u"_zf93_verify.py",
               u"_zf96_verify.py", u"_zf98_verify.py"]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def late_backup():
    u"""动它们之前先补进改前件（§10）；已经在里面的核对哈希"""
    os.makedirs(BK, exist_ok=True)
    lines = []
    for f in LATE_BACKUP:
        src = os.path.join(TOOLS, f)
        dst = os.path.join(BK, f)
        if os.path.exists(dst):
            if sha1(src) != sha1(dst):
                fails.append(u"%s 已在改前件里但内容不一致（有人在动它？）" % f)
            else:
                lines.append(u"已在改前件（哈希一致）  %s  %s" % (sha1(src), f))
            continue
        shutil.copy2(src, dst)
        if sha1(src) != sha1(dst):
            fails.append(u"%s 补抄后哈希不一致" % f)
        else:
            lines.append(u"本轮补抄                  %s  %s" % (sha1(dst), f))
        print(u"  [补账] %s → zf107_pre" % f)
    io.open(os.path.join(os.path.dirname(BK), u"_补说明.txt"), "w", encoding="utf-8",
            newline=u"\n").write(
        u"ZF107 改前件补账（照 ZF100 的先例）\n"
        u"原因：第一版 _zf107_backup.py 的名单是按「记得改过哪些」写的，漏了这 5 份\n"
        u"      —— 它们同样写死了 350 键，本轮要跟着改到 398。\n"
        u"时间：在 **_zf107_retarget.py 动手之前**补抄，内容仍是改前状态。\n\n"
        + u"\n".join(lines) + u"\n")
    print(u"  补账清单 → _补说明.txt")


def main():
    late_backup()
    n = 0
    for f, subs in PLAN:
        p = os.path.join(TOOLS, f)
        text = io.open(p, encoding="utf-8").read()          # ← 写前重读
        after = text
        for pat, rep, why in subs:
            after, cnt = re.subn(pat, rep, after)
            if cnt != 1:
                fails.append(u"%s：%s 的替换命中 %d 次（要求正好 1 次）" % (f, why, cnt))
        if after == text:
            fails.append(u"%s：一个字节都没变（正则是不是过时了？）" % f)
            continue
        try:
            compile(after, f, u"exec")
        except SyntaxError as e:
            fails.append(u"%s：改完语法不过（第 %s 行：%s）—— 不落盘" % (f, e.lineno, e.msg))
            continue
        io.open(p, "w", encoding="utf-8", newline=u"").write(after)
        back = io.open(p, encoding="utf-8").read()           # 回读
        left = len(re.findall(r"\b350\b", back))
        print(u"  [OK]   %-24s 替换 %d 处；残留 350 = %d" % (f, len(subs), left))
        if left:
            fails.append(u"%s：还残留 %d 处 350" % (f, left))
        n += 1
    print(u"\n改到的文件 %d 份" % n)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
