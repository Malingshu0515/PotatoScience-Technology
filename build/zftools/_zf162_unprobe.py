# -*- coding: utf-8 -*-
r'''_zf162_unprobe.py —— 摘掉 ZF162 探针：删类文件 + 删 `PotatoST.java` 里那一行，并**逐字节还原**。

判据（§4.161 那两条老账）：
  ① 摘完的 `PotatoST.java` 必须与 `check\PotatoST.java.before-probe-zf162` **逐字节相同**；
  ② `src\main\java` 里 `Zf162Check` 出现 **0** 次（类文件 + 任何引用都清掉）。

跑法：python build\zftools\_zf162_unprobe.py [--write]
'''
import hashlib
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
POT = os.path.join(JAVA, u"PotatoST.java")
DST_CHECK = os.path.join(JAVA, u"Zf162Check.java")
BAK = os.path.join(ROOT, r"build\zftools\check\PotatoST.java.before-probe-zf162")
INS = u"        Zf162Check.mount(modEventBus);   // ZF162 临时探针：mod 总线收能力注册 + 开服取证（跑完删这行）"


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

    text = io.open(POT, encoding="utf-8", newline=u"").read()
    if INS in text:
        if write:
            with io.open(POT, "w", encoding="utf-8", newline=u"") as fh:
                fh.write(text.replace(INS + u"\n", u"", 1))
            print(u"已删 PotatoST.java 里那一行")
        else:
            print(u"（没加 --write）会删 PotatoST.java 里那一行")

    text = io.open(POT, encoding="utf-8", newline=u"").read()
    same = os.path.exists(BAK) and sha(POT) == sha(BAK)
    hits = []
    for root, _dirs, files in os.walk(JAVA):
        for f in files:
            p = os.path.join(root, f)
            if u"Zf162Check" in io.open(p, encoding="utf-8", errors="replace").read():
                hits.append(os.path.relpath(p, JAVA))
    print(u"PotatoST.java 与挂载前逐字节一致：%s" % (u"是" if same else u"**否**"))
    print(u"src\\main\\java 里 Zf162Check 残留：%d 处 %s" % (len(hits), u" / ".join(hits)))
    return 0 if (same and not hits) else 1


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
