# -*- coding: utf-8 -*-
u"""_zf149_publish.py —— ZF149 发布：把新打的 0.12 换到 `release\\`，并写 `.sha1`。

口径（§4.92）：`.sha1` 是**纯哈希一行**（不是 `sha1sum` 那种两列格式）。
旧成品 `release\\PotatoST-0.12.jar` 的改前件在 `C:\\PotatoST救援\\zf149_pre\\`（先备份后覆盖）。
⚠ 只动 0.12 这两个文件；`PotatoST-0.11.jar` / 0.10 一个字不动（它们是别轮的门在用的参照物）。

跑法：python build\\zftools\\_zf149_publish.py [--write]
"""
import hashlib
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.12.jar")
DST = os.path.join(ROOT, "release", u"PotatoST-0.12.jar")
SHA = DST + u".sha1"
PRE = os.path.join(r"C:\PotatoST救援", "zf149_pre", r"release\PotatoST-0.12.jar")


def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def main(argv):
    write = u"--write" in argv
    if not os.path.isfile(SRC):
        print(u"!! 新产物不在：%s" % SRC)
        return 1
    if not os.path.isfile(PRE):
        print(u"!! 改前件不在（没备份就不许覆盖）：%s" % PRE)
        return 1
    new_sha = sha1(SRC)
    old_sha = sha1(DST) if os.path.isfile(DST) else u"(无)"
    print(u"改前 release\\PotatoST-0.12.jar ：%s（%d B）"
          % (old_sha[:12], os.path.getsize(DST) if os.path.isfile(DST) else 0))
    print(u"新产物 build\\libs\\potato_s_t-0.12.jar：%s（%d B）" % (new_sha[:12], os.path.getsize(SRC)))
    if old_sha == u"(无)" or old_sha[:12] != sha1(PRE)[:12]:
        print(u"⚠ 盘上的 0.12 与改前件不一致 —— 说明有人动过，停手先看清")
        return 1
    if not write:
        print(u"（没加 --write，只算不写）")
        return 0
    shutil.copy2(SRC, DST)
    io.open(SHA, u"w", encoding=u"ascii", newline=u"\n").write(new_sha + u"\n")
    a, b = sha1(DST), sha1(SRC)
    rec = io.open(SHA, encoding=u"ascii").read().strip()
    print(u"已替换；release 的 sha1 = %s（与 build\\libs 一致 = %s；.sha1 记录 = %s）"
          % (a[:12], a == b, rec == a))
    return 0 if (a == b and rec == a) else 1


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
