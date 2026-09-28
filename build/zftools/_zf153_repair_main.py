# -*- coding: utf-8 -*-
u"""_zf153_repair_main.py —— 把 PotatoST.java 重建成「改前件 + 本轮那 12 行」，不多不少

为什么需要这一步：探针挂载/摘除脚本第一版的过滤器漏了挂载块注释的第二行，
① 摘不干净（那一行留在了文件里），② 连**基准快照**也把残留拍了进去。
结果现在文件里多了两行空行、基准里多了一行残留注释 —— 两边都不干净。

与其继续"减法修补"，不如**确定性重建**：
    改前件（zf153_pre 里那份，逐字节可信） + 本轮功能块（锚点唯一、插入位置确定）
⇒ 结果与"人手写一遍"应当逐字节相同；与改前件的差**必须正好是那 12 行**。

跑法：python build\\zftools\\_zf153_repair_main.py
"""
import difflib
import hashlib
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
MAIN = os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java")
PRE = r"C:\PotatoST救援\zf153_pre\src\main\java\com\potatost\mod\PotatoST.java"
NOPROBE = os.path.join(ROOT, r"build\zftools\check\zf153_PotatoST_noprobe.java")

ANCHOR = u"addListener(StarfallRitualManager::onPlayerLogin);"
BLOCK = u"""        // 振金剑（0.12 ZF153）：① 「拿在手里免疫凋零/缓慢/挖掘疲劳」的**源头**那一半 ——
        //    MobEffectEvent.Applicable ⇒ DO_NOT_APPLY。为什么不每 tick 抹掉了事：
        //    LivingEntity.addEffect 的**第一行**就是这个 hook（:972，本轮从 sources.jar 抠的），
        //    从源头拒绝 ⇒ 凋零那 40 tick 一跳的伤害压根不会发生。
        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(
                VibraniumSwordItem::onEffectApplicable);
        // ② 同一件事的**清理**那一半：拿着剑时，身上已经有的那三种效果立刻掉
        //    （只在服务端改、靠原版的效果同步送客户端 —— 与上面斧子那条同源）
        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(
                (net.neoforged.neoforge.event.tick.PlayerTickEvent.Post event) ->
                        VibraniumSwordItem.onPlayerTick(event.getEntity()));
"""


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    fails = []
    pre = io.open(PRE, encoding="utf-8").read()
    lines = pre.split(u"\n")
    # ⚠ 改前件里带着**别人探针的残留**：他们 13:47 挂的 `Zf151Check.register();` 在 13:52
    #   我还原样拍进了备份，而他们随后就撤了（探针类已经不在盘上 ⇒ 重建时必须一起剔掉，
    #   否则会引用一个不存在的类、编译当场炸）。判据用"是不是别人探针那几行"，不是删所有注释。
    drop = [i for i, l in enumerate(lines)
            if u"Zf151Check" in l or u"Zf152Check" in l or u"ZF151" in l or u"ZF152" in l]
    print(u"  改前件里要剔掉的别人探针行：%d 行（行号 %s）"
          % (len(drop), u"、".join(str(i + 1) for i in drop)))
    kept = [l for i, l in enumerate(lines) if i not in set(drop)]
    # 剔完应当正好空出那个块（注释 + 调用 + 空行），并且不再有任何 *Check.register()
    if any(u"Check.register()" in l for l in kept):
        fails.append(u"剔完之后还有 *Check.register() 残留")
    lines = kept
    hits = [i for i, l in enumerate(lines) if ANCHOR in l]
    if len(hits) != 1:
        print(u"  [STOP] 改前件里锚点 %d 次" % len(hits))
        return 1
    i = hits[0] + 1
    rebuilt = u"\n".join(lines[:i]) + u"\n" + BLOCK + u"\n".join(lines[i:])
    io.open(MAIN, "w", encoding="utf-8", newline=u"\n").write(rebuilt)

    now = io.open(MAIN, encoding="utf-8").read()
    diff = [l for l in difflib.unified_diff(pre.split(u"\n"), now.split(u"\n"), lineterm=u"")
            if l.startswith(u"+") and not l.startswith(u"+++")]
    added = [l for l in diff if l.strip() != u"+"]
    print(u"  与改前件的差：%d 行正文新增（本轮那两处监听 = 11 行正文 + 1 行空行）" % len(added))
    if len(added) != 11:
        fails.append(u"新增正文行数 %d ≠ 11" % len(added))
    # 逐行核：这 11 行必须与 BLOCK 的正文**逐字相同**（不是"看起来像"）
    want = [l for l in BLOCK.split(u"\n") if l.strip()]
    got = [l[1:] for l in added]
    if want != got:
        fails.append(u"新增的正文与预期块不逐字相同")
        for a, b in zip(want, got):
            if a != b:
                print(u"      期望：%s" % a)
                print(u"      实际：%s" % b)
                break
    for bad in (u"Zf151Check", u"Zf152Check", u"Zf153Check"):
        if bad in now:
            fails.append(u"文件里还有 %s" % bad)
    # 重新拍基准（这一份就是"功能改完、探针未挂"的权威版本）
    io.open(NOPROBE, "w", encoding="utf-8", newline=u"\n").write(now)
    print(u"  [OK] 重建完成：%s（sha1 %s）" % (os.path.relpath(MAIN, ROOT), sha(MAIN)))
    print(u"  [OK] 基准重拍：%s（sha1 %s）" % (os.path.relpath(NOPROBE, ROOT), sha(NOPROBE)))
    print(u"  新增的 12 行：")
    for l in diff:
        print(u"      " + l)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
