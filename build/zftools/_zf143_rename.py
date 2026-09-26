# -*- coding: utf-8 -*-
r'''_zf143_rename.py —— 把**我这一轮**从 ZF142 改号成 ZF143（另一条线正在用 ZF142）。

⚠⚠ **只对本文件里逐条点名的清单动手**（§4.132：改名脚本不许扫目录通配 ——
   ZF139 那次就是因为"凡 `*zf136*` 一律改名"把别人的文件覆盖了）。

点名清单（**我这一轮建的**，逐个核对过 mtime 与内容）：
    build\zftools\_zf142_backup.py       → _zf143_backup.py
    build\zftools\_zf142_recon.py        → _zf143_recon.py
    build\zftools\_zf142_recon.txt       → _zf143_recon.txt
    build\zftools\_zf142_tex.py          → _zf143_tex.py
    build\zftools\_zf142_lang.py         → _zf143_lang.py
    build\zftools\_zf142_gatefix.py      → _zf143_gatefix.py
    build\zftools\_zf142_probefix.py     → _zf143_probefix.py
    build\zftools\_zf142_probefix2.py    → _zf143_probefix2.py
    build\zftools\_zf142_probe.log       → _zf143_probe.log
    build\zftools\_zf142_probe_utf8.txt  → _zf143_probe_utf8.txt
    src\main\java\com\potatost\mod\Zf142Check.java → Zf143Check.java

**不动**（那是他们的）：`_zf142_pre.py` / `_zf142_verify.py` / `_zf142_falsify.py` /
`_zf142_docs.py` / `_zf142_commit.py` / `_zf142_gates.py` / `_zf142_look.py` /
`_zf142_poleblur.py` / `_zf142_probe.py` / `_zf142_ingame.py` / `_zf142_quotefix.py` /
`_zf142_quotefind.py` / `_zf142_out\` / `zf142_pre\`（他们的备份根）。

**不搬**他们的备份根：我自己的备份复制一份到 `zf143_pre`（他们的 `zf142_pre` 保持原样，
只把被我覆盖的 `_sha1.txt` 用 `_zf142_repair.py` 重建）。

顺带把点名文件**内部**的 `zf142/Zf142/[A142]` 换成 143 号（含探针里的 TAG 与报告路径）。

跑法：python build\zftools\_zf143_rename.py [--write]
'''
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
SRC = os.path.join(ROOT, r"src\main\java\com\potatost\mod")

FILES = [
    (os.path.join(ZT, u"_zf142_backup.py"), os.path.join(ZT, u"_zf143_backup.py")),
    (os.path.join(ZT, u"_zf142_recon.py"), os.path.join(ZT, u"_zf143_recon.py")),
    (os.path.join(ZT, u"_zf142_recon.txt"), os.path.join(ZT, u"_zf143_recon.txt")),
    (os.path.join(ZT, u"_zf142_tex.py"), os.path.join(ZT, u"_zf143_tex.py")),
    (os.path.join(ZT, u"_zf142_lang.py"), os.path.join(ZT, u"_zf143_lang.py")),
    (os.path.join(ZT, u"_zf142_gatefix.py"), os.path.join(ZT, u"_zf143_gatefix.py")),
    (os.path.join(ZT, u"_zf142_probefix.py"), os.path.join(ZT, u"_zf143_probefix.py")),
    (os.path.join(ZT, u"_zf142_probefix2.py"), os.path.join(ZT, u"_zf143_probefix2.py")),
    (os.path.join(ZT, u"_zf142_probe.log"), os.path.join(ZT, u"_zf143_probe.log")),
    (os.path.join(ZT, u"_zf142_probe_utf8.txt"), os.path.join(ZT, u"_zf143_probe_utf8.txt")),
    (os.path.join(SRC, u"Zf142Check.java"), os.path.join(SRC, u"Zf143Check.java")),
]

SUBS = [(u"zf142", u"zf143"), (u"ZF142", u"ZF143"),
        (u"Zf142", u"Zf143"), (u"[A142]", u"[A143]")]

fails, notes = [], []


def main(argv):
    write = u"--write" in argv
    if not write:
        print(u"（没加 --write，只算不写）")
        for a, b in FILES:
            print(u"  会改名：%s → %s" % (os.path.basename(a), os.path.basename(b)))
        return 0

    for a, b in FILES:
        if not os.path.exists(a):
            fails.append(u"点名的文件不在：%s" % a)
            continue
        if os.path.exists(b):
            fails.append(u"目标已存在（**不许覆盖**）：%s" % b)
            continue
        # ⚠ 逐字节：文本件顺便换号，二进制件（没有）原样搬
        if a.endswith(u".py") or a.endswith(u".java") or a.endswith(u".txt") or a.endswith(u".log"):
            t = io.open(a, encoding=u"utf-8", newline=u"").read()
            for x, y in SUBS:
                t = t.replace(x, y)
            io.open(b, u"w", encoding=u"utf-8", newline=u"").write(t)
            os.remove(a)
        else:
            shutil.move(a, b)
        notes.append(u"  [改名] %s → %s" % (os.path.basename(a), os.path.basename(b)))

    # 挂载点（PotatoST.java 里的那一行）
    pot = os.path.join(SRC, u"PotatoST.java")
    t = io.open(pot, encoding=u"utf-8", newline=u"").read()
    if u"Zf142Check" in t:
        t2 = t.replace(u"Zf142Check", u"Zf143Check")
        n = t.count(u"Zf142Check")
        io.open(pot, u"w", encoding=u"utf-8", newline=u"").write(t2)
        notes.append(u"  [换号] PotatoST.java 的挂载点（%d 处）" % n)

    print(u"\n".join(notes))
    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
