# -*- coding: utf-8 -*-
u"""K14b 没咬住 —— 单独复现一次，看 A26 到底怎么算的（只读 + 临时改一处，跑完立即还原）。"""
import hashlib
import io
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
SWORD = os.path.join(ROOT, r"src\main\java\com\potatost\mod\VibraniumSwordItem.java")
VERIFY = os.path.join(ROOT, r"build\zftools\_zf153_verify.py")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


original = open(SWORD, "rb").read()
before = sha(SWORD)
text = original.decode("utf-8")
anchor = u"        target.hurtMarked = true;\n"
print(u"锚点出现 %d 次" % text.count(anchor))
patched = text.replace(anchor, anchor + u"        boolean hurt = target.hurt(source, damage);\n", 1)
io.open(SWORD, "w", encoding="utf-8", newline=u"\n").write(patched)

# 手工算一遍 A26 的两个下标（照 verify 里那段原样抄）
src = re.sub(u"/\\*.*?\\*/", u"", patched, flags=re.S)
src = re.sub(u"(?m)//.*$", u"", src)
i = src.find(u"public static boolean launch(")
j = src.find(u"private static void render(", i)
launch = src[i:j] if (i >= 0 and j >= 0) else u""
print(u"launch 切片长度 = %d" % len(launch))
print(u"target.hurt( 位置 = %d" % launch.find(u"target.hurt("))
print(u"setDeltaMovement( 位置 = %d" % launch.find(u"setDeltaMovement("))

r = subprocess.run([sys.executable, VERIFY, u"--fast"], cwd=ROOT, capture_output=True)
out = r.stdout.decode("utf-8", "replace")
for line in out.split(u"\n"):
    if u"A26" in line:
        print(u"verify 说：%s" % line)

open(SWORD, "wb").write(original)
print(u"还原：%s（%s → %s）" % (sha(SWORD) == before, before[:12], sha(SWORD)[:12]))
