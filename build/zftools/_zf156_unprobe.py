# -*- coding: utf-8 -*-
r'''_zf156_unprobe.py —— 摘掉 ZF156 探针，并**逐字节**核对 `PotatoST.java` 回到「本轮真实改动、但没探针」那一版。

⚠ 本轮与 ZF155 那次不同：`PotatoST.java` 里**本来就有一处真实改动**
  （注册附件表 `ModAttachments.ATTACHMENT_TYPES.register(modEventBus);`）。
  所以自检的基准不是"改前件"，而是"改前件 + 本轮那一处真实改动" ——
  拿改前件直接比会显示不一致，那是**基准选错**，不是挂载不互逆（§4.161 那条的第二种形态）。

跑法：python build\zftools\_zf156_unprobe.py [--write]
'''
import hashlib
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
POT = os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java")
DST_CHECK = os.path.join(ROOT, r"src\main\java\com\potatost\mod\Zf156Check.java")
PRE = os.path.join(r"C:\PotatoST救援", "zf156_pre", r"src\main\java\com\potatost\mod\PotatoST.java")

BLOCK = (u"\n        // \u26a0\u26a0 临时探针（ZF156）：① 端子连线 ② 手册只发一次 ③ 金属板跨 mod，"
         u"跑完由 _zf156_unprobe.py 删掉\n        Zf156Check.register();")

# 本轮对 PotatoST.java 的**真实改动**（写死在这里，供重建基准）
REAL_OLD = u"        ModDataComponents.DATA_COMPONENTS.register(modEventBus);\n"
REAL_NEW = (u"        ModDataComponents.DATA_COMPONENTS.register(modEventBus);\n"
            u"        // 玩家附件（0.13 ZF156）：手册「已经给过」的标记搬到这里 ——\n"
            u"        // 旧的 ServerPlayer.getPersistentData() 在换维度/死后重生的克隆里会被丢掉"
            u"（详见 ModAttachments 注释）。\n"
            u"        ModAttachments.ATTACHMENT_TYPES.register(modEventBus);\n")


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    write = u"--write" in argv
    text = io.open(POT, encoding=u"utf-8", newline=u"").read()
    if BLOCK in text:
        if write:
            io.open(POT, u"w", encoding=u"utf-8", newline=u"").write(text.replace(BLOCK, u"", 1))
            print(u"已摘掉探针块")
        else:
            print(u"（没加 --write，只算不写）会删掉探针块")
    else:
        print(u"  PotatoST.java 里没有探针块（已摘或还没挂）")
    if write and os.path.exists(DST_CHECK):
        os.remove(DST_CHECK)
        print(u"已删探针类 %s" % os.path.basename(DST_CHECK))

    cur = io.open(POT, encoding=u"utf-8", newline=u"").read()
    pre = io.open(PRE, encoding=u"utf-8", newline=u"").read()
    if pre.count(REAL_OLD) != 1:
        print(u"!! 基准重建失败：改前件里那行锚点命中 %d 次" % pre.count(REAL_OLD))
        return 2
    expect = pre.replace(REAL_OLD, REAL_NEW, 1)
    same = cur == expect
    print(u"现在         = %s（%d 字节）" % (sha(POT)[:16], len(cur.encode("utf-8"))))
    print(u"基准（改前+本轮真实改动） = %s（%d 字节）" % (hashlib.sha1(expect.encode("utf-8")).hexdigest()[:16],
                                                  len(expect.encode("utf-8"))))
    print(u"没有残留探针：%s" % (u"是" if u"Zf156Check" not in cur else u"**否**"))
    print(u"逐字节一致：%s" % (u"是" if same else u"**否**"))
    if not same:
        a, b = cur.split(u"\n"), expect.split(u"\n")
        for i in range(max(len(a), len(b))):
            x = a[i] if i < len(a) else u"(缺)"
            y = b[i] if i < len(b) else u"(多)"
            if x != y:
                print(u"  第一处差异 第 %d 行：\n    现在 %r\n    基准 %r" % (i + 1, x, y))
                break
    return 0 if (same and u"Zf156Check" not in cur) else 1


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
