# -*- coding: utf-8 -*-
u"""_zf155_fixhand.py —— 交接 §1「已发布成品」那一行的活体哈希/体积（锚点按**实际那行**取，不猜转义）。

那行的反引号早年被打歪成了反斜杠（`elease\\PotatoST-0.12.jar\\ = \\fa2c…`），
所以 ZF155 打包脚本里按正常 markdown 写的锚点命中 0 次 ⇒ C2「交接里有新哈希」红。
这里改成：定位含「已发布成品」的那一行，**只在这一行内**替换哈希 / 体积 / 补一句本轮内容。

跑法：python build\\zftools\\_zf155_fixhand.py [--write]
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.12.jar")
SHA = JAR + u".sha1"

OLD_SHA = u"fa2c550d941d5667aecddc3b45a09b12c09bb400"
NEW_SHA = io.open(SHA, encoding="ascii").read().strip()
NEW_SIZE = u"{:,}".format(os.path.getsize(JAR))
OLD_SIZE = u"5,848,073"
ADD = u" / **ZF155 通用升级模板**"


def main(argv):
    write = u"--write" in argv
    text = io.open(HAND, encoding="utf-8", newline="").read()
    lines = text.split(u"\n")
    hits = [i for i, l in enumerate(lines) if u"已发布成品" in l]
    print(u"「已发布成品」命中 %d 行：%s" % (len(hits), [i + 1 for i in hits]))
    if len(hits) != 1:
        print(u"!! 命中数不是 1，停手")
        return 1
    i = hits[0]
    old_line = lines[i]
    new_line = old_line.replace(OLD_SHA, NEW_SHA).replace(OLD_SIZE, NEW_SIZE)
    if u"ZF155" not in new_line:
        # 补在「最新一次重打」那一串的末尾（右括号之前）
        new_line = new_line.replace(u"ZF153 振金剑）", u"ZF153 振金剑" + ADD + u"）", 1)
    print(u"\n改前：%s" % old_line[:200])
    print(u"\n改后：%s" % new_line[:200])
    ok = NEW_SHA in new_line and NEW_SIZE in new_line and u"ZF155" in new_line
    print(u"\n判据：新哈希在=%s 新体积在=%s 本轮补记在=%s"
          % (NEW_SHA in new_line, NEW_SIZE in new_line, u"ZF155" in new_line))
    if not write:
        print(u"（没加 --write，只算不写）")
        return 0 if ok else 1
    lines[i] = new_line
    io.open(HAND, u"w", encoding="utf-8", newline=u"").write(u"\n".join(lines))
    print(u"已落盘")
    return 0 if ok else 1


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
