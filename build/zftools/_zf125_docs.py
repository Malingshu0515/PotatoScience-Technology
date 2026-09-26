# -*- coding: utf-8 -*-
u"""_zf125_docs.py —— ZF125 的文档四处（§4 三条新雷 / §5 一行 / §9 一节 / 交接 + 公告 + 贴图清单）

动六份文档，每处都断言锚点**恰好命中 1 次**，写完回读确认：
  ① `docs\\开发档案.md`：§4 三条新雷（§4.102 / §4.103 / §4.104）
  ② `docs\\开发档案.md`：§5 轮的表格加一行 ZF125
  ③ `docs\\开发档案.md`：§9 加一节 ZF125（放在 `## 10. 备份策略` 之前）
  ④ `docs\\多会话协作交接.md`：键数活体数字 464 → 476 + §6 加第 17 条
  ⑤ `docs\\UpdateAnnouncement_EN.md`：键数行 + §4 加一节大型柴油发电机
  ⑥ `docs\\贴图清单.md`：待画表加一行（控制器贴图是程序化占位图）

跑法：
    python build\\zftools\\_zf125_docs.py
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs")
ARCHIVE = os.path.join(DOC, u"开发档案.md")
HANDOVER = os.path.join(DOC, u"多会话协作交接.md")
ANNOUNCE = os.path.join(DOC, u"UpdateAnnouncement_EN.md")
TEXTURES = os.path.join(DOC, u"贴图清单.md")

notes, fails = [], []


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline=u"").write(text)


def patch(name, path, old, new, expect_after=None):
    text = read(path)
    nl = u"\r\n" if u"\r\n" in text else u"\n"
    o, n = old.replace(u"\n", nl), new.replace(u"\n", nl)
    cnt = text.count(o)
    if cnt == 0 and text.count(n) == 1:
        notes.append(u"%s（已经改过了，本次只核对）" % name)
        return
    if cnt != 1:
        fails.append(u"%s：锚点命中 %d 次（要 1 次）—— 停手" % (name, cnt))
        return
    write(path, text.replace(o, n, 1))
    back = read(path)
    if (n not in back) or (expect_after is not None and back.count(expect_after.replace(u"\n", nl)) != 1):
        fails.append(u"%s：回读不认" % name)
        return
    notes.append(u"%s（锚点 1 次命中，回读通过）" % name)


# ============================================================
# ① §4 三条新雷
# ============================================================

LESSONS = u"""
### 4.102 【省了一整个方块族】"某某是后来版本才有的"——**查 jar，别查记忆**（0.11 ZF125）

用户给的柴油发电机图纸第 2 层要 **【铜块】【铜格栅】【铜块】**（还特别注明「铜无论氧化/涂蜡程度都可以」）。
我**凭记忆**认定"铜格栅（copper grate）是 MC 1.21.4 才加的方块"，于是开工前的计划里写着
"新建一个 8 变体的铜格栅方块族"（4 氧化 × 涂蜡：8 个方块 + 8 个物品 + 4 张贴图 + 8 份模型 + 8 份方块状态 +
氧化/打蜡/刮除三套交互 + 配方 + 标签）——**那是这一轮工作量的大头**。

真去查 jar 之后（两条独立证据）：

```
# ① 反编译产物里就有那个类
build\\neoForm\\neoFormJoined1.21.1-20240808.144430\\raw.jar
  → net/minecraft/world/level/block/WeatheringCopperGrateBlock.class
  → Blocks.class 里能搜到字符串 copper_grate / waxed_oxidized_copper_grate …

# ② 客户端 jar 里 8 份方块状态齐全
E:\\PotatoST\\.gradle\\caches\\minecraft\\versions\\1.21.1\\client.jar
  → assets/minecraft/blockstates/{copper,exposed_copper,weathered_copper,oxidized_copper,
     waxed_copper,waxed_exposed_copper,waxed_weathered_copper,waxed_oxidized_copper}_grate.json
  → 15 份 data/minecraft/recipe/*copper_grate*.json、8 份 loot_table、4 张 textures/block/*_grate.png
```

**结论：MC 1.21.1 本来就有 `minecraft:copper_grate`，8 个氧化/涂蜡变体一个不缺** ⇒
这一轮**一个新方块都不用加**，图纸里那 3 格直接认原版方块（`Blocks.COPPER_GRATE` 那 8 个）。

**规矩**：§7 那条「怎么查原版行为，别靠记忆」不只是查**行为**，**查"有没有这个东西"同样适用**。
一个"要不要新建方块族"的判断，代价是几十份资源文件；而验证它只要一条 `Get-ChildItem`（找 jar）
+ 一次 `ZipFile` 列条目。**先花两分钟查，再决定要不要动手。**

### 4.103 【自己咬自己】判据与探针也会写错：注释、末尾逗号、多处插入、写死的期望值（0.11 ZF125）

本轮 `_zf125_verify.py` 第一次跑出来 **6 条红**、探针第一次跑出来 **4 条红**，**十条红里没有一条是机器的问题**，
全是**判据自己写错**。四种形态：

| 形态 | 具体 | 症状 | 正确写法 |
|---|---|---|---|
| 被**注释**咬到 | 源码里 {@code Report#ok()} 的 Javadoc **故意**引用 `holes.isEmpty()` 当反面教材 | `not in t` 那条判据假红 | 只查代码那一句：`re.search(r"return\\s+holes\\.isEmpty\\(\\)", t) is None` |
| 被**末尾逗号**咬到 | `Set.of(A, B, C)` 里**最后一个元素后面没有逗号**（是 `)`） | "铜块 8 个变体"假红 | 判据写 `Blocks\\.%s[,)]`，两种收尾都认 |
| 被**多处插入**咬到 | `StatusLampPart.java` 本轮插了**四处**（导入 / 黄灯 / 后缀 / 注释） | "改前件 = 现状删掉一段连续插入"这条判据假红 | 换成"把每段插入原样抠掉，必须逐字节回到改前件" |
| **期望值写死** | 探针里写"红石停机后柴油应剩 100 mB"，可上一段跑完本来就是 99 | 探针假红（机器行为完全正确） | 期望值必须由**当场记录的初值**推出来（`int before = ...`），不许写死整数 |

**规矩**：红了一条，先问"是**被测的东西**错了，还是**我的判据/期望**错了"。
后者的共同特征是：**把上下文（注释、分隔符、前一段留下的状态）当成了不变量**。
本轮这四条已经全部修掉，收尾是全绿（判据 92 项、探针 50 项）。

### 4.104 【拼接式补丁】新内容必须包含锚点、多行拼接要自己补分隔符（0.11 ZF125）

同一个"拼接"的病，本轮犯了两次（都被编译/解析当场抓住，没有流到成品里）：

1. **`apply(old, new)` 里 `new` 忘了把 `old` 接回去** —— `_zf125_java.py` 的 A 处写成
   `apply(..., A_ANCHOR, A_NEW)`，而 `A_NEW` 只写了新增段 ⇒ 锚点那一行
   （`LITHIUM_BATTERY_PLANT.get()).build(null));`）被**整行吃掉**，
   编译在 `ModBlocks.java:1012` 报「非法的表达式开始」。
   （B/C/D/E 四处写的是 `NEW = ANCHOR + 新内容`，没这个毛病 —— **同一个脚本里两种写法并存**，
   正是它没被一眼看出的原因。）修法是 `_zf125_fixA.py`：补回那一行，并**逐字节**证明
   "与改前件的差异只剩新增段"。
2. **多行拼接忘了补逗号** —— `_zf125_lang.py` 第一版把 11 个新键直接 `"\\n".join(...)`，
   只有第一条前面那行补了逗号 ⇒ 第一份 `zh_cn.json` 当场 `JSONDecodeError:
   Expecting ',' delimiter: line 467`（**四份里改到第一份就炸**，没有留下坏文件）。

**规矩**：凡是"读进来 → 拼一段 → 写回去"的脚本，两件事必须有：
① **锚点与新增段成对**（要么 `old+new`，要么对 `old` 单独断言"还在"）；
② 写完**回读**（JSON 要 `json.loads`、源码要编译、lang 要四份键集合比对）。
本轮两个脚本都补上了这两条（`apply()` 里回读、`_zf125_lang.py` 里 `json.loads` + 四份比对）。

"""

# ============================================================
# ② §5 一行
# ============================================================

ROW_ANCHOR = (u"⚠ 本轮**没有探针**（改的是 lang 的值 + 客户端标签页图标，无头服务端只能验到 lang 与源码）| 见 §9 |\n")

ROW_NEW = ROW_ANCHOR + (
    u"| ZF125 | **新建 `zf125_pre`**（**117 份**改前件：6 个既有 Java（`ModBlocks` / `ModItems` / "
    u"`ModMenus` / `PotatoST` / `PotatoSTClient` / `StatusLampPart`）+ 四份 lang + 两张挖掘标签 + "
    u"`_zf100~_zf103_verify` + 全部常驻校验脚本 + 4 份文档 + 旧成品 jar 与 `.sha1`；逐份核哈希 + "
    u"**回读证明** + **「21 条新增件动手前一条都不存在」**，失败 0） | 0.11：**大型柴油发电机（3×5×2 多方块）**。"
    u"用户原话（一条消息给全图纸与功能）：「加一个大型柴油发电机 3x5x2 …（30 格图纸）以柴油发电机控制器为正方向 "
    u"右键打开GUI 显示流体储罐（8000mB）工作指示灯 检测到红石信号停机 可以用流体泵泵入柴油 "
    u"或用柴油桶/含有柴油的油桶右键添加柴油 每t消耗1mb柴油 7.2kFE 柴油发电机控制器配方;"
    u"【】【流体管道】【】，【铜块】【熔炉】【铜块】，【】【钢板】【】」。"
    u"① **⚠ 差点白造一整个方块族**：我**凭记忆**以为「铜格栅是 1.21.4 才有的」，计划里已经排上"
    u"「8 变体铜格栅方块族」；查 jar 才发现 **MC 1.21.1 本来就有 `minecraft:copper_grate`（8 个氧化/涂蜡变体齐全）**"
    u"⇒ 本轮**一个新方块都没加**（立为 §4.102）；② **30 格逐格硬判**（口径同分馏塔；用户把每一格都写清楚了，"
    u"放宽成「是机器方块就算」反而会让他搭错也能成型）；唯一的放宽是**铜的 16 格随便搭**（铜块 8 变体 + 铜格栅 8 变体）"
    u"+ 三台机器方块只看种类不看朝向；**十行图纸全是回文** ⇒ 左右镜像不会搭错（合金炉当年就栽在镜像上）；"
    u"③ **电只从接线口出**：控制器正上方那一格【接线块】成型时换成 `diesel_generator_port`"
    u"（贴图与接线块**完全一样**、挖掉掉回接线块、未成型/没主控时能力返回 null），控制器本体**不**登记能量能力 —— "
    u"沿用电力高炉/合金炉那条「原来接线块的地方传电」；④ **里面那四台机器一个字节都不动**"
    u"（流体泵 ×1 / 低级发电机 ×2 / 燃烧反应室 ×1）：用户没说「吸收」，本轮**不发明**这条规则；"
    u"探针专门验了它们成型后仍是自己的方块与方块实体（不是「不渲染的部件格」——本机**没有 OBJ**，"
    u"换成部件格会在机器上破出洞来）；⑤ **界面**：一个 8000 mB 柴油罐 + 一盏工作指示灯"
    u"（用户点名「只有」这两样 ⇒ 故意没有能量条/进度条）；**状态码新起 19 = 结构不完整**（6~18 全被占了）；"
    u"⑥ **倒柴油两条路**：原版柴油桶（整桶 1000，塞不下就**一滴不倒**，倒空还一个空铁桶）+ "
    u"油桶/高压气罐（只认柴油，按罐里余量倒）；⑦ **两处自定的默认**（用户没给，已挂 §9）："
    u"**内部缓冲 = 1 tick 的产量 7200 FE**（一满就暂停烧油，不浪费柴油，与低级发电机同一条先例）、"
    u"**结构不完整照开界面但停机**（用户说的是「右键打开GUI」，没像合金炉那样要求先激活）；"
    u"⑧ **探针 50 项全绿**：照图纸搭 30 格自动成型（铜块/铜格栅**八种变体混着搭**）/ 接线口换进换出 / "
    u"缺一格 `holeCount` 精确报 1 处 / **200 tick 正好 1,440,000 FE 与 200 mB 柴油** / 缓冲满不烧油 / "
    u"红石停机 / 倒油四种结果 / 配方与 `potato_s_t:copper_blocks`（8 项）真的加载；"
    u"⚠ **探针第一版 4 条判据自己写错**（期望值算错）⇒ 机器行为全对，改判据后重跑（立为 §4.103）；"
    u"⑨ 往轮判据 retarget：`_zf100/_zf101/_zf102/_zf103_verify.py` 的键数 **464 → 476**；"
    u"⑩ 证据：`_zf125_verify.py` **92 项**、反证 **K187~K198 十二把刀**（逐把咬中指定检查）、四语言 **464 → 476 键** | 见 §9 |\n")


# ============================================================
# ③ §9 一节
# ============================================================

SECTION = u"""### ZF125（0.11）：大型柴油发电机（3×5×2 多方块） —— **已完成**

用户原话（**一条消息给全图纸与功能**）：

> 加一个大型柴油发电机 3x5x2 第一层【耐热金属块】【流体泵】【耐热金属块】，【耐热金属块】【低级发电机】
> 【耐热金属块】，【耐热金属块】【燃烧反应室】【耐热金属块】，【耐热金属块】【低级发电机】【耐热金属块】，
> 【耐热金属块】【柴油发电机控制器】【耐热金属块】第二层 【一般金属块】【耐热金属块】【一般金属块】，
> 【铜块】【铜格栅】【铜块】，【铜块】【铜格栅】【铜块】，【铜块】【铜格栅】【铜块】，
> 【一般金属块】【接线块】【一般金属块】（铜无论氧化/涂蜡程度都可以）以柴油发电机控制器为正方向
> 右键打开GUI 显示流体储罐（8000mB）工作指示灯 检测到红石信号停机 可以用流体泵泵入柴油
> 或用柴油桶/含有柴油的油桶右键添加柴油 每t消耗1mb柴油 7.2kFE
> 柴油发电机控制器配方;【】【流体管道】【】，【铜块】【熔炉】【铜块】，【】【钢板】【】

#### 一、做了什么

| # | 东西 | 落点 |
|---|---|---|
| ① | **30 格结构**（3 宽 × 5 深 × 2 层，**一格都不许少**） | 新 `DieselGeneratorStructure.java`；`inspect` 逐格硬判 + 报缺口的层/排/列/该放什么/现在是什么/坐标 |
| ② | **控制器**（有朝向 = 机器正面） | 新 `DieselGeneratorBlock` / `DieselGeneratorBlockEntity`（罐 8000 mB、每 tick 1 mB 柴油 → 7200 FE） |
| ③ | **出电口** | 新 `DieselGeneratorPortBlock` / `…BlockEntity`：成型时把控制器正上方那格【接线块】换成它，**只出不进**，未成型返回 null |
| ④ | **界面** | 新 `DieselGeneratorMenu` / `client\\DieselGeneratorScreen`：**一个 8000 mB 柴油罐 + 一盏工作指示灯**（用户点名只有这两样） |
| ⑤ | **倒柴油** | `DieselGeneratorBlock.pourFrom`（纯逻辑，探针直接调）：原版柴油桶 + 油桶/高压气罐两条路 |
| ⑥ | **状态码 19** | `StatusLampPart` 加 19 = 结构不完整 → 黄灯 + `no_structure`（6~18 全被占了） |
| ⑦ | **四语言 12 键** | `block` / `tooltip`（30 格摆放图）/ 5 个 `status` / `invalid`（8 个 %s）/ 3 个 `pour` ⇒ **464 → 476** |

**三处我替用户定的默认**（都写在类注释里，改起来是一行的事）：

1. **内部缓冲 = 1 tick 的产量（7200 FE）**：用户没给这个数。取 1 tick 的产量 ⇒ 缓冲一满就**暂停烧柴油**
   （`hasRoom()`，与低级发电机 ZF38「没地方存就暂停燃烧」同一条先例），既不浪费玩家的柴油，
   也不需要发明一个界面外的巨大数字。
2. **结构不完整照开界面、但停机**：用户原话是「右键打开GUI」，**没有**像合金炉那样说「先激活」⇒
   按字面来：界面照开，缺哪几格打在聊天栏（前 4 处），界面里那盏灯是 19 = 结构不完整。
3. **电只从接线口出**：控制器本体**不**登记能量能力 —— 沿用电力高炉「原来接线块的地方传电」与
   合金炉接线口那条老规矩。柴油则**控制器与接线口都收**（玩家把泵放正面或放机器顶上都能喂它）。

#### 二、⚠ 差点白造一整个方块族：铜格栅本来就有（新雷 §4.102）

用户图纸第 2 层要【铜块】【铜格栅】【铜块】。我**凭记忆**认定「copper grate 是 1.21.4 才加的方块」，
开工计划里已经排上「新建 8 变体铜格栅方块族」（8 方块 + 8 物品 + 4 贴图 + 8 模型 + 8 方块状态 +
氧化/打蜡/刮除三套交互 + 配方 + 标签）。**查了 jar** 才知道 1.21.1 本来就有：

```
build\\neoForm\\…\\raw.jar → WeatheringCopperGrateBlock.class、Blocks.class 里 copper_grate 字符串
.gradle\\caches\\minecraft\\versions\\1.21.1\\client.jar → 8 份 *_copper_grate.json + 8 份 loot_table + 4 张贴图
```

⇒ **本轮一个新方块都没加**：结构里那 3 格直接认原版 `Blocks.COPPER_GRATE` 那 8 个变体。
用户那句「（铜无论氧化/涂蜡程度都可以）」于是**原样成立**：铜块 8 变体 + 铜格栅 8 变体，
结构里 16 格全收（探针专门**混着搭**验过：6 格铜块用 6 种、3 格铜格栅用 3 种，一样成型）。

#### 三、连带改的四处（都是"被本轮的改动作废的判据"，不是放宽）

| 门 | 为什么 | 怎么改的 |
|---|---|---|
| `_zf100_verify.py` | `EXPECT_KEYS = 464` 是**活体数字** | → **476**（注释里点明 +12 键的来源） |
| `_zf101_verify.py` | 同上 | → **476** |
| `_zf102_verify.py` | 同上 | → **476** |
| `_zf103_verify.py` | 键数断言与**文案里的那个数**是两处 | 两处一起 → **476** |

⚠ 交接文档里写着"加一个语言键要改 **17 份**校验器" —— 那是 ZF117 那轮的实测名单；
本轮**只有这 4 份**把键数写成了字面量（其余的门是从四份互相比较得出，不写死数字），
所以**没有**去动那 17 份里的其它脚本（改没坏的门 = 放宽，本轮不做）。

#### 四、证据

| 项 | 值 |
|---|---|
| 探针 | 真服务端 `Zf125Check`：**50 项全绿**（照图纸搭 30 格自动成型 / 接线口换进换出 / 缺一格 `holeCount` 精确 1 处 / **200 tick = 1,440,000 FE 与 200 mB 柴油** / 缓冲满不烧油 / 红石停机 / 罐空停机 / 倒油四种结果 / 配方 3×3 与铜块标签 8 项真的加载）。⚠ 第一版 4 条判据**自己写错**（期望值算错）⇒ 改判据后重跑，见 §4.103 |
| 常驻校验 | `_zf125_verify.py` **92 项**：图纸逐字 / 九种映射 / 铜 8+8 变体 / `holeCount` 判据 / 8000·1·7200 / 五档状态 / 红石 / 倒油两条路 / 接线口未成型不给电 / 控制器本体不登记能量 / 六个既有文件"只动了该动的地方"（**改前件 = 现状删掉那一段插入**，逐字节）/ 资源与数据 / 四语言 476 键 |
| 反证刀 | **K187~K198 十二把**（逐把咬中指定检查）：罐容量 8000→8001 / 发电 7200→7201 / 删掉一个铜变体 / 接线块不认接线口 / 给控制器本体也登记能量 / 接线口不看成型 / 配方中排改掉 / zh_cn 少一个 %s / 方块状态少一个朝向 / 创造页那行删掉（§4.82 老坑）/ 往轮门写回 464 / 判定改回 `holes.isEmpty()`（§4.56 老坑） |
| 活体数字 | 四语言 **464 → 476** 键；配方 **60 → 61 份**（`crafting_shaped` 54 → **55**）；本模组方块 **+2**（控制器 + 接线口，接线口**没有物品形态**）；语言键数耦合的门只动了 **4 份** |
| 要你实测 | ① 控制器**右键**应当直接开界面（一个柴油罐 + 一盏灯）；② 拿**柴油桶**右键控制器能倒进 1000 mB、桶变空桶；③ 罐里有油、结构与红石都对时，**接线口旁边贴一个输入端子**才收得到电（7.2kFE/t 远超单个端子的 2048 上限，多贴几个或接铜线网）；④ 挖掉任意一格结构，界面里的灯应当变**黄**并显示「结构不完整」，聊天栏报出缺的那一格 |

**成品**：本轮**没有新成品** —— 见 §9 的成品账（`release\\` 由打包轮统一发布，本轮的 §4.92 老坑仍在：`.sha1` 里写着 `哈希  文件名` 两段，十道门只认纯哈希一行）。

"""

ANCHOR7 = u"## 7. 权威情报来源（怎么查原版行为，别靠记忆）\n"
ANCHOR10 = u"## 10. 备份策略\n"


# ============================================================
# ④ 交接文档
# ============================================================

KEYS_OLD = u"→ **464**（ZF122 星仪图之章 +10）。⚠ **ZF121 / ZF123 / ZF124 一个键都没加没删**（改的都是值）"
KEYS_NEW = (u"→ **464**（ZF122 星仪图之章 +10）→ **476**（ZF125 大型柴油发电机 +12）。"
            u"⚠ **ZF121 / ZF123 / ZF124 一个键都没加没删**（改的都是值）；"
            u"⚠ **ZF125 只动了 4 份写死键数的门**（`_zf100~_zf103_verify`），"
            u"下面那条「17 份」是 ZF117 的实测名单、不是每次都全动")

ITEM16_ANCHOR = (u"英文公告的**成就树**改了、**ZF107 那条 changelog 历史没动**；④ 本轮没有探针（改的是\n"
                 u"    lang 的值 + 客户端图标），证据是 31 项常驻校验 + 4 把反证刀。\n")

ITEM17 = ITEM16_ANCHOR + u"""
17. **ZF125 的账**：① **大型柴油发电机（3×5×2）已上线**：控制器 `diesel_generator_controller`
    + 接线口 `diesel_generator_port`（成型时替换控制器正上方那格接线块，**没有物品形态**，
    挖它掉一个接线块）；② **⚠ 铜格栅不用自己做** —— MC 1.21.1 本来就有 `minecraft:copper_grate`
    8 个氧化/涂蜡变体（§4.102 记了据以判断的两条 jar 证据）；③ **里面那四台机器不会被吃掉**
    （本轮明确**不做**"吸收成部件格"：本机没有 OBJ 模型，换成不渲染的部件格会在机器上破洞）；
    ④ **两处自定默认挂着待确认**：内部缓冲 = 1 tick 的产量 7200 FE（满则暂停烧油）、
    结构不完整照开界面但停机（灯是 19）；⑤ **状态码 19 = 结构不完整**是新号，
    以后哪台机器要用 19 先看语义能不能共用（§4.51 那条规矩）；⑥ 语言键 **464 → 476**
    ⇒ 只 retarget 了 `_zf100/_zf101/_zf102/_zf103_verify.py` 四份（其余的门不写死数字）；
    ⑦ 证据：探针 **50 项全绿** + `_zf125_verify.py` **92 项** + 反证 **K187~K198 十二把**。
"""


# ============================================================
# ⑤ 英文公告
# ============================================================

ANN_KEYS_OLD = u"- **4 languages:** English, 中文, 日本語, Русский (464 keys each)"
ANN_KEYS_NEW = u"- **4 languages:** English, 中文, 日本語, Русский (476 keys each)"

ANN_SECTION = u"""### Large Diesel Generator (new in 0.11 ZF125)
A 3x5x2 multiblock built out of blocks you already have. Layer 1 (bottom), middle column, back to
front: fluid pump, low generator, combustion chamber, low generator, **diesel generator controller**;
both side columns are heat-resistant metal blocks. Layer 2: common metal blocks on the back and front
rows, copper blocks flanking copper grates in the three middle rows, and a **wiring block** directly
above the controller (**any oxidation or waxed state of copper works - all 16 variants**).

- Right-click the controller: an 8000 mB diesel tank plus a status lamp. 1 mB of diesel per tick
  makes **7200 FE**; a redstone signal stops it (the fuel stays in the tank).
- Power leaves only through the port that the wiring block turns into once the structure is complete
  (same texture, drops a wiring block). The controller itself has no energy capability.
- Diesel goes in by pump (controller **or** the port, any side) or by right-clicking the controller
  with a diesel bucket or an oil bucket holding diesel. Diesel only - water is rejected.
- The four machines inside are **not** consumed: the pump, both low generators and the combustion
  chamber stay yours and keep working.
- Crafting the controller: fluid pipe on top, copper block - furnace - copper block in the middle,
  steel plate at the bottom (the copper may be any oxidation/waxed variant).

"""

ANN5_ANCHOR = u"## 5. Ores, materials and fluids\n"


# ============================================================
# ⑥ 贴图清单
# ============================================================

TEX_COUNT_OLD = u"## 待画（13 个，现在借的是原版贴图）"
TEX_COUNT_NEW = u"## 待画（14 个，现在借的是原版贴图）"

TEX_ROW_ANCHOR = (u"| `textures/block/` | `test_fluid_tank.png` | 测试流体储罐 | "
                  u"`minecraft:block/glass`, `minecraft:block/iron_block` |\n")
TEX_ROW_NEW = TEX_ROW_ANCHOR + (
    u"| `textures/block/` | `diesel_generator_controller.png` | 柴油发电机控制器 | "
    u"**程序化占位图**（`_zf125_assets.py` 画的 16×16：金属面板 + 四角铆钉 + 中间一扇能看到柴油液位的观察窗）"
    u"—— ⚠ 这一行是**手工**加的：`TextureCheck.py --plan` 只列「文件不存在」的贴图，而这张**存在** |\n")


def main():
    patch(u"① §4 三条新雷（§4.102~§4.104）", ARCHIVE, ANCHOR7, LESSONS + u"\n" + ANCHOR7)
    patch(u"② §5 加 ZF125 一行", ARCHIVE, ROW_ANCHOR, ROW_NEW)
    patch(u"③ §9 加 ZF125 一节", ARCHIVE, ANCHOR10, SECTION + ANCHOR10)
    patch(u"④a 交接文档键数 464 → 476", HANDOVER, KEYS_OLD, KEYS_NEW)
    patch(u"④b 交接文档加第 17 条", HANDOVER, ITEM16_ANCHOR, ITEM17)
    patch(u"⑤a 英文公告键数 464 → 476", ANNOUNCE, ANN_KEYS_OLD, ANN_KEYS_NEW)
    patch(u"⑤b 英文公告加大型柴油发电机一节", ANNOUNCE, ANN5_ANCHOR, ANN_SECTION + ANN5_ANCHOR)
    patch(u"⑥a 贴图清单待画 13 → 14", TEXTURES, TEX_COUNT_OLD, TEX_COUNT_NEW)
    patch(u"⑥b 贴图清单加一行", TEXTURES, TEX_ROW_ANCHOR, TEX_ROW_NEW)
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改动 %d 处" % len(notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
