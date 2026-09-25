# -*- coding: utf-8 -*-
u"""_zf109_unprobe.py —— 摘掉 ZF109 的临时探针（照 ZF107 那次"先抄后删"的规矩）

顺序（**上次就是省了第一步才要吃重建的苦**）：
  ① 先抄 `Zf109Check.java` → `build/zftools/check/`（核对 sha1 一致）；
  ② 再把 `PotatoST.java` 里那一行钩子删掉（要求正好命中 1 次）；
  ③ 才从 `src` 删掉探针；
  ④ 最后核对：`PotatoST` 里再也搜不到 `Zf109Check`，而存档那份哈希与源文件一致。
⚠ 本脚本不碰别的任何文件。
"""
import hashlib
import io
import os
import re
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
PROBE = os.path.join(JAVA, "Zf109Check.java")
ARCHIVE = os.path.join(ROOT, r"build\zftools\check\Zf109Check.java")
POTATO = os.path.join(JAVA, "PotatoST.java")

HOOK = (u"\n        // ---- ④ 本轮探针（ZF109，验完就摘）----\n"
        u"        Zf109Check.register();\n")

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    # ① 先抄
    os.makedirs(os.path.dirname(ARCHIVE), exist_ok=True)
    shutil.copy2(PROBE, ARCHIVE)
    if sha1(PROBE) != sha1(ARCHIVE):
        fails.append(u"存档与源文件哈希不一致")
    print(u"① 存档 %s（%d 字节，sha1 %s）" % (ARCHIVE, os.path.getsize(ARCHIVE), sha1(ARCHIVE)))

    # ② 摘钩子
    src = io.open(POTATO, encoding="utf-8").read()
    after, cnt = re.subn(re.escape(HOOK), u"\n", src)
    if cnt != 1:
        fails.append(u"PotatoST 里钩子段落命中 %d 次（要求 1 次）" % cnt)
    else:
        io.open(POTATO, "w", encoding="utf-8", newline=u"\n").write(after)
        print(u"② 钩子已摘（PotatoST.java 少了 %d 字节）" % (len(src) - len(after)))

    # ③ 删源文件
    os.remove(PROBE)
    print(u"③ 已从 src 删掉 %s" % PROBE)

    # ④ 核对
    back = io.open(POTATO, encoding="utf-8").read()
    if u"Zf109Check" in back:
        fails.append(u"PotatoST 里还残留 Zf109Check")
    if os.path.exists(PROBE):
        fails.append(u"探针还在 src 里")
    if not os.path.exists(ARCHIVE):
        fails.append(u"存档不见了")
    print(u"④ 核对：PotatoST 无残留 = %s；src 无探针 = %s；存档在 = %s"
          % (u"是" if u"Zf109Check" not in back else u"否",
             u"是" if not os.path.exists(PROBE) else u"否",
             u"是" if os.path.exists(ARCHIVE) else u"否"))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
