# -*- coding: utf-8 -*-
u"""_zf109_docs.py —— ZF109 的文档四处（0.11 采油机）

插四处，每处的锚点都要求**正好命中 1 次**（找不到或找到多处就报错退出，不猜）：
  · `docs/开发档案.md`：§4.79 + §4.80（本轮两条新雷）插在 §6.1 之前；
    §5 表加 ZF109 行（插在 ZF108 行之后）；§9 加 ZF109 小节（插在 §10 之前）；
  · `docs/UpdateAnnouncement_EN.md`：§3 机器表加一行、§5 加一小节、键数 398 → 408；
  · `docs/贴图清单.md`：末尾加 ZF109 那一节。
⚠ 中文里一律用「」，不许出现 ASCII 双引号（本工程老规矩）。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, r"docs\开发档案.md")
ANN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
PLAN = os.path.join(ROOT, r"docs\贴图清单.md")

fails = []


def read(p):
    return io.open(p, encoding="utf-8", newline="").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)


# ============================================================
#  §4.79 + §4.80
# ============================================================
SEC4 = u"""
### 4.79 【实现雷】1.21.1 **没有** `setBiome` / `fillBiome` / `getBiomes` —— 运行时改群系只有 `fillBiomesFromNoise` 一条路（0.11 ZF109）

采油机要把一片海洋油田「抽干」成普通海洋。动手前我按老规矩**不猜 API**：把
`neoforge-21.1.235-sources.jar`（7107 个真源码文件，5500 个 `net/minecraft`）解出来 +
`javap -p` 对着 jar 逐个核，结论是：

| 想要的名字 | 1.21.1 里有吗 | 真正的口子 |
|---|---|---|
| `ChunkAccess#getBiomes()` | **没有** | `LevelChunkSection#getBiomes()` 返回的是**只读**接口 `PalettedContainerRO`，里面的 `biomes` 字段是 private 且没有 setter |
| `ChunkAccess#fillBiome(...)` / `#setBiome(...)` | **没有** | 只有一个：`ChunkAccess#fillBiomesFromNoise(BiomeResolver, Climate.Sampler)` |
| `LevelChunkSection#setBiome(...)` | **没有** | `LevelChunkSection#fillBiomesFromNoise(BiomeResolver, Climate.Sampler, int, int, int)` |

原版 `/fillbiome` 指令（`FillBiomeCommand`）走的就是这条路 —— 照它抄就对了。
NeoForge 21.1.235 **没有**更高级的助手（1069 个 `net/neoforged` 文件里搜
`fillBiome|setBiome|BiomesFromNoise|resendBiome` 只有一个不相关的
`StructureSettingsBuilder#setBiomes`），群系那一套全是 worldgen 期的。
本工程**没有** `accesstransformer.cfg`（`build.gradle` 里那行是注释掉的）⇒ 也不需要 AT / mixin。

**三个会静默出错的坑（都写进代码注释了）**：

1. **`fillBiomesFromNoise` 会重写整根柱子** —— 它内部对每个 section 都 `biomes.recreate()`
   再问一遍 resolver。所以 resolver **必须在区域外原样返回旧群系**，否则整根柱子被抹平成一个群系；
2. **改完必须 `chunk.setUnsaved(true)`** —— `ChunkMap.save` 看到 `!isUnsaved()` 直接 return，
   **不落盘**（看起来一切正常，重启就白改了）；
3. **通知客户端要用 `ChunkMap#resendBiomesForChunks(List<ChunkAccess>)`** —— 1.21.1 这个方法
   **只发群系调色板**（`ClientboundChunksBiomesPacket`），不是整块重发。老教程里那种
   `ClientboundLevelChunkWithLightPacket` 重发整块的写法在这里既多余又是性能灾难。
   客户端收到后会自己清染色缓存 + 把渲染区块标脏，**不用重登**。

另外两条实测口径：`Level#getBiome(pos)` 是**合成查找**（`BiomeManager`，取四周 4 个 quart 格
加权），不是原始格子；`ChunkAccess#getNoiseBiome` 才是原始格子（quart 坐标）。
群系**会**随区块存盘（`ChunkSerializer` 每个 section 写 `biomes`），也没有任何服务端缓存会
让这次写入失效（`NaturalSpawner` 读的是活数据）。⚠ 必须在**服务端主线程**调用
（`ServerChunkCache#getChunk` 会检测跨线程并阻塞重派）。

### 4.80 【方法论】探针「数不对」时，先怀疑**夹具的几何**，不是先改代码（0.11 ZF109）

采油机的下探计数要验「中间夹一块石头就该断」。第一版探针把石头放在**链条下面那一格**，
期望 `n = 0`，结果实测 `n = 3` —— 看着像代码错了。其实**错的是我的预期**：
下探是「从机器往下数**连续**的一段」，石头垫在**下面**只是「到此为止」，上面那 3 根照样算；
要测「夹在中间」必须把石头放在**第 2 格**（那样只能数到 1 根）。

这条不改代码，改的是**探针的夹具**与文案：现在两条都测 ——
「链条下面垫石头 ⇒ n 仍是 3（只是到此为止）」与「石头夹在第 2 格 ⇒ 只数得到 1 根」。
§4.30 那条「先怀疑预期」在这儿第二次救场：**一个 FAIL 不等于一个 bug**，
先问「我这个测试摆的是不是我以为的那个样子」。
"""

# ============================================================
#  §5 表行（一行到底）
# ============================================================
ROW5 = (u"| ZF109 | **新建 `zf109_pre`**（105 份改前件：5 个既有 Java（`ModBlocks`/`ModMenus`/"
        u"`PotatoST`/`PotatoSTClient`/`client/gui/parts/StatusLampPart`）+ 四份 lang + "
        u"`data/minecraft/tags/block/mineable/pickaxe.json` + **全部常驻校验脚本**"
        u"（`_zf*_verify/repro/guard/falsify/gatesnap/gatecount` 一把抄全，不再赌「我记得改过哪几份」）"
        u"+ 3 份文档 + 旧成品 jar 与 `.sha1`；另存三张目录清单：`_recipe_before.txt`（**57** 份配方）、"
        u"`_java_before.txt`（**111** 份）、`_textures_before.txt`（**94** 张方块贴图）；"
        u"⚠ 另有 **1 份补账**：`client/gui/parts/FluidTankPart.java`（动手前没想到要碰界面部件 —— "
        u"采油机的大罐要横躺，最后决定给这一个部件加方向开关而不是复制一份，见 `zf109_pre\\_补说明.txt`）；"
        u"**先抄后动手**） | 0.11：**采油机（新机器）+ 运行时改群系**。用户原话见 §9 ZF109 那一节。"
        u"① **两个歧义数都是问过、用户拍板的**：耗能公式 `80n*1/10n+80n` 选 **B 读法 8n²+80n FE/t**"
        u"（n=1/2/3/10 → 88/192/312/1600）；「10*10」的单位选 **10×10 区块**（160×160 格）；"
        u"② **机器**：6 个新 Java（方块 / 方块实体 / 菜单 / 界面 / **群系转换器 `OilfieldDepletion`**）+ "
        u"6 处注册（`ModBlocks` 三件套 / `ModMenus` / `PotatoST` **两个能力**：收 FE + 只出不进的流体口 / "
        u"`PotatoSTClient` 界面）+ `StatusLampPart` 新起 **15「不在海洋油田」、16「下方没有含水锁链」**"
        u"两个共享状态码（先看能不能共用，不能才新起 —— 照 ZF96/ZF97 的规矩）；"
        u"③ **开工三条**：站在海洋油田群系 + 正下方是水（下探数含水锁链 = n，上限 64 格）"
        u"+ 有电（8n²+80n，储能 32768 是我定的数）；产油 10n mB/s（n/2 mB/t，整数攒零头）；"
        u"④ **抽干油田**：累计每 25~80 桶（每次重抽）把以机器为中心 10×10 区块里的海洋油田改成"
        u"旁边那种海洋（区域外一圈按区块投票、票同按 id 字典序、一格海都没有兜底 `minecraft:ocean`）；"
        u"⚠ 那 100 个区块含机器自己 ⇒ **抽一次就停机**（选项说明里已写明，用户接受）；"
        u"⑤ **界面**：一个**横躺**的 25B 油罐（`FluidTankPart` 加 horizontal 方向开关）+ 一盏工作指示灯，"
        u"**没有能量条**（用户点名不要）；罐下两行数字是我加的（说一声就删）；"
        u"⑥ **运行时改群系**这条硬骨头见 §4.79（1.21.1 没有 `setBiome`/`fillBiome`/`getBiomes`，"
        u"只有 `fillBiomesFromNoise`；`setUnsaved` + `resendBiomesForChunks` 一个都不能少） |")

# ============================================================
#  §9 小节
# ============================================================
SEC9 = u"""### ZF109（0.11）采油机：把海洋油田抽起来（**新机器 + 运行时改群系**）—— **未打包**

原话：「海洋油田可以利用起来了 加一个采油机（配方；【硬质钛合金】【耐热金属块】【硬质钛合金】，
【油桶】【高压气罐】【油桶】，【流体泵】【流体泵】【流体泵】） 在海洋油田群系工作
gui为一个大罐子25B储量（不是那种竖直的了 是一个横过来的矩形罐子）和一个工作指示灯
能量条不需要 下方必须有水源方块 检测下方连接的 含水锁链的数量
耗能公式为 80n*1/10n+80n FE/t 原油获取为 10n mb/s （n为下方含水锁链个数）
每开采25~80桶原油 附近10*10的海洋油桶群系会变成符合旁边群系的海洋（冻洋 暖洋 温带海洋...）」

**两个数我没自己发明，列了表问你、你拍板的**：

| 问题 | 三种读法 | 你选的 |
|---|---|---|
| 耗能公式 `80n*1/10n+80n` | A `80n+8` / **B `8n²+80n`** / C `88n` | **B**（n=1/2/3/10 → 88 / 192 / 312 / 1600 FE/t） |
| 「10\*10」的单位 | 100 格方块 / **10×10 区块（160×160 格）** | **10×10 区块** |

**开工三条（缺一不可）**：

1. **站在海洋油田群系里**（`potato_s_t:ocean_oilfield`）—— 不是就黄灯停机（状态码 **15**）；
2. **正下方是水**：从机器正下方一格一格往下走，**只要这一格的流体状态是水源就继续**，
   数到几根**含水锁链**（原版锁链 + `waterlogged=true`）就是 **n**；
   石头 / 空气 / **干**锁链都让下探当场停住；上限 **64 格**（我定的，用户没给）；
3. **有电**：**8n² + 80n FE/t**；储能 **32768 FE**（我定的 —— 用户只说了「能量条不需要」，那是界面的事）。

**产油**：**10n mB/s** ⇒ 每 tick 攒 n 个「半点」（n/2 mB/t），整数运算、零头留到下一 tick，不丢精度。
25B 大罐只出不进（管道 / 流体泵能抽走，灌不进去）；罐满 ⇒ 状态 4 且**不扣电**。

**抽干油田**：累计采出每够一次「欠账」（**25~80 桶**，每次到点后重新随机）就把
**以机器为中心的 10×10 区块**里所有「海洋油田」格子改成**旁边那种海洋**：
在区域**外**一圈按区块采样、票多者胜（票数相同按群系 id 字典序，保证可复现），
一格海都没有就兜底温带海洋 `minecraft:ocean`。
⚠ 那 100 个区块**包含机器自己** ⇒ **抽一次这台机器就停机**，要接着抽得挪到还剩油田的地方
—— 这一条写在问「10\*10 的单位」时的选项说明里（原话：转换后油机会因为不再是油田而停机，
等于把油田抽干），你选了它。

**1.21.1 运行时改群系这条硬骨头**：完整结论在 **§4.79**（`fillBiomesFromNoise` +
`setUnsaved(true)` + `resendBiomesForChunks` 三件套；`getBiomes`/`fillBiome`/`setBiome` 都不存在）。
转换器 `OilfieldDepletion` 还额外守住两条：**没加载的区块直接跳过**（不为了这 100 个区块去强加载）、
**只改「海洋油田」格子**（别的群系原样交回去，所以不会把整根柱子抹平）。

| | 改前 | 改后 |
|---|---|---|
| 机器 | 无 | `oil_pump` 采油机：方块 / 方块实体 / 菜单 / 界面 / 群系转换器 5 个新 Java |
| 配方 | 无 | 硬质钛合金 / 耐热金属块 / 硬质钛合金 ＋ 油桶 / 高压气罐 / 油桶 ＋ 流体泵 ×3（**照原话一个符号没改**） |
| 界面 | 无 | 横躺 25B 油罐 + 工作指示灯，**没有能量条**（+ 罐下两行数字，我加的） |
| 状态码 | 0/3/4/5 共享 | 新起 **15 = 不在海洋油田**、**16 = 下方没有含水锁链**（黄灯） |
| 资源 | 无 | 1 张新方块贴图（16×16 / 5 色 / 151 B，程序生成占位）+ blockstate + 两个模型 + 挖掘标签 |
| 四语言 | 398 键 | **408 键**（10 个新键：方块名 / tooltip / 两行界面数字 / 6 个状态灯文案） |

**证据**：

- [x] `build\\zftools\\_zf109_verify.py`：常驻校验（配方逐格核对用户原话那张九宫格 / 常数与公式**真算** /
      下探与抽干的语义 / 四语言 408 键且键序逐位相同 / 贴图色数与调色板 / 探针报告还在）
- [x] 探针 `Zf109Check.java`（真游戏 `runServer`）：**69 项全绿**，报告 `build\\zftools\\_zf109_probe_utf8.txt`；
      实测过的：两个能力真挂上了 / 群系门禁 15 / 没链条 16 / 3 根=3、干链子=2、石头垫下面=3、
      石头夹中间=1、70 根夹到 64 / n=3 跑 20 tick 正好 6240 FE + 30 mB、n=1 正好 1760 FE + 10 mB /
      罐满停机且不扣电 / `fill` 恒 0、`drain` 拿得到原油 / 红石停机 / **存档往返字段一致** /
      `convertAround(…, 10)`：chunks+skipped=100、cells=1536、目标 ∈ `#minecraft:is_ocean`、
      机器脚下不再是油田、区块被标脏、**下一 tick 立刻停机** / 一圈都写成暖洋时票选结果 = 暖洋
- [x] 探针存档：`build\\zftools\\check\\Zf109Check.java`（24632 B，sha1 `567357fd…`，**先抄后删**）
- [x] 反证刀 K99~K115（见汇报；每把都是「改一处语义 ⇒ 校验器必须 FAIL ⇒ 逐字节还原 ⇒ 回到全绿」）
- [x] 换行：本轮碰过的文件全 LF（§4.8）

**要你实测的**（进游戏）：

1. **摆一台**：拿硬质钛合金×2、耐热金属块、油桶×2、高压气罐、流体泵×3 合成，扔进海里；
2. **看不到油就按这条顺序查**：GUI 里那两行数字 —— 「含水锁链：N 根」是 0 就说明
   正下方没有**泡在水里的**锁链（挂链子的时候必须是水里的，干了不算）；
3. **接一根管道 + 流体泵**把油抽走（罐子只出不进，手倒不进去）；
4. **抽到 25~80 桶时看一片海变色**（冻洋/暖洋/温带海洋按旁边的海来定）——
   那一刻这台机器会**停机**（它自己脚下的油田也没了），这是设计，不是 bug。

**成品**：**本轮没有新成品** —— `release\\PotatoST-0.11.jar` 仍是 ZF103 那版 `90510e18…`。

"""

# ============================================================
#  公告：§3 表格行 + §5 小节 + 键数
# ============================================================
ANN_ROW = (u"| **Oil Extractor** (new in 0.11) | Runs **only in the Ocean Oilfield biome**, and only "
           u"when the column straight below it is water: hang waterlogged chains down from the "
           u"machine and that count is **n**. Drains with pipes / a fluid pump (its 25-bucket tank "
           u"is output-only). Every 25-80 buckets it pumps, the ocean oilfield in a **10x10 chunk** "
           u"area centred on the machine turns into the surrounding ocean - and since that area "
           u"includes the machine itself, it stops right after and has to be moved to whatever "
           u"oilfield is left. | **8n² + 80n FE/t** (n=10 -> 1,600); **10n mB/s** (n=10 -> 100); "
           u"25,000 mB tank; 32,768 FE buffer; no energy bar in its panel - just the tank and a "
           u"status lamp |")

ANN_SEC = u"""### The Oil Extractor and the Ocean Oilfield (new in 0.11)

The **Ocean Oilfield** biome (added in 0.11) is no longer just scenery - the **Oil Extractor**
pumps it dry:

- it works **only inside that biome**; anywhere else the status lamp goes yellow and it stops;
- the column **straight down** from the machine must be water. Walk down block by block while the
  block's fluid state is a water source, and count the **waterlogged chains**: that count is **n**
  (it stops at stone, air or a *dry* chain, and is capped at 64). Plain water blocks keep the walk
  going but do not count - so the machine has to stand over water, chains or no chains;
- power draw is **8n² + 80n FE/t** (88 / 192 / 312 / 1,600 at n = 1 / 2 / 3 / 10) and it produces
  **10n mB/s** of crude oil, straight into its **25-bucket tank**. The tank is output-only: pipes
  and fluid pumps can drain it, nothing can be poured in, and a full tank stops the machine
  without draining power;
- every **25-80 buckets** pumped (rerolled each time) it converts the **10x10 chunk** area centred
  on itself - every cell that is still Ocean Oilfield - into the ocean biome its neighbours vote
  for (frozen / cold / temperate / warm / lukewarm, deep variants included; a tie is broken by
  biome id, and if no neighbour is an ocean it falls back to `minecraft:ocean`).

⚠ Because that 160x160 area includes the machine's own position, **the machine stops after each
conversion** - move it to whatever oilfield is left to keep pumping. That is the point: an
oilfield is a finite resource now.

Under the hood this rewrites biome data in already-generated chunks. 1.21.1 has **no**
`setBiome` / `fillBiome` / `getBiomes` to call - the only public way is `ChunkAccess#
fillBiomesFromNoise`, the same one vanilla's `/fillbiome` command uses - and the change only
survives a save/reload if the chunk is marked unsaved, with clients told through
`ChunkMap#resendBiomesForChunks` (which sends biome palettes only, in 1.21.1).

"""

PLAN_SEC = u"""
## ZF109（0.11）：采油机（**1 张新方块贴图，程序生成占位**）

用户没给贴图也没要求画（原话里只有机器 / 界面 / 数值），但新方块没有 PNG 就是紫黑格 ⇒
照 ZF97 / ZF100 / ZF101 / ZF108 的先例先用程序生成一张能看的。

| 放哪 | 文件名 | 是什么 | 现在长什么样 |
|---|---|---|---|
| `textures/block/` | `oil_pump.png` | 采油机（六面同一张） | 深灰钢板 + 四角铆钉（`#9aa2ac`）+ 中间一台**横躺的油罐**（罐里是熔融亮色 `#e8912f`）+ 下面一个**朝下的吸油管口**。16×16 / **5 色** / 151 B |
| `blockstates/` | `oil_pump.json` | 方块状态 | 只有一种变体（**没有朝向**，与空气分离器 / 酸性反应室同款） |
| `models/block/` | `oil_pump.json` | 方块模型 | `parent = minecraft:block/cube_all`，六面都取上面那张图 |
| `models/item/` | `oil_pump.json` | 物品图标 | 直接父级到方块模型 |

生成脚本：`build\\zftools\\_zf109_textures.py`（顶部一张 16×16 的**字符图例表**；
不带 `--write` 只出预览 `build\\zftools\\_zf109_preview.png`，带 `--write` 才落盘 PNG）。

**要换手绘的**：直接覆盖 `textures/block/oil_pump.png`（16×16、RGBA、不透明），
**模型一个字不用改**；想在手绘之前先调我这张，就改图例表里那几个字符。
"""


def insert_before(text, anchor, payload, name):
    u"""在 anchor 那一行**之前**插 payload（anchor 必须正好命中 1 次）"""
    idx = [i for i, line in enumerate(text.split(u"\n")) if anchor in line]
    if len(idx) != 1:
        fails.append(u"%s：锚点命中 %d 次" % (name, len(idx)))
        return text
    lines = text.split(u"\n")
    payload_lines = payload.split(u"\n")
    if payload_lines and payload_lines[0] == u"":
        payload_lines = payload_lines[1:]
    if payload_lines and payload_lines[-1] == u"":
        payload_lines = payload_lines[:-1]
    out = lines[:idx[0]] + payload_lines + lines[idx[0]:]
    return u"\n".join(out)


def insert_after(text, anchor, payload, name):
    idx = [i for i, line in enumerate(text.split(u"\n")) if anchor in line]
    if len(idx) != 1:
        fails.append(u"%s：锚点命中 %d 次" % (name, len(idx)))
        return text
    lines = text.split(u"\n")
    payload_lines = payload.split(u"\n")
    if payload_lines and payload_lines[0] == u"":
        payload_lines = payload_lines[1:]
    if payload_lines and payload_lines[-1] == u"":
        payload_lines = payload_lines[:-1]
    out = lines[:idx[0] + 1] + payload_lines + lines[idx[0] + 1:]
    return u"\n".join(out)


def main():
    # ---- 开发档案 ----
    doc = read(DOC)
    if u"### 4.79 " in doc:
        fails.append(u"开发档案：§4.79 已经写过了（别插第二遍）")
    else:
        doc = insert_before(doc, u"### 6.1 加一个**音乐唱片**", SEC4, u"§4.79/4.80")
        doc = insert_after(doc, u"| ZF108 |", u"\n" + ROW5 + u"\n", u"§5 表行")
        doc = insert_before(doc, u"## 10. 备份策略", SEC9, u"§9 小节")
        write(DOC, doc)

    # ---- 英文公告 ----
    ann = read(ANN)
    if u"Oil Extractor" in ann:
        fails.append(u"公告：Oil Extractor 已经写过了")
    else:
        ann = insert_before(ann, u"| **Test Fluid Tank** / **Creative Cable**", ANN_ROW, u"公告 §3 行")
        # §5 的小节插在 Crude oil 那一节之后（下一个 "## 6." 之前）
        n = len(re.findall(r"^## 6\. ", ann, re.M))
        if n != 1:
            fails.append(u"公告：找不到 §6 的边界（命中 %d 次）" % n)
        else:
            ann = insert_before(ann, u"## 6. ", ANN_SEC, u"公告 §5 小节")
        ann, cnt = re.subn(r"\(398 keys each\)", u"(408 keys each)", ann)
        if cnt != 1:
            fails.append(u"公告：键数串 (398 keys each) 命中 %d 次（要求 1）" % cnt)
        write(ANN, ann)

    # ---- 贴图清单 ----
    plan = read(PLAN)
    if u"oil_pump.png" in plan:
        fails.append(u"贴图清单：oil_pump.png 已经写过了")
    else:
        plan = plan.rstrip(u"\n") + u"\n" + PLAN_SEC
        write(PLAN, plan)

    # ---- 回读核对 ----
    doc2, ann2, plan2 = read(DOC), read(ANN), read(PLAN)
    for p, t in ((DOC, doc2), (ANN, ann2), (PLAN, plan2)):
        if u"\r" in t:
            fails.append(u"%s：出现了 CR（§4.8 要求 LF）" % os.path.basename(p))
    if u"| ZF109 |" not in doc2:
        fails.append(u"§5 表行没写进去")
    if u"ZF109（0.11）" not in doc2:
        fails.append(u"§9 小节没写进去")
    if u"### 4.79 " not in doc2 or u"### 4.80 " not in doc2:
        fails.append(u"§4.79/4.80 没写进去")
    if u"(408 keys each)" not in ann2:
        fails.append(u"公告键数没改到 408")
    if u"oil_pump.png" not in plan2:
        fails.append(u"贴图清单没写进去")
    # 中文里不许出现 ASCII 双引号（只检查新插的段落）
    for name, text in (("§4", SEC4), ("§9", SEC9)):
        for line in text.split(u"\n"):
            if re.search(u"[\u4e00-\u9fff]\"", line) or re.search(u"\"[\u4e00-\u9fff]", line):
                fails.append(u"%s 里有 ASCII 双引号贴着中文：%s" % (name, line[:40]))
    print(u"开发档案：%d 行 → %d 行" % (len(read(DOC).split(u"\n")), len(doc2.split(u"\n"))))
    print(u"英文公告：%d 行 → %d 行" % (len(ann.split(u"\n")) + 1, len(ann2.split(u"\n"))))
    print(u"贴图清单：%d 行 → %d 行" % (len(plan.split(u"\n")), len(plan2.split(u"\n"))))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
