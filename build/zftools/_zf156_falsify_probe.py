# -*- coding: utf-8 -*-
r'''_zf156_falsify_probe.py —— ZF156 的**活体反证刀**：把修好的那行改坏，探针必须当场变红。

刀口：`TerminalBlockEntity.onChunkUnloaded()` 里 `this.unloadedWithChunk = true;` → `= false;`
  （= 回到 0.13 之前的行为：区块卸载时照样通知对端拆线）
预期：探针 A2/A3 变红（对端把线划掉了），B/C 那些检察照样绿（说明不是"整份探针崩了"）。

跑法：python build\zftools\_zf156_falsify_probe.py
  ⚠ 需要探针已经挂在树里（`_zf156_probe_mount.py --write`）。
'''
import hashlib
import io
import os
import re
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
TB = os.path.join(ROOT, r"src\main\java\com\potatost\mod\TerminalBlockEntity.java")
LOG = os.path.join(ROOT, r"build\zftools\_zf156_falsify_probe.log")
REPORT = os.path.join(ROOT, r"build\zftools\_zf156_probe_utf8.txt")

OLD = u"        this.unloadedWithChunk = true;"
NEW = u"        this.unloadedWithChunk = false;"


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_server():
    with io.open(LOG, "wb") as fh:
        r = subprocess.run([r"E:\PotatoST\gradlew.bat", u"runServer", u"--offline"],
                           cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, timeout=1200)
    return r.returncode


def report():
    return io.open(REPORT, encoding="utf-8", errors="replace").read() if os.path.isfile(REPORT) else u""


def red(text, code):
    # ⚠ 报告里的判定行是 `  [FAIL] A2 …`（`[A156] ` 前缀只打在 stdout 上）——
    #   第一版按 `[A156] [FAIL] A2` 去 match，于是"刀明明咬住了、脚本说没咬住"（§4.162 同族）。
    return re.search(u"(?m)^\\s*\\[FAIL\\]\\s+%s\\b" % code, text) is not None


def green(text, code):
    return re.search(u"(?m)^\\s*\\[OK\\]\\s+%s\\b" % code, text) is not None


def main():
    text = io.open(TB, encoding="utf-8", newline="").read()
    if text.count(OLD) != 1:
        print(u"!! 刀口没对准（命中 %d 次）" % text.count(OLD))
        return 2
    if u"Zf156Check" not in io.open(os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java"),
                                    encoding="utf-8").read():
        print(u"!! 探针没挂上，先跑 _zf156_probe_mount.py --write")
        return 2
    before = sha(TB)
    fails = []
    try:
        print(u"① 上刀：unloadedWithChunk 置真 → 置假（回到改前行为）")
        io.open(TB, "w", encoding="utf-8", newline="").write(text.replace(OLD, NEW, 1))
        rc = run_server()
        rep = report()
        io.open(os.path.join(ROOT, r"build\zftools\_zf156_falsify_probe_red.txt"),
                "w", encoding="utf-8", newline="\n").write(rep)
        print(u"   runServer 退出码 %s；报告判词：%s" % (rc, rep.splitlines()[2] if rep else u"(没报告)"))
        # ⚠ 只该红 A2/A3：刀砍的是"通知对端"这一半，A4（**被卸载那一份自己的表**）本来就没被清，
        #   改前改后都该是绿的 —— 拿它当"整份探针没崩"的对照用。
        for code in (u"A2", u"A3"):
            if not red(rep, code):
                fails.append(u"上刀后 %s 没红 —— 这把刀没咬住" % code)
        for code in (u"A4", u"B4", u"C2", u"C8"):
            if not green(rep, code):
                fails.append(u"上刀后 %s 不该红（整份探针是不是崩了？）" % code)
    finally:
        io.open(TB, "w", encoding="utf-8", newline="").write(text)
        if sha(TB) != before:
            fails.append(u"恢复后 TerminalBlockEntity.java 哈希不一致")

    print(u"② 拔刀后重跑一遍，必须回到 ALL OK")
    rc2 = run_server()
    rep2 = report()
    io.open(os.path.join(ROOT, r"build\zftools\_zf156_falsify_probe_green.txt"),
            "w", encoding="utf-8", newline="\n").write(rep2)
    verdict = rep2.splitlines()[2] if rep2 else u"(没报告)"
    print(u"   runServer 退出码 %s；报告判词：%s" % (rc2, verdict))
    if u"ALL OK" not in rep2 or red(rep2, u"A2"):
        fails.append(u"拔刀后没回到 ALL OK")
    print(u"-" * 78)
    if fails:
        print(u"活体反证 **失败** %d 条：" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    print(u"活体反证：**咬住**（上刀 A2/A3 红、A4/B/C 照旧绿；拔刀回到 ALL OK）")
    return 0


if __name__ == u"__main__":
    sys.exit(main())
