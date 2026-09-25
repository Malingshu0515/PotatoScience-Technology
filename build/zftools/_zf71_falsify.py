# -*- coding: utf-8 -*-
"""_zf71_falsify.py —— 反证：公告里改两个数字，事实核对必须挂

只改两处（都是"玩家会照着算"的数）：
  · 液压机 24,000 FE 一块板  ->  34,000
  · 电力高炉 10 seconds 一槽  ->  12 seconds
跑完**原样还原**（字节写回 + 核对哈希）。
"""
import hashlib
import io
import os
import subprocess
import sys

DOC = r"E:\PotatoST\docs\UpdateAnnouncement_EN.md"
VERIFY = r"E:\PotatoST\build\zftools\_zf71_verify.py"

MUTATIONS = [
    (u"**24,000 FE per plate**", u"**34,000 FE per plate**"),
    (u"each slot finishes in **10 seconds**", u"each slot finishes in **12 seconds**"),
]


def sha1(b):
    return hashlib.sha1(b).hexdigest()


def main():
    orig = io.open(DOC, "rb").read()
    text = orig.decode("utf-8")
    for old, new in MUTATIONS:
        if text.count(old) != 1:
            print(u"锚点没命中（%d 次）：%s" % (text.count(old), old))
            return 1
        text = text.replace(old, new, 1)
    io.open(DOC, "w", encoding="utf-8", newline="\n").write(text)
    print(u"已改 %d 处数字（24,000->34,000、10 s->12 s）" % len(MUTATIONS))
    try:
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        r = subprocess.run([sys.executable, VERIFY], capture_output=True, env=env)
        out = r.stdout.decode("utf-8", "replace")
        print(u"\n".join(l for l in out.split("\n") if "[FAIL]" in l or u"检查项" in l or u"失败项 =" in l))
        print(u"退出码 = %d" % r.returncode)
    finally:
        io.open(DOC, "wb").write(orig)
        back = io.open(DOC, "rb").read()
        print(u"\n已还原：%s（%s）" % (sha1(back)[:12], u"与改前一致" if back == orig else u"**不一致！**"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
