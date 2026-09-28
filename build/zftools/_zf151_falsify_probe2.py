# -*- coding: utf-8 -*-
u"""_zf151_falsify_probe2.py —— ZF151 开服反证（**只改数据**，探针一次性挂好不再反复摘挂）。

为什么要换一种做法：第一版反证脚本每把刀都"挂→摘"一遍探针，而那会儿另一条线（ZF153）
正在**同一个文件**上加监听 ⇒ 撞出过一次中间态（PotatoST.java:91 编译不过）。
这一版：探针**挂一次**，之后只动 `mineable/pickaxe.json` 这一个数据文件 ——
改坏 → 开服 → 断言 A1 变红 → 逐字节还原 → 再开服 → 断言回到 ALL OK → 最后摘探针。

跑法：python build\\zftools\\_zf151_falsify_probe2.py
"""
import hashlib
import io
import json
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
CHECK = os.path.join(ZT, "check", u"Zf151Check.java")
SRC = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
JAVA = os.path.join(SRC, u"Zf151Check.java")
REPORT = os.path.join(ZT, u"_zf151_probe_utf8.txt")
TAG = os.path.join(ROOT, "src", "main", "resources", "data", "minecraft", "tags", "block",
                   "mineable", "pickaxe.json")

MARKER = u"A1 每一台机器都在 mineable/pickaxe 里（镐子加速）"
fails = []


def run_server(tag):
    log = os.path.join(ZT, u"_zf151_falsify2_%s.log" % tag)
    with open(log, "wb") as fh:
        try:
            r = subprocess.run([os.path.join(ROOT, "gradlew.bat"), "runServer", "--offline",
                                "--console=plain"], cwd=ROOT, stdout=fh,
                               stderr=subprocess.STDOUT, timeout=420)
            rc = r.returncode
        except subprocess.TimeoutExpired:
            rc = 99
            subprocess.run([u"powershell", u"-NoProfile", u"-Command",
                            u"Get-Process java -ErrorAction SilentlyContinue | "
                            u"Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-20) } | "
                            u"Stop-Process -Force"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    rep = io.open(REPORT, encoding=u"utf-8").read() if os.path.isfile(REPORT) else u""
    return rc, rep


def verdict(rep):
    for l in rep.split(u"\n"):
        if u"判词" in l:
            return l.strip()
    return u"(没有报告)"


def main():
    # ---- 挂探针（只挂这一次） ----
    if not os.path.isfile(JAVA):
        subprocess.run([sys.executable, os.path.join(ZT, u"_zf151_probe_mount.py")],
                       stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        import shutil
        shutil.copy2(CHECK, JAVA)
    subprocess.run([sys.executable, os.path.join(ZT, u"_zf151_probe_mount.py"), u"--write"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    src = io.open(os.path.join(SRC, u"PotatoST.java"), encoding=u"utf-8", newline=u"").read()
    if u"Zf151Check.register();" not in src:
        print(u"!! 探针没挂上 —— 停手")
        return 1

    # ---- 先跑一次"好"的，确认基线全绿 ----
    if os.path.exists(REPORT):
        os.remove(REPORT)
    rc0, rep0 = run_server(u"base")
    print(u"  基线：%s" % verdict(rep0))
    base_green = u"判词：ALL OK" in rep0

    # ---- 改坏：把 fluid_exchanger 从标签里删掉 ----
    original = open(TAG, "rb").read()
    h0 = hashlib.sha1(original).hexdigest()
    table = json.loads(io.open(TAG, encoding=u"utf-8").read())
    table[u"values"] = [v for v in table[u"values"] if v != u"potato_s_t:fluid_exchanger"]
    io.open(TAG, u"w", encoding=u"utf-8", newline=u"\n").write(
        json.dumps(table, ensure_ascii=False, indent=2).replace(u"\n", u"\n") + u"\n")
    if os.path.exists(REPORT):
        os.remove(REPORT)
    rc1, rep1 = run_server(u"bad")
    hit = any(MARKER in l and u"[FAIL]" in l for l in rep1.split(u"\n"))
    print(u"  改坏后：%s ／ 命中 %r = %s" % (verdict(rep1), MARKER[:24], hit))
    open(TAG, "wb").write(original)
    restored = hashlib.sha1(open(TAG, "rb").read()).hexdigest() == h0

    # ---- 还原后再跑一次，回到全绿 ----
    if os.path.exists(REPORT):
        os.remove(REPORT)
    rc2, rep2 = run_server(u"good")
    print(u"  还原后：%s" % verdict(rep2))
    green = u"判词：ALL OK" in rep2

    # ---- 摘探针 ----
    subprocess.run([sys.executable, os.path.join(ZT, u"_zf151_unprobe.py")],
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    print(u"")
    print(u"================ ZF151 开服反证（数据刀） ================")
    print(u"  基线全绿     = %s" % (u"OK" if base_green else u"!!"))
    print(u"  改坏必红     = %s" % (u"OK" if hit else u"!!"))
    print(u"  逐字节还原   = %s" % (u"OK" if restored else u"!!"))
    print(u"  还原后回绿   = %s" % (u"OK" if green else u"!!"))
    if not base_green:
        fails.append(u"基线不是 ALL OK（rc=%d）" % rc0)
    if not hit:
        fails.append(u"改坏后没按预期变红（rc=%d）" % rc1)
    if not restored:
        fails.append(u"标签没还原成逐字节相同")
    if not green:
        fails.append(u"还原后没回到 ALL OK（rc=%d）" % rc2)
    print(u"  失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
