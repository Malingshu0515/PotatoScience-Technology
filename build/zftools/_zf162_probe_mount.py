# -*- coding: utf-8 -*-
r'''_zf162_probe_mount.py —— 挂上 ZF162 的临时探针（拷一个类 + 在 `PotatoST.java` **加一行**）。

⚠ 本轮与 ZF160 不同：探针要在 **mod 总线** 上收 `RegisterCapabilitiesEvent`（给
`minecraft:diamond` 当场挂一个真的物品流体能力），而 `@EventBusSubscriber` 只能挂 game 总线
⇒ 必须由 `@Mod` 构造期调 `Zf162Check.mount(modEventBus)`。
所以挂载 = ①拷类文件 ②在 `PotatoST.java` 的 `EbfFormedTrigger.TRIGGERS.register(modEventBus);`
那一行**之后**插一行（汇合点文件"只准加行"，§4.7）。
卸载要**逐字节还原**：备份件存在 `check\PotatoST.java.before-probe-zf162`。

跑法：python build\zftools\_zf162_probe_mount.py [--write]
'''
import hashlib
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
POT = os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java")
SRC_CHECK = os.path.join(ROOT, r"build\zftools\check\Zf162Check.java")
DST_CHECK = os.path.join(ROOT, r"src\main\java\com\potatost\mod\Zf162Check.java")
BAK = os.path.join(ROOT, r"build\zftools\check\PotatoST.java.before-probe-zf162")
ANCHOR = u"        EbfFormedTrigger.TRIGGERS.register(modEventBus);"
INS = u"        Zf162Check.mount(modEventBus);   // ZF162 临时探针：mod 总线收能力注册 + 开服取证（跑完删这行）"


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    write = u"--write" in argv
    text = io.open(POT, encoding="utf-8", newline=u"").read()
    if u"\r" in text:
        print(u"  !! PotatoST.java 是 CRLF —— 本脚本按 LF 写，先停手")
        return 1
    if text.count(ANCHOR) != 1:
        print(u"  !! 锚点不唯一（出现 %d 次）" % text.count(ANCHOR))
        return 1
    if u"Zf162Check" in text:
        print(u"  [跳过] PotatoST.java 里已经有 Zf162Check（幂等）")
        return 0
    if os.path.exists(DST_CHECK):
        print(u"  [跳过] %s 已挂（幂等）" % os.path.basename(DST_CHECK))
        return 0
    objs = [n for n in (u"Zf151Check", u"Zf153Check", u"Zf155Check", u"Zf156Check", u"Zf159Check", u"Zf160Check")
            if n in text]
    if objs:
        print(u"  [情报] PotatoST.java 里还挂着别人的探针：%s" % u", ".join(objs))
    if not write:
        print(u"（没加 --write，只算不写）会拷 %s 并在锚点后插一行"
              % os.path.basename(SRC_CHECK))
        return 0
    shutil.copy2(POT, BAK)
    if sha(POT) != sha(BAK):
        print(u"  !! 备份回读不一致")
        return 1
    shutil.copy2(SRC_CHECK, DST_CHECK)
    if sha(SRC_CHECK) != sha(DST_CHECK):
        print(u"  !! 探针类回读不一致")
        return 1
    new = text.replace(ANCHOR, ANCHOR + u"\n" + INS, 1)
    with io.open(POT, "w", encoding="utf-8", newline=u"") as fh:
        fh.write(new)
    print(u"已挂上 %s（%s）" % (os.path.basename(DST_CHECK), sha(DST_CHECK)[:12]))
    print(u"PotatoST.java 加了一行：改前 %s → 现在 %s（备份 %s）"
          % (sha(BAK)[:12], sha(POT)[:12], os.path.basename(BAK)))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
