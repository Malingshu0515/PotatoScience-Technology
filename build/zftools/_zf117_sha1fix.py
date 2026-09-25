# -*- coding: utf-8 -*-
u"""_zf117_sha1fix.py —— 把 `release\PotatoST-0.11.jar.sha1` 改回**纯哈希一行**（不动 jar 一个字节）

发现的经过：本轮跑全门快照（`_zf117_gatesnap.py`）时，**十道门**同时报同一句话 ——
`.sha1 与 jar 一致（303c5d46…）`。逐条读代码后确定：这些门（`_zf78 _zf79 _zf89 _zf90 _zf91
_zf94 _zf95 _zf98 _zf99 _zf102`）的判据都是

    rec = read(jar + ".sha1");  rec.strip().lower() == sha1(jar)

也就是**只认哈希那一行**；而 ZF114 那次打包的脚本 `_zf114_publish.py` 写的是
`sha1sum` 风格：`303c5d46…  PotatoST-0.11.jar`（带文件名）。
0.10 那版成品旁边留下的是纯哈希（`84d09345…`），0.09 那版是带名字的 —— 历史上两种都出现过，
但**当前盘上的十道门只认纯哈希**，而交接文档 §6 又写着"谁最后打包，谁负责把成品哈希对上门"。

⇒ 本脚本只做**对账**：把这一行改成纯哈希。**jar 本体一个字节不动**（哈希仍是 `303c5d46…`），
改前那一行已在本轮改前件 `C:\PotatoST救援\zf117_pre\release\PotatoST-0.11.jar.sha1` 里留着。

⚠ 这是**我的判断，不是用户的话**：另一种改法是把那十道门放宽成"两种格式都认"（我不选它，
因为十道门是既成契约，且 §6 明确指出账要对上）。要改成另一种，说一声，一行的事。
"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAR = os.path.join(ROOT, r"release\PotatoST-0.11.jar")
SIDE = JAR + u".sha1"
BK_SIDE = r"C:\PotatoST救援\zf117_pre\release\PotatoST-0.11.jar.sha1"

fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    jar_sha = sha1(JAR)
    jar_size = os.path.getsize(JAR)
    print(u"jar  : %s  %d B  sha1=%s" % (os.path.basename(JAR), jar_size, jar_sha))
    cur = read(SIDE)
    print(u"盘上 .sha1 内容 = %r" % cur)
    if cur.strip() == jar_sha:
        print(u"  [--]   已经是纯哈希一行，无需改动")
        return 0
    # 先确认它就是"sha1sum 风格"，别把别的东西当成它
    parts = cur.strip().split()
    if len(parts) != 2 or parts[0].lower() != jar_sha:
        fails.append(u".sha1 既不是纯哈希、也不是 'hash  文件名'（%r）—— 停手" % cur)
    else:
        print(u"  ⇒ 认出来了：sha1sum 风格（哈希 + 文件名 %s），哈希本身是对的" % parts[1])
    if os.path.exists(BK_SIDE):
        old = read(BK_SIDE)
        if old != cur:
            fails.append(u"改前件里那一行（%r）与盘上（%r）不一致 —— 先看清再改" % (old, cur))
    else:
        fails.append(u"改前件里没有这一份：%s" % BK_SIDE)
    if fails:
        print(u"\n失败项 = %d" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    io.open(SIDE, "w", encoding="utf-8", newline=u"").write(jar_sha + u"\n")
    back = read(SIDE)
    if back.strip() != jar_sha or back.count(u"\n") != 1:
        fails.append(u"回读失败：%r" % back)
    if sha1(JAR) != jar_sha or os.path.getsize(JAR) != jar_size:
        fails.append(u"jar 本体被动过了！")
    print(u"  [OK]   改成纯哈希一行：%r" % back)
    print(u"  [OK]   jar 本体未动（sha1 仍 %s，%d B）" % (sha1(JAR), os.path.getsize(JAR)))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
