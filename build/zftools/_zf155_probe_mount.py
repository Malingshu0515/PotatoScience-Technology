# -*- coding: utf-8 -*-
r'''_zf155_probe_mount.py —— 挂上 ZF155 的临时探针（往 `PotatoST.java` 构造器末尾加两行）

⚠ 汇合点文件只准加行（§4.7）：只插这一块，别的一个字节不动；
  跑完必须用 `_zf155_unprobe.py` 摘掉，并逐字节核对回到改前件（`zf155_pre`）。

⚠ 锚点沿用 ZF151 那次的**结构性锚点**（构造器收尾 `}` + 下一个方法签名）：
   上次锚在"别人探针那一行"上，结果别人把那一行摘了 ⇒ 挂载静默失败 ⇒ runServer 不 halt、
   反证脚本超时 900 秒。结构性锚点不会因为别人加删监听而变。

跑法：python build\zftools\_zf155_probe_mount.py [--write]
'''
import hashlib
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
POT = os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java")
PRE = os.path.join(r"C:\PotatoST救援", "zf155_pre", r"src\main\java\com\potatost\mod\PotatoST.java")

BLOCK = (u"\n        // \u26a0\u26a0 临时探针（ZF155）：通用升级模板（真\u00b7通用 + 冲突即禁用），"
         u"跑完由 _zf155_unprobe.py 删掉\n        Zf155Check.register();")
# ⚠ 锚点必须**把前面那行空行一起吃掉**（ZF155 实测踩到）：
#   上一版锚点是 `    }\n\n    private void registerCapabilities(`，而插入的东西自带一个前导 `\n`
#   ⇒ 挂载后 `));` 与注释之间多出一行、`    }` 前多出一行；`unprobe` 只删 BLOCK ⇒ **摘完比改前多 2 行空白**。
#   （ZF151 那条线当时看到这个差异，把它记成"别人这几分钟改的"——其实是我这套锚点的必然产物。）
#   把 `\n\n` 放进锚点、再由替换把它原样写回去，挂载/卸载就**严格互逆**了。
ANCHOR = (u"\n\n    }\n\n    private void registerCapabilities(RegisterCapabilitiesEvent event) {\n")
TAIL = (u"\n\n    }\n\n    private void registerCapabilities(RegisterCapabilitiesEvent event) {\n")


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    write = u"--write" in argv
    text = io.open(POT, encoding=u"utf-8", newline=u"").read()
    if u"Zf155Check" in text:
        print(u"  [跳过] PotatoST.java 里已经有 Zf155Check（幂等）")
        return 0
    if text.count(ANCHOR) != 1:
        print(u"!! 锚点命中 %d 次（应为 1）—— 停手，先看清构造器末尾" % text.count(ANCHOR))
        return 1
    new = text.replace(ANCHOR, BLOCK + TAIL, 1)
    if not write:
        print(u"（没加 --write，只算不写）待插入：%r" % BLOCK)
        return 0
    io.open(POT, u"w", encoding=u"utf-8", newline=u"").write(new)
    assert io.open(POT, encoding=u"utf-8", newline=u"").read() == new
    print(u"已挂上；%s" % sha1(POT))
    print(u"改前件 %s" % (sha1(PRE) if os.path.exists(PRE) else u"(不在)"))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
