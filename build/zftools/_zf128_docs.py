# -*- coding: utf-8 -*-
u"""_zf128_docs.py —— ZF128 的文档（档案 §4/§5/§9 + 交接 §6 + 英文公告）

用户原话：「成就栏换成毒马铃薯 但是成就还是粉碎机可以嘛」

落点：
  ① 档案 §4.110：**页签图标 = 根节点图标（同一个字段）** —— 查源码得出来的硬事实；
  ② 档案 §5：ZF128 那一行（插在 ZF127 行之后）；
  ③ 档案 §9：ZF128 小节（插在 `## 10. 备份策略` 之前）—— 顺便**收口 ZF124 挂着的那条账**；
  ④ 交接 §6 第 20 条；
  ⑤ 英文公告 §7：一句话说明页签图标（不改那棵树）。

跑法：
    python build\\zftools\\_zf128_docs.py
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
ARC = os.path.join(DOCS, u"开发档案.md")
HAND = os.path.join(DOCS, u"多会话协作交接.md")
ANN = os.path.join(DOCS, u"UpdateAnnouncement_EN.md")

notes, fails = [], []


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def insert_before(name, path, anchor, block):
    t = read(path)
    if block.strip().split(u"\n")[0] in t:
        notes.append(u"%s：已经有这一块（幂等跳过）" % name)
        return
    if t.count(anchor) != 1:
        fails.append(u"%s：锚点命中 %d 次（要 1 次）—— 停手" % (name, t.count(anchor)))
        return
    write(path, t.replace(anchor, block + anchor, 1))
    notes.append(u"%s" % name)


def insert_after_line(name, path, line_start, block):
    t = read(path)
    if block.strip().split(u"\n")[0] in t:
        notes.append(u"%s：已经有这一块（幂等跳过）" % name)
        return
    lines = t.split(u"\n")
    idx = [i for i, l in enumerate(lines) if l.startswith(line_start)]
    if len(idx) != 1:
        fails.append(u"%s：以 %r 开头的行有 %d 行（要 1 行）—— 停手" % (name, line_start, len(idx)))
        return
    lines.insert(idx[0] + 1, block.rstrip(u"\n"))
    write(path, u"\n".join(lines))
    notes.append(u"%s" % name)


LESSON = u'''### 4.110 【拆不开的字段】成就页签的图标**就是**根节点的图标（0.11 ZF128，查源码才知道）

用户问「成就栏换成毒马铃薯 但是成就还是粉碎机可以嘛」—— 想说"页签换图、树里那个根节点留旧的"。
**做不到**：原版这两处是**同一个字段**。硬证据取的是本工程编译用的那份源码
（`build\\neoForm\\neoFormJoined1.21.1-20240808.144430\\sources.jar`）：

| 文件:行 | 代码 | 含义 |
|---|---|---|
| `AdvancementTab.java:43` | `…, AdvancementNode rootNode, DisplayInfo display` | 页签构造拿到的是**根成就**的 `display`（第 154 行取的就是 `rootNode.advancement().display()`） |
| `AdvancementTab.java:51` | `this.icon = display.getIcon();` | **页签图标 = 根成就图标** |
| `AdvancementTab.java:52` | `this.title = display.getTitle();` | 页签悬浮名 = 根成就标题（ZF124 改名改的就是它） |
| `AdvancementTab.java:53` | `this.root = new AdvancementWidget(this, minecraft, rootNode, display);` | 树里那个根节点 widget 拿的是**同一个 `display` 对象** |
| `AdvancementWidget.java:162` | `guiGraphics.renderFakeItem(this.display.getIcon(), …)` | 节点方块画的也是 `display.getIcon()` |

**结论与口径**：
- 「页签图标 vs 根节点图标」不是两个可选项，**是一个**；要拆只能上客户端 mixin 改渲染（本项目不做）；
- 但「**图标** vs **判据/说明**」是两回事 —— 换图标**不影响**成就内容：探针在真服务端上
  交一个微型粉碎机 ⇒ 点亮；先交一个毒马铃薯 ⇒ **不亮**；
- **通用教训**：玩家（或自己）问"这两处能不能分开"时，**去源码里找那两处是谁画的**，
  一行 `grep` 的事；别凭"界面上看起来是两个地方"下结论（§4.102 同族：查 jar，别查记忆）。

**顺带记一个生成器陷阱**：`_zf107_adv.py` 里原来只有 `ROOT_ICON = "micro_crusher"`，
既当**判据**又当**图标**，而且写盘时拼死 `"potato_s_t:" + ROOT_ICON` ⇒
**谁重跑一次生成器，毒马铃薯就被悄悄写回粉碎机**（图标还要跨命名空间到 `minecraft:`，
那个拼接根本表达不出来）⇒ 本轮把它拆成 `ROOT_ICON_CRITERION` / `ROOT_ICON_DISPLAY` 两个常量
（§4.93「表与盘必须一致」的又一面）。

'''

ROW = u'''| ZF128 | **新建 `zf128_pre`**（**142 份**改前件：根成就 `new_beginning.json` + **`PotatoST.java`（探针挂载点 —— 从这一轮起坚持一开始就写进清单）** + 三份往轮门（`_zf70` / `_zf107` / `_zf124_verify`）+ 生成器 `_zf107_adv.py` + 四份 lang + 3 份文档 + 整个 `advancement\\` 目录（35 份）+ 全部 `_zf*_verify/_falsify/_guard/_repro/_audit` + 旧成品与 `.sha1`；逐份核哈希 + 回读证明 142/142） | 0.11：**成就页签的图标 微型粉碎机 → 毒马铃薯**（用户原话：「成就栏换成毒马铃薯 但是成就还是粉碎机可以嘛」）。① **查源码定了可行性**：页签图标与树里根节点的图标是**同一个字段**（`AdvancementTab.icon = display.getIcon()`，根节点 widget 拿的是同一个 `display`；证据与行号见 §4.110）⇒ 「页签换、节点不换」做不到；用户选的是"换，判据/说明照旧"；② 改动就**一行**：`new_beginning.json` 的 `display.icon.id` = `minecraft:poisonous_potato`（原版物品，**不用画贴图** ⇒ 待画清单仍 15 个、四语言仍 478 键、贴图/模型/配方一个字没动）；③ **判据一个字没动**：仍是 `inventory_changed` + `potato_s_t:micro_crusher`，标题/描述/背景/frame/hidden/toast 全部照旧（探针逐字段比过）；④ 三份往轮门 + 一份生成器跟平：⚠ 生成器 `_zf107_adv.py` 的 `ROOT_ICON` 原来一身兼二职（判据 + 图标）且拼死 `potato_s_t:` 前缀 ⇒ **重跑就会把图标写回粉碎机**，本轮拆成 `ROOT_ICON_CRITERION` / `ROOT_ICON_DISPLAY`；⑤ 证据：真服务端探针 **21 项全绿**（**交毒马铃薯 ⇒ 不亮**、**交微型粉碎机 ⇒ 点亮**）+ `_zf128_verify.py` **%d 项** + 反证 **K223~K226 四把刀**；⑥ ZF124 那条"页签图标要不要也换"的账**本轮收口**（用户要的是毒马铃薯，不是星轨坠） | 见 §4.110 / §9 |
'''

SECTION = u'''### ZF128（0.11）：成就页签的图标换成**毒马铃薯**（判据仍是微型粉碎机）—— **待你实测**

用户原话（接 ZF124 那条挂着的账问的）：

> 成就栏换成毒马铃薯 但是成就还是粉碎机可以嘛

#### 一、先回答"能不能"：**图标这一半拆不开，判据那一半没问题**

| 你想分的两半 | 能不能分开 | 依据 |
|---|---|---|
| **页签图标** vs **树里根节点那个小方块的图标** | ❌ **拆不开**（同一个字段） | `AdvancementTab.java:51` `this.icon = display.getIcon();`、`:53` 把同一个 `display` 交给根节点 widget、`AdvancementWidget.java:162` 画的也是 `display.getIcon()`（§4.110 有完整表） |
| **图标** vs **判据 / 说明 / 页签名字** | ✅ 各自独立，随便换 | 判据在 `criteria` 段、名字在 `display.title`（页签悬浮名 = 它）、说明在 `display.description` |

⇒ 你选的"换"= 页签与根节点**一起**变成毒马铃薯；成就**内容**（做出微型粉碎机）一个字没动。

#### 二、做了什么（就一行）

| # | 东西 | 值 |
|---|---|---|
| ① | `new_beginning.json` 的 `display.icon.id` | `potato_s_t:micro_crusher` → **`minecraft:poisonous_potato`**（原版物品，**不用画贴图**） |
| ② | 判据 `criteria.got` | **一个字没动**：`minecraft:inventory_changed` + `potato_s_t:micro_crusher` |
| ③ | 标题 / 描述 / 背景 / frame / hidden / toast | **一个字节没动**（页签名字仍是 `PotatoS&T`） |
| ④ | 三份往轮门 + 一份生成器 | 跟平（生成器那处是**真陷阱**：不拆常量的话，重跑一次就把图标写回粉碎机） |

**连锁面：零**。四语言仍 **478 键**、待画贴图仍 **15 个**、贴图/模型/配方/Java 一行没动
（毒马铃薯是原版物品，不是我们的模型 ⇒ 不进待画清单）。

#### 三、证据

| 项 | 值 |
|---|---|
| 探针 | 真服务端 `Zf128Check`：**21 项全绿** —— 图标的 item == `minecraft:poisonous_potato`（且**不再是**微型粉碎机、是**原版**命名空间、非空气、数量 1）/ 标题与描述仍是那两个 translate 键 / 背景图仍是 `common_metal_block` / frame·hidden·toast 没动 / 判据仍只有 `got` 一条且触发器是 `inventory_changed` / 树里仍恰好 1 个根挂在 `AdvancementTree.roots()` 里 / 本模组成就仍 **35** 条 / 只有根那条用毒马铃薯、别的成就图标仍全是本模组物品；**行为两条**：**交一个毒马铃薯 ⇒ 根成就仍然不亮**（负向对照）、**交一个微型粉碎机 ⇒ 点亮**（「成就还是粉碎机」） |
| 常驻校验 | `_zf128_verify.py` **%d 项**：数据逐字段（除 `icon.id` 外与改前件完全相同、文件大小只差 18 字节 = 一行替换）/ 四份往轮件跟平且能编译 / 树本体 35 份·1 根 / 公告与档案§4·§5·§9·交接§6 / **待画清单不许变** / 反向（我们没注册 `poisonous_potato`、`PotatoST.java` 干净且 == 改前件） |
| 反证刀 | **K223~K226 四把**：图标改回粉碎机 / 判据改成毒马铃薯（"成就"真被换了）/ 把生成器的两个常量又并回一个 / 待画清单表头改一个数 |
| 我自己写错的两条（如实记） | ① 探针第一版去 `Component.toString()` 里正则找 `translate=` ⇒ 两条假 FAIL（正路是 `getContents() instanceof TranslatableContents` 取 `getKey()`）；② 探针第一版把 `ClientInformation` 写成 `client.multiplayer` 包（1.21.1 它在 `server.level`）⇒ 编译期就红（§4.106 家族：期望/取证写错的第 N 次） |

#### 四、要你实测

**重启客户端**（或 `F3+T` 重载数据包）后打开成就界面：① 那个页签的图标应当是**毒马铃薯**；
② 点进去，树里根节点那个小方块**也**是毒马铃薯（同一个字段，躲不掉）；
③ 页签悬浮名仍是 `PotatoS&T`，那条成就的说明仍是「做出微型粉碎机 —— 它把矿石磨成粉，是后面一切的地基」。

**成品**：本轮**没有新成品**（`release\\` 一个字没动）。

'''

ANN_LINE = u'''
> ℹ️ **The advancement tab icon is now a poisonous potato** (0.11 ZF128), as requested. In vanilla the
> tab icon *is* the root advancement's icon — the tab button and the root node in the tree are drawn
> from the very same `display.icon` field (`AdvancementTab.icon = display.getIcon()`, and the root
> node's widget is built from that same `display`), so the two cannot show different items. The
> **achievement itself is unchanged**: it still unlocks by obtaining a Micro Crusher.
'''


def main():
    insert_before(u"档案 §4：新增 4.110", ARC,
                  u"## 7. 权威情报来源（怎么查原版行为，别靠记忆）", LESSON)
    insert_after_line(u"档案 §5：ZF128 那一行", ARC, u"| ZF127 | ", ROW % 0)
    insert_before(u"档案 §9：ZF128 小节", ARC, u"## 10. 备份策略", SECTION % 0)

    HANDOVER_ITEM = u'''20. **ZF128 的账（ZF124 那条"页签图标要不要换"的账本轮收口）**：① 用户原话
    「成就栏换成毒马铃薯 但是成就还是粉碎机可以嘛」—— 查源码后确认：**页签图标与树里根节点的
    图标是同一个字段**（`AdvancementTab.icon = display.getIcon()`，根节点 widget 拿的是同一个
    `display`；行号与出处见 §4.110）⇒ "页签换、节点不换"**做不到**（除非上客户端 mixin，本项目不做）；
    用户选的是"换，判据/说明照旧"。② 改动就一行：`new_beginning.json` 的 `display.icon.id`
    → `minecraft:poisonous_potato`；**判据仍是** `potato_s_t:micro_crusher`、标题/描述/背景全没动；
    ③ 连锁面**零**：四语言仍 478 键、待画贴图仍 15 个、Java/模型/配方一行没动（原版物品不进待画清单）；
    ④ ⚠ **生成器陷阱**：`_zf107_adv.py` 的 `ROOT_ICON` 原来一身兼二职（判据 + 图标）且拼死
    `potato_s_t:` 前缀 ⇒ **谁重跑一次就把图标写回粉碎机**；本轮拆成 `ROOT_ICON_CRITERION` /
    `ROOT_ICON_DISPLAY`。以后改根成就的**图标**，先看这两个常量。⑤ 证据：探针 **21 项全绿**
    （含"交毒马铃薯不亮 / 交微型粉碎机点亮"）+ `_zf128_verify.py` **%d 项** + 反证 **K223~K226 四把**。
'''
    insert_after_line(u"交接 §6：第 20 条", HAND, u"19. **ZF127 的账**", HANDOVER_ITEM % 0)

    # 英文公告：接在 §7 那句"35 advancements"介绍后面
    t = read(ANN)
    if u"The advancement tab icon is now a poisonous potato" in t:
        notes.append(u"公告：已经有那一段（幂等跳过）")
    else:
        anchor = u'''description of the step they unlock. Every description tells you **what to do next**, not what you just
picked up.
'''
        if t.count(anchor) != 1:
            fails.append(u"公告锚点命中 %d 次" % t.count(anchor))
        else:
            write(ANN, t.replace(anchor, anchor + ANN_LINE, 1))
            notes.append(u"公告 §7：补一段页签图标的说明")

    print(u"\n".join(u"  [OK] " + x for x in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
