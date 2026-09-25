# -*- coding: utf-8 -*-
u"""_zf78_docs4.py —— §9 那条反馈记录的锚点修正（我上一版把数字写成了带千分位的 `2,274,791`，
而文档里是 `%d` 打出来的 `2274791` ⇒ 锚点 0 命中）

这次按**文档里的原文**逐字取锚点，补上第四次打包的哈希与两件新功能。
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"
fails = []

OLD = (u"      这一版成品 = `bafa7853364ae22ff8f1e5e2b62aad085ed40dbb`"
       u"（2274791 B / 771 条目；同版本重打包 ⇒ 上一版 `2bf27d2c…` 作废）。")

NEW = (u"      第三次打包 = `bafa7853…`（上提 8 px）；**第四次（当前成品）= "
       u"`c9a3a492285af992bd93a11185a0d724d6d49449`**（2282004 B / 773 条目）—— 就是你点名的两件：\n"
       u"      ① **右键容器倒流体**：手上拿油桶（或任何流体容器）右键操作器 ⇒ 往**石油罐**倒 "
       u"1000 mB/次（罐里余量不足 1000 就倒多少算多少；罐满 / 流体不对 ⇒ 一滴不倒、"
       u"容器内容物一点不丢；空容器提示「手里的容器是空的」）。逻辑抽成 "
       u"`DistillationOperatorBlock.pourFrom`（纯函数），探针在没有玩家的服务端上直接验它"
       u"（§4.43 那一课：能不碰玩家对象就不碰）。\n"
       u"      ② **右击控制器显示排查信息**：数到塔 ⇒ 报「检测到 N 座分馏塔（最多认 4 座）」；"
       u"一座都没数到 ⇒ 报**最像的那一处**的第一处不符：第几层第几排第几列 + 坐标 + 应该是什么 + "
       u"实际是什么 + 112 格里错了几格（`DistillationTowerStructure.diagnose`）；"
       u"控制器**仍然没有 GUI**（不开界面、不存状态）。\n"
       u"      **探针在这轮抓到两个我自己的错**：㈠ 诊断候选里有个「退化锚点」—— 塔底正好落在"
       u"**控制器自己那格**（1 格不符 + 距离 0）⇒ 把真正只差一格的塔挤掉了；修法 ="
       u"「跳过包围盒里装着控制器的锚点」（控制器是实心方块、塔里不可能有它 ⇒ 这条跳过永远安全）"
       u"+ 给判分加第二判据「第一处不符越靠后越像」；㈡ 我探针里「拆」的那一格按图纸本来就是"
       u"**空腔**（第 4 层 `2..2`）⇒ 等于没拆、假 FAIL（老毛病：先怀疑期望）。探针 **125 项全 [OK]**。")


def main():
    t = io.open(DOC, encoding="utf-8").read()
    hits = t.count(OLD)
    if hits != 1:
        print(u"  [FAIL] 锚点命中 %d 次（必须 1 次）" % hits)
        return 1
    io.open(DOC, "w", encoding="utf-8", newline=u"\n").write(t.replace(OLD, NEW, 1))
    print(u"  [OK]   §9 反馈条目：补第四次打包 + 两件新功能 + 两个自捉 bug")
    after = io.open(DOC, encoding="utf-8").read()
    if u"c9a3a492285af992bd93a11185a0d724d6d49449" not in after:
        print(u"  [FAIL] 写完之后文档里还是没有新哈希")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
