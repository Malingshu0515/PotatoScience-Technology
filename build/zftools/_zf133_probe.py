# -*- coding: utf-8 -*-
"""_zf133_probe.py —— ZF133 挂/卸探针（严格互逆）

挂载：在 PotatoST 构造器末尾插**一行** `Zf133Check.register();`（+ 注释）。
卸下：`--off` 把那一行原样删掉，然后**逐字节**比改前件（sha1 相等才算干净）。

⚠ ZF127/ZF128 那两轮的教训（§4.108）：挂载脚本必须自己断言"删掉 == 改前件"，
   不能等到卸的时候才发现空行/缩进对不上。

跑法：python build\\zftools\\_zf133_probe.py          （挂）
      python build\\zftools\\_zf133_probe.py --off    （卸 + 逐字节核对）
"""
import hashlib
import io
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
MAIN = os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java")
SRC = os.path.join(ROOT, r"src\main\java\com\potatost\mod\Zf133Check.java")
ARCH = os.path.join(ROOT, r"build\zftools\check\Zf133Check.java")
BK = r"C:\PotatoST救援\zf133_pre\src\main\java\com\potatost\mod\PotatoST.java"

ANCHOR = ("        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(\n"
          "                (net.neoforged.neoforge.event.tick.PlayerTickEvent.Post event) ->\n"
          "                        StarSteelAxeItem.applyHoldEffect(event.getEntity()));\n")
HOOK = ("\n        // ⚠⚠ 临时探针（ZF133）：冲击波的端到端取证，跑完由 _zf133_probe.py --off 删掉\n"
        "        Zf133Check.register();\n")

OFF = "--off" in sys.argv


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    text = io.open(MAIN, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in text else "\n"
    hook = HOOK.replace("\n", nl)

    if OFF:
        fails = []
        if os.path.exists(SRC):
            shutil.copy2(SRC, ARCH)
            if sha(SRC) != sha(ARCH):
                fails.append("存档哈希不一致")
            else:
                print("  [OK] ① 存档 %s（%d B，sha1 %s）" % (ARCH, os.path.getsize(ARCH), sha(ARCH)[:16]))
        if hook in text:
            io.open(MAIN, "w", encoding="utf-8", newline="").write(text.replace(hook, "", 1))
            print("  [OK] ② 删掉那一行钩子（连同它上面那行注释与空行）")
        elif "Zf133Check" not in text:
            print("  [OK] ② PotatoST 里本来就没有挂载")
        else:
            fails.append("PotatoST 里还有 Zf133Check，但找不到原样文本 —— 别再瞎删")
        if os.path.exists(SRC):
            os.remove(SRC)
            print("  [OK] ③ 删掉探针源文件")
        after = io.open(MAIN, encoding="utf-8", newline="").read()
        if "Zf133Check" in after:
            fails.append("PotatoST.java 里还残留 Zf133Check")
        if os.path.exists(SRC):
            fails.append("探针源文件还在 src")
        if not os.path.exists(ARCH):
            fails.append("存档不在 check/")
        if not os.path.exists(BK):
            fails.append("改前件不在：%s" % BK)
        elif sha(BK) == sha(MAIN):
            print("  [OK] ④ PotatoST.java == 本轮的改前件？（注意：改前件是**加斧子之前**的，"
                  "现在里面还有 StarSteelAxeItem 那几行，所以这里应当不等）")
        for f in fails:
            print("  [FAIL] " + f)
        print("卸下完成，失败 %d 项" % len(fails))
        return

    before = len(text)
    n = text.count(ANCHOR)
    print("锚点出现 %d 次" % n)
    assert n == 1, "锚点不唯一"
    assert "Zf133Check" not in text, "似乎已经挂过了"
    new = text.replace(ANCHOR, ANCHOR + hook, 1)
    assert len(new) == before + len(hook), "单段插入判据不成立"
    io.open(MAIN, "w", encoding="utf-8", newline="").write(new)
    print("  [OK] 已挂载：%s (+%d 字符)" % (MAIN, len(hook)))

    # 互逆自检：把刚插的删掉，必须逐字节回到原文
    check = io.open(MAIN, encoding="utf-8", newline="").read().replace(hook, "", 1)
    if check == text:
        print("  [OK] 互逆自检通过（删掉那一行 == 挂载前的原文）")
    else:
        print("  [FAIL] 互逆自检失败！挂载/卸载不是严格互逆")
        sys.exit(1)


main()
