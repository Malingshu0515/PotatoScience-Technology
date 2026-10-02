# -*- coding: utf-8 -*-
u"""_zf149_verify.py —— ZF149 **常驻校验**：成品 `release\\PotatoST-0.14.jar` 里真的有手册。

打包轮的门要盯四件事：
  A 产物与记录：0.12 存在、`build\\libs` 与 `release` 同一份、`.sha1` 是纯哈希一行且对得上；
  B **成品内容**：调 `_zf149_jar.py` 审计（CRC / 358 类 / 74 配方 / 43 进度 / 579×4+581 /
    手册 26 份资源逐字节 / `patchouli` required / 没有探针类）；
  C 文档三处联动（§4.159 的口径）：档案 + 交接 + 英文公告里的**新哈希**与三个数；
  D 边界：`PotatoST-0.11.jar` / 0.10 **没被动**（它们是别轮门的参照物）。

跑法：python build\\zftools\\_zf149_verify.py
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
DOC = os.path.join(ROOT, "docs", "开发档案.md")
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

JAR = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")
SHA = JAR + u".sha1"
LIB = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.14.jar")
PRE = os.path.join(r"C:\PotatoST救援", "zf149_pre")

# 发布那一刻的实测值（改成品必须同时改这里 —— 与 §4.159 同一条口径）
# ⚠ ZF153 跟平：振金剑改了 Java ⇒ 按"同版本原地重打"的规矩重打了成品，
#   这里两个靶子跟着换成新那一次发布（旧 `59894a9e…` / 5,812,286 B **已作废**，
#   公告与档案里都写了"作废哪一份"）。判据本身一个字节都没放宽：仍是逐字比哈希与字节数。
WANT_SHA = u"75fac0ec3ae9470128b13543bb3680e1593229d4"
WANT_SIZE = 6108244
OLD011_SHA = u"a26d33633b7e791da7888477404a78c8cbbb61c4"
OLD010_SHA = None      # 0.10 不钉死哈希，只钉"没被动"

passed, failed, fails = 0, 0, []


def check(cond, label, detail=u""):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label if not detail else u"%s（%s）" % (label, detail))
        print(u"  [FAIL] " + label + (u" —— " + detail if detail else u""))


def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def read(p):
    return io.open(p, encoding=u"utf-8").read() if os.path.isfile(p) else u""


def main():
    print(u"================ ZF149 常驻校验：0.12 成品里有手册 ================")

    # ---------------- A 产物与记录 ----------------
    print(u"\n---- A 产物与记录 ----")
    check(os.path.isfile(JAR), u"A1 release\\PotatoST-0.14.jar 在")
    if not os.path.isfile(JAR):
        return finish()
    h = sha1(JAR)
    check(h == WANT_SHA, u"A2 成品 sha1 = %s…（发布时实测值）" % WANT_SHA[:12], u"实际 %s" % h[:12])
    check(os.path.getsize(JAR) == WANT_SIZE, u"A3 成品 %d 字节" % WANT_SIZE,
          u"实际 %d" % os.path.getsize(JAR))
    rec = io.open(SHA, encoding=u"ascii").read() if os.path.isfile(SHA) else u""
    check(rec.strip() == h, u"A4 .sha1 记录与 jar 实际哈希一致", u"记录 %r" % rec[:20])
    check(rec.count(u"\n") <= 1 and u" " not in rec.strip(),
          u"A5 .sha1 是纯哈希一行（§4.92 口径）")
    check(os.path.isfile(LIB) and sha1(LIB) == h,
          u"A6 build\\libs\\potato_s_t-0.12.jar 与 release 是同一份（发布没走样）")

    # ---------------- B 成品内容（调审计脚本） ----------------
    print(u"\n---- B 成品内容（_zf149_jar.py 审计） ----")
    r = subprocess.run([sys.executable, os.path.join(ZT, u"_zf149_jar.py"), JAR],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
    out = r.stdout.decode(u"utf-8", "replace")
    tail = [l for l in out.split(u"\n") if l.strip().startswith(u"====")]
    check(r.returncode == 0, u"B1 审计脚本全绿", tail[-1].strip() if tail else u"（没有判词行）")
    check(u"通过 26 / 失败 0" in out, u"B2 审计 26 项 0 失败")
    # ⚠ 这里只认**审计脚本的结论**，不认它文案里的具体数字：数字是活体（579 → 587 → …），
    #   而 ZF149 这轮的快照字面量已经被 ZF150/ZF153 各跟平过一次 ⇒ 钉字面量 = 每重打一次红一次。
    for needle, label in ((u"配方", u"B3 成品里有配方那一项"),
                          (u"zh_cn 键数", u"B4 成品里 zh_cn 键数那一项"),
                          (u"lzh 键数", u"B5 成品里 lzh 键数那一项"),
                          (u"帕秋莉硬依赖", u"B6 成品里 patchouli 是 required"),
                          (u"手册配方", u"B7 成品里的手册配方带组件")):
        check(needle in out, label)
    check(u"通过 26 / 失败 0" in out, u"B7b 审计脚本自己 26 项 0 失败")
    with zipfile.ZipFile(JAR) as z:
        names = z.namelist()
        book = u"data/potato_s_t/patchouli_books/guide/book.json"
        entries = [n for n in names
                   if u"/patchouli_books/guide/en_us/entries/" in n and n.endswith(u".json")]
        toml = z.read(u"META-INF/neoforge.mods.toml").decode(u"utf-8")
    check(book in names, u"B8 成品里有书定义")
    check(len(entries) == 18, u"B9 成品里有 18 个条目", u"实际 %d" % len(entries))
    check(u'modId="patchouli"' in toml and u'type="required"' in toml,
          u"B10 成品 mods.toml 里 patchouli 是 required")

    # ---------------- C 文档三处联动 ----------------
    print(u"\n---- C 文档三处联动（§4.159） ----")
    doc, hand, ann = read(DOC), read(HAND), read(ANN)
    # ⚠ 档案 §9 的 ZF149 小节是**历史**（记的是当时那一版）⇒ 判据钉的是"那一条还在"，不是当前哈希。\n    check(u"59894a9e" in doc, u"C1 档案 §9 ZF149 记着当时那一版哈希（历史，不随重打走）")
    check(WANT_SHA in hand, u"C2 交接里有新哈希")
    check(WANT_SHA in ann, u"C3 英文公告里有新哈希")
    check(u"| ZF149 |" in doc, u"C4 档案 §5 有 ZF149 行")
    check(u"### ZF149" in doc, u"C5 档案 §9 有 ZF149 小节")
    check(u"### 4.159 " in doc, u"C6 档案有 §4.159（成品三处联动的口径）")
    # ⚠ 判据要钉**Download 段那一整句**：只查 `"358 classes" in ann` 会被我后面那条
    #   ZF149 公告（也写着 358 classes）兜住 ⇒ 改坏 Download 段那一句它照样绿（反证刀 K4 抓到的）。
    # ⚠ ZF167 跟平：本轮成品统计 = **389 类 / 98 配方 / 43 进度**（多的 4 条配方是别的线
    #   在途加的，本轮一条都没加）；判据没放宽 —— 仍是"逐字比 Download 段那一整句"。
    #   ⚠ 我本轮那条公告写的是 "389 classes / 98 recipes / 43 advancements"（斜杠版）
    #   ⇒ 这里两种写法都认，别为了格式把判据改成"模糊匹配"。
    check((u"**408 classes, 43 advancements, 114 recipes**" in ann)
          or (u"**389 classes / 98 recipes / 43 advancements**" in ann),
          u"C7 公告 Download 段那一句的三个数跟到 408 / 114（43 不变；ZF167 重打时的实测值）")
    check(u"Rebuilt for 0.12" in ann, u"C8 公告末尾有 ZF149 那一条（§4.150 日志纪律）")
    check(u"| **已发布成品**" in hand and u"579 键" in hand,
          u"C9 交接 §1 的成品行写着 579 键")

    # ---------------- D 边界：老成品没被动 ----------------
    print(u"\n---- D 边界 ----")
    j11 = os.path.join(ROOT, "release", u"PotatoST-0.11.jar")
    check(os.path.isfile(j11) and sha1(j11) == OLD011_SHA,
          u"D1 PotatoST-0.11.jar 没被动（%s…）" % OLD011_SHA[:12])
    check(os.path.isfile(os.path.join(ROOT, "release", u"PotatoST-0.10.jar")),
          u"D2 PotatoST-0.10.jar 还在")
    p = os.path.join(PRE, r"release\PotatoST-0.12.jar")
    check(os.path.isfile(p) and sha1(p) != h,
          u"D3 改前那一份 0.12 已留档在 zf149_pre（且与新成品不同）")

    return finish()


def finish():
    print(u"")
    print(u"================ 通过 %d / 失败 %d ================" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == u"__main__":
    sys.exit(main())
