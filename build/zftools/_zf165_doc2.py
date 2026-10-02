#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ZF165 交接页记账：往 docs/多会话协作交接.md 插入
   ① §5.3.3（Curios 饰品栏联动这一轮的对外提醒）
   ② §6 的第 37 条（本轮欠的账）
   ③ §1 活体数字表里加一行「ZF165 新增（未打包）」

只写交接页一份；写前留底到 build/tmp/zf165/。
⚠ 一律**按行锚点插入**（ZF159 的教训：字面块替换会把人家的正文顶掉）。
"""

import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DOC = r"E:\PotatoST\docs\多会话协作交接.md"
BACKUP = r"E:\PotatoST\build\tmp\zf165\多会话协作交接.md.before-zf165"

SEC533 = """### 5.3.3 ZF165：Curios 饰品栏联动 —— 谁要接着写"饰品"，先读这一节的三个坑

这一轮给用户做了两件事：**星璨钢头盔能进"首饰"槽**（+2 护甲 / 夜视 III 13 s）、
**通用机械的喷气背包能进"背饰"槽**（正常起飞、正常耗氢）。实现落在一个新文件
`src\\main\\java\\com\\potatost\\mod\\CuriosBridge.java`（**全工程唯一** import
`top.theillusivec4.curios.*` 的地方，公开签名里没有 Curios 类型）。三个坑按踩到的顺序写：

1. **⚠⚠ 槽位"定义好了"≠"玩家身上有"**：Curios 有三层数据，第③层最容易漏 ——
   `data/<命名空间>/curios/entities/*.json` 才是"把槽位分给实体"的那一份。
   Curios 自己的 jar 里**一个都没有**，整合包里只有 Create 写了一份、而且只给了 `head`。
   少了它：标签对、能力对、`isStackValid` 也 true，**但玩家饰品栏里没有格子、且不报任何错**。
   我们补的是 `data/potato_s_t/curios/entities/players.json`（`head` + `back`，不带 `replace`
   ⇒ 与 Create 那份**合并**）。完整论证见档案 §4.173。
2. **⚠ 标签文件不吃 `neoforge:conditions`**（`TagFile.CODEC` 只认 values/replace/remove，
   `TagLoader` 不走 `ConditionalOps`）⇒ 写了是**静默无效**；而 `required` 缺省为 true，
   **一个解析不出来的必需项会让整个标签不被注册**。给"对端可能没装"的物品挂标签要用
   `{"id": "mekanism:jetpack", "required": false}`。见档案 §4.174。
3. **⚠ 饰品槽里的护甲物品本身不给护甲值**：Curios 只把 `ICurio#getAttributeModifiers`
   返回的东西加到玩家身上，物品自己那份 `ItemAttributeModifiers`（`ArmorItem` 的 5.5）
   **不参与结算**。所以"只 +2 护甲"是白拿的；反过来，**任何**想在饰品槽里给属性的实现
   都必须自己回报（包括 Mek 喷气背包那 5 点护甲 —— 进背饰槽就没了，这只在档案里记了一笔）。

**这一轮对别人的影响（重要）**：

- **`curios` 进了 `neoforge.mods.toml`，是 `required`** ⇒ **0.13 起本模组需要 Curios**。
  理由：`ICurioItem` 是**接口**，只要物品类 implements 它，任何模组的 `instanceof ICurioItem`
  都会触发 JVM 解析该接口，没装 Curios 的实例会当场崩；要做成"可选"必须把实现类与注册类
  拆开、全程 `ModList` 挡。**别顺手把 toml 里那条改成 optional**（`_zf165_gate.py` D1 在盯）。
- **`build.gradle` 多了一行 `compileOnly files('libs/curios-neoforge-9.5.1+1.21.1.jar')`**
  + `libs/` 下多了那份 411 KB 的 jar（LGPL-3.0-or-later，随仓库提供以便离线构建）。
- **数据侧多了 3 个文件**：`data/curios/tags/item/head.json`、`.../back.json`、
  `data/potato_s_t/curios/entities/players.json`。前两个在 **curios 命名空间**下 ——
  谁要往 `#curios:head`/`#curios:back` 加东西，**自己开自己的文件**（同名标签是合并语义），
  别去改我们这份。⚠ 顺手提醒：`data/curios/tags/item/curio.json`（那个"任意槽都合法"的标签）
  **不要**往里塞东西 —— 那会让物品在每个槽都能放。

**没做、也不打算做的两件事**（有意为之，别当 bug 修）：头盔在饰品槽里**不**进"四件套"
（`hasFullStarSteelSet` 只认原版四个装备槽，本轮没改宽）；给饰品槽加说明行要动五份 lang 的
键数，为两行字不划算 —— 副词条由 Curios 自己的 `curios.modifiers.head` 那条词条显示。
"""

ITEM37 = """37. **ZF165 的账（0.13：Curios 饰品栏联动 —— 头盔进头饰槽 / Mek 喷气背包进背饰槽）**：
    ① 用户原话与逐条落实见档案 §5 的 ZF165 行 + §9 的待实测段；两个新坑见 **§4.173**
    （Curios 的"槽位↔实体"第三层数据，少了一切入看起来都对但不生效）与 **§4.174**
    （标签文件不吃 `neoforge:conditions`；必需项缺失会丢掉整张标签）。
    ② **软硬依赖的分界**：`mekanism` 那边照旧是**可选**（`ModList.isLoaded` 挡 + 物品 id 解析成
    air 就跳过），`curios` 这边是**硬依赖**（`ICurioItem` 是接口，理由见 §5.3.3）。
    ③ **单一 import 面**：全工程只有 `CuriosBridge.java` import Curios（`Zf165Check` 是临时探针，
    跑完已删）；`_zf165_gate.py` A7/A8 钉住"只有这一个文件 + 公开签名里没有 Curios 类型"。
    ④ **探针 `Zf165Check` 38/0**（把 Curios 9.5.1 + Mek 10.7.19 拷进 `run/server/mods` 跑、
    跑完删掉）：两个标签的内容、两条能力、三条负对照、真 `ServerPlayer` 里护甲正好 +2、
    真 `ModArmorSet.onPlayerTick` 给出夜视 III / 260 tick、反复穿脱 3 轮不漂、摘下回到初值、
    Mek 自己的 `findFirstCurio`/`getActiveJetpack` 认背饰槽里的喷气背包。
    ⑤ **常驻门 `_zf165_gate.py` 43/0**；**五份 lang 一个字节没改**（键数门一份都不用动）。
    ⑥ ⚠ **本轮没重打成品**（`release\\PotatoST-0.13.jar` 里还没有这一轮）——
    下次打包必须带上，§4.159 三处联动照旧。
"""

ROW = ("| ZF165 新增（**未打包**） | 新文件 `CuriosBridge.java`（class 377 → 378）+ 3 个数据文件"
       "（`data/curios/tags/item/{head,back}.json`、`data/potato_s_t/curios/entities/players.json`）"
       "+ `build.gradle` 一行 compileOnly + `libs/curios-neoforge-9.5.1+1.21.1.jar` + "
       "`neoforge.mods.toml` 的 curios 依赖 + `ModArmorMaterials.hasStarSteelHelmet` 改一行。"
       "**五份 lang 未动** |\n")


def main():
    src = io.open(DOC, "r", encoding="utf-8", newline="").read()
    if "\r\n" in src:
        print("!! 交接页是 CRLF，本脚本按 LF 处理 —— 先确认再跑")
        return 1
    lines = src.split("\n")
    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    if not os.path.exists(BACKUP):
        io.open(BACKUP, "w", encoding="utf-8", newline="").write(src)
        print("留底 -> " + BACKUP)

    # ① §5.3.3：插在 "## 6. 我这边欠的账" 之前
    idx6 = [i for i, l in enumerate(lines) if l.startswith("## 6. 我这边欠的账")]
    if len(idx6) != 1:
        print("!! 锚点 '## 6.' 不唯一：%d 处" % len(idx6))
        return 2
    if any(l.startswith("### 5.3.3 ") for l in lines):
        print("!! 已经有 §5.3.3 了，拒绝重复插入")
        return 3
    lines[idx6[0]:idx6[0]] = SEC533.split("\n") + [""]
    print("① 已插入 §5.3.3（在 §6 之前）")

    # ② §6 第 37 条：接在第 36 条那一大段之后（下一个 "---" 或 "## " 之前）
    idx36 = [i for i, l in enumerate(lines) if l.startswith("36. **ZF164 的账")]
    if len(idx36) != 1:
        print("!! 锚点第 36 条不唯一：%d 处" % len(idx36))
        return 4
    if any(l.startswith("37. **ZF165 的账") for l in lines):
        print("!! 已经有第 37 条了，拒绝重复插入")
        return 5
    j = idx36[0] + 1
    while j < len(lines) and not lines[j].startswith("---") and not lines[j].startswith("## "):
        j += 1
    lines[j:j] = [""] + ITEM37.split("\n")
    print("② 已插入 §6 第 37 条")

    # ③ §1 活体数字表：挂在 "| ZF159 新增（未打包）" 那一行之后（没有就挂在最后一行表格之后）
    anchor = [i for i, l in enumerate(lines) if l.startswith("| ZF159 新增")]
    if len(anchor) == 1:
        lines.insert(anchor[0] + 1, ROW.rstrip("\n"))
        print("③ 已插入 §1 活体数字行（在 ZF159 那行之后）")
    else:
        # 退路：找 §1 里最后一个以 "| " 开头且含 "未打包" 的行
        cand = [i for i, l in enumerate(lines[:120]) if l.startswith("| ") and "未打包" in l]
        if not cand:
            print("!! 找不到 §1 的活体数字锚点（ZF159=%d 处）" % len(anchor))
            return 6
        lines.insert(cand[-1] + 1, ROW.rstrip("\n"))
        print("③ 已插入 §1 活体数字行（退路锚点）")

    out = "\n".join(lines)
    io.open(DOC, "w", encoding="utf-8", newline="").write(out)
    print("写完：%d -> %d 行" % (len(src.split("\n")), len(lines)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
