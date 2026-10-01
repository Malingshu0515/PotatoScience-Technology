# -*- coding: utf-8 -*-
r'''_zf156_probe_mount.py —— 挂上 ZF156 的临时探针（① 拷探针类 ② 往 `PotatoST.java` 构造器末尾加一行）

⚠ 汇合点文件只准加行（§4.7）：只插这一块，别的一个字节不动；
   跑完必须用 `_zf156_unprobe.py` 摘掉，并逐字节核对回到改前件（zf156_pre）。

⚠ 锚点沿用 ZF151/ZF155 那次的**结构性锚点**（构造器收尾 `}` + 下一个方法签名），
   并把前面那行空行一起吃进锚点 —— 这样挂载/卸载严格互逆（ZF155 实测踩过，档案 §4.163⑤）。

跑法：python build\zftools\_zf156_probe_mount.py [--write]
'''
import hashlib
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
POT = os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java")
SRC_CHECK = os.path.join(ROOT, r"build\zftools\check\Zf156Check.java")
DST_CHECK = os.path.join(ROOT, r"src\main\java\com\potatost\mod\Zf156Check.java")
PRE = os.path.join(r"C:\PotatoST救援", "zf156_pre", r"src\main\java\com\potatost\mod\PotatoST.java")

BLOCK = (u"\n        // \u26a0\u26a0 临时探针（ZF156）：① 端子连线 ② 手册只发一次 ③ 金属板跨 mod，"
         u"跑完由 _zf156_unprobe.py 删掉\n        Zf156Check.register();")
ANCHOR = (u"\n\n    }\n\n    private void registerCapabilities(RegisterCapabilitiesEvent event) {\n")
TAIL = (u"\n\n    }\n\n    private void registerCapabilities(RegisterCapabilitiesEvent event) {\n")


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    write = u"--write" in argv
    text = io.open(POT, encoding=u"utf-8", newline=u"").read()
    if u"Zf156Check" in text:
        print(u"  [跳过] PotatoST.java 里已经有 Zf156Check（幂等）")
        return 0
    others = [n for n in (u"Zf151Check", u"Zf153Check", u"Zf155Check", u"Zf148Check")
              if n in text]
    if others:
        print(u"!! 盘上还挂着别人的探针：%s —— 先等它撤（§4.7 汇合点别叠罗汉）" % u", ".join(others))
        return 1
    if text.count(ANCHOR) != 1:
        print(u"!! 锚点命中 %d 次（应为 1）—— 停手，先看清构造器末尾" % text.count(ANCHOR))
        return 1
    if os.path.exists(DST_CHECK):
        print(u"!! %s 已存在 —— 停手，先弄清是谁的" % DST_CHECK)
        return 1
    new = text.replace(ANCHOR, BLOCK + TAIL, 1)
    if not write:
        print(u"（没加 --write，只算不写）待插入：%r" % BLOCK)
        return 0
    shutil.copy2(SRC_CHECK, DST_CHECK)
    assert sha(SRC_CHECK) == sha(DST_CHECK), u"探针类拷贝后哈希不一致"
    io.open(POT, u"w", encoding=u"utf-8", newline=u"").write(new)
    assert io.open(POT, encoding=u"utf-8", newline=u"").read() == new
    print(u"已挂上探针类 %s（%s）" % (os.path.basename(DST_CHECK), sha(DST_CHECK)[:12]))
    print(u"PotatoST.java 现在 %s" % sha(POT)[:12])
    print(u"改前件 %s" % (sha(PRE)[:12] if os.path.exists(PRE) else u"(不在)"))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
