# -*- coding: utf-8 -*-
u"""_zf148_font2.py —— ZF148 侦察⑤：把 1.21.1 客户端 jar 里的 font 目录整个列出来。

上一步发现 `font/include/unifont.json` 是 `{"providers":[]}`（空的），
这与「原版中文能正常显示」矛盾 ⇒ 要么 CJK 数据在别的文件（unifont.zip / unihex），
要么这个 client.jar 不是完整资源。列表一出来就有定论。
"""
import io
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")
JAR = r"E:\PotatoST\.gradle\caches\minecraft\versions\1.21.1\client.jar"

z = zipfile.ZipFile(JAR)
names = [n for n in z.namelist() if u"assets/minecraft/font/" in n]
print(u"font 目录下 %d 项：" % len(names))
for n in sorted(names):
    info = z.getinfo(n)
    print(u"  %-60s %8d B" % (n.replace(u"assets/minecraft/font/", u""), info.file_size))
z.close()

import os
d = os.path.dirname(JAR)
print(u"")
print(u"同目录里的其它 jar：")
for fn in sorted(os.listdir(d)):
    p = os.path.join(d, fn)
    if os.path.isfile(p):
        print(u"  %-40s %8.1f MB" % (fn, os.path.getsize(p) / 1048576.0))
