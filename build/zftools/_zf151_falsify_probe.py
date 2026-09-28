# -*- coding: utf-8 -*-
u"""_zf151_falsify_probe.py —— ZF151 反证刀（**真开服**那一把）：探针到底咬不咬用户的原始 bug。

流程：挂探针 → **把修复撤掉**（SolarPanelBlock 的 getDrops 改成返回空表 = 复现"挖了不掉"）
→ runServer → 断言报告里出现指定 FAIL → **逐字节还原** → 再 runServer → 断言回到 ALL OK → 摘探针。

跑法：python build\\zftools\\_zf151_falsify_probe.py      （两次开服，约 2~4 分钟）
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
CHECK = os.path.join(ZT, "check", u"Zf151Check.java")
SRC = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
JAVA = os.path.join(SRC, u"Zf151Check.java")
REPORT = os.path.join(ZT, u"_zf151_probe_utf8.txt")
SOLAR = os.path.join(SRC, u"SolarPanelBlock.java")

OLD = u"        return List.of(new ItemStack(this));"
NEW = u"        return List.of();      // [ZF151 反证] 复现「挖了不掉」"
MARKERS = [u"B4 Block.getDrops 正好 1 个太阳能板", u"B7 掉落链逐段成立", u"B8 该链产出的就是太阳能板本身"]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_server(tag):
    log = os.path.join(ZT, u"_zf151_falsify_%s.log" % tag)
    with open(log, "wb") as fh:
        try:
            r = subprocess.run([os.path.join(ROOT, "gradlew.bat"), "runServer", "--offline",
                                "--console=plain"],
                               cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, timeout=420)
            rc = r.returncode
        except subprocess.TimeoutExpired:
            # ⚠ 探针没挂上时服务器**不会 halt**，脚本会一直等到超时 —— 本轮真踩过一次（900 秒）。
            #   超时 = 一次明确的失败信号，别让它把整个脚本炸掉；顺手把僵住的 JVM 收掉。
            rc = 99
            subprocess.run([u"powershell", u"-NoProfile", u"-Command",
                            u"Get-Process java -ErrorAction SilentlyContinue | "
                            u"Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-20) } | "
                            u"Stop-Process -Force"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    rep = io.open(REPORT, encoding=u"utf-8").read() if os.path.isfile(REPORT) else u""
    return rc, rep


def main():
    shutil.copy2(CHECK, JAVA)
    m = subprocess.run([sys.executable, os.path.join(ZT, u"_zf151_probe_mount.py"), u"--write"],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    mout = m.stdout.decode(u"utf-8", u"replace")
    print(u"  挂载：%s" % mout.strip().split(u"\n")[-1])
    src = io.open(os.path.join(SRC, u"PotatoST.java"), encoding=u"utf-8", newline=u"").read()
    if u"Zf151Check.register();" not in src:
        print(u"!! 探针没挂上（PotatoST.java 里没有 Zf151Check.register()）—— 停手，先修锚点")
        return 1

    original = open(SOLAR, "rb").read()
    h0 = hashlib.sha1(original).hexdigest()
    text = io.open(SOLAR, encoding=u"utf-8", newline=u"").read()
    if text.count(OLD) != 1:
        print(u"!! 改前串命中 %d 次" % text.count(OLD))
        return 1
    io.open(SOLAR, u"w", encoding=u"utf-8", newline=u"").write(text.replace(OLD, NEW, 1))
    if os.path.exists(REPORT):
        os.remove(REPORT)
    rc, rep = run_server(u"bad")
    hits = [m for m in MARKERS if any(m in l and u"[FAIL]" in l for l in rep.split(u"\n"))]
    red = len(hits) == len(MARKERS)
    print(u"  撤掉修复后：判词 = %s" % ([l for l in rep.split(u"\n") if u"判词" in l] or [u"(无报告)"])[0])
    print(u"  期望红的 %d 条里命中 %d 条" % (len(MARKERS), len(hits)))
    open(SOLAR, "wb").write(original)
    restored = sha1(SOLAR) == h0
    if os.path.exists(REPORT):
        os.remove(REPORT)
    rc2, rep2 = run_server(u"good")
    green = u"判词：ALL OK" in rep2
    print(u"  还原后：判词 = %s" % ([l for l in rep2.split(u"\n") if u"判词" in l] or [u"(无报告)"])[0])
    subprocess.run([sys.executable, os.path.join(ZT, u"_zf151_unprobe.py")],
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    print(u"")
    print(u"================ ZF151 开服反证 ================")
    print(u"  撤掉修复必红 = %s（%d/%d）" % (u"OK" if red else u"!!", len(hits), len(MARKERS)))
    print(u"  逐字节还原   = %s" % (u"OK" if restored else u"!!"))
    print(u"  还原后回绿   = %s" % (u"OK" if green else u"!!"))
    if not red:
        fails.append(u"撤掉修复后探针没按预期变红（rc=%d）" % rc)
    if not restored:
        fails.append(u"没还原成逐字节相同")
    if not green:
        fails.append(u"还原后没回到 ALL OK（rc=%d）" % rc2)
    print(u"  失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
