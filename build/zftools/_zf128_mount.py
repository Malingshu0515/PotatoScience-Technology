# -*- coding: utf-8 -*-
u"""_zf128_mount.py —— 把探针挂到 `PotatoST` 构造器末尾（ZF128）

⚠ **这次挂载与卸载是严格互逆的**（ZF127 吃过"挂载吃掉一个空行、卸载没还"的亏，§4.108）：
   插入的是**单独一行钩子**（前面的空行原样留着）⇒ 卸载时只删那一行，`PotatoST.java`
   自然回到改前件，不需要"以改前件为权威"再覆盖一次。

`PotatoST.java` 是 **LF**（`.gitattributes` 是 `* -text`）⇒ 按它自己的换行插。

跑法：
    python build\\zftools\\_zf128_mount.py
"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MAIN = r"E:\PotatoST\src\main\java\com\potatost\mod\PotatoST.java"
BK = r"C:\PotatoST救援\zf128_pre\src\main\java\com\potatost\mod\PotatoST.java"
HOOK = u"        Zf128Check.register();   // ← 临时探针（ZF128），跑完删\n"
# 锚点：监听行 + 空行 + 收尾大括号（钩子插在**空行之后**，空行原样保留）
ANCHOR = u"        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(StarfallRitualManager::onPlayerLogin);\n\n    }\n"
fails, notes = [], []


def main():
    text = io.open(MAIN, encoding="utf-8", newline=u"").read()
    nl = u"\r\n" if u"\r\n" in text else u"\n"
    if u"Zf128Check" in text:
        notes.append(u"已经挂过（幂等跳过）")
    else:
        a = ANCHOR.replace(u"\n", nl)
        if text.count(a) != 1:
            fails.append(u"锚点命中 %d 次（要 1 次）—— 停手" % text.count(a))
        else:
            # ⚠ 搜索串与替换串都要用**这个文件自己的换行**拼（第一版混了字面量 \n，
            #   在 CRLF 文件上会命中 0 次 —— 这个文件恰好是 LF，但别靠运气）
            old_tail = nl + nl + u"    }" + nl
            new_tail = nl + nl + HOOK.replace(u"\n", nl) + u"    }" + nl
            new = a.replace(old_tail, new_tail, 1)
            io.open(MAIN, "w", encoding="utf-8", newline=u"").write(text.replace(a, new, 1))
            notes.append(u"挂上 %s" % HOOK.strip())
    back = io.open(MAIN, encoding="utf-8", newline=u"").read()
    if back.count(u"Zf128Check") != 1:
        fails.append(u"Zf128Check 出现 %d 次（要 1 次）" % back.count(u"Zf128Check"))
    # 自证：把那一行删掉必须**逐字节**回到改前件 ⇒ 卸载脚本只删一行就够
    stripped = back.replace(HOOK.replace(u"\n", nl), u"", 1)
    pre = io.open(BK, encoding="utf-8", newline=u"").read()
    if stripped == pre:
        notes.append(u"互逆自证：删掉那一行 == 改前件（sha1 %s）"
                     % hashlib.sha1(pre.encode("utf-8")).hexdigest()[:16])
    else:
        fails.append(u"互逆自证失败：删掉钩子后与改前件不同（差 %d 字节）"
                     % abs(len(stripped) - len(pre)))
    notes.append(u"PotatoST.java sha1 = %s" % hashlib.sha1(open(MAIN, "rb").read()).hexdigest()[:16])
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
