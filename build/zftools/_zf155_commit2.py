# -*- coding: utf-8 -*-
u"""_zf155_commit2.py —— 打包轮的提交（**只 add 我这一轮的路径**）。

与第一份 `_zf155_commit.py` 同一套纪律：显式清单 + 提交前重跑门 + 从不 `git add -A`。
⚠ 多线共树：`docs/协作日志.md`（别人新建的）与 `_zf141_recon.py` / `_zf45_recipes.py`（别人在途）
**不在清单里**，脚本会断言这一点。

跑法：python build\\zftools\\_zf155_commit2.py [--write]
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\cmd\git.exe"
ZT = os.path.join(ROOT, "build", "zftools")
MSG = os.path.join(ZT, u"_zf155_commit_msg2.txt")

MINE = [
    u"docs/UpdateAnnouncement_EN.md",
    u"docs/多会话协作交接.md",
    u"build/zftools/_zf149_verify.py",
    u"build/zftools/_zf155_verify.py",
    u"build/zftools/_zf155_falsify.py",
    u"build/zftools/_zf155_pkg.py",
    u"build/zftools/_zf155_packfix.py",
    u"build/zftools/_zf155_packcheck.py",
    u"build/zftools/_zf155_jarcheck.py",
    u"build/zftools/_zf155_commit2.py",
    u"build/zftools/_zf155_commit_msg2.txt",
]
FORBIDDEN = [u"docs/协作日志.md", u"build/zftools/_zf141_recon.py", u"build/zftools/_zf45_recipes.py"]


def git(*args):
    r = subprocess.run([GIT, u"-c", u"core.quotepath=false"] + list(args), cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def main(argv):
    write = u"--write" in argv
    bad = [f for f in FORBIDDEN if f in MINE]
    if bad:
        print(u"!! 清单里混进了别人的路径：%s" % bad)
        return 1
    existing = [f for f in MINE if os.path.exists(os.path.join(ROOT, f))]
    print(u"待提交 %d 份：" % len(existing))
    for f in existing:
        print(u"   " + f)

    print(u"\n提交前重跑三份门")
    ok = True
    for script in (u"_zf155_verify.py", u"_zf149_verify.py", u"_zf155_jarcheck.py"):
        r = subprocess.run([sys.executable, os.path.join(ZT, script)], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
        out = r.stdout.decode("utf-8", "replace")
        tail = [l for l in out.split(u"\n") if u"====" in l or u"判词" in l]
        print(u"   %-24s rc=%d  %s" % (script, r.returncode, (tail[-1].strip() if tail else u"")[:80]))
        ok = ok and r.returncode == 0

    if not write:
        print(u"\n（没加 --write：只算不写）")
        return 0 if ok else 1
    if not ok:
        print(u"\n!! 有门没绿，不提交")
        return 1
    rc, out = git(u"add", u"--", *existing)
    print(u"\ngit add rc=%d %s" % (rc, out.strip()[:200]))
    rc, out = git(u"commit", u"-F", MSG)
    print(u"commit rc=%d\n%s" % (rc, out.strip()[:1200]))
    return 0 if rc == 0 else 1


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
