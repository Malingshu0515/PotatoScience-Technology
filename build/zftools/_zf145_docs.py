# -*- coding: utf-8 -*-
r'''_zf145_docs.py —— ZF145 的文档（纯插入 / 定点替换；锚点唯一性先验）

四处：
  ① 档案 §5 加 ZF145 行（插在最后一个 `| ZF14x |` 行之后）
  ② 档案 §4 加 4.148（幂等前缀雷）+ 4.149（判据扫描器的盲区），插在 `## 7. 权威情报来源` 之前
  ③ 档案 §9 加 ZF145 小节，插在 `## 10. 备份策略` 之前
  ④ 交接 §1 的活体数字（键数 492 → 508、进度 35 → 43 条）+ 键数链条补一环；§6 加第 27 条
  ⑤ 英文公告：`35 advancements` → `43 advancements`，并在末尾补 ZF145 条目

跑法：python build\zftools\_zf145_docs.py [--write]
'''
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
KEYS, NODES = 508, 43
fails, notes, plan = [], [], []


def read(p):
    return io.open(p, encoding="utf-8", newline="").read()


def before(text, anchor, block, label):
    if text.count(anchor) != 1:
        fails.append(u"%s：锚点命中 %d 次（应为 1）" % (label, text.count(anchor)))
        return text
    notes.append(u"  [插] " + label)
    return text.replace(anchor, block + anchor, 1)


def once(text, old, new, label):
    if new in text and old not in text:
        notes.append(u"  [跳过] %s（已经改过，幂等）" % label)
        return text
    if text.count(old) != 1:
        fails.append(u"%s：命中 %d 次（应为 1）" % (label, text.count(old)))
        return text
    notes.append(u"  [改] " + label)
    return text.replace(old, new, 1)


ROW = r'''| ZF145 | **新建 `zf145_pre`**（**88 份**改前件：四份 lang / **全部常驻门**（`_zf*_verify.py` + `_zf100_recipe_guard.py`）/ 三份文档 / `_zf104_gates.*` / `PotatoST.java`（⚠ 探针挂载点 —— 这次**动手前**就写进清单了，§6 第 9/14/18 条那三次漏账的教训）；逐份核哈希 + 回读，失败 0。⚠ 开工前查过轮号：`build\zftools` 下没有别的 `_zf145_*`、救援目录下没有 `zf145_pre`（§4.147） | 0.11：**成就树补线**（用户原话「是时候更新一下成就啦宝宝」）。ZF117 那条线之后新加的内容**一条进度都没有** ⇒ 补 **8 条**：振金锭 / 振金套（challenge）/ 钛合金套（一条老空洞）/ 星璨钢工具五件（「或」）/ **星辉斩**（全树**唯一**一条击杀型：判据是**伤害类型标签**而不是物品，challenge）/ 星仪图之章 / 大型柴油发电机 / 银线。四语言 **492 → 508** 键、进度 **35 → 43** 条；新增 1 个标签 `tags/damage_type/star_steel_slash.json`；**Java / 配方 / 贴图一行没动**（纯数据 + 门跟平） | 见 §9 ｜ 见 §4.148~§4.149 |
'''

SEC4 = r'''### 4.148 【工具雷】幂等判断写成 `new in text and old not in text` —— 只要 `old` 是 `new` 的**前缀**，就永远判不出"已经改过"（0.11 ZF145）

`_zf139/_zf141/_zf144_gatefix.py` 里那句幂等判据是
`if new in text and old not in text: skip`。本轮 `_zf145_gatefix.py` 照抄了它，
而其中一对是「**在已有片段后面追加**」型的改动：

    old: ALL_NODES = OLD_NODES + NEW_NODES + ZF117_NODES
    new: （注释 + ZF145_NODES 列表 +）ALL_NODES = OLD_NODES + NEW_NODES + ZF117_NODES + ZF145_NODES

`old` 是 `new` 里那一行**去掉后缀的前缀** ⇒ 改完之后 `old in text` **仍然成立** ⇒
`new in text and old not in text` 为假 ⇒ 幂等判断失效 ⇒ 第二次跑会把整块**再插一遍**
（盘上会留下两份 `ZF145_NODES = [...]`）。

**干跑（不加 `--write`）当场抓到了它，一个字节都没写盘。** 这一条之所以能抓到，正是因为
"默认只算不写、要写才加 `--write`"是这个脚本族的规矩。
⇒ 判据改成 `if new in text: skip`（"新文本已经在"就是"这一处已经改过"的充分条件；
`old` 还在不在**不影响**这个判断）。**同类**：凡是"在一个已有片段后面追加/包一层"的替换，
都属于这一族，别用"旧文本已消失"当幂等条件。

### 4.149 【判据雷】`mod_ids()` 只扫 `register("…")` —— 走**私有注册器**的物品在"盘上注册名单"里一直缺席（0.11 ZF120 埋 / ZF145 抓）

`_zf107_verify.py` 的 `mod_ids()` 用一条正则扫 `ModItems / ModBlocks / PotatoSTOres / ModArmorItems`
里的注册名：`register\(\s*"([a-z0-9_]+)"`。而 ZF120 那四件振金甲走的是**私有注册器**
`registerVibranium("vibranium_helmet", …)` ⇒ 正则扫不到 ⇒ 这四件**从来不在**那份名单里。

它一直没暴露，是因为**从来没有哪个进度的判据点名振金甲**；ZF145 第一次点名，
当场得到 **4 条假 FAIL**（"判据物品不在盘上注册"——而它们明明注册得好好的）。
⇒ 往扫描器里补一条 `registerVibranium\(`（**补全 = 更严**，不是放宽断言）。

**教训**：判据扫描器本身要有"**扫到了几个**"的自检 —— 名单为空或明显偏少时应当报错，
否则"扫不到"会伪装成"东西不在盘上"，把真雷（物品没注册）和假雷（扫描器看不见）混成一堆。
'''

SEC9 = r'''### ZF145（0.11）成就树补线 —— 8 条新进度 + 星辉斩的击杀判据 —— **待你实测**

用户原话：「是时候更新一下成就啦宝宝」。

ZF117 那条线把树补到 35 条之后，**新加的内容一条进度都没有**（振金、星仪图之章、
大型柴油发电机、银线、星璨钢五件工具、剑的星辉斩）。本轮补 **8 条**，一条老节点的字节都没动。

#### 一、8 条新节点（父 / 框 / 判据）

| 节点 | 父 | 框 | 图标 | 判据 |
|---|---|---|---|---|
| `vibranium` 炼出振金 | `star_steel` | goal | 振金锭 | 拿到振金锭 |
| `vibranium_armor` 振金套装 | `vibranium` | **challenge** | 振金胸甲 | 四件**各占一个组**（真「与」） |
| `titanium_armor` 钛合金套装 | `titanium_tools` | goal | 钛合金胸甲 | 四件各占一个组（真「与」） |
| `star_steel_tools` 星璨钢工具 | `star_steel` | goal | 星璨钢镐 | **五件塞进同一个组**（真「或」，与 `titanium_tools` 同一条先例） |
| `star_steel_slash` 星辉斩 | `star_steel` | **challenge** | 星璨钢剑 | **击杀型**：`player_killed_entity` + `killing_blow` 点名伤害类型标签（**没有物品判据**） |
| `star_chart_tome` 星仪图之章 | 根 | task | 星仪图之章 | 拿到书 |
| `diesel_generator` 大型柴油发电机 | `stronger_power` | goal | 柴油发电机控制器 | 拿到控制器 |
| `silver_wire` 银线 | `wiring` | task | 银线轴 | 拿到银线轴 |

#### 二、星辉斩那条「击杀型」判据 —— 本工程第一次用伤害类型标签

`player_killed_entity` 的 `killing_blow` 收的是 `DamageSourcePredicate`，它**只能按标签**筛伤害类型
（`DamageSourcePredicate.CODEC` 的 `tags` 字段，见 1.21.1 源码与 `adventure/blowback.json` 的先例）
⇒ 本轮新增 `data\potato_s_t\tags\damage_type\star_steel_slash.json`：

    { "values": [ "potato_s_t:star_steel_slash" ] }

标签名与 ZF144 那个伤害类型**同名**（不同注册表，合法，原版 `minecraft:is_projectile` 就是这么干的）。
判据那一格写的是 `"killing_blow": { "tags": [ { "expected": true, "id": "potato_s_t:star_steel_slash" } ] }`。

#### 三、四处**我定的**（用户没说的，改起来都是一处）

1. **`star_steel_tools` 用「或」**（拿到任意一件工具就点亮），与 `titanium_tools` / `pressing`
   同一条先例；三套盔甲反过来用「与」（四件全要）。⚠ 两者的写法差别是**规格**不是风格：
   `inventory_changed` 的 `items` 数组是**「与」**⇒「或」必须写成"多条判据塞进**同一个** requirement 组"（§4.74）。
2. **`vibranium` 挂 `star_steel`**（合金线的顶：那一炉就吃硬质钛合金与星璨钢那条线的产物）。
3. **`diesel_generator` 挂 `stronger_power`**（"更强劲的电源"的下一级；配方要钢板 + 铜块）。
4. **`titanium_armor` 是补的一条老空洞** —— 三套盔甲里唯一没有节点的（ZF117 只补了 `titanium_tools`）。

#### 四、活体数字（本轮）

| 项 | 变化 |
|---|---|
| 四语言键数 | **492 → 508**（8 条 × 标题/说明 = 16 键 × 4 语言） |
| 进度条数 | **35 → 43** |
| 成就键 | 70 → **86** 个 |
| 新增资源 | 8 个进度 JSON + 1 个伤害类型标签；**Java / 配方 / 贴图一行没动** |
| 成品 jar | **没重新打包** ⇒ `RELEASE_KEYS` 保持 **487**（成品里是别的线 23:22 打的那份） |

#### 五、证据

1. **真服务端探针** `Zf145Check`（已归档 `build\zftools\check\Zf145Check.java`，报告
   `_zf145_probe_utf8.txt`）：**111 项全绿、0 FAIL** —— 43 条全加载、父链逐条对、图标/frame/hidden、
   `requirements` 覆盖判据、「或/与」的组数、**伤害类型标签真的解析出来且正好 1 个值**，
   以及**真触发**：逐条喂物品点亮 8 条、三套盔甲**只给三件不许亮**（真「与」）、
   只给一把锹就点亮工具那条（真「或」）、
   ⚠ **先反后正**：拿原版 `player_attack` 打死一只僵尸 ⇒ 星辉斩**不**亮；再用
   `potato_s_t:star_steel_slash` 打死一只 ⇒ 才亮（这一对才是"标签判据真的在起作用"的证据）。
2. **常驻校验** `_zf145_verify.py`（项数见它自己的输出）：账目（另 35 份逐字节 = 开工前）、
   树形闭合、8 条新节点的结构逐字写死、标签文件逐字节、四语言 508 键、跟平、探针、文档。
3. **反证刀** `_zf145_falsify.py`：见它自己的输出。
4. ⚠ **两条实测提示**：① 成就界面里 `star_steel_tools` 是**任意一件**工具就亮，别以为是"集齐五件"；
   ② 星辉斩那条**要拿剑气把人打死**才亮（打残不算），死法文案是「%1$s被星光贯穿」。
'''

HAND27 = r'''27. **ZF145 的账（成就树补线）**：① 用户原话「是时候更新一下成就啦宝宝」。
    补了 **8 条**（振金锭 / 振金套 / 钛合金套 / 星璨钢五件工具 / **星辉斩** / 星仪图之章 /
    大型柴油发电机 / 银线），选中口径与四处"我定的"全文在档案 §9。
    ② 四语言 **492 → 508** 键、进度 **35 → 43** 条；**新增 1 个伤害类型标签**
    `data\potato_s_t\tags\damage_type\star_steel_slash.json`（星辉斩的击杀判据按标签筛伤害类型，
    这是本工程第一次用伤害类型标签）。**Java / 配方 / 贴图一行没动。**
    ③ 证据：探针 **111 项全绿**（含"先反后正"的击杀对照与"只给三件不许亮"）、
    `_zf145_verify.py` 常驻校验、`_zf145_falsify.py` 反证刀。
    ④ ⚠ **本轮没打包** ⇒ `RELEASE_KEYS` 保持 **487**（成品是别的线 23:22 打的那份）；
    谁再打包，谁就负责再看一眼这个数。
    ⑤ ⚠ **门跟平**：键数 492 → 508 打到 **30 份**常驻门（`_zf145_gatefix.py` 逐份记命中次数），
    进度条数 35 → 43 打到 5 份；**两条历史注释刻意没改**（`_zf119` 的 ZF121 retarget 说明、
    `_zf93` 讲成品 jar 的那行）—— 它们说的不是"盘上现在的键数"。
    ⑥ ⚠ **顺手补掉一处 ZF120 起就埋着的判据盲区**：`_zf107_verify.py` 的 `mod_ids()` 只扫
    `register("…")`，扫不到走私有注册器 `registerVibranium("…")` 的四件振金甲 ⇒
    判据点名振金甲时假 FAIL。已补全（§4.149）。**如果你们哪条门也在扫注册名，照同一处补。**
    ⑦ ⚠ **润色线请注意**：这 8 条新节点的标题/说明已经写进四语言（508 键），
    你们要改文案**只改值**不会打到我的门（`_zf145_verify.py` 只钉"我加的那 16 个键的值没被改"，
    别人的改动只打印不判 —— 与 ZF139 同一条口径）。

'''

ANN_ENTRY = r'''
---

## New in 0.11 ZF145 — advancement tree, part two (8 new nodes)

The tree grew from **35 to 43 advancements**, and everything added since the last pass now has a node:

| Node | Frame | How you get it |
|---|---|---|
| **Forge the Vibranium** | goal | Run the Alloy Smelter batch (1 Hard Titanium Alloy + 8 Thermal Metal + 2 High Carbon Steel + 3 Silver + 12 Gold, plus 1 Raw Vibranium + 2 Netherite Scrap) |
| **Vibranium Suit** | challenge | Upgrade all four titanium pieces at a Smithing Table with Vibranium Ingots |
| **Titanium Alloy Suit** | goal | Craft all four titanium pieces (24 Light Titanium Alloy) |
| **Star Steel Tools** | goal | Craft **any one** of the five Star Steel tools (sword / axe / shovel / pickaxe / hoe) |
| **Starlight Slash** | challenge | Finish a mob with the Star Steel Sword's Shift + right-click slash |
| **Star Chart Tome** | task | Craft the tome (4 Paper + 4 Amethyst Shards + 1 Glowstone) |
| **Large Diesel Generator** | goal | Craft the controller block of the 3x5x2 machine |
| **Silver Wire** | task | Craft a Silver Wire Spool (2 Silver Ingots -> 4 wire, 8 wire + 1 Empty Spool) |

⚡ **Starlight Slash is the first advancement in this mod that does not check an item.** It is granted by
`player_killed_entity` filtered on a **damage type tag** (`potato_s_t:star_steel_slash`) — so you have to
actually kill something *with the slash*; a normal sword swing does not count (and the probe verifies
exactly that, both ways).
'''

ANN_OLD = u"**35 advancements** walk you from your first machine"
ANN_NEW = u"**43 advancements** walk you from your first machine"


def main(argv):
    write = u"--write" in argv

    doc = read(DOC)
    lines = doc.split(u"\n")
    idx = [i for i, l in enumerate(lines) if l.startswith(u"| ZF14") and l.rstrip().endswith(u"|")]
    # 最后一个 `| ZF14x |` 行（ZF143）之后插
    rows = [i for i, l in enumerate(lines) if l.startswith(u"| ZF14")]
    if not rows:
        fails.append(u"§5 里找不到任何 `| ZF14x |` 行")
    else:
        lines.insert(rows[-1] + 1, ROW.rstrip(u"\n"))
        notes.append(u"  [插] 档案 §5 加 ZF145 行（插在第 %d 行之后）" % (rows[-1] + 1))
        doc = u"\n".join(lines)
    doc = before(doc, u"## 7. 权威情报来源", SEC4, u"档案 §4 加 4.148~4.149")
    doc = before(doc, u"## 10. 备份策略", SEC9, u"档案 §9 加 ZF145 小节")
    plan.append((DOC, read(DOC), doc))

    hand = read(HAND)
    hand = once(hand, u"| 语言键数 | **492 键 × 4**", u"| 语言键数 | **508 键 × 4**",
                u"交接 §1：键数 492 → 508")
    hand = once(hand, u"→ **492**（ZF144 星璨钢锹 + 剑的三行说明 + 剑气死亡文案 +5）。",
                u"→ **492**（ZF144 星璨钢锹 + 剑的三行说明 + 剑气死亡文案 +5）"
                u"→ **508**（ZF145 成就树补线：8 条进度 × 标题/说明 = +16）。",
                u"交接 §1：键数链条补一环")
    hand = once(hand, u"| 进度（成就） | **35 条**（3 老 + 24 ZF107 + 8 ZF117），一个标签页 |",
                u"| 进度（成就） | **43 条**（3 老 + 24 ZF107 + 8 ZF117 + **8 ZF145**），一个标签页 |",
                u"交接 §1：进度 35 → 43 条")
    hand = once(hand, u"24. **⚠ ZF139 的归档探针与它自己的报告对不上", HAND27 + u"24. **⚠ ZF139 的归档探针与它自己的报告对不上",
                u"交接 §6：加第 27 条")
    plan.append((HAND, read(HAND), hand))

    ann = read(ANN)
    ann = once(ann, ANN_OLD, ANN_NEW, u"公告开头：35 → 43 advancements")
    if u"ZF145" in ann:
        notes.append(u"  [跳过] 英文公告里已经有 ZF145 了（幂等）")
    else:
        ann = ann.rstrip(u"\n") + u"\n" + ANN_ENTRY
        notes.append(u"  [插] 英文公告补 ZF145 条目")
    plan.append((ANN, read(ANN), ann))

    print(u"")
    for n in notes:
        print(n)
    print(u"")
    if fails:
        print(u"失败项 = %d（一个字节都没写）" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    print(u"待写：%d 份" % len(plan))
    if not write:
        print(u"（没加 --write，只算不写）")
        return 0
    final = {}
    for p, _o, new in plan:
        final[p] = new
    for p, _o, new in plan:
        io.open(p, u"w", encoding=u"utf-8", newline=u"").write(new)
    for p, want in final.items():
        assert read(p) == want, p
    print(u"已写盘；回读 %d 份逐字节等于**该路径最后一条**计划" % len(final))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
