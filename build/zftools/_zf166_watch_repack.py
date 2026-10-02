# -*- coding: utf-8 -*-
u"""_zf166_watch_repack.py —— **守着重打**：每一段时间试一次 `compileJava`，一旦编译通过就立刻
把"干净重打 + 文档跟平 + 关键门"一条龙跑完（因为另一条线此刻的中间态编译不过，而他们的文件我不碰）。

流程（每轮）：
  1. `gradlew compileJava --offline` —— 不通就记一行、睡 120 秒重来（最多 --tries 次）；
  2. 通了 ⇒ 调 `_zf166_repack.py --write`（build → 逐字节拷成发布件 → 自检 → 文档跟平）；
  3. 跑关键门：`_zf166_verify.py` / `_zf149_verify.py` / `_zf149_jar.py` / `_zf162_verify.py`
     / `_zf164_verify.py` / `_zf155_jarcheck.py` / `_zf156_jarcheck.py`；
  4. 结果写进 `build\\zftools\\_zf166_watch.log` 并退出（0 = 全部绿）。

跑法：python build\\zftools\\_zf166_watch_repack.py [--tries 20]
"""
import io
import os
import subprocess
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
LOG = os.path.join(ZT, u"_zf166_watch.log")
GATES = [u"_zf166_verify.py", u"_zf149_verify.py", u"_zf149_jar.py", u"_zf162_verify.py",
         u"_zf164_verify.py", u"_zf155_jarcheck.py", u"_zf156_jarcheck.py"]


def log(line):
    stamp = time.strftime(u"%H:%M:%S")
    text = u"[%s] %s" % (stamp, line)
    print(text)
    with io.open(LOG, "a", encoding="utf-8", newline=u"\n") as fh:
        fh.write(text + u"\n")


def run(args, timeout=1200):
    return subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=timeout)


def main(argv):
    tries = 20
    if u"--tries" in argv:
        tries = int(argv[argv.index(u"--tries") + 1])
    gradlew = os.path.join(ROOT, u"gradlew.bat")
    for i in range(1, tries + 1):
        r = run([gradlew, u"compileJava", u"--offline", u"--console=plain"])
        ok = r.returncode == 0 and b"BUILD SUCCESSFUL" in r.stdout
        first_err = u""
        for line in r.stdout.decode("utf-8", "replace").split(u"\n"):
            if u"错误:" in line or u"error:" in line:
                first_err = line.strip()[:120]
                break
        log(u"第 %d/%d 次 compileJava：%s%s" % (i, tries, u"通过" if ok else u"不通",
                                             u"" if ok else u"（%s）" % first_err))
        if ok:
            log(u"编译通过 ⇒ 开始干净重打")
            r2 = run([sys.executable, os.path.join(ZT, u"_zf166_repack.py"), u"--write"])
            log(u"_zf166_repack.py 退出码 %d" % r2.returncode)
            for line in r2.stdout.decode("utf-8", "replace").strip().split(u"\n"):
                log(u"    " + line)
            if r2.returncode != 0:
                log(u"重打失败，退出（留给下一轮人工看）")
                return 1
            bad = []
            for g in GATES:
                rg = run([sys.executable, os.path.join(ZT, g)], timeout=600)
                mark = u"绿" if rg.returncode == 0 else u"红"
                log(u"    %s -> %s" % (g, mark))
                if rg.returncode != 0:
                    bad.append(g)
            if bad:
                log(u"关键门还有红的：%s" % bad)
                return 1
            log(u"全部绿 ⇒ 可以提交/推送了（成品已逐字节等于构建产物，A6 也绿了）")
            return 0
        time.sleep(120)
    log(u"试了 %d 次都没等到编译通过 —— 放弃，等下一轮" % tries)
    return 1


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
