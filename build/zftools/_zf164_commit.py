# -*- coding: utf-8 -*-
u"""_zf164_commit.py —— 只把我的路径 `git add` 进暂存区并提交（§4：绝不 `git add -A`）。

跑法：python build\\zftools\\_zf164_commit.py            # 只列清单
      python build\\zftools\\_zf164_commit.py --write --commit
"""
import glob
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
PATHS = [
    r"build.gradle",
    r"libs\Mekanism-1.21.1-10.7.19.85.jar",
    r"src\main\java\com\potatost\mod\MekChemicalBridge.java",
    r"src\main\java\com\potatost\mod\FillingMachineBlockEntity.java",
    r"build\zftools\check\Zf164Check.java",
    r"build\zftools\_zf164_plan.md",
    r"build\zftools\_zf149_verify.py",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.13.jar",
    r"release\PotatoST-0.13.jar.sha1",
    # 本轮的一份性报告（可复现的证据）
    r"build\zftools\_zf164_probe_utf8.txt",
    r"build\zftools\_zf164_gatesnap.txt",
]
MSG = u"ZF164 0.13：灌装机 × Mekanism —— 喷气背包能灌我们的氢了（0.13）"


def main(argv):
    write = u"--write" in argv
    paths = list(PATHS) + sorted(glob.glob(os.path.join(ZT, u"_zf164_*.py")))
    paths = sorted(set(p.replace(u"/", os.sep) for p in paths))
    exist, missing = [], []
    for p in paths:
        (exist if os.path.exists(os.path.join(ROOT, p)) else missing).append(p)
    print(u"要 add 的路径 %d 个（不在盘上的 %d 个）" % (len(exist), len(missing)))
    for m in missing:
        print(u"  （不在盘上）%s" % m)
    if not write:
        for p in exist:
            print(u"  " + p)
        return 0
    r = subprocess.run([u"git", u"-C", ROOT, u"add", u"--"] + exist,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(r.stdout.decode("utf-8", "replace"))
    staged = subprocess.run([u"git", u"-C", ROOT, u"diff", u"--cached", u"--name-status"],
                            stdout=subprocess.PIPE).stdout.decode("utf-8", "replace")
    print(u"----- 暂存区 -----")
    print(staged)
    print(u"暂存条目 = %d" % len([l for l in staged.split(u"\n") if l.strip()]))
    if u"--commit" in argv:
        r2 = subprocess.run([u"git", u"-C", ROOT, u"commit", u"-m", MSG],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(r2.stdout.decode("utf-8", "replace"))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
