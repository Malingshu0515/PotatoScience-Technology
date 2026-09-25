# -*- coding: utf-8 -*-
u"""_zf118_docs.py —— ZF118 文档：档案 §5/§9/§4 + 交接文档活体数字 + 英文公告

并发环境（同一棵树上 ZF116 素材线还在跑）⇒ 一律「按**行首前缀**定位 → 插入 → 立刻回读断言」（§4.84）。
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ARCH = ROOT + r"\docs\开发档案.md"
HAND = ROOT + r"\docs\多会话协作交接.md"
ANN = ROOT + r"\docs\UpdateAnnouncement_EN.md"

fails, notes = [], []


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def insert_after_prefix(path, prefix, block, label):
    raw = read(path)
    probe = [l for l in block.split(u"\n") if l.strip()][0]
    if probe in raw:
        notes.append(label + u"（已经在盘上，跳过）")
        return True
    lines = raw.split(u"\n")
    hits = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if not hits:
        fails.append(u"%s：找不到行首前缀 %r" % (label, prefix[:40]))
        return False
    lines[hits[0] + 1:hits[0] + 1] = block.split(u"\n")
    write(path, u"\n".join(lines))
    if probe not in read(path):
        fails.append(u"%s：回读失败" % label)
        return False
    notes.append(label)
    return True


def insert_before_exact(path, exact, block, label):
    raw = read(path)
    probe = [l for l in block.split(u"\n") if l.strip()][0]
    if probe in raw:
        notes.append(label + u"（已经在盘上，跳过）")
        return True
    if raw.count(exact) != 1:
        fails.append(u"%s：锚点出现 %d 次" % (label, raw.count(exact)))
        return False
    write(path, raw.replace(exact, block + exact, 1))
    if probe not in read(path):
        fails.append(u"%s：回读失败" % label)
        return False
    notes.append(label)
    return True


def sub_once(path, old, new, label):
    raw = read(path)
    if new in raw and old not in raw:
        notes.append(label + u"（已经是新值，跳过）")
        return True
    if raw.count(old) != 1:
        fails.append(u"%s：锚点出现 %d 次" % (label, raw.count(old)))
        return False
    write(path, raw.replace(old, new, 1))
    if new.split(u"\n")[0] not in read(path):
        fails.append(u"%s：回读失败" % label)
        return False
    notes.append(label)
    return True


ROW = (
    u"| ZF118 | **新建 `zf118_pre`**（188 份改前件：生成器表 `_zf45_recipes.py` + **盘上 59 份配方全抄** + "
    u"11 份配方耦合校验 + 全部常驻校验脚本 + 3 份文档 + 旧成品 jar 与 `.sha1`；逐份核哈希、失败 0。"
    u"**预防性补账 1 份**：`PotatoST.java`（探针挂载点）这次在挂钩子**之前**先抄（等级 ①：`git cat-file blob HEAD:` "
    u"逐字节相同，sha1 `f5989035…`），见 `zf118_pre\\_补说明.txt`） "
    u"| 0.11：**星轨坠的合成配方**。用户原话：「星轨坠配方；中间一个下界之星 上下左右各一个星璨钢 四角放岩浆块」。"
    u"① 图纸逐格照抄 ⇒ `MSM / SNS / MSM`（M=岩浆块 四角、S=星璨钢锭 上下左右、N=下界之星 中心），产物 **×1**，"
    u"`category=misc`；② 按**生成器规矩**走：只改 `_zf45_recipes.py` 的表再 `--write`，白拿两样机械核对"
    u"（本模组 id 查注册 / 原版 id 查 `client.jar` 的物品模型）+ 表与 JSON 逐字节一致；"
    u"③ **踩出一笔旧账**：ZF112 改过 `lithium_battery.json`（碳酸锂→锂电池原件、板→纸）却**只改了 JSON、没改表**"
    u"⇒ 本轮生成器一跑就把那张图纸**打回旧版**，被我的前置断言（写盘前逐份比 `zf118_pre` 的哈希）当场抓住 ⇒ "
    u"还原 JSON + 把表改成真图纸 + 用表重跑互证（§4.93）；④ 新立一条**常驻检查**：生成器表里 **31 条**逐条与盘上 "
    u"JSON 比（以后谁再手改 JSON 当场红）；⑤ 证据：真服务端探针 `Zf118Check`（**照着图纸摆 9 格让 "
    u"`getRecipeFor` 去匹配** + `assemble` + 4 组负向 + 合成出来真能点亮 ZF117 那条隐藏进度）、"
    u"`_zf118_verify.py`（**56 项**）、反证 7 把刀；⑥ 活体数字：配方 **59 → 60 份**、`crafting_shaped` "
    u"**53 → 54**、生成器表 **30 → 31 条**；四语言**仍 448 键**（加配方不动文案 ⇒ 21 份键数校验一份都不用改） | 见 §9 |"
)

SEC9 = u'''
### ZF118（0.11）星轨坠的合成配方（+ 生成器表与盘对账）—— **未打包**

用户原话：「星轨坠配方；中间一个下界之星 上下左右各一个星璨钢 四角放岩浆块」

ZF114 把星轨坠做出来时**没有配方**（用户当时说"先不给"），ZF117 因此把它做成**隐藏彩蛋位**的成就。
这一轮配方到了：

```
【岩浆块】   【星璨钢锭】  【岩浆块】
【星璨钢锭】 【下界之星】  【星璨钢锭】        →  星轨坠 ×1（category = misc）
【岩浆块】   【星璨钢锭】  【岩浆块】
```

#### 一、按规矩走生成器，不手写 JSON

配方只写在 `build\\zftools\\_zf45_recipes.py` 的表里，再 `--write` 生成
`data\\potato_s_t\\recipe\\starfall_pendant.json`。这样白拿两样机械核对：

1. **id 真的存在** —— 本模组查四个注册类，原版查 `client.jar` 的 `assets/minecraft/models/item/*.json`
   （`minecraft:magma_block` / `minecraft:nether_star` 都在）；
2. **表与盘逐字节一致** —— 本轮把这条从"只盯个别配方"扩成**整表 31 条逐条比**，写进
   `_zf118_verify.py` 的 B8（常驻）。

#### 二、踩出一笔旧账：**ZF112 改配方时只改了 JSON，没改表**（§4.93）

我一跑 `--write`，脚本的**前置断言**（写盘前后逐份比 `zf118_pre` 的 59 份哈希）就报：

```
!! 生成器表把别的配方改了！['lithium_battery.json']
```

diff 一看：盘上（ZF112 之后）是 `minecraft:paper` ×6 + `potato_s_t:lithium_battery_component`，
而表里还是 ZF100 那版（铝板 / 铜板 / 碳酸锂）—— **生成器把 ZF112 的改动打回了旧版**。
处理：① 从改前件**逐字节还原**那份 JSON；② 把表里那条改成真图纸；
③ 用改好的表**重跑**，产物与还原件逐字节相同（两条路互证）。这一步见 `_zf118_fixtable.py`。

#### 三、证据

| 项 | 值 |
|---|---|
| 配方 | `MSM / SNS / MSM`，`M=minecraft:magma_block`、`S=potato_s_t:star_steel_ingot`、`N=minecraft:nether_star` → 星轨坠 ×1 |
| 探针 | `Zf118Check.java`（真 `runServer`）：`byKey` 加载 + **照图纸摆 9 格让 `getRecipeFor` 匹配**（形状真的对）+ `assemble` 出 1 个 + **4 组负向**（中心换下界砖 / 右上留空 / 四角换岩浆膏 / 九格全岩浆块 —— 都不许匹配到这条）+ **端到端**：把合成出来的星轨坠给假玩家 ⇒ ZF117 那条隐藏进度点亮 |
| 探针存档 | `build\\zftools\\check\\Zf118Check.java`（**先抄后删**，§10.1） |
| 常驻校验 | `_zf118_verify.py`（**56 项**）：图纸**按位置**逐格核（不是只看 key 表）、表↔盘逐字节、59 份旧配方逐字节未变、没有第二条产出星轨坠的配方、整表 31 条对账、四语言仍 448 键 |
| 反证刀 | **K150~K156（7 把）**：图案改转置 / 中心换成下界砖 / 产物数量改 4 / 四角换成岩浆膏 / 删掉配方文件 / 表改了不重跑 / 公告那句退回 no recipe yet —— 每把都必须咬住指定的检查 |
| 活体数字 | 配方 **59 → 60 份**；`crafting_shaped` **53 → 54**；生成器表 **30 → 31 条**；四语言**仍 448 键** |

**要你实测的**（进游戏）：拿 4 个岩浆块 + 4 个星璨钢锭 + 1 个下界之星，在工作台摆成上面那张图 ⇒ 出 1 个星轨坠；
JEI 里搜「星轨坠」现在能看到这条配方。

**成品**：**本轮没有新成品** —— `release\\PotatoST-0.11.jar` 仍是 ZF114 打的 **`303c5d468b96826ef6836b0a4e54ccb8a539557c`**（4,298,939 B，432 键，不含 ZF116~ZF118）。
下一轮打包要作废的是**它**。

'''

PITFALL = u'''
### 4.93 【生成器雷】配方表与盘上 JSON **脱钩**：手改 JSON 会在下次重跑时被**静默打回**（0.11 ZF118）

本工程的合成配方有一条老规矩（ZF45 起）：**配方只写在生成器表 `_zf45_recipes.py` 里，
再 `--write` 生成 JSON**；表里的 id 会被机械核对（本模组查注册、原版查 `client.jar` 的物品模型）。
ZF69 那一轮还把「表 ↔ JSON 逐字节一致」立成了门。

**ZF112 踩了这条**：用户要「三元锂配方里的碳酸锂改成锂电池原件 金属板统一换成纸」——
那一轮**直接改了 `lithium_battery.json`，没有同步生成器表**。
于是那张图纸在表里还是旧版（铝板 / 铜板 / 碳酸锂），而门只盯着它自己那条（`heat_sink`），谁也没发现。

**ZF118 加星轨坠时引爆**：按规矩跑 `--write` ⇒ 生成器把 `lithium_battery.json`
**打回 ZF100 的旧图纸**。抓住它的是我这次特意加的一道前置断言：
**写盘前先逐份比 `zf118_pre` 里那 59 份配方的哈希**（`_zf118_recipe.py` 的 ③）。
处理：还原 JSON + 把表改成真图纸 + 用表重跑互证（两条路逐字节相同）。

**规矩（两条）**：

1. **改配方 = 改表 + 重跑**。直接编辑 `data\\potato_s_t\\recipe\\*.json` 的后果不是"当下报错"，
   而是**下一次谁跑生成器谁把它打回去** —— 而且那次 diff 会出现在**别人的轮次**里，极难归因。
2. **重跑生成器之前，先抄一份配方目录**（本轮 `zf118_pre` 抄了 59 份）；
   跑完立刻逐份比哈希 —— 这一步是**零成本**的，它本轮直接抓住了一处静默回退。
   同一个检查现在也**常驻**了：`_zf118_verify.py` 的 B8 把整表 31 条逐条与盘上比。

'''

ANN_ENTRY = u'''
- **Starfall Pendant recipe (0.11 ZF118)** - the meteor pendant is craftable now: **4 Magma Blocks in the corners, 4 Star Steel Ingots on the four edges, and a Nether Star in the middle** -> 1 Starfall Pendant. Use it (right-click) and a meteor comes down from y=200 thirty seconds later; see section 6 for what it does.
'''

fails_placeholder = None


def main():
    # ---------- 档案 ----------
    insert_after_prefix(ARCH, u"| ZF117 |", ROW, u"档案 §5 加 ZF118 行")
    insert_before_exact(ARCH, u"## 10. 备份策略", SEC9, u"档案 §9 加 ZF118 小节")
    insert_before_exact(ARCH, u"## 7. 权威情报来源（怎么查原版行为，别靠记忆）",
                        PITFALL, u"档案 §4 加 4.93")

    # ---------- 交接：活体数字 ----------
    sub_once(HAND,
             u"| 配方 | `data\\potato_s_t\\recipe\\` **59 份**（其中 `crafting_shaped` **53** 条） | 多条线都会加 |",
             u"| 配方 | `data\\potato_s_t\\recipe\\` **60 份**（其中 `crafting_shaped` **54** 条）；"
             u"生成器表 `_zf45_recipes.py` **31 条** | 多条线都会加；⚠ 改配方**只改表再 `--write`**（§4.93） |",
             u"交接 §1 配方活体数字")
    # ---------- 交接：§5.4 配方那条 ----------
    sub_once(HAND,
             u"- 要能合成：配方写进生成器表 `build\\zftools\\_zf45_recipes.py`（**表与 JSON 必须一致**，有门在比），",
             u"- 要能合成：配方写进生成器表 `build\\zftools\\_zf45_recipes.py`（**表与 JSON 必须一致**，"
             u"`_zf118_verify.py` 的 B8 现在**整表逐条**在比），\n"
             u"  ⚠ **别直接编辑 `recipe\\*.json`** —— ZF112 就是这么干的（碳酸锂→锂电池原件那轮），"
             u"结果 ZF118 一跑生成器就把那张图纸**打回旧版**（§4.93）。改配方 = 改表 + `--write`；",
             u"交接 §5.4 配方那条")
    print(u"\n".join(u"  [OK] " + n for n in notes))

    # ---------- 交接：§6 欠账（在 ZF117 那节后面追加 ZF118 两条）----------
    raw = read(HAND)
    anchor = u"10. **ZF117 的账目补记**"
    add = (u"11. **ZF118 的账**：① 星轨坠配方上线之后，ZF117 给它做的**隐藏彩蛋位**是不是要挪进主线"
           u"（挂到 `star_steel` 下面、取掉 `hidden`）—— 一句话就改；\n"
           u"    ② ZF112 那笔「手改 JSON 没改表」的老账本轮已收口（表改成真图纸 + 逐字节互证），"
           u"**但配方耦合的 9 道门的名单还没跟**（仍是打包轮的活，现在盘上 **60 份 / 54 条**）。\n")
    if u"11. **ZF118 的账**" in raw:
        notes.append(u"交接 §6 已有 ZF118 条目（跳过）")
    elif raw.count(anchor) == 1:
        i = raw.find(anchor)
        j = raw.find(u"\n", i) + 1
        write(HAND, raw[:j] + add + raw[j:])
        notes.append(u"交接 §6 追加 ZF118 两条")
    else:
        fails.append(u"交接 §6：锚点 %r 出现 %d 次" % (anchor, raw.count(anchor)))

    # ---------- 英文公告 ----------
    sub_once(ANN, u"└── + Starfall Pendant    the meteor pendant (no recipe yet)",
             u"└── + Starfall Pendant    the meteor pendant (4 Magma Blocks + 4 Star Steel Ingots + a Nether Star)",
             u"公告 §7 树里那行")
    raw = read(ANN)
    if u"Starfall Pendant recipe (0.11 ZF118)" in raw:
        notes.append(u"公告已有 ZF118 条目（跳过）")
    else:
        if not raw.endswith(u"\n"):
            raw += u"\n"
        write(ANN, raw + ANN_ENTRY)
        if u"Starfall Pendant recipe (0.11 ZF118)" in read(ANN):
            notes.append(u"公告追加 ZF118 变更条目")
        else:
            fails.append(u"公告：追加条目回读失败")

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
