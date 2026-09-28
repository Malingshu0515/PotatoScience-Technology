# -*- coding: utf-8 -*-
r'''_zf151_probe_mount.py —— 挂上 ZF151 的临时探针（往 `PotatoST.java` 构造器末尾加两行）

⚠ 汇合点文件只准加行（§4.7）：只插这一块，别的一个字节不动；
  跑完必须用 `_zf151_unprobe.py` 摘掉，并逐字节核对回到改前件（`zf151_pre`）。

跑法：python build\zftools\_zf151_probe_mount.py [--write]
'''
import hashlib
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
POT = os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java")
PRE = os.path.join(r"C:\PotatoST救援", "zf151_pre", r"src\main\java\com\potatost\mod\PotatoST.java")

BLOCK = (u"\n        // \u26a0\u26a0 临时探针（ZF151）：挖掘口径（太阳能板掉落 / 镐子标签 / 空手掉落），"
         u"跑完由 _zf151_unprobe.py 删掉\n        Zf151Check.register();")

# ⚠ 锚点从 ZF148 那次的「StarfallRitualManager::onPlayerLogin」改到**别人探针那一行之后**：
#   ZF149/ZF150 之间另一条线把自己的 `Zf150Check.register();` 挂进了同一个构造器
#   ⇒ 本轮插在它**后面**，一个字都不碰它（§4.7 多线共树：只加自己的行）。
# ⚠ 锚点第二次改：原来是"插在 ZF150 探针那一行后面"，可**他们把那一行摘掉了**
#   ⇒ 锚点消失 ⇒ 挂载静默失败 ⇒ 服务器不 halt、反证脚本超时 900 秒（真踩了）。
#   现在改成**构造器末尾 + 下一个方法签名**这段（结构性的、不会因为别人加删监听而变化）。
ANCHOR = (u"    }\n\n    private void registerCapabilities(RegisterCapabilitiesEvent event) {\n")


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    write = u"--write" in argv
    text = io.open(POT, encoding=u"utf-8", newline=u"").read()
    if u"Zf151Check" in text:
        print(u"  [跳过] PotatoST.java 里已经有 Zf151Check（幂等）")
        return 0
    if text.count(ANCHOR) != 1:
        print(u"!! 锚点命中 %d 次（应为 1）—— 停手，先看清构造器末尾" % text.count(ANCHOR))
        return 1
    # ⚠ 插在**构造器里面**：`BLOCK` 在前、构造器的收尾 `}` 在后。
    #   第一版写成 `u"    }" + BLOCK + …` ⇒ 把语句插到了**类体里** ⇒ javac 报
    #   `需要<标识符>`，指的就是 `Zf151Check.register();` 那一句（本轮真踩，浪费了两轮开服）。
    new = text.replace(ANCHOR,
                       BLOCK + u"\n\n    }\n\n    private void registerCapabilities("
                       u"RegisterCapabilitiesEvent event) {\n", 1)
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
