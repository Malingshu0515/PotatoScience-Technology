# -*- coding: utf-8 -*-
u"""_zf148_stack.py —— ZF148 侦察⑦：1.21.1 的 ItemStack 编解码器到底认不认 `components`。

配方产物要带 `patchouli:book` 组件（不带就是一本废书），所以必须确认
① 组件字段叫什么；② 组件的 Codec 是「完整对象」还是「补丁」。
直接翻 neoforge-21.1.235-sources.jar 里的 ItemStack.java / DataComponentPatch.java。
"""
import io
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")
JAR = r"E:\PotatoST\.gradle\repositories\ng_dummy_ng\net\neoforged\neoforge\21.1.235\neoforge-21.1.235-sources.jar"

z = zipfile.ZipFile(JAR)
target = u"net/minecraft/world/item/ItemStack.java"
src = z.read(target).decode(u"utf-8", u"replace")
lines = src.split(u"\n")
print(u"---- %s（%d 行）里 CODEC 附近 ----" % (target, len(lines)))
for i, ln in enumerate(lines):
    if u"CODEC" in ln or u"MAP_CODEC" in ln or u"components" in ln.lower() and u"Codec" in ln:
        print(u"%5d: %s" % (i + 1, ln.rstrip()))
z.close()

print(u"")
print(u"---- DataComponentPatch 的 Codec 定义 ----")
z = zipfile.ZipFile(JAR)
target2 = u"net/minecraft/core/component/DataComponentPatch.java"
src2 = z.read(target2).decode(u"utf-8", u"replace")
for i, ln in enumerate(src2.split(u"\n")):
    if (u"CODEC" in ln or u"Codec" in ln) and u"static" in ln:
        print(u"%5d: %s" % (i + 1, ln.rstrip()))
z.close()
