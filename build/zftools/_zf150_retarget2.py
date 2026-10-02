# -*- coding: utf-8 -*-
"""_zf150_retarget2.py —— 补全：把**真判据**里残留的 579 全部跟到 583

第一版只改了 `_zf145_verify.py` F 组那张表里的 20 份。
但盘上还有一批**没进那张表**的硬断言，它们同样钉着 579：

  · `_zf103_verify.py:713` 断言文案里写着「总键数 579」（数已改成 583，文案没跟）
  · `_zf112_verify.py:260/274` 断言文案 + 公告那句
  · `_zf117_verify.py:45` `KEY_OLD, KEY_NEW = 432, 579`
  · `_zf125_verify.py:437` `all(len(tables[l]) == 579 ...)`
  · `_zf125_verify.py:503-510` 它自己还在**交叉检查**别的门写着 579（F 组跟平）
  · `_zf109_verify.py:419` 公告那句 `(579 keys each)`
  · 以及 `_zf117/_zf118/_zf119/_zf145` 等文件里**文档字符串**对 579 的引用

处理原则：**只改数值与那句"当前值"文案，历史叙述不动**（例如
「ZF125 起 579」这种讲历史的句子保留，但把"当前值"那半句改掉会失真 ——
所以对文档字符串一律**保守跳过**，只改会真的跑到判据的那几处）。
每处都打印出来，人工可核。
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOOLS = r"E:\PotatoST\build\zftools"
DOC_EN = r"E:\PotatoST\docs\UpdateAnnouncement_EN.md"
OLD, NEW = 579, 583
fails = []

# (文件, 旧串, 新串, 说明)  —— 都是**会跑到判据**的地方
PATCHES = [
    ("_zf103_verify.py",
     u'check(len(table) == %d, u"%s：总键数 %d（… + ZF112 锂电池构造间 9 + ZF125 柴油发电机 11）"',
     u'check(len(table) == %d, u"%s：总键数 %d（… + ZF112 锂电池构造间 9 + ZF125 柴油发电机 11 + ZF150 四种粒 4）"',
     u"断言文案里的总键数"),
    ("_zf112_verify.py", u'eq(u"%s 键数 %d" % name, EXPECT_KEYS, len(now))',
     u'eq(u"%s 键数 %d" % name, EXPECT_KEYS, len(now))', u"（文案里是 %%d，无需改）"),
    ("_zf112_verify.py", u'check(u"公告键数已重定目标到 %d", u"(%d keys each)" in read(',
     u'check(u"公告键数已重定目标到 %d", u"(%d keys each)" in read(', u"（同上，%%d）"),
    ("_zf117_verify.py", u"KEY_OLD, KEY_NEW = 432, 579", u"KEY_OLD, KEY_NEW = 432, 583",
     u"KEY_NEW 活体值"),
    ("_zf118_verify.py", u"KEY_NEW = 579", u"KEY_NEW = 583", u"KEY_NEW 活体值"),
    ("_zf119_verify.py", u"KEY_OLD, KEY_NEW = 448, 579", u"KEY_OLD, KEY_NEW = 448, 583",
     u"KEY_NEW 活体值"),
    ("_zf125_verify.py", u"all(len(tables[l]) == 579 for l in tables)",
     u"all(len(tables[l]) == 583 for l in tables)", u"四语言键数硬断言"),
    ("_zf125_verify.py", u"check(u\"E12 四份都是 579 键（本轮 +12：11 个机键 + 接线口那个）\"",
     u"check(u\"E12 四份都是 583 键（ZF125 的 579 + ZF150 四种粒 4）\"", u"E12 断言文案"),
    ("_zf125_verify.py", u'u"EXPECT_KEYS = 579"', u'u"EXPECT_KEYS = 583"', u"F 组跟平靶子"),
    ("_zf125_verify.py", u'u"len(table) == 579" in read(p) and u"总键数 579" in read(p)',
     u'u"len(table) == 583" in read(p) and u"总键数 583" in read(p)', u"F2 跟平靶子"),
    ("_zf125_verify.py", u'check(u"F1 %s 的键数跟到 579" % n', u'check(u"F1 %s 的键数跟到 583" % n',
     u"F1 断言文案"),
    ("_zf125_verify.py", u'check(u"F2 _zf103_verify.py 的键数与文案都跟到 579"',
     u'check(u"F2 _zf103_verify.py 的键数与文案都跟到 583"', u"F2 断言文案"),
    ("_zf109_verify.py", u'u"(579 keys each)"', u'u"(583 keys each)"', u"公告那句"),
    ("_zf145_verify.py", u"KEYS_ALL = 579", u"KEYS_ALL = 583", u"上一轮的 KEYS_ALL"),
]


def main():
    print(u"== 逐处打补丁 ==")
    for fn, old, new, why in PATCHES:
        p = os.path.join(TOOLS, fn)
        if not os.path.exists(p):
            fails.append(u"%s 不在" % fn)
            print(u"  !! %s 不在" % fn)
            continue
        t = io.open(p, encoding="utf-8").read()
        if old == new:
            print(u"  [略] %-22s %s" % (fn, why))
            continue
        if new in t and old not in t:
            print(u"  [幂等] %-20s %s" % (fn, why))
            continue
        n = t.count(old)
        if n != 1:
            fails.append(u"%s：%s 锚点 %d 次" % (fn, why, n))
            print(u"  !! %-22s %s 锚点 %d 次" % (fn, why, n))
            continue
        io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old, new))
        b = io.open(p, encoding="utf-8").read()
        if new in b:
            print(u"  [OK] %-22s %s" % (fn, why))
        else:
            fails.append(u"%s 回读失败" % fn)

    print(u"\n== 公告那句 ==")
    if os.path.exists(DOC_EN):
        t = io.open(DOC_EN, encoding="utf-8").read()
        o, n_ = u"(%d keys each)" % OLD, u"(%d keys each)" % NEW
        if n_ in t and o not in t:
            print(u"  [幂等] 已是 %s" % n_)
        elif t.count(o) == 1:
            io.open(DOC_EN, "w", encoding="utf-8", newline="\n").write(t.replace(o, n_))
            print(u"  [OK] 英文公告 %s -> %s" % (o, n_))
        else:
            fails.append(u"公告里 %s 出现 %d 次" % (o, t.count(o)))
            print(u"  !! 公告里 %s 出现 %d 次" % (o, t.count(o)))
    else:
        fails.append(u"公告文件不在")
        print(u"  !! 公告文件不在")

    print(u"\n== 复查：还有哪些**非注释行**写着 %d ==" % OLD)
    left = []
    for f in sorted(os.listdir(TOOLS)):
        if not re.match(r"^_zf\d+_verify\.py$", f):
            continue
        for i, ln in enumerate(io.open(os.path.join(TOOLS, f), encoding="utf-8").read().split(u"\n"), 1):
            if re.search(r"\b%d\b" % OLD, ln) and not ln.strip().startswith(u"#"):
                left.append((f, i, ln.strip()[:88]))
    if left:
        for f, i, ln in left:
            print(u"  %s:%d  %s" % (f, i, ln))
        print(u"  ⚠ 上面这些若确实是判据，还要改；若只是字符串/叙述，留着无害 —— **逐条看过再定**。")
    else:
        print(u"  [OK] 没有残留")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
