# -*- coding: utf-8 -*-
r'''_zf160_unprobe.py —— 摘掉 ZF160 探针（删类文件），并核对 `PotatoST.java` 逐字节没动。

跑法：python build\zftools\_zf160_unprobe.py [--write]
'''
import hashlib
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
POT = os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java")
DST_CHECK = os.path.join(ROOT, r"src\main\java\com\potatost\mod\Zf160Check.java")
PRE = os.path.join(r"C:\PotatoST救援", "zf160_pre", r"src\main\java\com\potatost\mod\PotatoST.java")


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    write = u"--write" in argv
    if os.path.exists(DST_CHECK):
        if write:
            os.remove(DST_CHECK)
            print(u"已删探针类 %s" % os.path.basename(DST_CHECK))
        else:
            print(u"（没加 --write，只算不写）会删 %s" % os.path.basename(DST_CHECK))
    else:
        print(u"  探针类不在（已删或还没挂）")
    cur = sha(POT)
    snap_p = os.path.join(ROOT, r"build\zftools\_zf160_pot_sha.txt")
    snap = io.open(snap_p, encoding="ascii").read().strip() if os.path.exists(snap_p) else u""
    text = io.open(POT, encoding="utf-8", errors="replace").read()
    no_probe = u"Zf160Check" not in text
    same = bool(snap) and cur == snap
    print(u"PotatoST.java = %s / 挂载那一刻 = %s" % (cur[:16], snap[:16] or u"(没快照)"))
    print(u"没有残留 Zf160Check：%s" % (u"是" if no_probe else u"**否**"))
    print(u"与挂载那一刻逐字节一致：%s%s" % (u"是" if same else u"**否**",
                                            u"" if same else u"（若只是别人这几分钟改了它，属正常）"))
    return 0 if no_probe else 1


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
