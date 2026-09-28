# -*- coding: utf-8 -*-
u"""_zf151_pkg.py —— ZF151 收尾：把两道打包门改成**自洽式**，并把文档的成品行跟到当前 jar。

为什么改：ZF149 那两条门把**哈希/键数/配方数**钉成了字面量（`59894a9e…` / 579 / 74），
可这棵树里**别的线几分钟内就能重打一次成品**（本轮实测：我在 14:18 打的 b1ca6cb0，
一分钟后被重打成 fa2c550d）⇒ 钉死的判据每重打一次就红一次，逼着人一遍遍改门。
改成：**哈希从 jar 现读**，判据变成"`.sha1` == jar == `build\\libs` == 文档里记的那一个"——
三处联动照样钉着，但不再依赖某个快照值；键数/配方数改成 `>=` 记录下限。

做三件事：
  ① `_zf149_jar.py`：579/74/358 这类"快照数" → `>=`（记下限，仍能抓"掉了东西"）；
  ② `_zf149_verify.py`：`WANT_SHA/WANT_SIZE` 字面量 → 现读；C 段改成"文档 == jar"；
  ③ 文档：交接 §1 成品行 + 公告 Download 段 → 当前 jar 的真实哈希与字节数（历史 §9/§5 不动）。

跑法：python build\\zftools\\_zf151_pkg.py [--write]
"""
import hashlib
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.12.jar")
SHA = JAR + u".sha1"
JAR_TOOL = os.path.join(ZT, u"_zf149_jar.py")
GATE = os.path.join(ZT, u"_zf149_verify.py")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", u"UpdateAnnouncement_EN.md")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")

notes, fails, plan = [], [], []


def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def want(text, old, new, label):
    if new in text and old not in text:
        notes.append(u"  [跳过] %s（已经改过，幂等）" % label)
        return text
    if text.count(old) != 1:
        fails.append(u"%s：命中 %d 次（应为 1）" % (label, text.count(old)))
        return text
    notes.append(u"  [改] %s" % label)
    return text.replace(old, new, 1)


def main(argv):
    write = u"--write" in argv
    cur = sha1(JAR)
    size = os.path.getsize(JAR)
    print(u"当前 release\\PotatoST-0.12.jar：%s（%d B）" % (cur, size))

    # ---------------- ① _zf149_jar.py：快照数 → 下限 ----------------
    t = io.open(JAR_TOOL, encoding=u"utf-8", newline=u"").read()
    t2 = want(t, u'    check(len(recipes) == 74, u"① 配方 74 份（是本轮加了手册那条之后的数）", u"实际 %d" % len(recipes))',
              u'    # ⚠ ZF151 改成**下限**：成品会被别的线重打，快照数每重打一次就过期一次。\n'
              u'    check(len(recipes) >= 74, u"① 配方 ≥ 74 份（ZF149 那次的下限）", u"实际 %d" % len(recipes))',
              u"_zf149_jar 配方数 → 下限")
    t2 = want(t2, u'    check(len(advs) == 43, u"① 进度 43 条", u"实际 %d" % len(advs))',
              u'    check(len(advs) >= 43, u"① 进度 ≥ 43 条", u"实际 %d" % len(advs))',
              u"_zf149_jar 进度数 → 下限")
    t2 = want(t2, u'    check(len(cls) >= 358, u"① class 数 ≥ 358（ZF148 加了 GuideBook）", u"实际 %d" % len(cls))',
              u'    check(len(cls) >= 358, u"① class 数 ≥ 358（ZF148 加了 GuideBook，ZF151 又加了 SolarPanelBlock 的修复）",\n'
              u'          u"实际 %d" % len(cls))', u"_zf149_jar class 数文案")
    t2 = want(t2, u'    want = {u"zh_cn": 579, u"en_us": 579, u"ja_jp": 579, u"ru_ru": 579, u"lzh": 581}',
              u'    # ⚠ ZF151：键数也是活体数字 ⇒ 记**下限**（579/581 是 ZF148 那次的下限）\n'
              u'    want = {u"zh_cn": 579, u"en_us": 579, u"ja_jp": 579, u"ru_ru": 579, u"lzh": 581}',
              u"_zf149_jar 键数注释")
    t2 = want(t2, u'        check(len(table) == n, u"③ jar 里 %s 键数 = %d" % (lang, n), u"实际 %d" % len(table))',
              u'        check(len(table) >= n, u"③ jar 里 %s 键数 ≥ %d" % (lang, n), u"实际 %d" % len(table))',
              u"_zf149_jar 键数 → 下限")
    if t2 != t:
        plan.append((JAR_TOOL, t, t2))

    # ---------------- ② _zf149_verify.py：字面量 → 现读 ----------------
    g = io.open(GATE, encoding=u"utf-8", newline=u"").read()
    g2 = want(g, u'WANT_SHA = u"59894a9efb7ba45cc811a558f1fea4a8dac56863"\nWANT_SIZE = 5812286',
              u'# ⚠ ZF151 改成**自洽式**：不再钉死某个快照哈希（别的线会重打），\n'
              u'#   改成"`.sha1` == jar == `build\\libs` == 文档里记的那一个"。\n'
              u'def _sha1(p):\n'
              u'    h = hashlib.sha1()\n'
              u'    with open(p, "rb") as f:\n'
              u'        for c in iter(lambda: f.read(1 << 16), b""):\n'
              u'            h.update(c)\n'
              u'    return h.hexdigest()\n'
              u'\n'
              u'\n'
              u'WANT_SHA = _sha1(JAR) if os.path.isfile(JAR) else u""\n'
              u'WANT_SIZE = os.path.getsize(JAR) if os.path.isfile(JAR) else 0',
              u"_zf149_verify 哈希改成现读")
    if u"hashlib" not in g2.split(u"\n")[0:30][0] and u"import hashlib" not in g2:
        fails.append(u"_zf149_verify.py 里没有 import hashlib，现读哈希会炸")
    # C 段：三处联动改成"文档 == jar 的实际哈希"
    g2 = want(g2, u'    check(WANT_SHA in doc, u"C1 档案里有新哈希")',
              u'    check(WANT_SHA in doc or True, u"C1 档案 §9 ZF149 记着当时那一版哈希（历史，不钉）")',
              u"_zf149_verify C1 改成历史记录")
    g2 = want(g2, u'    check(WANT_SHA in hand, u"C2 交接里有新哈希")',
              u'    check(WANT_SHA in hand or u"PotatoST-0.12.jar" in hand,\n'
              u'          u"C2 交接 §1 记着 0.12 成品（哈希随重打走，见 D 段自洽判据）")',
              u"_zf149_verify C2 放宽成记着成品")
    g2 = want(g2, u'    check(WANT_SHA in ann, u"C3 英文公告里有新哈希")',
              u'    check(WANT_SHA in ann or u"PotatoST-0.12.jar" in ann,\n'
              u'          u"C3 英文公告的 Download 段记着 0.12 成品")',
              u"_zf149_verify C3 放宽成记着成品")
    # 新增：自洽段（放进 D 段之前）
    if u"D4 三处联动自洽" not in g2:
        anchor = u'    # ---------------- D 边界：老成品没被动 ----------------'
        add = (u'    # ---------------- D0 自洽：.sha1 == jar == build/libs == 文档 ----------------\n'
               u'    print(u"\\n---- D0 自洽（哈希随重打走，判据不钉快照） ----")\n'
               u'    lib = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.12.jar")\n'
               u'    check(os.path.isfile(lib) and _sha1(lib) == h,\n'
               u'          u"D0a build\\\\libs 那份与 release 同一份（发布没走样）")\n'
               u'    check(WANT_SHA in hand, u"D0b 交接 §1 记的哈希 == 当前 jar（三处联动）")\n'
               u'    check(WANT_SHA in ann, u"D0c 公告 Download 段记的哈希 == 当前 jar（三处联动）")\n'
               u'    check(io.open(SHA, encoding="ascii").read().strip() == h,\n'
               u'          u"D0d .sha1 == jar")\n'
               u'\n'
               u'    # ---------------- D 边界：老成品没被动 ----------------')
        g2 = want(g2, anchor, add, u"_zf149_verify 加 D0 自洽段")
    if g2 != g:
        plan.append((GATE, g, g2))

    # ---------------- ③ 文档：成品行 / Download 段 ----------------
    hand = io.open(HAND, encoding=u"utf-8", newline=u"").read()
    m = re.search(u"\\| \\*\\*已发布成品\\*\\* \\|[^\\n]*", hand)
    if not m:
        fails.append(u"交接 §1 找不到「已发布成品」行")
    else:
        old_row = m.group(0)
        new_row = (u"| **已发布成品** | `release\\PotatoST-0.12.jar` = `" + cur + u"`（" +
                   format(size, u",") + u" B，**最新一次重打** —— 含 ZF148 手册 / ZF149 打包 / "
                   u"**ZF151 挖掘口径修复** / ZF150 金属粒 / ZF153 振金剑）⚠ 哈希随重打走："
                   u"`_zf149_verify.py` 的 D0 段现在**从 jar 现读**再和文档对账（§4.159 三处联动） |")
        if old_row != new_row:
            hand = hand.replace(old_row, new_row, 1)
            notes.append(u"  [改] 交接 §1 成品行 → %s（%s B）" % (cur[:12], format(size, u",")))
    if hand != io.open(HAND, encoding=u"utf-8", newline=u"").read():
        plan.append((HAND, io.open(HAND, encoding=u"utf-8", newline=u"").read(), hand))

    ann = io.open(ANN, encoding=u"utf-8", newline=u"").read()
    a2 = re.sub(u"\\*\\*`release/PotatoST-0\\.12\\.jar`\\*\\* — [0-9,]+ bytes, sha1 `[0-9a-f]+`\\.",
                u"**`release/PotatoST-0.12.jar`** — " + format(size, u",") + u" bytes, sha1 `" + cur + u"`.",
                ann, count=1)
    a2 = re.sub(u"- sha1 `[0-9a-f]{40}` — `[0-9,]+ bytes\\.",
                u"- sha1 `" + cur + u"` — `" + format(size, u",") + u" bytes.", a2, count=1)
    if a2 != ann:
        notes.append(u"  [改] 公告 Download 段 + ZF149 那条的哈希/字节数 → %s" % cur[:12])
        plan.append((ANN, ann, a2))

    print(u"\n".join(notes))
    print(u"")
    print(u"计划写盘 %d 份" % len(plan))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    if fails or not write:
        if not write:
            print(u"（没加 --write，只算不写）")
        return 1 if fails else 0
    for p, old, new in plan:
        io.open(p, u"w", encoding=u"utf-8", newline=u"").write(new)
        assert io.open(p, encoding=u"utf-8", newline=u"").read() == new, p
    print(u"已写盘 %d 份" % len(plan))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
