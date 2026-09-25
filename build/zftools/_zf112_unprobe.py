# -*- coding: utf-8 -*-
u"""_zf112_unprobe.py —— 摘掉 ZF112 的临时探针（先抄后删）"""
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
PROBE = os.path.join(JAVA, "Zf112Check.java")
ARCHIVE = os.path.join(ROOT, r"build\zftools\check\Zf112Check.java")
POTATO = os.path.join(JAVA, "PotatoST.java")
HOOK = (u"\n        // ---- ④ 本轮探针（ZF112，验完就摘）----\n"
        u"        Zf112Check.register();\n")
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    os.makedirs(os.path.dirname(ARCHIVE), exist_ok=True)
    shutil.copy2(PROBE, ARCHIVE)
    if sha1(PROBE) != sha1(ARCHIVE):
        fails.append(u"存档哈希不一致")
    print(u"① 存档 %s（%d 字节，sha1 %s）" % (ARCHIVE, os.path.getsize(ARCHIVE), sha1(ARCHIVE)))
    src = io.open(POTATO, encoding="utf-8").read()
    after, cnt = re.subn(re.escape(HOOK), u"\n", src)
    if cnt != 1:
        fails.append(u"钩子命中 %d 次" % cnt)
    else:
        io.open(POTATO, "w", encoding="utf-8", newline=u"\n").write(after)
        print(u"② 钩子已摘（少 %d 字节）" % (len(src) - len(after)))
    os.remove(PROBE)
    back = io.open(POTATO, encoding="utf-8").read()
    if u"Zf112Check" in back or os.path.exists(PROBE):
        fails.append(u"还有残留")
    print(u"③ 探针已从 src 删掉；PotatoST 无残留 = %s" % (u"是" if u"Zf112Check" not in back else u"否"))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
