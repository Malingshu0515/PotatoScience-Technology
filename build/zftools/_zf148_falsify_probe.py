# -*- coding: utf-8 -*-
u"""_zf148_falsify_probe.py —— ZF148 反证刀（**真开服**那两把）：探针自己到底咬不咬人。

两把刀都只改**资源**（不用重编 Java，`runServer` 会自己跑 processResources）：
  K15 `book.json` 的 model 写回带 `item/` 的错写法 ⇒ 探针 B11 必须变红；
  K16 配方产物去掉 `patchouli:book` 组件 ⇒ 探针 D7 必须变红。
每把都走：挂探针 → 改一处 → runServer → 断言报告里出现**指定 FAIL** → 逐字节还原 →
再 runServer → 断言报告回到 `ALL OK`；最后摘探针（并逐字节核对 PotatoST.java）。

跑法：python build\\zftools\\_zf148_falsify_probe.py        （要跑 4 次开服，约 4~6 分钟）
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
CHECK = os.path.join(ZT, "check", u"Zf148Check.java")
SRC = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
JAVA = os.path.join(SRC, u"Zf148Check.java")
REPORT = os.path.join(ZT, u"_zf148_probe_utf8.txt")
BOOK = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\patchouli_books\guide\book.json")
RECIPE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe\guide_book.json")

KNIVES = [
    (u"K15 book.json 的 model 写回带 item/ 的错写法", BOOK,
     u'"model": "potato_s_t:guide_book"', u'"model": "potato_s_t:item/guide_book"',
     u"B11 model 键写字面量"),
    (u"K16 配方产物去掉 patchouli:book 组件", RECIPE,
     u'    "components": {\n      "patchouli:book": "potato_s_t:guide"\n    }\n',
     u'    "components": {}\n', u"D4 产物带 patchouli:book 组件"),
]

fails, rows = [], []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_server(tag):
    log = os.path.join(ZT, u"_zf148_falsify_%s.log" % tag)
    with open(log, "wb") as fh:
        r = subprocess.run([os.path.join(ROOT, "gradlew.bat"), "runServer", "--offline", "--console=plain"],
                           cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, timeout=900)
    rep = io.open(REPORT, encoding=u"utf-8").read() if os.path.isfile(REPORT) else u""
    return r.returncode, rep


def has_fail(rep, marker):
    return any(marker in l and u"[FAIL]" in l for l in rep.split(u"\n"))


def main():
    only = [a for a in sys.argv[1:] if not a.startswith(u"--")]
    knives = [k for k in KNIVES if not only or any(o in k[0] for o in only)]
    # ---- 0. 挂探针 ----
    shutil.copy2(CHECK, JAVA)
    subprocess.run([sys.executable, os.path.join(ZT, u"_zf148_probe_mount.py"), u"--write"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    for label, path, old, new, marker in knives:
        original = open(path, "rb").read()
        h0 = hashlib.sha1(original).hexdigest()
        text = io.open(path, encoding=u"utf-8", newline=u"").read()
        if text.count(old) != 1:
            fails.append(u"%s：改前串命中 %d 次" % (label, text.count(old)))
            continue
        io.open(path, u"w", encoding=u"utf-8", newline=u"").write(text.replace(old, new, 1))
        if os.path.exists(REPORT):
            os.remove(REPORT)
        rc, rep = run_server(u"bad")
        red = has_fail(rep, marker)
        open(path, "wb").write(original)
        restored = sha1(path) == h0
        if os.path.exists(REPORT):
            os.remove(REPORT)
        rc2, rep2 = run_server(u"good")
        green = (u"ALL OK" in rep2) and not has_fail(rep2, marker)
        rows.append((label, red, restored, green))
        if not red:
            fails.append(u"%s：探针**没红**（rc=%d）" % (label, rc))
        if not restored:
            fails.append(u"%s：还原后不是逐字节相同" % label)
        if not green:
            fails.append(u"%s：还原后探针没回到 ALL OK（rc=%d）" % (label, rc2))

    # ---- 摘探针 ----
    subprocess.run([sys.executable, os.path.join(ZT, u"_zf148_unprobe.py")],
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    print(u"================ ZF148 反证刀（开服 %d 把） ================" % len(knives))
    print(u"%-52s %-6s %-8s %-8s" % (u"刀", u"变红", u"逐字节还原", u"回绿"))
    for label, a, b, c in rows:
        print(u"%-52s %-6s %-8s %-8s" % (label[:50], u"OK" if a else u"!!", u"OK" if b else u"!!",
                                         u"OK" if c else u"!!"))
    print(u"")
    print(u"刀数 = %d   全中 = %d   失败 = %d" % (len(knives), len([r for r in rows if r[1] and r[2] and r[3]]), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
