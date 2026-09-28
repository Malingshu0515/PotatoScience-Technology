# -*- coding: utf-8 -*-
u"""_zf153_retarget.py —— 把「语言键数」这个**活体数字**从 583 跟到 587（lzh 585 → 589）

ZF153 加了 **4 个键**（振金剑的物品名 + 三行 Shift 说明）= 每份语言文件 **+4**
⇒ 四语言 583 → **587**、`lzh` 585 → **589**。

为什么必须一起改（照 ZF117/ZF119/ZF125/ZF150 的成例）：盘上有 **33 份常驻门**把键数
**写死在判据里**，它们同时还有一套**互相盯**的检查（`_zf145_verify.py` 的 F 组会去
`_zf100~_zf141_verify` 里找 `EXPECT_KEYS = <数>`、`_zf125_verify.py` 的 F 组去盯
`_zf103_verify.py` 的文案）—— 只改一半就会红一半。

⚠ **只改"真判据"与活体文案，不碰历史**：
  · `_zf150_docs.py` / `_zf150_retarget*.py` / `_zf150_repair.py` / `_zf150_lzh.py` /
    `_zf150_fix78b.py` / `_zf150_scan.py` 是 **ZF150 那一轮的过程脚本**，
    它们记的是"579 → 583 那一次是怎么做的" ⇒ **一个字都不许动**（改了就篡改历史）。
  · 公告里 `579 keys each` / `508 to 579` 那两句是**上一版的叙述**，同样不动；
    只改**当前值那一句**（`(583 keys each)`）。
  · `_zf117_verify.py` 里的 `KEY_OLD = 432` 是**旧值哨兵**（它专门去别的门里找 432 残留），不动。

写盘前一律 `ast.parse` 自检（ZF150 那次就是靠它挡住了跨行 check() 被改坏）。
跑法：python build\\zftools\\_zf153_retarget.py
"""
import ast
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
DOC_EN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
DOC_HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")

OLD4, NEW4 = 583, 587      # 四语言
OLD5, NEW5 = 585, 589      # lzh

# 33 份**常驻**门（含 ZF150 自己那份 verify；不含它的过程脚本）
VERIFY = [
    u"_zf71_verify.py", u"_zf73_verify.py", u"_zf75_verify.py", u"_zf78_verify.py",
    u"_zf79_verify.py", u"_zf80_verify.py", u"_zf82_verify.py", u"_zf93_verify.py",
    u"_zf96_verify.py", u"_zf97_verify.py", u"_zf98_verify.py", u"_zf100_verify.py",
    u"_zf101_verify.py", u"_zf102_verify.py", u"_zf103_verify.py", u"_zf107_verify.py",
    u"_zf109_verify.py", u"_zf111_verify.py", u"_zf112_verify.py", u"_zf114_verify.py",
    u"_zf117_verify.py", u"_zf118_verify.py", u"_zf119_verify.py", u"_zf122_verify.py",
    u"_zf125_verify.py", u"_zf126_verify.py", u"_zf127_verify.py", u"_zf128_verify.py",
    u"_zf139_verify.py", u"_zf141_verify.py", u"_zf145_verify.py", u"_zf148_verify.py",
    u"_zf150_verify.py",
]

# 改完之后**再修**的几句"跟着数字一起要改的文案"（整段替换，避免拼出错误的算术）
LABEL_FIXES = [
    (u"_zf125_verify.py",
     u'check(u"E12 四份都是 587 键（ZF125 的 587 + ZF150 四种粒 4）"',
     u'check(u"E12 四份都是 587 键（… + ZF150 四种粒 4 + ZF153 振金剑 4）"'),
]

fails, notes = [], []


def check(label, ok, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label, (u"   " + detail) if detail else u""))
    if not ok:
        fails.append(label + (u" | " + detail if detail else u""))
    return ok


def patch_py(fn):
    p = os.path.join(TOOLS, fn)
    if not os.path.exists(p):
        check(u"%s 在盘上" % fn, False)
        return 0
    src = io.open(p, encoding="utf-8").read()
    if u"\n583" not in src and u"583" not in src and u"585" not in src:
        return 0
    out = re.sub(r"\b%d\b" % OLD4, str(NEW4), src)
    out = re.sub(r"\b%d\b" % OLD5, str(NEW5), out)
    for f2, old, new in LABEL_FIXES:
        if f2 == fn and old in out:
            out = out.replace(old, new)
    if out == src:
        return 0
    try:
        ast.parse(out)
    except SyntaxError as e:
        check(u"%s 改后语法错误（没写盘）" % fn, False, str(e))
        return 0
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(out)
    n = len(re.findall(r"\b%d\b" % NEW4, out)) + len(re.findall(r"\b%d\b" % NEW5, out))
    print(u"      %-24s 583→587 / 585→589，命中 %d 处" % (fn, n))
    return n


def main():
    # ---------- ① 33 份常驻门 ----------
    print(u"① 33 份常驻门里的活体数字：583 → 587（lzh 585 → 589）")
    total = 0
    for fn in VERIFY:
        total += patch_py(fn)
    print(u"      本次实际改写 %d 处（幂等重跑会是 0）" % total)
    # ⚠ 判据盯的是**状态**不是增量：33 份每一份都该含新数字（第一次跑完就是恒真的，
    #   重跑不会假红 —— 第一版这里写成"total > 0"，幂等重跑当场红，是我的判据不对）
    have = [fn for fn in VERIFY
            if re.search(r"\b%d\b" % NEW4, io.open(os.path.join(TOOLS, fn),
                                                  encoding="utf-8").read())]
    check(u"33 份都含新数字 %d" % NEW4, len(have) == len(VERIFY),
          u"%d / %d" % (len(have), len(VERIFY)))

    # 处理完再扫一遍：这些文件里旧数字应当清零
    left = []
    for fn in VERIFY:
        src = io.open(os.path.join(TOOLS, fn), encoding="utf-8").read()
        for m in re.finditer(r"\b(%d|%d)\b" % (OLD4, OLD5), src):
            left.append(u"%s:%s" % (fn, m.group(0)))
    check(u"33 份里旧数字 %d/%d 清零" % (OLD4, OLD5), not left, u"、".join(left[:5]))

    # ---------- ② 英文公告（当前值那一句） ----------
    print(u"\n② 英文公告的当前值那句")
    ann = io.open(DOC_EN, encoding="utf-8").read()
    old_s = u"(%d keys each)" % OLD4
    new_s = u"(%d keys each)" % NEW4
    if old_s in ann:
        io.open(DOC_EN, "w", encoding="utf-8", newline=u"\n").write(ann.replace(old_s, new_s))
        check(u"公告：%s → %s" % (old_s, new_s), True)
    else:
        check(u"公告已经是 %s（幂等）" % new_s, new_s in ann)
    back = io.open(DOC_EN, encoding="utf-8").read()
    check(u"公告回读：有 %s、没有 %s" % (new_s, old_s), new_s in back and old_s not in back)
    # 历史叙述（579 keys each / 508 to 579）必须原样留着
    check(u"公告里的历史叙述没被动（579 keys each 仍在）", u"579 keys each" in back)

    # ---------- ③ 交接文档的活体数字 ----------
    print(u"\n③ 交接文档 §1 的活体数字")
    hand = io.open(DOC_HAND, encoding="utf-8").read()
    subs = [
        (u"**%d 键 × 4**" % OLD4, u"**%d 键 × 4**" % NEW4, 1),
        # ⚠ 锚点是「；lzh = 581 = 四份 + …」——**不是**「（lzh」（第一版写错，
        #   当场被"锚点 0 次"挡住 ⇒ 没写盘、也没假装成功）
        (u"lzh = 581 = 四份", u"lzh = %d = 四份" % NEW5, 1),
    ]
    for old, new, want in subs:
        n = hand.count(old)
        if n == want:
            hand = hand.replace(old, new)
            check(u"交接：%s（%d 处）" % (old[:26], n), True)
        elif new in hand and n == 0:
            check(u"交接：已经是目标值（幂等）", True, new[:26])
        else:
            check(u"交接：锚点 %s 出现 %d 次（期望 %d）" % (old[:26], n, want), False)
    # 活体数字链条补两段（579 那条是 ZF148 写的，后面 ZF150/ZF153 各 +4）
    tail_old = u"= **+71**）。"
    tail_new = (u"= **+71**）→ **583**（ZF150 四种粒 +4）→ "
                u"**587**（ZF153 振金剑：物品名 + 三行说明 = **+4**）。")
    if tail_old in hand and u"**587**（ZF153" not in hand:
        hand = hand.replace(tail_old, tail_new, 1)
        check(u"交接：活体数字链条补上 ZF150 / ZF153 两段", True)
    else:
        check(u"交接：链条已是目标状态（幂等或锚点缺失）", u"**587**（ZF153" in hand)
    io.open(DOC_HAND, "w", encoding="utf-8", newline=u"\n").write(hand)
    back = io.open(DOC_HAND, encoding="utf-8").read()
    check(u"交接回读：有 %d 键 × 4 与 lzh %d" % (NEW4, NEW5),
          u"**%d 键 × 4**" % NEW4 in back and u"lzh = %d" % NEW5 in back)

    # ---------- ④ 全量语法自检 ----------
    print(u"\n④ 全部 _zf*_verify.py 语法自检")
    bad = []
    for f in sorted(os.listdir(TOOLS)):
        if f.startswith(u"_zf") and f.endswith(u"_verify.py"):
            try:
                ast.parse(io.open(os.path.join(TOOLS, f), encoding="utf-8").read())
            except SyntaxError as e:
                bad.append(u"%s: %s" % (f, e))
    check(u"全部能解析（%d 份）" % len([f for f in os.listdir(TOOLS)
                                    if f.startswith(u"_zf") and f.endswith(u"_verify.py")]),
          not bad, u"；".join(bad[:3]))

    # ---------- ⑤ 历史脚本一个字没动 ----------
    print(u"\n⑤ 历史脚本不许被碰")
    HIST = [u"_zf150_docs.py", u"_zf150_fix78b.py", u"_zf150_lzh.py", u"_zf150_repair.py",
            u"_zf150_retarget.py", u"_zf150_retarget2.py", u"_zf150_retarget3.py",
            u"_zf150_retarget4.py", u"_zf150_scan.py"]
    import hashlib
    bk = r"C:\PotatoST救援\zf153_pre\build\zftools"
    same, moved = [], []
    for fn in HIST:
        p1, p2 = os.path.join(TOOLS, fn), os.path.join(bk, fn)
        if os.path.exists(p1) and os.path.exists(p2):
            h1 = hashlib.sha1(open(p1, "rb").read()).hexdigest()
            h2 = hashlib.sha1(open(p2, "rb").read()).hexdigest()
            if h1 == h2:
                same.append(fn)
            else:
                moved.append(fn)
    check(u"9 份 ZF150 过程脚本与改前件逐字节相同", not moved,
          u"被改动：%s" % u"、".join(moved) if moved else u"%d 份" % len(same))

    print(u"\n备注：")
    for n in notes:
        print(u"  - " + n)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
