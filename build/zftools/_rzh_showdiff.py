# -*- coding: utf-8 -*-
r"""_rzh_showdiff.py —— 把语言文件的**未提交改动**逐条列成「旧 -> 新」，UTF-8 落盘。

为什么不用 `git diff`：PowerShell 把 git 的 UTF-8 输出按 GBK 解码，中文全成乱码；
再叠加 `>` 重定向写 UTF-16，read 工具直接拒读。所以自己走 git 的 stdout 字节流。

用法：`python build/zftools/_rzh_showdiff.py [语言]`
"""
from __future__ import print_function
import io
import json
import os
import subprocess
import sys

GIT = r"C:\Program Files\Git\cmd\git.exe"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REL = u"src/main/resources/assets/potato_s_t/lang/%s.json"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_showdiff.txt")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]


def git_show_head(rel):
    p = subprocess.run([GIT, u"show", u"HEAD:" + rel], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        return None
    return json.loads(p.stdout.decode(u"utf-8"))


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else None
    lines = []
    for loc in LOCALES:
        if want and want != loc:
            continue
        old = git_show_head(REL % loc)
        with io.open(os.path.join(ROOT, REL % loc), encoding=u"utf-8") as f:
            new = json.load(f)
        if old is None:
            lines.append(u"%s: HEAD 里没有这个文件" % loc)
            continue
        diffs = [(k, old.get(k, u"<无>"), new.get(k, u"<无>"))
                 for k in sorted(set(old) | set(new)) if old.get(k) != new.get(k)]
        lines.append(u"")
        lines.append(u"########## %s：%d 处不同（HEAD %d 键 / 现在 %d 键）"
                     % (loc, len(diffs), len(old), len(new)))
        for k, a, b in diffs:
            lines.append(u"")
            lines.append(u"  ---- %s" % k)
            lines.append(u"   旧 %s" % a.replace(u"\n", u"\\n"))
            lines.append(u"   新 %s" % b.replace(u"\n", u"\\n"))
    with io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(u"\n".join(lines) + u"\n")
    print(u"wrote %s" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
