# -*- coding: utf-8 -*-
u"""_zf155_packfix.py —— 重打之后的收尾：把"当前成品"提法按**正则**跟平（不写死旧哈希）。

为什么改成正则：挂载点/文档里的哈希每重打一次就变一次，写死旧值当锚点的做法已经连坑两轮
（交接那行早年还被打歪成了反斜杠）。这里改成：
  · 交接 §1「已发布成品」那一行：里面的 40 位 sha1 → 当前 `.sha1`；`<数字> B` → 当前体积；
  · 英文公告：所有 `NNNNNNN bytes` → 带千分位的当前体积（哈希已在打包脚本里按值替换过）。

跑法：python build\\zftools\\_zf155_packfix.py [--write]
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.12.jar")
SHA = JAR + u".sha1"

fails, notes = [], []
SHA_RE = re.compile(r"\b[0-9a-f]{40}\b")
SIZE_RE = re.compile(r"\b\d{4,}\s*B\b")


def main(argv):
    write = u"--write" in argv
    sha = io.open(SHA, encoding="ascii").read().strip()
    size = os.path.getsize(JAR)
    size_str = u"{:,}".format(size)
    print(u"当前成品：%d 字节 / %s" % (size, sha))

    # ① 交接 §1 成品行
    text = io.open(HAND, encoding="utf-8", newline="").read()
    lines = text.split(u"\n")
    idx = [i for i, l in enumerate(lines) if u"已发布成品" in l]
    if len(idx) != 1:
        fails.append(u"「已发布成品」命中 %d 行" % len(idx))
    else:
        i = idx[0]
        old = lines[i]
        new = SHA_RE.sub(sha, old)
        new = SIZE_RE.sub(u"%s B" % size_str, new)
        # 千分位（原行是 5,848,073 B 这种）
        new = re.sub(r"\b(\d{1,3}(?:,\d{3})+|\d{4,})\s*B\b", u"%s B" % size_str, new)
        print(u"  交接行：%s" % (u"已更新" if new != old else u"无需改"))
        if new != old:
            notes.append(u"  [改] 交接 §1 成品行 → %s B / %s" % (size_str, sha[:12]))
            if write:
                lines[i] = new
                io.open(HAND, u"w", encoding="utf-8", newline=u"").write(u"\n".join(lines))
        if sha not in new:
            fails.append(u"交接行里没写上新哈希")

    # ② 公告体积格式统一（哈希已由打包脚本按值换过）
    ann = io.open(ANN, encoding="utf-8", newline="").read()
    fixed = re.sub(r"(?<![,\d])(\d{7})(?=\s*bytes)", lambda m: u"{:,}".format(int(m.group(1))), ann)
    n = len(re.findall(r"(?<![,\d])\d{7}(?=\s*bytes)", ann))
    print(u"  公告：%d 处 7 位体积补千分位" % n)
    if n and write:
        io.open(ANN, u"w", encoding="utf-8", newline=u"").write(fixed)
    if write and not n:
        notes.append(u"  [跳过] 公告体积格式已经统一")

    # ③ 终检
    ann2 = io.open(ANN, encoding="utf-8", newline="").read()
    hand2 = io.open(HAND, encoding="utf-8", newline="").read()
    for label, txt in ((u"公告", ann2), (u"交接", hand2)):
        if sha not in txt:
            fails.append(u"%s 里没有当前哈希" % label)
    print(u"  公告里当前哈希 %d 处；交接里 %d 处" % (ann2.count(sha), hand2.count(sha)))
    print(u"\n".join(notes))
    print(u"\n%s；失败 %d" % (u"已落盘" if write else u"（没加 --write，只算不写）", len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
