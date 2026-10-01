# -*- coding: utf-8 -*-
r'''_zf160_probe_mount.py —— 挂上 ZF160 的临时探针（**只拷一个类文件**，不动 `PotatoST.java`）。

为什么这轮不挂 `PotatoST.java`：那一刻盘上正挂着另一条线的 `Zf159Check`（汇合点不能叠罗汉，§4.7）。
本探针自带 `@EventBusSubscriber(modid = PotatoST.MODID)`（默认 game 总线，与 `GuideBook` 同款写法）
⇒ 只要类在源码树里就会自动注册。于是：
  · 挂载 = 拷 `check\Zf160Check.java` → `src\main\java\com\potatost\mod\Zf160Check.java`
  · 卸载 = 删掉它（`_zf160_unprobe.py`），并核对 `PotatoST.java` 的 sha1 **一个字节没变**

跑法：python build\zftools\_zf160_probe_mount.py [--write]
'''
import hashlib
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
POT = os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java")
SRC_CHECK = os.path.join(ROOT, r"build\zftools\check\Zf160Check.java")
DST_CHECK = os.path.join(ROOT, r"src\main\java\com\potatost\mod\Zf160Check.java")
PRE = os.path.join(r"C:\PotatoST救援", "zf160_pre", r"src\main\java\com\potatost\mod\PotatoST.java")


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    write = u"--write" in argv
    if os.path.exists(DST_CHECK):
        print(u"  [跳过] %s 已挂（幂等）" % os.path.basename(DST_CHECK))
        return 0
    text = io.open(POT, encoding="utf-8", newline=u"").read()
    others = [n for n in (u"Zf151Check", u"Zf153Check", u"Zf155Check", u"Zf156Check", u"Zf159Check")
              if n in text]
    if others:
        print(u"  [情报] 盘上还挂着别人的探针：%s —— 本探针**不碰** PotatoST.java，不受影响"
              % u", ".join(others))
    if not write:
        print(u"（没加 --write，只算不写）会拷 %s" % os.path.basename(SRC_CHECK))
        return 0
    shutil.copy2(SRC_CHECK, DST_CHECK)
    assert sha(SRC_CHECK) == sha(DST_CHECK)
    # ⚠ 记下"挂载那一刻 PotatoST.java 的 sha1"：本轮不动它，但**别人**的探针正挂在里面，
    #   所以卸载时拿"改前件"比会显示不一致 —— 基准要用这个快照（§4.161 那条"基准选错"的变体）。
    io.open(os.path.join(ROOT, r"build\zftools\_zf160_pot_sha.txt"), "w",
            encoding="ascii", newline="\n").write(sha(POT) + u"\n")
    print(u"已挂上 %s（%s）" % (os.path.basename(DST_CHECK), sha(DST_CHECK)[:12]))
    print(u"PotatoST.java = %s（快照已存 _zf160_pot_sha.txt；本轮**不动**它）" % sha(POT)[:12])
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
