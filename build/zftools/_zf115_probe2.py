# -*- coding: utf-8 -*-
u"""_zf115_probe2.py —— 把探针那两条"满罐"的账改对（罐 800 ⇒ 开机 800、跑完剩 200），
跑完 runServer 后再由 `--finish` 收尾（存档 + 摘钩子 + 删源文件）。"""
import hashlib
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
SRC = os.path.join(JAVA, "Zf112Check.java")
ARCH = os.path.join(ROOT, r"build\zftools\check\Zf112Check.java")
POTATO = os.path.join(JAVA, "PotatoST.java")
HOOK = u"\n\n        Zf112Check.register();"

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def patch():
    t = io.open(SRC, encoding="utf-8").read()
    pairs = [
        (u'eq("开机前罐里有 600 mB（一炉的量）", 600, be.getTank().getFluidAmount());',
         u'eq("开机前罐里有 800 mB（满罐，一炉只吃 600）", 800, be.getTank().getFluidAmount());'),
        (u'eq("硫酸正好扣掉 600 mB", 0, be.getTank().getFluidAmount());',
         u'eq("硫酸正好扣掉 600 mB（800 − 600 = 200）", 200, be.getTank().getFluidAmount());'),
    ]
    for old, new in pairs:
        if t.count(old) != 1:
            fails.append(u"锚点命中 %d 次：%s" % (t.count(old), old[:40]))
            continue
        t = t.replace(old, new, 1)
    io.open(SRC, "w", encoding="utf-8", newline=u"\n").write(t)
    print(u"探针两条账已改成满罐口径")


def finish():
    shutil.copy2(SRC, ARCH)
    if sha1(SRC) != sha1(ARCH):
        fails.append(u"存档哈希不一致")
    print(u"① 存档 %s（%d B，sha1 %s）" % (ARCH, os.path.getsize(ARCH), sha1(ARCH)))
    t = io.open(POTATO, encoding="utf-8").read()
    if t.count(HOOK) != 1:
        fails.append(u"钩子命中 %d 次" % t.count(HOOK))
    else:
        io.open(POTATO, "w", encoding="utf-8", newline=u"\n").write(t.replace(HOOK, u"", 1))
        print(u"② 钩子已摘")
    os.remove(SRC)
    back = io.open(POTATO, encoding="utf-8").read()
    if u"Zf112Check" in back or os.path.exists(SRC):
        fails.append(u"还有残留")
    print(u"③ 探针已从 src 删掉；PotatoST 无残留 = %s" % (u"是" if u"Zf112Check" not in back else u"否"))


if __name__ == "__main__":
    if "--finish" in sys.argv:
        finish()
    else:
        patch()
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    sys.exit(1 if fails else 0)
