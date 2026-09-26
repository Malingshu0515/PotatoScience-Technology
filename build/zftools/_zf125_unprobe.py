# -*- coding: utf-8 -*-
u"""_zf125_unprobe.py —— 跑完把探针卸干净（ZF125）

四步：① 先抄存档到 `check/Zf125Check.java`；② 摘掉 `PotatoST` 里那一行钩子；
③ 删 src 里的探针；④ 逐字节证明 `PotatoST.java` 回到**预期状态**。

⚠ 这里的"预期状态"不是改前件原样：ZF125 本来就往 `PotatoST.java` 里插了一段
   （㊿/51 两处能力登记）。所以判据是「改前件 + ZF125 那一段插入」——
   脚本里把那段插入**原样重写一遍**（与 `_zf125_java.py` 的 D_NEW 逐字相同），
   抠掉它与钩子行之后必须与 `zf125_pre` 里的改前件逐字节相同。

跑法：
    python build\\zftools\\_zf125_unprobe.py
"""
import difflib
import hashlib
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
SRC = os.path.join(JAVA, "Zf125Check.java")
ARCH = os.path.join(ROOT, r"build\zftools\check\Zf125Check.java")
MAIN = os.path.join(JAVA, "PotatoST.java")
BK = r"C:\PotatoST救援\zf125_pre\src\main\java\com\potatost\mod\PotatoST.java"
HOOK = u"        Zf125Check.register();   // ← 临时探针（ZF125），跑完删\n"

# 第一版只摘了钩子那一行 ⇒ 多留一个空行；这两条是"善后"用的原样文本
STRAY = (u"        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener("
         u"StarfallRitualManager::onPlayerLogin);\n\n\n    }\n")
GOOD = (u"        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener("
        u"StarfallRitualManager::onPlayerLogin);\n\n    }\n")

# 与 `_zf125_java.py` 的 D_NEW 逐字相同（改前件 + 这一段 == 预期状态）
INSERT = u"""
        // ㊿ 大型柴油发电机（0.11 ZF125）：**出电口挂在接线口那一格**，控制器本体不登记能量能力 ——
        //     这是本工程多方块机器的老规矩（电力高炉 / 合金炉都是"电只从接线口走"）。
        //     接线口交出来的是"只出不进"的接口（canExtract 恒真），邻居的 INPUT 端子会主动来抽；
        //     结构没成型时 getEnergyStorage() 返回 null ⇒ 整个能力不存在。
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.DIESEL_GENERATOR_PORT_BE.get(),
                (port, side) -> port.getEnergyStorage());

        // 51 大型柴油发电机：8000 mB 柴油罐 —— **只进不出**（泵灌得进来、一滴抽不出去）。
        //     控制器本体与接线口**都**登记：玩家把泵放控制器正面、或放机器顶上（接线口上方）都能喂它，
        //     两条路没有方向限制（用户原话「可以用流体泵泵入柴油」）。
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.DIESEL_GENERATOR_BE.get(),
                (machine, side) -> machine.getFluidHandler());
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.DIESEL_GENERATOR_PORT_BE.get(),
                (port, side) -> port.getFluidHandler());
"""

fails, notes = [], []


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.exists(SRC):
        shutil.copy2(SRC, ARCH)
        if sha(SRC) != sha(ARCH):
            fails.append(u"存档哈希不一致")
        else:
            notes.append(u"① 存档 %s（%d B，sha1 %s）" % (ARCH, os.path.getsize(ARCH), sha(ARCH)[:16]))
    else:
        notes.append(u"① src 里已经没有探针源文件（可能已经卸过）")

    text = io.open(MAIN, encoding="utf-8", newline=u"").read()
    nl = u"\r\n" if u"\r\n" in text else u"\n"
    hook = HOOK.replace(u"\n", nl)
    # 挂载时插的是「空行 + 钩子行 + 空行」⇒ 摘的时候要连**紧挨着的那一个空行**一起摘，
    # 否则会留下一个多余空行（第一版就是只摘了钩子那一行，收尾的逐字节比对当场抓到）。
    hook_pad = nl + hook
    if hook_pad in text:
        io.open(MAIN, "w", encoding="utf-8", newline=u"").write(text.replace(hook_pad, u"", 1))
        notes.append(u"② 摘掉 PotatoST 里那一行挂载（连它前面那个空行一起）")
    elif hook in text:
        # 只有钩子行（有人手工加的写法）：摘掉它，再把多出来的空行收掉
        fixed = text.replace(hook, u"", 1).replace(nl + nl + nl + u"    }" + nl,
                                                   nl + nl + u"    }" + nl, 1)
        io.open(MAIN, "w", encoding="utf-8", newline=u"").write(fixed)
        notes.append(u"② 摘掉钩子行并收掉多出来的空行")
    elif STRAY.replace(u"\n", nl) in text:
        # 钩子已经摘过了、但留下了一个多余空行（本脚本第一版跑过一次的状态）
        io.open(MAIN, "w", encoding="utf-8", newline=u"").write(
            text.replace(STRAY.replace(u"\n", nl), GOOD.replace(u"\n", nl), 1))
        notes.append(u"② 钩子早摘过了 —— 这次只收掉上次留下的那个多余空行")
    elif u"Zf125Check" not in text:
        notes.append(u"② PotatoST 里本来就没有挂载（已经卸过）")
    else:
        fails.append(u"PotatoST 里还有 Zf125Check，但找不到那一行的原样文本 —— 别再瞎删")

    if os.path.exists(SRC):
        os.remove(SRC)
        notes.append(u"③ 删掉探针源文件 Zf125Check.java")

    after = io.open(MAIN, encoding="utf-8", newline=u"").read()
    if u"Zf125Check" in after:
        fails.append(u"PotatoST.java 里还残留 Zf125Check")
    if os.path.exists(SRC):
        fails.append(u"探针源文件还在 src")
    if not os.path.exists(ARCH):
        fails.append(u"存档不在 check/")

    # ---- ④ 与「改前件 + ZF125 那一段能力登记」逐字节比 ----
    # ⚠ 那一段是插在 `registerCapabilities` **中间**的（锂电池构造间那条注释之后），
    #    不是文件末尾 ⇒ 判据必须是"把这一段原样抠掉之后 == 改前件"，不能拿改前件去拼尾巴。
    if not os.path.exists(BK):
        fails.append(u"改前件不在：%s" % BK)
    else:
        before = io.open(BK, encoding="utf-8", newline=u"").read()
        ins = INSERT.replace(u"\n", nl)
        cur = after
        if cur.count(ins) != 1:
            fails.append(u"能力登记那一段在现状里命中 %d 次（要 1 次）—— 别瞎抠" % cur.count(ins))
        else:
            stripped = cur.replace(ins, u"", 1)
            if stripped == before:
                notes.append(u"④ 抠掉能力登记那一段后 == 改前件（逐字节，%d B ↔ %d B）"
                             % (len(stripped.encode(u"utf-8")), len(before.encode(u"utf-8"))))
            else:
                diff = difflib.unified_diff(before.split(u"\n"), stripped.split(u"\n"),
                                            u"改前件", u"抠掉之后", lineterm=u"", n=1)
                for l in list(diff)[:24]:
                    print(u"  " + l[:150])
                fails.append(u"PotatoST.java 没有回到预期状态")

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
