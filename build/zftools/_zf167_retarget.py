# -*- coding: utf-8 -*-
u"""_zf167_retarget.py —— 把「语言键数」这个活体数字从 605 跟到 620（lzh 607 → 622）

ZF167 加了 **15 个键**（空铝罐 / 可乐两个名字 + 可乐两行说明 + 机器名 + 机器说明 +
两条手倒提示 + 七条状态灯）⇒ 四语言 605 → **620**、`lzh` 607 → **622**。

⚠ 只动**常驻门**（`_zf*_verify.py` / `_zf*_jarcheck.py`）里的活体数字；
  别的轮次的**过程脚本**（`_zf166_docs.py` / `_zf166_repack.py` / `_zf162_pkg.py` …）
  记的是"那一次是怎么做的" ⇒ 一个字都不许动（改了就是篡改历史，ZF150/ZF153 同一条口径）。

跑法：python build\\zftools\\_zf167_retarget.py
"""
import ast
import glob
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
DOC_EN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
DOC_HAND = os.path.join(ROOT, r"docs\多会话协作交接.md")

OLD4, NEW4 = 605, 620      # 四语言
OLD5, NEW5 = 607, 622      # lzh

fails, notes = [], []


def check(label, ok, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label, (u"   " + detail) if detail else u""))
    if not ok:
        fails.append(label)
    return ok


def resident_scripts():
    out = []
    for pat in (u"_zf*_verify.py", u"_zf*_jarcheck.py"):
        for p in sorted(glob.glob(os.path.join(TOOLS, pat))):
            name = os.path.basename(p)
            if name.startswith(u"_zf167"):
                continue        # 我自己的：断言是相对的，不含活体数字
            out.append(p)
    return out


def main():
    print(u"① 常驻门里的活体数字：605 → 620（lzh 607 → 622）")
    touched = 0
    for p in resident_scripts():
        src = io.open(p, encoding="utf-8").read()
        if not re.search(u"\\b(%d|%d)\\b" % (OLD4, OLD5), src):
            continue
        out = re.sub(u"\\b%d\\b" % OLD4, str(NEW4), src)
        out = re.sub(u"\\b%d\\b" % OLD5, str(NEW5), out)
        if out == src:
            continue
        try:
            ast.parse(out)
        except SyntaxError as e:
            check(u"%s 改后语法错误（没写盘）" % os.path.basename(p), False, str(e))
            continue
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(out)
        n = len(re.findall(u"\\b%d\\b" % NEW4, out)) + len(re.findall(u"\\b%d\\b" % NEW5, out))
        print(u"      %-26s 命中 %d 处" % (os.path.basename(p), n))
        touched += 1
    check(u"至少改到一份常驻门", touched > 0, u"共 %d 份" % touched)

    left = []
    for p in resident_scripts():
        src = io.open(p, encoding="utf-8").read()
        for m in re.finditer(u"\\b(%d|%d)\\b" % (OLD4, OLD5), src):
            left.append(u"%s:%s" % (os.path.basename(p), m.group(0)))
    check(u"常驻门里旧数字 %d/%d 清零" % (OLD4, OLD5), not left, u"、".join(left[:5]))

    print(u"\n② 英文公告的当前值那句")
    ann = io.open(DOC_EN, encoding="utf-8").read()
    old_s, new_s = u"(%d keys each)" % OLD4, u"(%d keys each)" % NEW4
    if old_s in ann:
        io.open(DOC_EN, "w", encoding="utf-8", newline=u"\n").write(ann.replace(old_s, new_s))
        check(u"公告：%s → %s" % (old_s, new_s), True)
    else:
        check(u"公告已经是 %s（幂等）" % new_s, new_s in ann)
    back = io.open(DOC_EN, encoding="utf-8").read()
    check(u"公告回读：有 %s、没有 %s" % (new_s, old_s), new_s in back and old_s not in back)

    print(u"\n③ 交接文档 §1 的活体数字")
    hand = io.open(DOC_HAND, encoding="utf-8").read()
    subs = [(u"**%d 键 × 4**" % OLD4, u"**%d 键 × 4**" % NEW4),
            (u"lzh = %d = 四份" % OLD5, u"lzh = %d = 四份" % NEW5)]
    for old, new in subs:
        n = hand.count(old)
        if n == 1:
            hand = hand.replace(old, new)
            check(u"交接：%s" % old, True)
        elif n == 0 and new in hand:
            check(u"交接：已经是目标值（幂等）", True, new)
        else:
            check(u"交接：锚点 %s 出现 %d 次" % (old, n), False)
    io.open(DOC_HAND, "w", encoding="utf-8", newline=u"\n").write(hand)
    back = io.open(DOC_HAND, encoding="utf-8").read()
    check(u"交接回读：有 %d 键 × 4 与 lzh %d" % (NEW4, NEW5),
          (u"**%d 键 × 4**" % NEW4 in back) and (u"lzh = %d" % NEW5 in back))

    print(u"\n④ 全部 _zf*_verify.py 语法自检")
    bad = []
    for f in sorted(os.listdir(TOOLS)):
        if f.startswith(u"_zf") and f.endswith(u"_verify.py"):
            try:
                ast.parse(io.open(os.path.join(TOOLS, f), encoding="utf-8").read())
            except SyntaxError as e:
                bad.append(u"%s: %s" % (f, e))
    check(u"全部能解析", not bad, u"；".join(bad[:3]))

    print(u"\n备注：")
    for n in notes:
        print(u"  - " + n)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
