# -*- coding: utf-8 -*-
u"""_zf148_api.py —— ZF148 侦察⑧：探针要用到的两个 API 事实。

① `CreativeModeTab` 在 1.21.1 里怎么把物品列表拿出来（想验证帕秋莉的
   `creative_tab` 键到底有没有把手册塞进我们那个物品栏）；
② 帕秋莉 `Book` 的字段是不是 public（探针要直接读 id / name / creativeTab）。
"""
import io
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")
SRC = r"E:\PotatoST\.gradle\repositories\ng_dummy_ng\net\neoforged\neoforge\21.1.235\neoforge-21.1.235-sources.jar"
JAR = r"E:\PotatoST\libs\Patchouli-1.21.1-93-NEOFORGE.jar"

z = zipfile.ZipFile(SRC)
src = z.read(u"net/minecraft/world/item/CreativeModeTab.java").decode(u"utf-8", u"replace")
print(u"======== CreativeModeTab 的公开方法 ========")
for i, ln in enumerate(src.split(u"\n")):
    s = ln.strip()
    if s.startswith(u"public ") and u"(" in s and u")" in s:
        print(u"%5d: %s" % (i + 1, s))
    if u"buildContents" in s and u"*" not in s:
        print(u"%5d: %s" % (i + 1, s))
z.close()

print(u"")
print(u"======== 帕秋莉 Book 的字段（javap） ========")
import subprocess
out = subprocess.run([r"C:\Program Files\Microsoft\jdk-21.0.10.7-hotspot\bin\javap.exe",
                      u"-p", u"-classpath", JAR, u"vazkii.patchouli.common.book.Book"],
                     capture_output=True)
txt = out.stdout.decode(u"utf-8", u"replace")
for ln in txt.split(u"\n"):
    if u"public" in ln and u"(" not in ln:
        print(u"  " + ln.strip())
    elif u"class Book" in ln:
        print(u"  " + ln.strip())
