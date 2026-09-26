# -*- coding: utf-8 -*-
u"""_zf127_docs3.py —— 补 §4.109（**刀**自己出的三种毛病）+ 把 §9 那行同步

跑反证刀时抓到的三处**刀自己的毛病**（机器都没错，§4.30 家族）：

  ① **判据太弱**：`A2 银线轴登记` 原来只查片段 `durability(32)));` ——
     那段文本铜线轴 / 动力线缆轴上也有 ⇒ K207 把银线轴改成 16，**门还是绿的**。
     判据必须**连着 id / 上下文一起锚**。
  ② **刀的锚点没按文件自己的换行换算**：`TerminalBlockEntity.java` 是 CRLF，
     而刀里写的是 `\n` ⇒ K212/K213/K214 三条当场报"锚点命中 0 次"（§4.8 老雷的新面）。
  ③ **改了判据的标签文本、忘了同步刀的 `expect`** ⇒ K220 明明咬红了，却被记成"咬错了检查"。

跑法：
    python build\\zftools\\_zf127_docs3.py
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ARC = r"E:\PotatoST\docs\开发档案.md"
notes, fails = [], []

LESSON = u'''### 4.109 【刀自己的毛病】判据太弱 / 锚点没换算换行 / `expect` 忘了同步（0.11 ZF127）

反证刀的职责是"把判据咬红"，可刀自己也会出三种毛病 —— 本轮三种**全撞上**（机器都没错）：

| 毛病 | 现场 | 修法 |
|---|---|---|
| **判据太弱**：片段文本在别处也有 | `A2 银线轴登记` 原来只查 `durability(32)));` —— 铜线轴 / 动力线缆轴上同样是这句 ⇒ K207 把银线轴的 32 改成 16，**门照样全绿** | 判据要**连着 id / 上下文一起锚**（改成查 `ITEMS.register("silver_wire_spool",` + 下一整行） |
| **刀的锚点没按文件自己的换行换算** | `TerminalBlockEntity.java` 是 **CRLF**，刀里写的是 `\\n` ⇒ K212/K213/K214 三条一起报"锚点命中 0 次"（§4.8 那条老雷的新面） | 刀在动手前先探一次换行（`\\r\\n` 就用 `\\r\\n`），再拿换算后的锚点去比 |
| **改判据的标签、忘了同步刀的 `expect`** | F1 的标签从"…没有裸的 476"改成"…旧键数"之后，K220 明明把门咬红了，却被记成"咬错了检查" | 刀与被咬的判据是**一对**：改标签就一起改 `expect`，改完重跑一遍刀 |

**顺带一条**：K207 这次"没咬住"**不是白跑** —— 它是本轮**唯一**能发现那条弱判据的办法。
刀不咬，先怀疑**判据**，再怀疑刀（§4.30）。

'''

ROW_OLD = (u"| 我自己写错的判据（如实记） | **探针三条**：① 反例\"8 根铜线围空线轴不匹配任何配方\""
           u"（其实能出铜线轴）；② \"线轴用完手里是空的\"（空线轴会被塞回刚空出的那一格）；"
           u"③ \"铜线那根一 tick 1024\"（忘了给那头的端子灌电）；**常驻校验三条**："
           u"④ 拿 `pattern` 字面值比银/铜（字母不同是正常的）；⑤ F1 **自指**（标签里就写着旧数字）；"
           u"⑥ H1 用 `silver*` 通配（把银锭/银板也算进来了）—— **六条全是期望写错，机器没错**（§4.106） |")

ROW_NEW = (u"| 我自己写错的判据（如实记） | **探针三条**：① 反例\"8 根铜线围空线轴不匹配任何配方\""
           u"（其实能出铜线轴）；② \"线轴用完手里是空的\"（空线轴会被塞回刚空出的那一格）；"
           u"③ \"铜线那根一 tick 1024\"（忘了给那头的端子灌电）；**常驻校验三条**："
           u"④ 拿 `pattern` 字面值比银/铜（字母不同是正常的）；⑤ F1 **自指**（标签里就写着旧数字）；"
           u"⑥ H1 用 `silver*` 通配（把银锭/银板也算进来了）；**刀自己的三条**：⑦ 判据太弱"
           u"（`durability(32)));` 铜线轴上也有 ⇒ K207 没咬住）；⑧ 刀的锚点没按 CRLF 换算"
           u"（K212/K213/K214 报\"锚点命中 0 次\"）；⑨ 改了判据标签忘了同步刀的 `expect`"
           u"（K220 被记成\"咬错了检查\"）—— **九条全是判据/刀写错，机器没错**（§4.106 / §4.109） |")


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def main():
    t = read(ARC)
    anchor = u"## 7. 权威情报来源（怎么查原版行为，别靠记忆）"
    if u"### 4.109" in t:
        notes.append(u"§4.109 已经写过（幂等跳过）")
    elif t.count(anchor) == 1:
        io.open(ARC, "w", encoding="utf-8", newline=u"").write(t.replace(anchor, LESSON + anchor, 1))
        notes.append(u"§4 新增 4.109（刀自己的三种毛病）")
    else:
        fails.append(u"§4 锚点命中 %d 次" % t.count(anchor))

    t = read(ARC)
    if u"**刀自己的三条**" in t:
        notes.append(u"§9 那行已经同步（幂等跳过）")
    elif t.count(ROW_OLD) == 1:
        io.open(ARC, "w", encoding="utf-8", newline=u"").write(t.replace(ROW_OLD, ROW_NEW, 1))
        notes.append(u"§9：\"我写错的判据\"那行补上刀的三条（六条 → 九条）")
    else:
        fails.append(u"§9 锚点命中 %d 次" % t.count(ROW_OLD))

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
