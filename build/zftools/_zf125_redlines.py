# -*- coding: utf-8 -*-
u"""_zf125_redlines.py —— 把指定几道门的 `!!` 失败行抽成一份小清单（供文件工具阅读）

口径：**在进程内**用 subprocess 抓 stdout（UTF-8 解码），只留 `!!` 行并截到 160 字符
⇒ 控制台是 GBK 也不会乱码、也不会把整份语言键表灌进上下文。

跑法：
    python build\\zftools\\_zf125_redlines.py
"""
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ZT = r"E:\PotatoST\build\zftools"
OUT = os.path.join(ZT, u"_zf125_redlines.txt")
NAMES = [u"_zf71_verify.py", u"_zf73_repro.py", u"_zf73_verify.py", u"_zf74_verify.py",
         u"_zf75_verify.py", u"_zf78_verify.py", u"_zf80_verify.py", u"_zf81_verify.py",
         u"_zf82_verify.py", u"_zf89_verify.py", u"_zf90_verify.py", u"_zf91_verify.py",
         u"_zf93_verify.py", u"_zf94_verify.py", u"_zf95_verify.py", u"_zf96_verify.py",
         u"_zf97_verify.py", u"_zf98_verify.py", u"_zf99_verify.py", u"_zf100_verify.py",
         u"_zf100_recipe_guard.py", u"_zf101_verify.py", u"_zf102_verify.py",
         u"_zf109_verify.py", u"_zf111_verify.py", u"_zf112_verify.py", u"_zf117_verify.py",
         u"_zf118_verify.py", u"_zf119_verify.py", u"_zf124_verify.py"]


def main():
    out = []
    for n in NAMES:
        p = os.path.join(ZT, n)
        if not os.path.exists(p):
            continue
        try:
            r = subprocess.run([sys.executable, p], stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=300)
            text = r.stdout.decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            text = u"**超时**"
        reds = [l.strip() for l in text.split(u"\n") if l.strip().startswith(u"!!")]
        if not reds:
            continue
        out.append(u"=== %s（%d 条）===" % (n, len(reds)))
        for l in reds:
            out.append(u"   " + l[:160])
    io_out = u"\n".join(out) + u"\n"
    import io
    io.open(OUT, "w", encoding="utf-8", newline=u"\n").write(io_out)
    print(u"%d 份有红 → %s（%d 行）" % (len([l for l in out if l.startswith(u"===")]),
                                    OUT, len(out)))


if __name__ == u"__main__":
    main()
