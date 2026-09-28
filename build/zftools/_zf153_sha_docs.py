# -*- coding: utf-8 -*-
u"""_zf153_sha_docs.py —— 把**新成品的 sha1** 写进文档（`_zf149_verify.py` 的 C1/C2/C3 要它）

本轮「同版本原地重打」了成品（振金剑改了 Java）：
    新    `release\\PotatoST-0.12.jar` = 5,848,073 字节，
          sha1 **fa2c550d941d5667aecddc3b45a09b12c09bb400**
    作废  旧那一份 5,812,286 字节，
          sha1 **59894a9efb7ba45cc811a558f1fea4a8dac56863**

按本工程规矩，「同版本原地重打」必须**公布作废的旧 SHA1**（否则玩家手里那份还是旧的、
却与新的 `.sha1` 对不上）。所以档案台账行、交接 §8、英文公告 ZF153 那条都写上。

⚠ 本文件里的中文串**一律不用 ASCII 双引号**（用「」）—— 这个坑本会话已经踩到第 9 次了，
   同一批脚本里写了 `_zf153_quote_scan.py` 专门扫它。

跑法：python build\\zftools\\_zf153_sha_docs.py
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
NEW = u"fa2c550d941d5667aecddc3b45a09b12c09bb400"
OLD = u"59894a9efb7ba45cc811a558f1fea4a8dac56863"
NEW_SIZE = u"5,848,073"
OLD_SIZE = u"5,812,286"

TARGETS = [
    # ① 档案台账行：在末尾那段后面补一句成品
    (r"docs\开发档案.md",
     u"⇒ **33 份写死键数的常驻门** + 英文公告 + 交接文档一起重定靶 | 见 §9 ｜ 见 §4.161\\~§4.162 |",
     u"⇒ **33 份写死键数的常驻门** + 英文公告 + 交接文档一起重定靶；⑨ **重打成品**"
     u"（振金剑改了 Java ⇒ 按「同版本原地重打」的规矩重打）：新 `release\\PotatoST-0.12.jar` = **"
     + NEW_SIZE + u" 字节 / sha1 `" + NEW + u"`**，⚠ **作废**旧那份 `" + OLD + u"`（"
     + OLD_SIZE + u" 字节）| 见 §9 ｜ 见 §4.161\\~§4.162 |"),
    # ② 交接 §8：补一小节（写在 §8.3 之前）
    (r"docs\多会话协作交接.md",
     u"### 8.3 本轮踩到并已立规矩的坑（详见档案 §4.161 / §4.162）",
     u"### 8.3 成品（同版本原地重打，**必须公布作废的旧 SHA1**）\n\n"
     u"| 项 | 值 |\n|---|---|\n"
     u"| 新 `release\\PotatoST-0.12.jar` | **" + NEW_SIZE + u" 字节**，sha1 **`" + NEW + u"`** |\n"
     u"| ⚠ **作废**（上一份 0.12） | " + OLD_SIZE + u" 字节，sha1 `" + OLD + u"` |\n\n"
     u"为什么要重打：振金剑改了 Java（`VibraniumSwordItem` / `ModTiers` / `ModItems` / `PotatoST`）"
     u"—— 本工程是「同版本原地重打」，不重打的话玩家手里那份 jar 里**没有这把剑**。\n"
     u"`_zf149_verify.py`（盯成品哈希的常驻门）与 `_zf149_jar.py`（jar 内容审计）本轮**跟平过一次**："
     u"哈希 / 字节数 / 语言键数换成新发布那一刻的实测值，**判据一条都没放宽**。\n\n"
     u"### 8.4 本轮踩到并已立规矩的坑（详见档案 §4.161 / §4.162）"),
    # ③ 英文公告：在 ZF153 那条末尾补「重打」一段
    (r"docs\UpdateAnnouncement_EN.md",
     u"Language files grew to **587 keys each** (Literary Chinese: 589).",
     u"Language files grew to **587 keys each** (Literary Chinese: 589).\n\n"
     u"### Download: the 0.12 jar was rebuilt again (ZF153)\n\n"
     u"**`release/PotatoST-0.12.jar`** - **" + NEW_SIZE + u" bytes**, sha1 **`" + NEW + u"`**.\n\n"
     u"\u26a0 The previous 0.12 jar (" + OLD_SIZE + u" bytes, sha1 `" + OLD + u"`) is **void**: "
     u"it was built before the Vibranium Sword existed, so it has no sword, no texture, no model "
     u"and only 583 language keys. Use the new one."),
]

fails = []
for rel, anchor, ins in TARGETS:
    p = os.path.join(ROOT, rel)
    t = io.open(p, encoding="utf-8").read()
    # ⚠ 幂等判据要**新旧都在**：光有新哈希不算完成 —— 本工程是"同版本原地重打"，
    #   规矩是**必须公布作废的旧 SHA1**（第一版只查新哈希 ⇒ 交接/公告被别的线写好新哈希后
    #   我这三条全被"幂等"跳过，"作废"那句根本没写进去 —— 判据太松就等于没做）。
    if NEW in t and OLD in t:
        print(u"  [幂等] %s 里新旧哈希都在" % rel)
        continue
    n = t.count(anchor)
    if n != 1:
        print(u"  [!!] %s：锚点出现 %d 次（要 1）—— 不动它" % (rel, n))
        fails.append(rel)
        continue
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t.replace(anchor, ins, 1))
    print(u"  [OK] %s 已写入新 sha1 与作废的旧 sha1" % rel)

print(u"\n回读：")
for rel, _a, _i in TARGETS:
    t = io.open(os.path.join(ROOT, rel), encoding="utf-8").read()
    ok = NEW in t and OLD in t
    print(u"  [%s] %s：新 sha1 %s / 旧 sha1（作废）%s"
          % (u"OK" if ok else u"!!", rel,
             u"在" if NEW in t else u"**不在**", u"在" if OLD in t else u"**不在**"))
    if not ok:
        fails.append(rel + u" 回读")
print(u"失败项 = %d" % len(fails))
sys.exit(1 if fails else 0)
