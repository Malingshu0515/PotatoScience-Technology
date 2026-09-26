# -*- coding: utf-8 -*-
r"""_rzh_run_verifiers.py —— 把 zftools 下所有往轮门的校验器跑一遍，只报结论行。

为什么需要：这个仓库的平行线共用一棵树，每轮都可能有别的线的门变红。
翻译线只关心"我这一改有没有把**本来绿的**门弄红"。所以这个脚本：

  1. 只跑文件名像校验器的（`*_verify.py` / `*_check*.py`），按名字排序；
  2. 每个门单独起进程、给超时，崩了也算一条结果，不拖垮整轮；
  3. 只截末尾几行（各门的结论都在末尾），全量日志写进 `_rzh_verifiers.log`。

⚠ 只读：不写任何语言文件、不改任何源码。
用法：`python build/zftools/_rzh_run_verifiers.py [关键字过滤]`
"""
from __future__ import print_function
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LOG = os.path.join(HERE, u"_rzh_verifiers.log")


def find_verifiers():
    names = []
    for n in sorted(os.listdir(HERE)):
        if not n.endswith(u".py"):
            continue
        if u"_verify" in n or u"_check" in n.lower():
            if n.startswith(u"_rzh_run_verifiers"):
                continue
            names.append(n)
    return names


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else u""
    names = [n for n in find_verifiers() if want in n]
    print(u"共 %d 个校验器%s\n" % (len(names), (u"（过滤 %r）" % want) if want else u""))

    log = []
    summary = []
    for n in names:
        try:
            p = subprocess.run([sys.executable, os.path.join(HERE, n)],
                               cwd=ROOT, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=300)
            out = p.stdout.decode(u"utf-8", u"replace")
            rc = p.returncode
        except subprocess.TimeoutExpired:
            out, rc = u"<超时 300 秒>", -9
        except Exception as e:                      # noqa: BLE001
            out, rc = u"<起不来: %s>" % e, -1

        log.append(u"\n" + u"=" * 78 + u"\n== %s (exit %s)\n" % (n, rc) + u"=" * 78 + u"\n" + out)

        tail = [l for l in out.split(u"\n") if l.strip()][-6:]
        fails = re.findall(u"(失败项[^0-9]*\\d+|\\bFAIL\\b|不通过|\\d+\\s*条?失败)", out)
        summary.append((n, rc, fails[-1] if fails else u"", tail))

    with io.open(LOG, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(u"\n".join(log))
    print(u"全量日志 -> %s\n" % LOG)

    green = red = 0
    for n, rc, mark, tail in summary:
        ok = (rc == 0)
        green += 1 if ok else 0
        red += 0 if ok else 1
        print(u"%-28s exit=%-4s %s" % (n, rc, u"绿" if ok else (u"红  " + mark)))
    print(u"\n合计：绿 %d / 红 %d（共 %d）" % (green, red, len(summary)))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
