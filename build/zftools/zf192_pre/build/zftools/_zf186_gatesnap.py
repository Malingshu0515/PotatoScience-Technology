# -*- coding: utf-8 -*-
u"""_zf186_gatesnap.py —— 全门快照（ZF186 轮，**只读**）。

口径与 `_zf107/_zf109/_zf111/_zf112/_zf113/_zf119/_zf121/_zf125/_zf128/_zf139/_zf141/_zf148/_zf155/_zf160/_zf166_gatesnap.py` 一样：
  · 逐份跑常驻校验（`_zf*_verify.py` / `*_repro.py` / `*_guard.py` / `*_audit.py`）；
  · 每份最多 300 秒，超时按**红**记（§4.77：卡死不是绿）；
  · 只打印「通过/失败」那行 + 前 3 条 FAIL，不打印全文。
⚠ 本脚本**不修改任何文件**（它只跑门、只写自己的报告 txt）。
⚠⚠ **白名单式**选脚本：只挑名字里带 verify / repro / guard / audit 的（`*_falsify*.py` 是**反证刀**，
   它会**真的改源码**再改回来 —— 全门快照绝不能碰它；`*_backup/_docs/_repack/_bump/_apply/_wire/_probe` 同理）。

跑法：python build\\zftools\\_zf186_gatesnap.py --out build\\zftools\\_zf186_gatesnap.txt
"""
import glob
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ZT = r"E:\PotatoST\build\zftools"
ALLOW = (u"_verify.py", u"_repro.py", u"_guard.py", u"_audit.py")


def pick():
    names = []
    for p in sorted(glob.glob(os.path.join(ZT, u"_zf*.py"))) + sorted(glob.glob(os.path.join(ZT, u"_rzh*.py"))):
        b = os.path.basename(p)
        if u"falsify" in b or u"_bak" in b:
            continue
        if any(b.endswith(a) for a in ALLOW):
            names.append(b)
    return names


def main(argv):
    out_path = u""
    if u"--out" in argv:
        out_path = argv[argv.index(u"--out") + 1]
    lines = []

    def say(s):
        lines.append(s)
        print(s)

    names = pick()
    green, red, missing = [], [], []
    detail = {}
    for n in names:
        p = os.path.join(ZT, n)
        if not os.path.exists(p):
            missing.append(n)
            continue
        try:
            r = subprocess.run([sys.executable, p], stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=300)
            out = r.stdout.decode("utf-8", "replace")
            rc = r.returncode
        except subprocess.TimeoutExpired:
            out, rc = u"**超时 300 秒**", 99
        line = u""
        for l in out.split(u"\n"):
            if u"通过" in l and u"失败" in l:
                line = l.strip()
        if not line:
            for l in out.split(u"\n"):
                if u"失败" in l and (u"=" in l or u"：" in l):
                    line = l.strip()
        fails = [l.strip() for l in out.split(u"\n") if l.strip().startswith(u"!!")][:3]
        if not fails:
            fails = [l.strip() for l in out.split(u"\n") if l.strip().startswith(u"- ")]
            fails = [f for f in fails if u"—" in f or u"缺" in f][:3]
        if rc == 0:
            green.append(n)
        else:
            red.append(n)
            detail[n] = (line or (u"（没有'通过/失败'汇总行，退出码 %d）" % rc), fails)

    say(u"================= 全门快照（ZF186） =================")
    say(u"脚本 = %d   绿 = %d   红 = %d   不存在 = %d\n" % (len(names), len(green), len(red), len(missing)))
    say(u"---- 红的（按脚本名）----")
    for n in red:
        line, fails = detail[n]
        say(u"  !! %-26s %s" % (n, line[:110]))
        for f in fails:
            say(u"        %s" % f[:120])
    say(u"\n---- 绿的 ----")
    for n in green:
        say(u"  OK %s" % n)
    if missing:
        say(u"\n---- 不在盘上的（本轮还没写或名字不同）----")
        for n in missing:
            say(u"  -- %s" % n)
    say(u"\n判词：绿 %d / 红 %d（红的逐条看上面）" % (len(green), len(red)))

    if out_path:
        io.open(out_path, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(lines) + u"\n")
        print(u"（已写 %s）" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
