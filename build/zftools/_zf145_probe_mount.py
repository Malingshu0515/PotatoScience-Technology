# -*- coding: utf-8 -*-
r'''_zf145_probe_mount.py —— 挂上 ZF145 的临时探针（往 `PotatoST.java` 构造器末尾加两行）

⚠ 这是**汇合点文件只准加行**（§4.7）的那一类：只插这一块，别的一个字节不动；
  跑完必须用 `_zf145_unprobe.py` 摘掉，并逐字节核对回到改前件（`zf145_pre`）。

跑法：python build\zftools\_zf145_probe_mount.py [--write]
'''
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
POT = os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java")
PRE = os.path.join(r"C:\PotatoST救援", "zf145_pre", r"src\main\java\com\potatost\mod\PotatoST.java")

BLOCK = (u"\n        // \u26a0\u26a0 临时探针（ZF145）：成就树补线（43 条 + 真触发 + 伤害类型标签），"
         u"跑完由 _zf145_unprobe.py 删掉\n        Zf145Check.register();")

# 构造器末尾那一句的锚点（唯一）
ANCHOR = (u"        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener("
          u"StarfallRitualManager::onPlayerLogin);\n\n    }\n")


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    write = u"--write" in argv
    text = io.open(POT, encoding=u"utf-8", newline=u"").read()
    if u"Zf145Check" in text:
        print(u"  [跳过] PotatoST.java 里已经有 Zf145Check（幂等）")
        return 0
    if text.count(ANCHOR) != 1:
        print(u"!! 锚点命中 %d 次（应为 1）—— 停手，先看清构造器末尾" % text.count(ANCHOR))
        return 1
    new = text.replace(ANCHOR, ANCHOR.replace(u"\n\n    }\n", BLOCK + u"\n\n    }\n"), 1)
    if not write:
        print(u"（没加 --write，只算不写）待插入：%r" % BLOCK)
        return 0
    io.open(POT, u"w", encoding=u"utf-8", newline=u"").write(new)
    assert io.open(POT, encoding=u"utf-8", newline=u"").read() == new
    print(u"已挂上；%s" % sha1(POT))
    print(u"改前件 %s" % (sha1(PRE) if os.path.exists(PRE) else u"(不在)"))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
