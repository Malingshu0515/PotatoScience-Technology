# -*- coding: utf-8 -*-
u"""_zf160_renumber.py —— 本轮撞号处理：我的 §4.167 改成 §4.168（别人先占了 4.167）。

先只读打印所有 `4.167` 出现处（带上下文），再（`--write`）**只改我自己的那几处**：
  ① 我的小节标题 `### 4.167 【工具雷】探针别等 tick…（0.13 ZF160）`
  ② 我的 §5 行（`| ZF160 |` 那一行）里的 `§4.167`
  ③ 交接 §6 第 34 条里的 `§4.167`
  ④ `_zf160_verify.py` 的 C1 判据
别人的 §4.167 / §4.166（ZF159 那条线）一个字不碰。

跑法：python build\\zftools\\_zf160_renumber.py [--write]
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
VER = os.path.join(ROOT, "build", "zftools", u"_zf160_verify.py")

MY_TITLE_OLD = u"### 4.167 \u3010\u5de5\u5177\u96f7\u3011\u63a2\u9488\u522b\u7b49 tick"
MY_TITLE_NEW = u"### 4.168 \u3010\u5de5\u5177\u96f7\u3011\u63a2\u9488\u522b\u7b49 tick"


def show(path, label):
    text = io.open(path, encoding="utf-8").read()
    print(u"---- %s 里所有 4.167 出现处 ----" % label)
    for i, line in enumerate(text.split(u"\n"), 1):
        if u"4.167" in line:
            print(u"  %d: %s" % (i, line[:150]))
    return text


def main(argv):
    write = u"--write" in argv
    doc = show(DOC, u"档案")
    hand = show(HAND, u"交接")
    ver = show(VER, u"_zf160_verify.py")

    if doc.count(MY_TITLE_OLD) != 1:
        print(u"!! 我的标题锚点命中 %d 次 —— 停手" % doc.count(MY_TITLE_OLD))
        return 1
    doc2 = doc.replace(MY_TITLE_OLD, MY_TITLE_NEW, 1)

    # 我的 §5 行：`| ZF160 | …（整行）` 里的 §4.167 → §4.168
    m = re.search(u"(?m)^\\| ZF160 \\|.*$", doc2)
    if not m:
        print(u"!! 找不到 §5 的 ZF160 行")
        return 1
    row = m.group(0)
    row2 = row.replace(u"§4.167", u"§4.168")
    doc2 = doc2[:m.start()] + row2 + doc2[m.end():]
    print(u"§5 行里改了 %d 处 §4.167" % (row.count(u"§4.167")))

    # 交接 §6 第 34 条
    h2 = hand
    k = hand.find(u"34. **ZF160 \u7684\u8d26")
    if k < 0:
        print(u"!! 交接里找不到第 34 条")
        return 1
    end = hand.find(u"\n\n", k)
    seg = hand[k:end if end > 0 else len(hand)]
    seg2 = seg.replace(u"§4.167", u"§4.168")
    h2 = hand[:k] + seg2 + hand[(end if end > 0 else len(hand)):]
    print(u"交接第 34 条里改了 %d 处 §4.167" % (seg.count(u"§4.167")))

    v2 = ver.replace(u'### 4.167', u'### 4.168').replace(u"u\"C1 \u6863\u6848 \u00a74.167 \u4e00\u8282\"",
                                                        u"u\"C1 \u6863\u6848 \u00a74.168 \u4e00\u8282\"")
    v2 = v2.replace(u"C \u6587\u6863\u4e0e\u6210\u54c1\uff1a\u00a74.167", u"C \u6587\u6863\u4e0e\u6210\u54c1\uff1a\u00a74.168")
    print(u"_zf160_verify.py 里 C1 判据改了 %d 处" % (ver.count(u"### 4.167")))

    print(u"")
    print(u"改后：我这一节的号 = 4.168；档案里 `### 4.168` 出现 %d 次（应为 1）"
          % doc2.count(u"### 4.168"))
    if not write:
        print(u"（没加 --write，只算不写）")
        return 0
    io.open(DOC, u"w", encoding="utf-8", newline=u"").write(doc2)
    io.open(HAND, u"w", encoding="utf-8", newline=u"").write(h2)
    io.open(VER, u"w", encoding="utf-8", newline=u"").write(v2)
    print(u"  已写 档案 / 交接 / _zf160_verify.py")
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
