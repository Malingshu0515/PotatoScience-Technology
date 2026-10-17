# -*- coding: utf-8 -*-
u"""_zf202_fix.py —— 收尾补丁（本轮自己踩的两处）。

① `_zf186_verify.py` / `_zf196_repack.py` 里那些 **`zfNNN_pre` 备份路径**被 0.15→0.16 / 0.14→0.15
   的替换连坐改坏了（它们是**历史备份里那份 jar**，必须指回 0.14）⇒ 还原成 0.14。
   教训：替换"当前成品"路径时，**凡含 `_pre` / `pre_jar` / `PRE_JAR` 的行一律跳过**（_zf202_bump.py 的护栏
   只挡了 `OLD_JAR`，不够）。
② `_zf198_verify.py`（常驻门）的 D2 里还残留 `ver.group(1) == u"0.15"` 与标签里的 0.15 ⇒ 跟到 0.16。

跑法：python build\\zftools\\_zf202_fix.py [--write]
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")
ZT = os.path.join(r"E:\PotatoST\PotatoSTneoforge1.21.1", "build", "zftools")

FIXES = [
    (u"_zf186_verify.py", u'r"release\\PotatoST-0.16.jar"', u'r"release\\PotatoST-0.14.jar"'),
    (u"_zf196_repack.py", u'"zf196_pre", "release", u"PotatoST-0.16.jar"',
     u'"zf196_pre", "release", u"PotatoST-0.14.jar"'),
    (u"_zf196_repack.py", u'"zf196_pre", "release", u"PotatoST-0.15.jar"',
     u'"zf196_pre", "release", u"PotatoST-0.14.jar"'),
    (u"_zf198_verify.py", u'ver.group(1) == u"0.15"', u'ver.group(1) == u"0.16"'),
    (u"_zf198_verify.py", u'D2 jar 内 `version=\\"0.15\\"`', u'D2 jar 内 `version=\\"0.16\\"`'),
]


def main(argv):
    write = u"--write" in argv
    n_ok = 0
    for fn, a, b in FIXES:
        p = os.path.join(ZT, fn)
        t = io.open(p, encoding="utf-8", newline=u"").read()
        if b in t and a not in t:
            print(u"  %-20s 已是目标形态，跳过" % fn)
            n_ok += 1
            continue
        if a not in t:
            print(u"  %-20s 锚点找不到：%s" % (fn, a[:40]))
            continue
        t = t.replace(a, b)
        print(u"  %-20s 修 %s → %s" % (fn, a[-26:], b[-26:]))
        if write:
            io.open(p, "w", encoding="utf-8", newline=u"").write(t)
        n_ok += 1
    # 复查：常驻门里不许再有 0.15 的版本断言
    bad = []
    for fn in (u"_zf186_verify.py", u"_zf196_repack.py", u"_zf198_verify.py"):
        t = io.open(os.path.join(ZT, fn), encoding="utf-8").read()
        for m in re.finditer(u'PotatoST-0\\.1[56]\\.jar', t):
            line_start = t.rfind(u"\n", 0, m.start()) + 1
            line = t[line_start:t.find(u"\n", m.end()) if t.find(u"\n", m.end()) > 0 else len(t)]
            if u"_pre" in line or u"PRE_JAR" in line or u"pre_jar" in line:
                if u"PotatoST-0.14.jar" not in line:
                    bad.append((fn, line.strip()[:90]))
    print(u"复查（备份路径必须是 0.14）：%s" % (bad or u"干净"))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
