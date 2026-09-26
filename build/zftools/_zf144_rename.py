# -*- coding: utf-8 -*-
r'''_zf144_rename.py —— 把**我这一轮**从 ZF143 改号成 ZF144。

原因：另一条线**也在用 ZF143**（`_zf143_apply.py` / `_zf143_docs.py` / `_zf143_look.py` /
`_zf143_preview.py` / `_zf143_row.txt` / `_zf143_section.md`，23:39~23:41 就建好了）。
我改号到 ZF143（23:50）之后才看见 ⇒ 再改一次到 **ZF144**（盘上与备份根都空着，实测过）。

⚠ **只对本文件点名的那几份动手**（§4.132/§4.147：改名脚本不许扫通配）。
⚠ 做之前先逐个核过：名单里这几份**都是我的**（mtime 23:50 那批 + 我新写的），
   与他们的 `_zf143_*`（23:39~23:41 那批）**没有一个重名**。

点名清单：_zf143_backup / recon(.py/.txt) / tex / lang / gatefix / probefix / probefix2 /
         probe.log / probe_utf8.txt / bkfix / unprobe / rename  → 换成 `_zf144_`
         （`_zf143_rename.py` 自己改名成 `_zf144_rename.py`）
         `Zf143Check.java`（已归档到 check/）→ `Zf144Check.java`（check/ 里那份也一起改）
         `PotatoST.java` 里的挂载点（若还在）
         `C:\PotatoST救援\zf143_pre` → `zf144_pre`

跑法：python build\zftools\_zf144_rename.py [--write]
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
CHECK = os.path.join(ZT, "check")
SRC = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
OLD_BK = os.path.join(r"C:\PotatoST救援", "zf143_pre")
NEW_BK = os.path.join(r"C:\PotatoST救援", "zf144_pre")

NAMES = [u"_zf143_backup.py", u"_zf143_recon.py", u"_zf143_recon.txt", u"_zf143_tex.py",
         u"_zf143_lang.py", u"_zf143_gatefix.py", u"_zf143_probefix.py",
         u"_zf143_probefix2.py", u"_zf143_probe.log", u"_zf143_probe_utf8.txt",
         u"_zf143_bkfix.py", u"_zf143_unprobe.py"]

SUBS = [(u"zf143", u"zf144"), (u"ZF143", u"ZF144"), (u"Zf143", u"Zf144"), (u"[A143]", u"[A144]")]

fails, notes = [], []


def main(argv):
    if u"--write" not in argv:
        print(u"（没加 --write）会改名：%s" % u"、".join(NAMES))
        return 0

    # ① 先核"重名冲突"：目标名一个都不许已经存在
    for n in NAMES:
        tgt = os.path.join(ZT, n.replace(u"_zf143_", u"_zf144_"))
        if os.path.exists(tgt):
            fails.append(u"目标已存在，**不许覆盖**：%s" % tgt)
    for extra in (u"Zf143Check.java", u"_zf143_rename.py"):
        pass
    if fails:
        print(u"\n".join(fails))
        return 1

    # ② 改我这批脚本
    for n in NAMES:
        a = os.path.join(ZT, n)
        b = os.path.join(ZT, n.replace(u"_zf143_", u"_zf144_"))
        if not os.path.isfile(a):
            fails.append(u"点名的文件不在：%s" % n)
            continue
        t = io.open(a, encoding=u"utf-8", newline=u"").read()
        for x, y in SUBS:
            t = t.replace(x, y)
        io.open(b, u"w", encoding=u"utf-8", newline=u"").write(t)
        os.remove(a)
        notes.append(u"  [改名] %s → %s" % (n, os.path.basename(b)))

    # ③ 我自己这份改名脚本
    a = os.path.join(ZT, u"_zf143_rename.py")
    if os.path.isfile(a):
        notes.append(u"  [留档] _zf143_rename.py 原样留着（它记的是那一次改名，不该被改内容）")

    # ④ 探针源码（src 里已被归档删除 ⇒ 只处理 check/ 里那份）
    for d in (CHECK, SRC):
        p = os.path.join(d, u"Zf143Check.java")
        if os.path.isfile(p):
            t = io.open(p, encoding=u"utf-8", newline=u"").read()
            for x, y in SUBS:
                t = t.replace(x, y)
            io.open(os.path.join(d, u"Zf144Check.java"), u"w", encoding=u"utf-8",
                    newline=u"").write(t)
            os.remove(p)
            notes.append(u"  [改名] %s → Zf144Check.java" % os.path.basename(p))

    # ⑤ 挂载点（现在应当已经摘掉了；留着这条是为了幂等）
    pot = os.path.join(SRC, u"PotatoST.java")
    t = io.open(pot, encoding=u"utf-8", newline=u"").read()
    if u"Zf143Check" in t:
        io.open(pot, u"w", encoding=u"utf-8", newline=u"").write(t.replace(u"Zf143Check", u"Zf144Check"))
        notes.append(u"  [换号] PotatoST.java 的挂载点")

    # ⑥ 备份根改名
    if os.path.isdir(OLD_BK) and not os.path.isdir(NEW_BK):
        shutil.move(OLD_BK, NEW_BK)
        notes.append(u"  [改名] 备份根 zf143_pre → zf144_pre")
        # 根里的两份说明也换号
        for n in (u"_说明.txt", u"_sha1.txt"):
            p = os.path.join(NEW_BK, n)
            if os.path.isfile(p) and n == u"_说明.txt":
                s = io.open(p, encoding=u"utf-8", newline=u"").read()
                for x, y in SUBS:
                    s = s.replace(x, y)
                io.open(p, u"w", encoding=u"utf-8", newline=u"").write(s)

    print(u"\n".join(notes))
    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
