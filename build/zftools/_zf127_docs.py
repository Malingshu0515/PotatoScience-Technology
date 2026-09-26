# -*- coding: utf-8 -*-
u"""_zf127_docs.py —— ZF127 的文档三件套（档案 / 交接 / 英文公告）

落点（都按**锚点**插，不整份覆盖）：
  ① `docs\\开发档案.md` §4：4.105 分档公式把最低档顶高 / 4.106 负向对照要指明反对照哪一条 /
     4.107 探针调 protected 的 useItemOn / 4.108 挂载与卸载必须对称；
  ② 同文件 §5：ZF127 那一行（插在 ZF126 行之后）；
  ③ 同文件 §9：ZF127 小节（插在 `## 10. 备份策略` 之前）；
  ④ `docs\\多会话协作交接.md`：§1 的活体数字（键数 478 / 配方 68 份）与 §6 第 19 条；
  ⑤ `docs\\UpdateAnnouncement_EN.md`：§1 动力网络表里加银线两行 + 一段说明。

⚠ 所有中文串一律用「」，不许 ASCII 引号（§4.24 族）；脚本自己做幂等检查（跑第二遍不会重复插）。

跑法：
    python build\\zftools\\_zf127_docs.py
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


LESSONS = u'''### 4.105 【分档公式】`max(旧值, 新档 × 2)` 会把**最低档**一起顶高（0.11 ZF127，探针一次抓出 6 条红）

给端子加"银线档"时，容量第一版写成 `Math.max(MAX_ENERGY, lineRate * 2)` —— 看着对称，
**代进铜线档就错了**：`max(2048, 2048×2) = 4096` ⇒ 纯铜端子的缓冲从 2048 变 4096、
一 tick 从 1024 变 2048 —— 一处**静默改掉了既有内容的行为**（用户只要求加银线）。
真服务端探针一次抓出 6 条红（`capacityFor(2048)` / 铜线容量 / 铜线一 tick 1024 /
拆线后缩回 2048 / 老存档夹电量 / 银线那对的对照值），改一处公式**全绿**。

**规矩**：凡是"分档 / 按类型取值"的公式，**先把最低档代进去算一遍**，
并且判据里必须有**一条**断言"最低档 == 改动前"。
正确写法是分档而不是取大：`lineRate <= TRANSFER_RATE ? MAX_ENERGY : lineRate * 2`。

### 4.106 【自己咬自己·续】探针里的"负向对照"必须点明**反对照的是哪一条**（0.11 ZF127）

本轮三处判据/探针的期望写错，全是"我以为是 A，其实是 B"（§4.30 家族的第三次成批出现）：

| 症状 | 真相 |
|---|---|
| 断言"8 根**铜线**围空线轴 ⇒ 不匹配任何配方" ⇒ 假 FAIL | 那个摆法**本来就**能出**铜线轴**（另一条正当配方）⇒ 应断言"做出来的是铜线轴、不是银线轴" |
| 断言"线轴用完手里那格是空的" ⇒ 假 FAIL | 破损回调先把空线轴塞回背包，而**刚空出来的那一格就是第一个空位** ⇒ 手里拿着的正是那个空线轴（原版行为，不是 bug） |
| 断言"铜线那根一 tick 传 1024" ⇒ 得 0 | 那头的端子是新建的、**我忘了给它灌电**；而且它在 `NONE` 模式，`receiveEnergy` 恒 0 |

**规矩**：写"反向对照"之前先把**正向**那条摆出来问一句"它到底会走到哪去"；
探针里每个期望值都要能说出"这个数是**哪条规则**算出来的"。

### 4.107 【探针雷】`BlockBehaviour.useItemOn` 是 protected：跨包探针调不动，改走 `gameMode`（0.11 ZF127）

想在探针里"模拟玩家右键方块"，第一版直接写 `ModBlocks.TERMINAL.get().useItemOn(...)` ⇒
**编译期就被挡**：那个方法声明在 `net.minecraft.world.level.block.state.BlockBehaviour`，
探针与它不同包、也不是它的子类（Java 的 protected 规则：跨包访问必须在子类里、
而且接收者得是子类类型）。

正路是 `ServerPlayerGameMode.useItemOn(player, level, stack, hand, hit)` ——
**玩家右键真正走的那条路**，反而更真（还顺带过了 reach 与"方块是否启用"那几道闸门）。
两个配套细节：① 用 `FakePlayerFactory.get(level, new GameProfile(uuid, name))` 造人；
② **必须 `setGameMode(GameType.SURVIVAL)`** —— 创造模式 `hurtAndBreak` 第一行就 `return`，
耐久类断言会变成假绿（或假红）。

### 4.108 【挂载/卸载不对称】挂探针时吃掉一个空行，卸载时就要还回来（0.11 ZF127）

`_zf127_mount.py` 把钩子插在监听行后面时**顺手吃掉了那个空行**，而 `_zf127_unprobe.py`
只按"删掉『空行 + 钩子』"的写法摘 ⇒ 摘完比改前件**少一个空行**，
`PotatoST.java` 与 `zf127_pre` 的 sha1 对不上 —— 这正是那条"逐字节证明"抓出来的（不是空跑）。

**规矩**：挂载脚本与卸载脚本要么**严格互逆**，要么卸载时**以改前件为权威**：
先 `diff` 确认"只差这一点"，再从改前件覆盖，并把差异如实写进说明。
（本轮就是这么收的：`diff` 只有那一行空行 ⇒ 覆盖 ⇒ sha1 `2e6bf0855f256d98` 一致。）

'''

ROW = u'''| ZF127 | **新建 `zf127_pre`**（**302 份**改前件：4 份要改的 Java + **`PotatoST.java`（探针挂载点 —— 前三次都漏，这次一开始就写进清单）** + 四份 lang + 配方生成器表 + 全部 `_zf*_verify/_falsify/_guard/_repro/_audit` + 整个 `recipe\\` 与 `models\\item\\` 目录 + 4 份文档 + 旧成品与 `.sha1`；逐份核哈希 + 回读证明 302/302 全过。⚠ **我自己的 slip**：点名件清单里把 `client\\TerminalRenderer.java` 写漏了一层目录 ⇒ 脚本报 1 条"点名件没抄到"，**文件其实抄到了**（逐字节核过，见 §9 那张表）） | 0.11：**银线 / 银线轴**。用户原话：「加一个银线轴 和铜线轴一致（先搞银线 配方什么的都一致只不过铜的换成银的） 材质先不画 连接线缆还是一样的像素大小 只不过变成银白色的 传输速率 16134Fe/t」。① 两个物品：`silver_wire`（2 个银锭 → 4 根）+ `silver_wire_spool`（8 根银线围 1 个空线轴 → 1 个；**耐久 32**、右键连线、耗尽返还空线轴、连接距离 16 格 —— 与铜线轴**逐项一致**）；② **单线速率 16134 FE/t**，与铜线（2048）在**同一条 FE 网络**上：连接改成"对端 → 这条线自己的速率"（`Map<BlockPos,Integer>`，NBT 两种格式都认），端子能力按**接到的最高档**伸缩（铜线档 2048 **一个字节没变**、银线档 32268 = 2×16134）；③ 线缆渲染成**银白色**，**线径 `WIRE_RADIUS` 一个字节没改**（用户点名"像素大小一样"）；④ **材质先不画**：两个模型借原版贴图占位 ⇒ 待画清单 **13 → 15**（这条链四处一起跟平）；⑤ 顺手修掉 `_zf71_verify.py` 缺的 §4.81 UTF-8 stdout 钉子；⑥ 证据：真服务端探针 **45 项全绿** + `_zf127_verify.py` **%d 项** + 反证 **K205~K222 十八把刀** | 见 §4.105 ~ §4.108 / §9 |
'''

SECTION = u'''### ZF127（0.11）：银线 / 银线轴（同一条 FE 网络上的**高速档**）—— **待你实测**

用户原话：

> 加一个银线轴 和铜线轴一致（先搞银线 配方什么的都一致只不过铜的换成银的） 材质先不画 连接线缆还是一样的像素大小 只不过变成银白色的 传输速率 16134Fe/t

#### 一、做了什么

| # | 东西 | 落点 |
|---|---|---|
| ① | **银线 `silver_wire`** | 2 个银锭（`#c:ingots/silver`）→ 4 根 —— 与铜线那张图纸**逐字对应**，只把铜换成银 |
| ② | **银线轴 `silver_wire_spool`** | 8 根银线围 1 个空线轴 → 1 个；**耐久 32**、右键连线、耗尽返还空线轴、连接距离 **16 格** —— 与铜线轴逐项一致 |
| ③ | **单线速率 16134 FE/t** | `TerminalBlockEntity.SILVER_TRANSFER_RATE = 16_134`（铜线仍是 `TRANSFER_RATE = 2048`） |
| ④ | **线缆变成银白色** | `TerminalRenderer` 多一组银色常量，**按每条线自己的速率上色**；**线径 `WIRE_RADIUS` 一个字节没改** |
| ⑤ | **材质先不画** | 两个模型借原版贴图占位（铁粒 / 铁锭）⇒ `贴图清单.md` 待画 **13 → 15** |

#### 二、那个 16134 是怎么"真的跑起来"的（设计口径 —— 我定的，要改都是一处）

铜线跟银线在**同一条 FE 网络**上（同一个连接集合、同一套输入/输出模式），
**每条连接线各自记着自己的速率**（`Map<对端, 速率>`），端子的**能力**按它接到的**最高档**伸缩：

| 端子接的线 | 缓冲上限 | 单次收/放 | 一 tick 实际能传多少（"差额一半"规则） |
|---|---|---|---|
| 只有铜线 | **2048**（一个字没改） | 2048 | **1024**（= ZF126 之前的行为，探针实测回归） |
| 接了银线 | **32268** = 2 × 16134 | 16134 | **16134**（上游把端子补满时，探针连跑 3 tick 都是这个数） |

- 为什么缓冲要 **2 × 速率**：均衡规则是"移动差额的一半"，要把 rate 传满，两端电量差得有 2 × rate；
- ⚠ **上游供不上时按差额一半降档**（端子只有 16134 时一 tick 只传 8067）—— 规则本身，探针里如实记了一条；
- **混着接**：银线段跑 16134、铜线段跑 2048（探针在**同一个对端**上同 tick 对照过：16134 / 1024）；
- 拿银线轴在**已经连好的铜线**上再连一次 = **就地升级**成银线（扣 1 点耐久）；拿铜线轴连银线**不会降级**；
- 银线拆掉 ⇒ 缓冲缩回 2048，多出来的电**夹掉**（不做"隔空搬运"）；
- **老存档照读**：读盘认两种格式（新的 `CompoundTag{pos,rate}` 与老的 `ListTag<LongTag>`），
  老存档里的线按铜线 2048 算，不会掉线。

#### 三、证据

| 项 | 值 |
|---|---|
| 探针 | 真服务端 `Zf127Check`：**45 项全绿** —— 常量 16134 / 铜线三档没被改 / `capacityFor(2048) == 2048` / 两条配方在真 `RecipeManager` 里摆得出来（含"少一块料"与"拿铜线冒充"两条反向对照）/ **FakePlayer 拿真银线轴右键两次**连成线（两端都记 16134、耐久 −1、耗尽返还空线轴）/ **一 tick 真传 16134**（铜线那对同条件 1024，回归）/ 连跑 3 tick 都是 16134 / 上游供不上时按差额一半 8067 / 铜线就地升级成银线且不降级 / 拆线后容量缩回并夹电量 / 新格式往返 + **老格式照读** |
| 常驻校验 | `_zf127_verify.py` **%d 项**：物品与注册 / 端子网络（速率·分档容量·每线速率·NBT 两格式）/ 接线与渲染（**线径那一行与改前件逐字节相同**）/ 资源（两条配方与铜线**除材料外结构相同**、且与生成器表逐字节一致、**不许有自己的 png**）/ 四语言 478 键且老键值逐字未变 / 活体数字与门跟平 / 文档 / 反向 |
| 反证刀 | **K205~K222 十八把**：速率 / 容量公式（**探针抓到的真 bug**）/ 耐久 / 创造页 / 银白色 / 线径 / 分支速率 / 老格式兜底 / 存盘 rate / 夹电量 / 中文名 / 只加一份语言 / 配方材料 / 手改 JSON / 补一张 png / 往轮门 / 待画链 / 公告键数 —— 逐把咬中指定检查 |
| 探针抓到的真 bug（如实记） | 容量第一版 `Math.max(MAX_ENERGY, rate*2)` 把**铜线档**也顶成 4096（一 tick 从 1024 变 2048）⇒ 6 条红；改成 `lineRate <= TRANSFER_RATE ? MAX_ENERGY : lineRate * 2` 后全绿（§4.105） |
| 我自己写错的判据（如实记） | ① 反例"8 根铜线围空线轴不匹配任何配方"（其实能出铜线轴）；② "线轴用完手里是空的"（空线轴会被塞回刚空出的那一格）；③ "铜线那根一 tick 1024"（忘了给那头的端子灌电）—— 三条都是**期望写错**，机器没错（§4.106） |
| 活体数字 | 四语言 **476 → 478** 键（27 份常驻门 retarget）；配方 **66 → 68 份**（`crafting_shaped` 56 → **58**）；表 `_zf45_recipes.py` 定形 **34** 条 + 锻造台 4 条；待画贴图 **13 → 15**（四处一起改） |
| 挂载点（第四次终于没漏） | `PotatoST.java` **一开始就在改前件清单里**；⚠ 但挂载脚本吃掉了它前面那个空行、卸载脚本没还 ⇒ sha1 对不上 ⇒ 按"改前件是权威"覆盖回来（§4.108） |

**成品**：本轮**没有新成品**（`release\\` 一个字没动）。

#### 四、要你实测

1. 进创造页看**银线**与**银线轴**（名字是中文的、图标是**占位**：铁粒 / 铁锭）；
2. 拿银线轴右键两个端子（距离 ≤ 16 格）——**线应该是银白色**、粗细和铜线一模一样；
   铜线轴连的线仍应是古铜色；
3. 把柴油发电机（7.2kFE/t）接到一个银线端子上：挨着接线口放**一个**输入端子就够吃了
   （铜线时代要贴好几个 —— 单线一 tick 只走 1024，银线能走 16134）；
4. 已经连好的**铜线**上再用银线轴连一次 = 就地升级；用铜线轴再连**不会**降级；
5. 挖掉一端 ⇒ 另一端的缓冲缩回 2048（界面/悬浮框能看到）。

#### 五、我定的默认（用户没说的，都挂在这儿，改都是一处）

1. **银线进的是同一条 FE 网络**（不是另开一套）：所以铜线银线可以混着接、模式（输入/输出）也是同一个 —— 这是"和铜线轴一致"的字面读法；要改成"两套独立网络"是另一件事（数据模型要动）；
2. **端子的能力跟着最高档线缆走**（缓冲 32268 / 单次 16134）—— 不这么做的话 16134 这个数**永远跑不满**（会卡在 `MAX_ENERGY ÷ 2 = 1024`），用户给的数就白给了；
3. **拿铜线轴连银线不降级**（`rate` 只升不降）；
4. **拆线后多出来的电夹掉**（不返还、不掉落）；
5. 银线的**贴图还没画**（用户点名）—— 借的是原版铁粒 / 铁锭，画好之后换 `models/item/silver_wire*.json` 的 `layer0` 两行即可。

'''

ANN_BLOCK = u'''> ⚡ **New in 0.11 ZF127 — the Silver Wire.** The same FE network now has **two cable tiers**:
> the **Copper Wire Spool** (2,048 FE/t per link, unchanged) and the **Silver Wire Spool**
> (**16,134 FE/t per link**). Craft it exactly like the copper one with silver instead of copper
> (2 silver ingots → 4 silver wires; 8 silver wires around an empty spool → 1 spool); it has the same
> 32 uses, the same 16-block link distance and the same "breaks into an empty spool" behaviour.
> The cable is drawn **silver-white** and is **exactly as thick as the copper one** (same 1-pixel
> radius). A terminal wired with silver gets a **32,268 FE buffer** (2 × the line rate, so a full
> line can actually move 16,134 FE in one tick); terminals wired only with copper behave exactly as
> before. Copper and silver links can be mixed on the same terminal — each link runs at its own rate.
> Textures for the two new items are **not drawn yet** (as requested): they borrow the vanilla iron
> nugget / iron ingot sprites for now.

'''

HANDOVER_ITEM = u'''19. **ZF127 的账**：① **银线 / 银线轴**上线（`silver_wire` / `silver_wire_spool`，单线
    **16134 FE/t**，铜线仍 2048）；两者在**同一条 FE 网络**上，连接改成"对端 → 这条线自己的速率"，
    端子能力按**接到的最高档**伸缩 —— **纯铜端子一个字节的行为都没变**（2048 缓冲 / 一 tick 1024，探针实测回归）。
    ⚠ **老存档兼容**：读盘认两种 NBT 格式（新 `CompoundTag{pos,rate}` / 老 `ListTag<LongTag>`），
    老线按铜线算 —— 动这段之前先看 `Zf127Check` 的 ⑧ 段。② **材质先不画**（用户点名）⇒
    两个模型借原版贴图占位（铁粒 / 铁锭）⇒ 待画 **13 → 15**，这条链**四处一起改**
    （公告那句 / `_zf71_verify.py` / `_zf90_verify.py` 两条 / `docs\\贴图清单.md` 重跑 `--plan`）。
    ③ 语言键 **476 → 478** ⇒ 27 份常驻门 retarget（见 `_zf127_retarget.py` 的逐份命中次数）；
    ⚠ `_zf125_falsify.py` / `_zf126_falsify.py` 里那两处 476 是**历史刀的记录**，**不许改**。
    ④ 顺手补掉 `_zf71_verify.py` 缺的 §4.81 UTF-8 stdout 钉子（它之前在快照里"假绿"过）。
    ⑤ 配方 **66 → 68 份**（`crafting_shaped` 56 → 58）—— 那 9 道"配方名单"的门**仍是打包轮的活**。
    ⑥ ⚠ **`copper_wire_spool.json` 至今不在生成器表里**（当年手写的那条）—— 本轮**没动它**
    （补进表会被 `--write` 重排键序、打到别条线"配方逐字节未变"的门）；这条缺口留给打包轮或用户拍板。
    ⑦ 证据：探针 **45 项全绿** + `_zf127_verify.py` **%d 项** + 反证 **K205~K222 十八把**。
'''

fails_placeholder = u"%d"


def main():
    # ① 档案 §4
    insert_before(u"档案 §4：新增 4.105 ~ 4.108", ARC,
                  u"## 7. 权威情报来源（怎么查原版行为，别靠记忆）", LESSONS)
    # ② 档案 §5（先占位，跑完校验器再回填项数）
    insert_after_line(u"档案 §5：ZF127 那一行", ARC, u"| ZF126 | ", ROW % 0)
    # ③ 档案 §9
    insert_before(u"档案 §9：ZF127 小节", ARC, u"## 10. 备份策略", SECTION % 0)
    # ④ 交接文档
    t = read(HAND)
    if u"478 键 × 4" in t:
        notes.append(u"交接 §1：键数已经是 478（幂等跳过）")
    else:
        old = u"| 语言键数 | **464 键 × 4**"
        if t.count(old) != 1:
            fails.append(u"交接 §1：键数那格锚点命中 %d 次" % t.count(old))
        else:
            t = t.replace(old, u"| 语言键数 | **478 键 × 4**", 1)
            write(HAND, t)
            notes.append(u"交接 §1：键数 464 → 478")
    t = read(HAND)
    old_chain = u"→ **476**（ZF125 大型柴油发电机 +12）。"
    if old_chain in t:
        t = t.replace(old_chain, u"→ **476**（ZF125 大型柴油发电机 +12）→ **478**（ZF127 银线 / 银线轴 +2）。", 1)
        write(HAND, t)
        notes.append(u"交接 §1：键数那条链子补上 478")
    t = read(HAND)
    old_rec = u"| 配方 | `data\\potato_s_t\\recipe\\` **60 份**（其中 `crafting_shaped` **54** 条）；生成器表 `_zf45_recipes.py` **31 条** |"
    if old_rec in t:
        t = t.replace(old_rec, u"| 配方 | `data\\potato_s_t\\recipe\\` **68 份**（其中 `crafting_shaped` **58** 条）；生成器表 `_zf45_recipes.py` 定形 **34** 条 + 锻造台 **4** 条 |", 1)
        write(HAND, t)
        notes.append(u"交接 §1：配方数 60/54 → 68/58")
    elif u"68 份" in read(HAND):
        notes.append(u"交接 §1：配方数已经是 68/58（幂等跳过）")
    else:
        fails.append(u"交接 §1：配方那一行的锚点没命中")
    insert_after_line(u"交接 §6：第 19 条", HAND, u"18. **ZF126 的账**", HANDOVER_ITEM % 0)
    # ⑤ 公告
    insert_after_line(u"公告 §1：银线两行 + 说明", ANN,
                      u"| **Creative Cable** | Infinite FE source.", ANN_BLOCK)
    t = read(ANN)
    if u"| **Silver Wire Spool** |" not in t:
        old = u"| **Creative Cable** | Infinite FE source. Right-click to set the transfer rate (creative/testing). |\n"
        row = (u"| **Copper Wire Spool** | The 2,048 FE/t tier. Right-click one terminal, then a second "
               u"one to link them (max 16 blocks apart). |\n"
               u"| **Silver Wire Spool** | The **16,134 FE/t** tier (new in 0.11 ZF127). Same 32 uses, "
               u"same 16-block link distance, same behaviour as the copper spool — the cable is just "
               u"drawn silver-white. A terminal wired with silver gets a bigger buffer, so the line "
               u"can really move 16,134 FE per tick. |\n")
        if t.count(old) == 1:
            write(ANN, t.replace(old, old + row, 1))
            notes.append(u"公告 §1：动力网络表里加了银线轴那一行")
        else:
            fails.append(u"公告 §1：表格锚点命中 %d 次" % t.count(old))

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
