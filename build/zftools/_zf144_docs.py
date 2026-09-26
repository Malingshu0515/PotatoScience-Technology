# -*- coding: utf-8 -*-
r'''_zf144_docs.py —— ZF144 的文档 + 凭据（纯插入 / 定点替换；锚点唯一性先验）

⚠ 两个轮号都被占了才轮到 144：ZF142（他们的星图极带模糊）、ZF143（他们的贴图清单/preview）。
   全过程记在档案 §4.147 与交接 §6。

跑法：python build\zftools\_zf144_docs.py [--write]
'''
import glob
import hashlib
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
CRED = os.path.join(ROOT, "build", u"用户素材", u"_来源凭据.json")
USER = os.path.join(ROOT, "build", u"用户素材")
KEYS = 492
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
    if text.count(old) != 1:
        fails.append(u"%s：命中 %d 次（应为 1）" % (label, text.count(old)))
        return text
    notes.append(u"  [改] " + label)
    return text.replace(old, new, 1)


def live():
    src = os.path.join(ROOT, "src", "main")
    javas = [p for p in glob.glob(os.path.join(src, "java", "**", "*.java"), recursive=True)
             if not re.match(r"^Zf\d+Check\.java$", os.path.basename(p))]
    res = [p for p in glob.glob(os.path.join(src, "resources", "**", "*"), recursive=True)
           if os.path.isfile(p)]
    recipes = glob.glob(os.path.join(src, "resources", "data", "potato_s_t", "recipe", "*.json"))
    shaped = sum(1 for p in recipes if u"crafting_shaped" in read(p))
    return {"java": len(javas), "res": len(res), "recipe": len(recipes), "shaped": shaped}


L = live()

ROW = u'''| ZF144 | **新建 `zf144_pre`**（**143 份**改前件：`StarSteelSwordItem` / `StarSteelTools` / `ModTiers` / `ModItems` / `PotatoST`（探针挂载点）/ 四份 lang / 凭据 / 四份文档 / 门清单与计数器 / **全部常驻门**；逐份核哈希 + 回读，失败 0。⚠ 本根是从 `zf142_pre` **搬**过来的（不是重跑的）—— 见 §4.147） | 0.11：**星璨钢锹 + 剑的第二个技能「星辉斩」**（用户原话「锹现在放用户素材了 然后剑你看看能不能再加个特殊技能」）。① **锹**：与另外四把**共用同一档位**（1192 / 9.0 / 8.0 / 钻石 / 22），显示伤害 **13.5**（= 1 + 4.5 + 8）、攻速 **1.0 次/秒** —— 落在镐（13.0）与剑（16.0）之间，正是**原版**"锹比镐高 0.5 点、但挥得慢"的关系；技能仍是「与夜同频」，说明共用 `star_steel_tool.1`；配方照原版锹（1 锭 + 2 棍竖排）；② **星辉斩**（剑，Shift + 右键）：扣 **100** 耐久、**15 秒**冷却，朝面向斩出一道 **8 × 3 × 3** 的剑气，**贯穿**沿途所有敌人各 **12** 点并照亮 5 秒；**身后与隔墙打不到**；③ 几何用**走廊坐标**投影（朝向 + 法线），不逐格采样；"隔墙"用**原版 `level.clip`** 射线；④ 剑气是**本工程第二个自定义伤害类型** `potato_s_t:star_steel_slash`（`effects=hurt`）⇒ 死亡文案「%1$s被星光贯穿」；⑤ 剑改用自己那组三行说明（说明的**键前缀与行数已参数化**，锹/镐/锄仍共用一句）；⑥ 四语言 **487 → 492** 键；配方 **72 → 73**（shaped **62 → 63**） | 见 §9 ｜ 见 §4.146~§4.147 |
'''

SEC4 = u'''### 4.146 【陷阱】"依赖场地"的探针判据必须**先把场地做出来**；实体要**先定位再入世**；施法者要**每次重新摆正**（0.11 ZF144）

本轮探针第一版把剑气那 6 条判据全跑成红的，查了四轮才见底 —— **三层根因叠在一起**：

1. **场地**：试验场选在 (420,100,100)，那里**地形比 y=100 高** ⇒ 靶子一放进去就埋在方块里，
   "隔墙"那条原版射线**每次都命中** ⇒ 一条都打不到。改成**真的挖一个空腔**，并补一条"中间是空气吗"的对照。
2. **实体要先进世界**：`addFreshEntity` 是在 (0,0,0) 那会儿登记进实体管理器的，之后 `setPos(420,…)`
   只是挪坐标 —— 而**换区块要等它下一次 tick 才改归档**，一个不在已加载区块里的实体又**根本不会 tick**
   ⇒ 管理器里它永远留在原点那个 section，`getEntities(caster, 远处AABB)` **永远数不到**。
   ⇒ **先给位置，再 `addFreshEntity`**；并把区块显式 `getChunk` 加载出来（实体查询只看已加载区块）。
3. **玩家会掉下去**：`ServerPlayer` 的出生保护要烧 61 tick（§4.128），**那 61 次 tick 里它受重力掉到地面**
   （实测 y 100 → **51.58**）；后来量冷却又原地 tick 302 次，`setNoGravity(true)` 也没挡住它再沉 **3.77 格**。
   剑气的纵向窗口只有 ±1.5 ⇒ "打死 5 点血的靶子"命中 0 个。
   ⇒ 立一条 `recenter(caster)`：**判据依赖位置，就在判据之前把位置摆正**。

**方法论**：这三层都不是"代码错了"，而是"**探针以为的前提不成立**"。
凡是靠"场地/位置/实体在不在世界里"的判据，都要配一条**把前提本身量出来**的对照
（本轮补了五条：场地是空气 / `addFreshEntity` 成功 / `getEntities` 数得到 / caster 没掉下去 /
灵敏度对照"普通伤害打得进去"）。**"0 伤害"到底是几何拒绝还是场地问题，只有这些对照能分开。**

### 4.147 【流程雷】"改轮号之前先查有没有人占" —— 我第二次栽在同一个坑里，这次连**轮号连撞两回**、还覆盖了别人的备份清单（0.11 ZF144）

- ZF139 那轮踩过：改名脚本扫通配，覆盖了别人的 `_zf138_*`（§4.132）。
- 本轮**又**踩，而且更重：我取了 **ZF142**，而另一条线**已经在用 ZF142**（星图极带横向模糊，
  他们的 `_zf142_pre.py` 23:33 就建好了备份根 `C:\\PotatoST救援\\zf142_pre`）。
  我的 `_zf142_backup.py`（23:39）写的是**同一个目录** ⇒ **覆盖了他们的 `_sha1.txt`**。
  改号到 **ZF143** 之后才发现 **ZF143 也在被他们用**（`_zf143_apply.py` / `_zf143_docs.py` /
  `_zf143_look.py` / `_zf143_preview.py`，23:39~23:41）⇒ 再改到 **ZF144**。

**已做的（不伪造、只重建）**：`_zf142_repair.py` 按**他们脚本里那份 `FILES` 清单 + 它自己那四条 glob**，
对备份根里**现存的那一份**重算 sha1、按他们的格式写回 `_sha1.txt`（两边重叠的件内容本来就相同 ⇒
重建结果与他们原来那份一致）；说明写进 `zf142_pre\\_补说明_被误覆盖的sha1清单.txt`。
**没有**重跑他们的 `_zf142_pre.py`（现在重跑会把"我改过之后"的内容抄成"改前件"，那才是真污染），
**没有**删他们目录里任何一个文件。

**规矩（在 §4.132 上再收紧两条）**：
1. **开工第一件事是"查盘上有没有人在用这个轮号"** —— 判据**不是**"档案 §5 表里有没有这一行"
   （别人的**在途**文件根本不在档案里），而是 `Get-ChildItem build\\zftools -Filter '*zfNNN*'`
   数一遍；**备份根也算**（`C:\\PotatoST救援\\zfNNN_pre` 存在就是被占）。
2. **改名脚本永远只对自己点名的清单动手**，而且**先核目标名不存在**（`os.path.exists` 就停手）——
   本轮两次改名都加了这一条，两次都没覆盖到他们的文件。

'''

SEC9 = u'''### ZF144（0.11）星璨钢锹 + 剑的「星辉斩」—— **待你实测**

用户原话：「锹现在放用户素材了 然后剑你看看能不能再加个特殊技能」。

#### 一、锹（素材 `星璨铲子.png`）

身份先说清楚：alpha 掩码与原版六档 × 五种工具共 30 张图逐个算 IoU ⇒ **锹 0.9815**
（第二名锄只有 0.6154）—— 没有歧义（`_zf144_recon.txt`）。

| 工具 | 显示伤害 | 攻速 | DPS | 备注 |
|---|---|---|---|---|
| 斧 | 17.0 | 0.9 | 15.3 | ZF133，一个字没动 |
| 剑 | 16.0 | 1.6 | 25.6 | ZF141 |
| **锹（本轮）** | **13.5** | 1.0 | 13.5 | 落在镐与剑之间 —— 原版就是"锹比镐高 0.5 点、挥得慢" |
| 镐 | 13.0 | 1.2 | 15.6 | ZF141 |
| 锄 | 12.0 | 1.0 | 12.0 | ZF141 |

档位与另外四把**同一个对象**（1192 / 9.0 / 8.0 / 钻石 / 22）；技能仍是「与夜同频」；
配方 = 原版锹图纸（`X / # / #`），材料换成星璨钢锭。

#### 二、剑的第二个技能「星辉斩」（Shift + 右键）

| 项 | 值 |
|---|---|
| 出手代价 | **100 点耐久**（斧子冲击波是 120 —— 剑轻一些） |
| 冷却 | **15 秒**（与斧子同一个节奏） |
| 范围 | 面向 **8 × 3 × 3**，**贯穿**沿途所有敌人 |
| 伤害 | 每人 **12 点**，并被星辉照亮 **5 秒** |
| 打不到谁 | 身后的（0.5 格以内不算）、超出 8 格的、横向偏出 1.5 格的、**隔着墙的** |
| 样子 | 沿走廊撒 `END_ROD` 粒子 + 一声三叉戟投掷（**全在服务端发** ⇒ 不需要任何客户端代码） |
| 死亡文案 | 自定义伤害类型 `potato_s_t:star_steel_slash` ⇒ 「**%1$s被星光贯穿**」 |

**为什么不像斧子那样做成"每 tick 推进的波"**：斧子那道波要**拆方块**（砍树），必须一格一格推进、
还要处理"撞墙即停""10 秒没碰到木头就散"；剑气只是**一瞬间**打一条走廊，扫一次就够 ——
少一整套状态机、少一个每 tick 监听、也少一份"退场清理"的账。

#### 三、⚠ 我替你定的（你没说的；改都是一处）

1. 锹的**伤害 13.5**（取原版"锹 = 镐 + 0.5"的相对关系，而不是与镐一样 13.0）；
2. 星辉斩的**代价 100 / 冷却 15 秒 / 伤害 12 / 范围 8×3×3 / 发光 5 秒** —— 全是本轮定的
   （斧子那套是 120 / 15 秒 / 6 宽 3 高；剑这套按"更轻、更长"给）；
3. 剑气**不额外加规则**（走原版 `hurt`：正常吃护甲、正常有无敌帧）；
4. 它**不区分昼夜**（技能②与"与夜同频"是两件事，白天照样放）。

#### 四、证据

| 项 | 值 |
|---|---|
| 探针 | `_zf144_probe_utf8.txt` **67 项全绿**：锹的档位/属性 13.5·1.0 / 挖泥土速度 9.0（对照：挖石头不掉落）/ 白天采掘 1·攻击 2、夜晚两样全 0 / 真合成网格出锹、同图纸换钻石出原版锹 / **正前方 3 格挨 12.0**、身后·超程·出宽·隔墙**四种负向各 0**、墙拆了又打得中、贯穿两个目标都挨 / 出手扣 100 并进冷却、不按 Shift·冷却中·耐久不足三种都不出手 / 命中者发光 100 tick / **死亡那一刻的文案键与 `%1$s` 解析** / 旧账（剑的夜晚不磨损、斧子的手持急迫）没坏 |
| 常驻校验 | `_zf144_verify.py`（项数见它自己的输出） |
| 反证刀 | `_zf144_falsify.py`（见它自己的输出） |
| 活体数字 | 四语言 **487 → 492** 键；配方 **72 → 73**（shaped **62 → 63**）；Java **+1**（`StarSteelShovelItem`）；资源 **+4**（1 配方 + 1 模型 + 1 贴图 + 1 伤害类型） |
| 门 | `_zf104_gates.ps1` 加两段；常驻门跟平键数与配方数；**没动**另一条线在途的 `_zf142_verify.py` 与 `_zf143_*` |
| 未打包 | 本轮**没有重新打包** ⇒ `release\\PotatoST-0.11.jar` 仍是别的线 23:22 打的那份（487 键），`RELEASE_KEYS = 487` 保持不动 |

#### 五、要你实测

1. 工作台：**1 星璨钢锭 + 2 木棍**竖着摆 ⇒ 出一把**星璨钢锹**（挖泥土/沙子/雪飞快，伤害 13.5）；
2. 拿**星璨钢剑**按 **Shift + 右键** ⇒ 面前扫出**一条 8 格长的星光**，沿途的怪一起挨 12 点、
   并且**亮起来 5 秒**；身后的怪**打不到**，隔着墙也打不到；
3. 出手后剑**扣 100 耐久**、快捷栏进 **15 秒**冷却；不按 Shift 右键**什么都不会发生**、也不扣耐久；
4. 被这一下打死的怪，死因应是「**XXX被星光贯穿**」（XXX 是它自己的名字）；
5. Shift 看说明：剑应是**三行**，锹应与镐/锄一样**一行**。

'''

ANN_ENTRY = u'''
- **Star Steel shovel + the sword's Starlight Slash (0.11 ZF144)** - two additions. (1) The **Star Steel Shovel** joins the set: the same shared tier as the sword/pickaxe/hoe/axe (**1192 durability, diamond mining level, speed 9.0**), **13.5 attack damage at 1.0 hits/s** - between the pickaxe (13.0) and the sword (16.0), which is exactly vanilla's own relationship (a shovel hits 0.5 harder than a pickaxe but swings slower). It keeps the "in tune with the night" skill and uses the vanilla shovel recipe (one Star Steel Ingot over two sticks). (2) The **Star Steel Sword gets a second skill**: **shift + right-click fires an 8-block Starlight Slash** - it costs **100 durability**, has a **15 s cooldown**, pierces **every** enemy in an 8 x 3 x 3 corridor for **12 damage**, lights each one up for **5 seconds**, and **cannot reach behind you or through walls**. It uses the mod's **second custom damage type** (`potato_s_t:star_steel_slash`), so anything killed by it dies to "... was pierced by starlight". The sword's tooltip is now three lines of its own; the shovel/pickaxe/hoe still share one.
'''


def patch_cred(text):
    data = json.loads(text)
    before = len(data)
    name = u"星璨铲子.png"
    src = os.path.join(USER, name)
    if not os.path.isfile(src):
        fails.append(u"凭据：素材不在 %s" % src)
        return text
    sha = hashlib.sha1(open(src, "rb").read()).hexdigest()
    dst = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item\star_steel_shovel.png")
    if not os.path.isfile(dst) or hashlib.sha1(open(dst, "rb").read()).hexdigest() != sha:
        fails.append(u"凭据：素材与在用贴图不同哈希")
        return text
    if name not in data:
        data[name] = {
            "原名": name, "sha1": sha, "bytes": os.path.getsize(src), "轮次": u"ZF144",
            "说明": u"用户 ZF144 给的星璨钢锹贴图（16x16 RGBA）。身份核实：alpha 掩码与原版六档**锹**的 "
                    u"IoU 均为 **0.9815**（第二名锄只有 0.6154）⇒ 与文件名一致、没有歧义。"
                    u"原字节复制成 textures/item/star_steel_shovel.png"}
    notes.append(u"  [改] 凭据 %d → %d 条（sha1 现算）" % (before, len(data)))
    return json.dumps(data, ensure_ascii=False, indent=2) + u"\n"


def main(argv):
    write = u"--write" in argv

    doc = read(DOC)
    lines = doc.split(u"\n")
    idx = [i for i, l in enumerate(lines) if l.startswith(u"| ZF141 |")]
    if len(idx) != 1:
        fails.append(u"§5 里 `| ZF141 |` 命中 %d 行（应为 1）" % len(idx))
    else:
        lines.insert(idx[0] + 1, ROW.rstrip(u"\n"))
        notes.append(u"  [插] 档案 §5 加 ZF144 行")
        doc = u"\n".join(lines)
    doc = before(doc, u"## 7. 权威情报来源", SEC4, u"档案 §4 加 4.146~4.147")
    doc = before(doc, u"## 10. 备份策略", SEC9, u"档案 §9 加 ZF144 小节")
    plan.append((DOC, read(DOC), doc))

    hand = read(HAND)
    hand = once(hand, u"| 语言键数 | **487 键 × 4**", u"| 语言键数 | **492 键 × 4**",
                u"交接 §1：键数 487 → 492")
    hand = once(hand, u"→ **487**（ZF141 星璨钢剑/镐/锄：三件工具名 + 一句共用的技能说明 +4）。",
                u"→ **487**（ZF141 星璨钢剑/镐/锄：三件工具名 + 一句共用的技能说明 +4）"
                u"→ **492**（ZF144 星璨钢锹 + 剑的三行说明 + 剑气死亡文案 +5）。",
                u"交接 §1：键数链条补一环")
    hand = once(hand, u"| 配方 | `data\\potato_s_t\\recipe\\` **72 份**（其中 `crafting_shaped` **62** 条）",
                u"| 配方 | `data\\potato_s_t\\recipe\\` **73 份**（其中 `crafting_shaped` **63** 条）",
                u"交接 §1：配方 72 → 73")
    hand = once(hand, u"24. **⚠ ZF139 的归档探针与它自己的报告对不上",
                u"""25. **ZF144 的账（星璨钢锹 + 剑的星辉斩）**：① 用户原话「锹现在放用户素材了
    然后剑你看看能不能再加个特殊技能」。做了**锹**（共用档位、伤害 13.5、原版锹图纸）+
    剑的**第二个技能「星辉斩」**（Shift + 右键：扣 100 耐久 / 15 秒冷却 / 8×3×3 走廊 /
    各 12 点 / 发光 5 秒 / 身后与隔墙打不到），伤害类型是本工程第二个自定义的
    `potato_s_t:star_steel_slash`（死亡文案「%1$s被星光贯穿」）。
    ② 四语言 **487 → 492** 键、配方 **72 → 73**（shaped 62 → 63）⇒ 门已跟平。
    ③ 证据：探针 **67 项全绿**；常驻校验与反证刀的项数见它们自己的输出。
    ④ 本轮**没有重新打包** ⇒ `RELEASE_KEYS` 保持 **487**（成品是别的线 23:22 打的那份）。
    ⑤ ⚠ **另一条线的 `_zf142_verify.py` / `_zf143_*` 我一个字没动**：你们那条门里若钉着键数 487，
    现在应当是红的 —— **请你们自己跟到 492**（我刻意不碰在途文件，§4.7）。

26. **⚠ 撞号事故（我这条线自己欠的，如实记着）**：本轮一开始取了 **ZF142**，
    而**另一条线正在用 ZF142**（星图极带横向模糊：`_zf142_pre.py` 23:33 就建了备份根
    `C:\\PotatoST救援\\zf142_pre`）。我的 `_zf142_backup.py`（23:39）写的是**同一个目录** ⇒
    **覆盖了他们的 `_sha1.txt`**。改号到 **ZF143** 后才发现 **ZF143 也在被他们用**
    （`_zf143_apply.py` / `_zf143_docs.py` / `_zf143_look.py` / `_zf143_preview.py`，23:39~23:41）
    ⇒ 最终定 **ZF144**（盘上与备份根都空着，实测过）。
    ① 已做的：`_zf142_repair.py` 按**他们脚本里那份 `FILES` 清单 + 它自己那四条 glob**、
    对备份根里现存的那一份重算 sha1、按他们的格式写回；说明写在
    `zf142_pre\\_补说明_被误覆盖的sha1清单.txt`。两边重叠的件内容本来就相同，所以重建结果与他们原来那份一致。
    ② **没做**：没有重跑他们的 `_zf142_pre.py`（重跑会把"我改过之后"的内容抄成"改前件"——
    那才是真污染）、没有删他们目录里任何一个文件。
    ③ 我这一轮的备份根是 `zf144_pre`，此后不再动 `zf142_pre` / `zf143_*`。
    ④ 已立 §4.147：**开工第一件事是"查盘上有没有人在用这个轮号"**
    （`Get-ChildItem build\\zftools -Filter '*zfNNN*'`；**别人的在途文件不在档案里**，
    `C:\\PotatoST救援\\zfNNN_pre` 存在也算被占）。
    ⑤ **请你们核对**：若重建的 `_sha1.txt` 有哪一条与记忆不符，**以备份件本身为准**
    （备份件一个字节都没被我改过，我只覆盖过 `_sha1.txt`）。

24. **⚠ ZF139 的归档探针与它自己的报告对不上""",
                u"交接 §6：加第 25 / 26 条")
    plan.append((HAND, read(HAND), hand))

    ann = read(ANN)
    if u"ZF144" in ann:
        notes.append(u"  [跳过] 英文公告里已经有 ZF144 了（幂等）")
    else:
        plan.append((ANN, ann, ann.rstrip(u"\n") + u"\n" + ANN_ENTRY))
        notes.append(u"  [插] 英文公告补 ZF144 条目")

    plan.append((CRED, read(CRED), patch_cred(read(CRED))))

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
    if write:
        for p, _o, new in plan:
            io.open(p, u"w", encoding=u"utf-8", newline=u"").write(new)
        for p, _o, new in plan:
            assert read(p) == new, p
        print(u"已写盘；回读 %d 份逐字节一致" % len(plan))
    else:
        print(u"（没加 --write，只算不写）")
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
