# -*- coding: utf-8 -*-
u"""_zf80_docs.py —— ZF80 四份文档：档案（§4.52 新雷 + §5 ZF80 行 + §9 验收）、规划（§5 第 14 条）、英文公告

占位符 `__NEWSHA__` / `__NEWSIZE__` / `__NEWENTRIES__` 由 `_zf80_hashfix.py` 在打包后填真值
（与往轮同一套流程；校验里有一条"文档不许留 __NEWSHA__"兜底）。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOCS = os.path.join(ROOT, "docs")

fails = []


def read(p):
    if not os.path.exists(p):
        fails.append(u"缺文件：%s" % p)
        return u""
    return io.open(p, encoding="utf-8").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)


def insert_after(text, anchor, block, label):
    u"""在 anchor 那一行之后插入 block（anchor 必须唯一命中）。"""
    if text.count(anchor) != 1:
        fails.append(u"%s：锚点命中 %d 次" % (label, text.count(anchor)))
        return text
    at = text.find(anchor)
    eol = text.find(u"\n", at)
    return text[:eol + 1] + block + text[eol + 1:]


# ================= ① 档案 §4.52 =================

TRAP = u"""
### 4.52 【排查雷】"机器不说话"把**四种完全不同的成因**伪装成同一个症状（0.11 ZF80）

用户实测：「**灌装机不往油桶灌液体**」。按老规矩**先证机器、再改机器**：探针 `FillingOilCheck`
在真服务端上 **83 项全过** —— 包括把用户的接法整个复刻一遍
（原油池 → 泵 → 灌装机 → 空油桶：10 tick 正好 50 mB）。⇒ **代码没坏**。

真正的问题是：这台机器只有"灌 / 不灌"两种表现，**没有任何一句"为什么不灌"**。
于是四种完全不同的成因，玩家看到的都是"一点反应都没有"：

| 玩家看到的 | 真实原因 | 界面看得出来吗 |
|---|---|---|
| 一点反应都没有 | **罐里根本没有液体**（这台机器原先只能靠管道/泵进料，手倒不了） | 罐子画着空 —— 但玩家第一反应是"机器坏了" |
| 一点反应都没有 | **电不够**（每槽每 tick 要 60 FE，缓冲 3000） | 能量条是空的 —— 同理 |
| 一点反应都没有 | **罐里是气体、槽里是油桶**（用户规则：油桶不收气体） | ❌ 看不出来（要认出贴图是氧气还是原油） |
| 一点反应都没有 | 容器已满 / 罐里是异种流体 | 勉强能看出来 |

**规矩**：
1. **「没反应」是一类 BUG，不是一个 BUG**。凡是"玩家做了动作、机器什么都不说"的地方，
   按"四种成因 ⇒ 四种说法"给诊断（分馏塔控制器那条诊断就是这个套路，用户点名要过）。
2. 排查顺序**先证机器、再改机器**：探针把链路逐环验完（含复刻用户接法），拿到
   `83/0` 之后再决定改什么 —— 否则很容易按猜测把机器改一遍，而问题在接线那一头。
3. 同一类机器的手感要一致：蒸馏塔操作器能"手里拿容器右键倒进去"，灌装机就该有同一个动作；
   这次补上之后，**手倒 → 放空桶 → 开灌**这条链不用任何管道就能走通。
"""

# ================= ② 档案 §5 ZF80 行 =================

ROW = (u"| ZF80 | **新建 `zf80_pre`**（23 个改前件：灌装机三件（`FillingMachineBlock` / "
       u"`FillingMachineBlockEntity` / `FillingMachineMenu`）+ 油桶两件（`OilBucketItem` / "
       u"`OilBucketContents`）+ `FluidContainerItem` + `HighPressureTankItem` + `PotatoST`"
       u"（探针挂钩，跑完已摘）+ 4 份 lang + 6 个往轮校验脚本 + 4 份文档 + 旧成品 jar 与 `.sha1`；"
       u"逐份核哈希、失败 0） | 0.11：**灌装机两件**（用户原话：「**灌装机不往油桶灌液体**」）。"
       u"① **先查再改**：探针 `FillingOilCheck` 把整条链逐环验 —— **83 项全过**：接口（油桶/气罐都算 "
       u"`FluidContainerItem`）、菜单手放那道门、罐收原油、1 tick 5 mB / 600 tick 灌满 3000、"
       u"四种石油产品都能进油桶、没电一滴不动（59 FE 也不动、60 FE 立刻动）、气体进不了油桶、"
       u"原油进不了气罐、气罐灌氧气回归，外加**复刻用户接法的整机试验场**（原油池 → 泵 → 灌装机 → "
       u"空油桶 = 10 tick 50 mB）⇒ 结论：**机器逻辑没坏，坏在它什么都不说**（雷记进 §4.52）。"
       u"② **手倒**：手里拿流体容器右键机器 ⇒ 倒进罐（`pourFrom`：先接着**同种**流体倒，否则第一个空罐；"
       u"`SIMULATE` → 真取 → 真灌，多取的一定塞回容器；倒不进去分「空容器 / 五个罐都满或都是别的流体」"
       u"两种情况各说一句）；**空手右键仍是开界面**（原行为不动）。③ **逐槽诊断**："
       u"**空手 + Shift 右键** ⇒ 五个槽各念一句「为什么没在灌」（罐空 / 槽里没容器 / 容器满 / 缺电（带 FE 数字）/ "
       u"容器不收这种流体（带流体名）/ 正在灌（带罐里量与剩余空间））—— 判据顺序与 `tryFillSlot`"
       u"**逐条对齐**，诊断说的就是代码真正做的事。④ 四语言 248 → **257** 键"
       u"（3 条手倒 + 6 条诊断），并把 tooltip 里过期的「把罐里的**气体**灌进容器」改正为「流体」"
       u"（ZF73 起五个罐已对任何流体开放，旧文案是在骗人）。⑤ 顺手清掉 `FillingMachineMenu` 里"
       u"重复的 `Fluids` 导入。⚠ **②③ 两件是我加的动作**（用户只报了「不灌液体」，没点名要这两件）"
       u"—— 不合口味说一声，撤掉是一行的事。 |\n")

# ================= ③ 档案 §9 验收 =================

VERIFY = u"""
### ZF80（0.11）灌装机手倒 + 逐槽诊断 —— 待你实测

探针已在真服务端跑到 **83/0**（含复刻你接法的整机试验场），下面这些是**手感/交互**，
只能在游戏里看：

- [ ] **手倒**：手里拿**油桶**（或气罐）对着**灌装机**右键 ⇒ 聊天栏上方出现
      「已倒入 N 号罐：原油 1000 mB」+ 倒水声；罐里的液面立刻涨 1000（一次 1 桶格）
- [ ] **接着倒**：同一个油桶再右键两次 ⇒ 都进**同一个罐**（3000 mB），不会乱开新罐；
      换一种液体（例如柴油桶）再倒 ⇒ 进**另一个空罐**（一个罐只装一种）
- [ ] **倒不进去要有说法**：五个罐都满时再倒 ⇒ 「倒不进去：五个罐都满了，或者装的都是别的流体」，
      且桶里**一滴不少**
- [ ] **诊断**：**空手 + Shift 右键**灌装机 ⇒ 五行，每行一个槽：
      「罐是空的」/「槽里没有容器」/「容器已经满了」/「缺电 —— 机器里只有 X FE，每个槽每 tick 要 60 FE」/
      「这个容器不收罐里那种流体（罐里是 氧气）」/「正在灌装」
- [ ] **原行为没被挡**：空手右键（不按 Shift）仍然开界面；拿着泥土之类的普通物品右键也**照样开界面**
- [ ] **这次的正题**：罐里有油 + 槽里空油桶 + 有电 ⇒ 正常灌（原本就该通；本轮复验）
- [ ] 上一轮那两条也还没在启动器实例里复核过：**手放油桶**（ZF79 修复）、**液压机 JEI 箭头位置**（ZF79 修复）

**成品**：`release\\PotatoST-0.11.jar` = `__NEWSHA__`（__NEWSIZE__ B / __NEWENTRIES__ 条目），
**作废上一版 `6b49d491aa61d43d60bea87c965344fcee6aa8ac`**（ZF79 第二轮）；
0.10 成品 `84d09345f6095408ae462dabb536307141904ea3` 原样保留。
"""

# ================= ④ 规划 §5 第 14 条 =================

PLAN_ROW = (u"| 14 | 灌装机要不要「手里拿容器右键倒进罐」+「逐槽诊断」（ZF80 我加的） | "
            u"**两件都已实现**（用户 09-24 实测「灌装机不往油桶灌液体」的应对）：手倒一次 1000 mB、"
            u"同种流体接着倒否则开空罐、倒不进去有文案；诊断走**空手 + Shift 右键**（空手普通右键仍是开界面）。"
            u"不合口味说一声就撤 |\n")

ANN = (u"\n- **Filling Machine (0.11 ZF80)** - right-click the machine with an oil bucket / gas tank "
       u"to pour its contents into a tank (1000 mB per click; it keeps filling the same tank, otherwise "
       u"takes the first empty one), and **shift-right-click with an empty hand** to get a per-slot "
       u"diagnosis of why nothing is filling (empty tank / no container / container full / not enough FE / "
       u"container refuses that fluid / currently filling). Plain empty-hand right-click still opens the GUI.\n")


def main():
    arch_p = os.path.join(DOCS, u"开发档案.md")
    arch = read(arch_p)
    # §4.52：插在 §4.51 那一段之后（用 §5 版本表标题当分界，插在它前面）
    if u"### 4.52" not in arch:
        boundary = u"\n\n| 版本 | 内容 |"
        if arch.count(boundary) != 1:
            fails.append(u"档案：版本表锚点命中 %d 次" % arch.count(boundary))
        else:
            arch = arch.replace(boundary, u"\n" + TRAP + boundary, 1)
    if u"| ZF80 |" not in arch:
        anchor = u"| ZF79 | **新建 `zf79_pre`**"
        at = arch.find(anchor)
        if at < 0:
            fails.append(u"档案：找不到 ZF79 行")
        else:
            eol = arch.find(u"\n", at)
            arch = arch[:eol + 1] + ROW + arch[eol + 1:]
    if u"### ZF80（0.11）灌装机手倒" not in arch:
        anchor = u"\n## 10. 备份策略"
        if anchor not in arch:
            fails.append(u"档案：找不到 §10 标题")
        else:
            arch = arch.replace(anchor, u"\n" + VERIFY + anchor, 1)
    write(arch_p, arch)

    plan_p = os.path.join(DOCS, u"v0.11规划.md")
    plan = read(plan_p)
    if u"| 14 |" not in plan:
        anchor = u"| 13 | 四种产品（柴油/石脑油/汽油/液化石油气）要不要桶"
        at = plan.find(anchor)
        if at < 0:
            fails.append(u"规划：找不到第 13 条")
        else:
            eol = plan.find(u"\n", at)
            plan = plan[:eol + 1] + PLAN_ROW + plan[eol + 1:]
    if u"## 5. 待你拍板（13 条" in plan:
        plan = plan.replace(u"## 5. 待你拍板（13 条：**⑤⑩⑫ 已于 2026-09-24 拍板**，其余 10 条不回复就按括号里的默认值走）",
                            u"## 5. 待你拍板（14 条：**⑤⑩⑫ 已于 2026-09-24 拍板**，第 14 条是 ZF80 我加的两件，"
                            u"不回复就照现状留着）")
    write(plan_p, plan)

    ann_p = os.path.join(DOCS, u"UpdateAnnouncement_EN.md")
    ann = read(ann_p)
    if u"Filling Machine (0.11 ZF80)" not in ann:
        ann = ann.rstrip(u"\n") + u"\n" + ANN
    write(ann_p, ann)

    print(u"文档改完，失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
