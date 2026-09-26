# -*- coding: utf-8 -*-
u"""_zf127_gatesnap.py —— 全门快照（ZF127 轮，**只读**）

口径与 `_zf107/_zf109/_zf111/_zf112/_zf113/_zf119/_zf121/_zf125_gatesnap.py` 完全一样，
名单加上 ZF123 之后的几道（`_zf126_verify.py` / `_zf127_verify.py` / `_zf109_tabaudit.py`）：
  · 逐份跑 `build/zftools/_zf*_verify.py` 这类常驻校验（含 repro / guard 的静态检查）；
  · 每份最多跑 300 秒，超时按**红**记（§4.77：卡死不是绿）；
  · 只打印"通过/失败"那行 + 前 3 条 FAIL，不打印全文（全文留在各自的输出里）。
⚠ 本脚本**不修改任何文件**。

⚠ **为什么多了 `--out`**：PowerShell 的 `>` 重定向写的是 **UTF-16LE**（§4.5 那条老雷），
  所以快照自己把 UTF-8 写盘，不靠外壳重定向。

跑法：
    python build\\zftools\\_zf127_gatesnap.py --out build\\zftools\\_zf127_gatesnap_before.txt
"""
import io
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ZT = r"E:\PotatoST\build\zftools"
NAMES = ["_zf64_verify.py", "_zf70_verify.py", "_zf71_verify.py", "_zf72_verify.py",
         "_zf73_repro.py", "_zf73_verify.py", "_zf74_verify.py", "_zf75_verify.py",
         "_zf78_verify.py", "_zf79_verify.py", "_zf80_verify.py", "_zf81_verify.py",
         "_zf82_verify.py", "_zf89_verify.py", "_zf90_verify.py", "_zf91_verify.py",
         "_zf92_verify.py", "_zf93_verify.py", "_zf94_verify.py", "_zf95_verify.py",
         "_zf96_verify.py", "_zf97_verify.py", "_zf98_verify.py", "_zf99_verify.py",
         "_zf100_verify.py", "_zf100_recipe_guard.py", "_zf101_verify.py",
         "_zf102_verify.py", "_zf103_verify.py", "_zf104_verify.py", "_zf107_verify.py",
         "_zf108_verify.py", "_zf109_verify.py", "_zf111_verify.py", "_zf112_verify.py",
         "_zf113_verify.py", "_zf114_verify.py", "_zf117_verify.py", "_zf118_verify.py",
         "_zf119_verify.py", "_zf121_verify.py", "_zf123_verify.py", "_zf123_langaudit.py",
         "_zf124_verify.py", "_zf125_verify.py", "_zf126_verify.py", "_zf127_verify.py",
         "_zf109_tabaudit.py"]


def main(argv):
    out_path = u""
    if u"--out" in argv:
        out_path = argv[argv.index(u"--out") + 1]
    lines = []

    def say(s):
        lines.append(s)
        print(s)

    green, red, missing = [], [], []
    detail = {}
    for n in NAMES:
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

    say(u"================= 全门快照（ZF127） =================")
    say(u"绿 = %d   红 = %d   不存在 = %d\n" % (len(green), len(red), len(missing)))
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
