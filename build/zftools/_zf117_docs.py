# -*- coding: utf-8 -*-
r"""_zf117_docs.py —— ZF117 文档：档案 §5 加一行 / §9 加一节 / §4 加三条雷
+ 交接文档的活体数字 + 英文公告的进度章节

并发环境（同一棵树上 ZF116 素材线还在跑）⇒ 一律「按**行首前缀**定位 → 插入 → 立刻回读断言」，
绝不整份覆盖（§4.84）。
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


def insert_after_prefix(path, prefix, block, label, limit=3):
    u"""在第 limit 个（默认：前 3 个之内最后一个）以 prefix 开头的行**之后**插入 block"""
    raw = read(path)
    lines = raw.split(u"\n")
    probe = [l for l in block.split(u"\n") if l.strip()][0]
    if probe in raw:
        notes.append(label + u"（已经在盘上，跳过）")
        return True
    hits = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if not hits:
        fails.append(u"%s：找不到行首前缀 %r" % (label, prefix[:40]))
        return False
    i = hits[0]
    lines[i + 1:i + 1] = block.split(u"\n")
    text = u"\n".join(lines)
    write(path, text)
    if probe not in read(path):
        fails.append(u"%s：回读找不到插入内容" % label)
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
        fails.append(u"%s：锚点 %r 出现 %d 次" % (label, exact[:40], raw.count(exact)))
        return False
    write(path, raw.replace(exact, block + exact, 1))
    if probe not in read(path):
        fails.append(u"%s：回读找不到插入内容" % label)
        return False
    notes.append(label)
    return True


def sub_once(path, old, new, label):
    raw = read(path)
    n = raw.count(old)
    if n != 1:
        fails.append(u"%s：锚点出现 %d 次（要求 1）" % (label, n))
        return False
    write(path, raw.replace(old, new, 1))
    back = read(path)
    if new not in back:
        fails.append(u"%s：回读失败" % label)
        return False
    notes.append(label)
    return True


ROW = (
    u"| ZF117 | **新建 `zf117_pre`**（155 份改前件：四份 lang + 27 份 advancement + `_zf107_adv`/`_zf107_verify` "
    u"+ 全部常驻校验脚本 + 3 份文档 + 旧成品 jar 与 `.sha1`；逐份核哈希、失败 0。"
    u"⚠ **另有 1 份补账**：`PotatoST.java` —— 探针要往它的构造器末尾挂一行，我写清单时漏了它；"
    u"用「`git cat-file blob HEAD:…` == 摘掉钩子后的盘上文件」两条路逐字节证明（sha1 `f5989035…`，"
    u"见 `zf117_pre\\_补说明.txt`）） "
    u"| 0.11：**进度树补线：8 条新节点 + 顺手修 ZF115 漏的那四句状态文案**。用户原话「嗯嗯 成就该更新了宝宝」。"
    u"① **8 条节点**＝6 条 ZF107 之后的新内容（采油机 / 锂电池构造间 / 三元聚合物锂电池 / 星璨钢 / "
    u"星璨钢套装 / 星轨坠）+ 2 条**老空洞**（海盐 / 液体物流：`electrolyzer` 的说明写着「加海盐再电解」，"
    u"全树却没有一处说海盐哪来）；"
    u"② 判据沿用 §4.74：「或」= 多判据同一个 requirement 组（7 条），「与」= 每判据各占一组"
    u"（星璨钢套装四件）；触发器只用 `inventory_changed`，不动 Java；"
    u"③ 四语言 **432 → 448 键**（16 键 ×4；旧 16 份 + 新 5 份往轮校验与英文公告一次重定目标）；"
    u"④ `_zf107_verify.py` 的总数 27 → **35**（新立 `EXPECT_NODES`）并把 `frame=challenge` 与 `hidden` "
    u"拆成两张表（§4.90）；"
    u"⑤ **顺手修 ZF115 的漏账**：界面状态灯那句「硫酸不够…」四语言都还写着 10 mB / 6000 mB"
    u"（玩家悬停看到的就是它）⇒ 改成 1 mB / 600 mB，并给 `_zf112_verify.py` 加 6.5 段常驻检查（§4.91）；"
    u"⑥ 全门快照抓出 **ZF114 打包的 `.sha1` 写了 `hash  文件名`**（十道门只认纯哈希一行）⇒ 对账"
    u"（jar 本体一个字节没动，§4.92）；"
    u"⑦ 探索型证据：探针 `Zf117Check` **455 项 ALL OK**（35 条全加载 / 父链逐条 / 「与」只给三件不亮 / "
    u"隐藏那条照样能亮 / 无关物品（扳手）一条不亮 / 真游戏念出修好的状态文案）、`_zf117_verify.py` "
    u"**203 项**、反证 **K138~K149 十二把刀** | 见 §9 |"
)

SEC9 = u'''
### ZF117（0.11）进度树补线：8 条新节点（+ 补 ZF115 漏的四句状态文案）—— **未打包**

用户原话：「嗯嗯 成就该更新了宝宝」

ZF107 立下这棵树时说的是「**只有里程碑才给成就**、说明文字写下一步该干什么」。那之后又长了
六样东西（采油机、星璨钢、星璨钢套装、锂电池构造间、三元锂、星轨坠/粗振金），一条节点都没有 ——
这一轮把它们补上，顺带补两条**老空洞**。

#### 一、8 条新节点（全部只用数据包触发器，Java 一行没动）

| 节点 | 父 | 框架 | 图标 | 判据 | 说的是什么 |
|---|---|---|---|---|---|
| `oil_pump` 海底油田 | `distillation` | goal | 采油机 | 拿到采油机 | 站在海洋油田里、正下方一串含水锁链 = 井深 n；8n²+80n FE/t、10n mB/s、25B 横罐只出不进；抽够 25~80 桶，附近 10×10 区块的油田变成旁边的海洋（那一刻它自己停机） |
| `lithium_battery_plant` 锂电池构造间 | `acid` | goal | 构造间 | 拿到构造间 | 通硫酸（1 mB/t、一炉 600 mB），四槽各一份：粗锰/粗铝 · 镍/粗镍 · 碳酸锂 · 钴/粗钴 → 30 秒一个锂电池原件；**不耗电**；碳酸锂 = 锂矿精粉进电力高炉 |
| `lithium_battery` 三元聚合物锂电池 | `lithium_battery_plant` | task | 三元锂 | 拿到三元锂 | 纸 + 电容 + 一般金属块 + 锂电池原件；一块 4M FE，能叠成金字塔（2×2 六层 / 3×3 十二层 / 5×5 三十二层），只有底面能接线 |
| `star_steel` 星璨钢 | `hard_alloy` | goal | 星璨钢锭 | 拿到星璨钢锭 | 合金炉：下界合金锭 + 4 高碳钢 + 钴 + 银 + 铜，另吃 1 深层钴矿石 + 1 末影水晶 → 3 锭；12000 FE/t 跑满 30 秒（一炉 720 万 FE） |
| `star_steel_armor` 星璨钢套装 | `star_steel` | **challenge** | 星璨钢胸甲 | **四件全要**（「与」） | 头盔 5 + 胸甲 8 + 护腿 7 + 靴子 4 = 24 个锭；本模组最硬的一套 |
| `starfall` 星轨坠 | `new_beginning` | challenge · **隐藏** | 星轨坠 | 拿到星轨坠**或**粗振金 | 4 点耐久一次扣 1；30 秒红色倒计时，前 10 秒可取消；陨石从 y=200 砸下，7~20 威力带火，15 以上固定夹 3 块粗振金 |
| `salt` 海盐 | `steel` | task | 海盐 | 拿到海盐**或**晒盐机 | 晒盐机不用喂东西（通电快得多）；海盐进电解器出氯气，或交给盐分解构器拆成氯化钠 |
| `fluid_logistics` 液体物流 | `stronger_power` | task | 流体泵 | 拿到流体泵**或**容器换流器 | 泵只搬不存、优先送目标收得下的、能抽干世界里的液体源方块；换流器拿 1 个空桶换出罐里 1000 mB 对应的桶 |

#### 二、六处**我定的**（用户没说的，等拍板；改都是一行）

1. **采油机挂 `distillation`**（它是原油的另一个来源，接在分馏塔之后）；
2. **星璨钢挂 `hard_alloy`**（合金线的血统：轻质 → 硬质 → 星璨），不挂 `stable_block`；
3. **星轨坠挂根、且隐藏** —— 它与两张唱片一样**没有配方**（ZF114 明说"先不给配方"），
   做成主线上的一环会留下一个**生存永远点不亮的格子**；隐藏位把它变成彩蛋，等配方上线再考虑挪进主线；
4. **星璨钢套装是明面 challenge**（不隐藏）：它真能打出来，只是要 24 个锭；
5. **海盐挂 `steel`**（晒盐机配方要高碳钢 + 银板，与电解器同层）；
6. **液体物流挂 `stronger_power`**（流体泵配方要发电机 + 电容）。

⚠ **星轨坠那条现在生存里拿不到**（道具无配方）—— 这是**如实反映**盘上现状，不是漏做；
哪天给了配方/来源，把它从 `new_beginning` 挪进主线 + 取掉 `hidden` 即可。

#### 三、覆盖面：哪些机器**仍然没有**节点（有意）

`空气分离器`（并进「合成氨」的说明）、`加氢脱硫反应仓`（并进「硫」）、`灌装机`（并进「气体的存取」）、
`液压机`（并进「压成板」）、`分馏塔操作器`（并进「分馏塔」）、以及全部中间零件
（加热装置 / 散热装置 / 线轴 / 各种板 / 热力金属 / 光伏原件 / 硅 / 磁铁 / 墨粉 / 铀锭 / 扳手）。
**这与 ZF107 的「别太烦琐」是同一条口径** —— 一个 Tab、35 个里程碑。

#### 四、顺手修的两笔账

1. **ZF115 漏的第四处**（§4.91）：界面状态灯那句 `gui.potato_s_t.lithium_battery_plant.status.no_acid`
   在四语言里都还写着「每 tick 要 10 mB（一炉 6000 mB）」⇒ 全改成 **1 mB / 600 mB**，
   并给 `_zf112_verify.py` 加 **6.5 段**常驻检查（4 语言 × 3 条：必须有 1 mB/600 mB、不许有 10/6000）。
   同一轮清掉 `LithiumBatteryPlantBlockEntity` 里 ZF115 那次补丁**叠在一起的旧 javadoc**（8000 那版）。
2. **ZF114 打包的 `.sha1` 格式**（§4.92）：盘上写的是 `hash  文件名`，而十道门判据是
   `rec.strip().lower() == sha1(jar)` ⇒ 全门快照里那十道门一起红。**只改那一行**（jar 本体零改动、
   哈希仍 `303c5d46…`），六道门当场转绿；并给 `_zf117_verify.py` 加 E8/E9 两条钉住格式。

#### 五、数字与证据

| 项 | 值 |
|---|---|
| 节点 | **27 → 35**（`_zf107_verify.py` 的 `EXPECT_NODES = 35`） |
| 四语言 | **432 → 448 键**（21 份往轮校验 + 英文公告一起重定目标；键集合四份一致） |
| 新文件 | `advancement\\{oil_pump,lithium_battery_plant,lithium_battery,star_steel,star_steel_armor,starfall,salt,fluid_logistics}.json` |
| 老节点 | 27 份**逐字节未变**（`_zf117_verify.py` A4 内嵌 sha1 表比对） |
| 探针 | `Zf117Check.java`（真 `runServer`）**455 项 ALL OK**，报告 `build\\zftools\\_zf117_probe_utf8.txt`；存档 `build\\zftools\\check\\Zf117Check.java`（28613 B，sha1 `efb0b057…`，**先抄后删**） |
| 常驻校验 | `_zf117_verify.py`（203 项）＋ 27 项改名/重定目标进 21 份旧门 |
| 反证刀 | **K138~K149（12 把）全咬住**：父链 / hidden / 图标 / 「与」写成「或」/ 老节点被动 / 野文件 / 键被删 / 老键改值 / ASCII 引号 / 状态文案退回旧数字 / 节点数改回 27 / 旧键数 432 复活 |
| 生成器 | `_zf117_adv.py`（表驱动；**重跑幂等**：已同值就跳过、有别的值就报冲突停手） |
| 全门快照 | `build\\zftools\\_zf117_gatesnap.txt`（脚本 `_zf117_gatesnap.py`，38 道门） |

**要你实测的**（进游戏）：

1. 打开成就界面 ⇒ 同一棵树上应当多出 **8 个格子**：分馏塔下面「海底油田」、酸性反应室下面
   「锂电池构造间 → 三元聚合物锂电池」、硬质钛合金下面「星璨钢 → 星璨钢套装」、
   钢下面「海盐」、更强劲的电源下面「液体物流」；
2. 拿一件星璨钢装备 ⇒ 只有凑齐**四件**才会亮「星璨钢套装」（差一件不亮）；
3. 「星轨坠」应当是**隐藏**的（没拿到之前看不见）；
4. 锂电池构造间在**缺硫酸**时把鼠标停在状态灯上 ⇒ 这句现在写「每 tick 要 1 mB（一炉 600 mB）」。

**成品**：**本轮没有新成品** —— `release\\PotatoST-0.11.jar` 仍是 ZF114 打的
**`303c5d468b96826ef6836b0a4e54ccb8a539557c`**（4,298,939 B，432 键，**不含本轮的 8 条进度**）。
本轮构建产物是 `build\\libs\\potato_s_t-0.11.jar` = **`7f0a325002a415a9ee1f0b0a58ce3bc543b389cc`**（4,307,139 B）
—— ⚠ 它里面**同时含 ZF116 尚未提交的三张盔甲贴图**，所以**打包轮要重打**。

'''

PITFALLS = u'''
### 4.90 【校验雷】`frame = challenge` 与 `hidden` 是**两件事**（0.11 ZF117）

ZF107 立树时的两条彩蛋（两张唱片）**恰好**既 challenge 又 hidden，于是那一轮的门把它们写成了一张表：

```python
eq(u"A7 %s 的 frame 符合设计" % n,
   "challenge" if n in HIDDEN else ("goal" if n in GOALS else "task"), ...)
```

也就是"**隐藏 ⇔ 挑战**"。ZF117 第一条**明面挑战**（星璨钢套装：要 24 个锭，但玩家看得见目标）
一上线，这条等式当场散架 —— 门会把 `challenge` 判成"应该是 task"。

**规矩**：`frame`（外观：方形 / 圆角 / 带边框）与 `hidden`（能不能提前看见）是**两个正交字段**，
门里必须拆成两张表：`CHALLENGES`（frame）与 `HIDDEN`（hidden），`HIDDEN ⊆ CHALLENGES` 只是**约定**、
不是定义。本轮 `_zf107_verify.py`（`A7` 改读 `CHALLENGES`）与探针 `Zf117Check` 都按这个改了。

### 4.91 【连带雷】改一个常数，要连"**界面上念出来的那句话**"一起改（0.11 ZF117，复盘 ZF115）

ZF115 把锂电池构造间的硫酸从 10 mB/t 砍到 1 mB/t、罐 8000 → 800，改了五处：两个常量、
四语言**介绍**（tooltip）、探针里的字面量、`_zf112_verify.py` 的断言、反证刀 K133/K134。
**漏了第六处**：界面**状态灯**那句 `…status.no_acid`（玩家把鼠标停在灯上看到的就是它），
四语言里都还写着「每 tick 要 10 mB（一炉 6000 mB）」。

根因不是"忘了"，是**门没管**：`_zf112_verify.py` 只钉了 `tooltip.*` 里的数字，
没钉 `gui.*.status.*` 里的数字。所以这轮的修法不是"下次记得"，而是**把状态文案也钉进门**：
`_zf112_verify.py` 新增 6.5 段，四语言各三条（必须有 `1 mB` / `600 mB`，不许有 `10 mB` / `6000 mB`）。

**规矩**：**文案里的数字是活体数字的一种**。凡是一个常数会出现在玩家看得见的句子里，
那个句子必须有一道门钉着 —— 否则改常数时它一定会烂掉，而且**只有玩家看得见**。

### 4.92 【发布雷】`.sha1` 旁边那一行有**两种写法**，而十道门只认一种（0.11 ZF117）

ZF114 打包时 `_zf114_publish.py` 写的是 `sha1sum` 风格：

```
303c5d468b96826ef6836b0a4e54ccb8a539557c  PotatoST-0.11.jar     ← ZF114 写的（带文件名）
84d09345f6095408ae462dabb536307141904ea3                        ← 0.10 那版（纯哈希）
```

而盘上十道门（`_zf78 _zf79 _zf89 _zf90 _zf91 _zf94 _zf95 _zf98 _zf99 _zf102`）的判据都是

```python
rec = read(jar + ".sha1");  rec.strip().lower() == sha1(jar)
```

⇒ **十道门一起红**，而红的话术是"`.sha1` 与 jar 一致（303c5d46…）"——
看起来像哈希算错了，其实是**格式**不对（哈希一直是对的）。

**规矩**：`release\\*.sha1` **只写哈希那一行**（0.10 的写法）。本轮只改了那一行
（jar 本体零改动，哈希仍 `303c5d46…`），六道门当场转绿，并在 `_zf117_verify.py` 加 E8/E9 钉住格式。
**发现它的是"全门快照"这一步** —— 不跑快照，这十道红会一直挂着当成"老账"。

'''

ANN_TREE = u'''```
A New Beginning!        obtain a Micro Crusher
├── Grind It Down       Iron Dust / Carbon Dust
├── Press It Flat       any metal plate
├── Wire It Up          Terminal Block / Wiring Block
├── First Watt          Low-Tier Generator
│   ├── A Stronger Power Source   Generator + Power Capturer
│   │   └── Fluid Logistics       Fluid Pump / Fluid Exchanger
│   └── Clean Energy 101          place a Solar Panel
├── Capacitor           Capacitor
│   ├── * Electric Blast Furnace  controller + 3×3×3 shell
│   │   ├── * Thus Steel Was Made High Carbon Steel
│   │   │   ├── * Titanium        Titanium Ingot
│   │   │   ├── Electrolysis      Electrolyzer
│   │   │   ├── Sea Salt          Salt Dryer / Sea Salt
│   │   │   ├── Storing Gas       Gas Tank + Filling Machine
│   │   │   └── Oil               scoop crude oil with an Oil Bucket
│   │   │       └── * Distillation Tower
│   │   │           ├── Diesel & Gasoline
│   │   │           ├── Sulfur
│   │   │           ├── * Oil Under the Sea   Oil Pump
│   │   │           └── * Combustion Chamber ── * Acidic Reaction Chamber
│   │   │                                           └── * Lithium Battery Plant
│   │   │                                               └── Ternary Polymer Lithium Battery
│   │   └── * Alloy Smelter
│   │       ├── Lightweight Titanium Alloy
│   │       │   ├── Titanium Tools
│   │       │   └── * Hard Titanium Alloy ── Stable Metal Block
│   │       │                         └── * Star Steel ── + Star Steel Suit
│   │       └── (…)
│   └── (Electrolysis ── Ammonia)
├── + The Anvil and the Republic / + Jasmine Flower   the two music discs
└── + Starfall Pendant    the meteor pendant (no recipe yet)
```'''

HAND_TABLE_OLD = u'''| 语言键数 | **417 键 × 4**（zh_cn / en_us / ja_jp / ru_ru，四份键集合必须完全一致） | 翻译润色线正在重写**值**；键数的活体数字：… → 398 → 408 → **417**（ZF112） |
| 进度（成就） | **27 条**（3 老 + 24 新），一个标签页 | 主项目线（ZF107，已提交） |'''
HAND_TABLE_NEW = u'''| 语言键数 | **448 键 × 4**（zh_cn / en_us / ja_jp / ru_ru，四份键集合必须完全一致） | 翻译润色线正在重写**值**；键数的活体数字：… → 408（ZF109）→ 432（ZF114）→ **448**（ZF117） |
| 进度（成就） | **35 条**（3 老 + 24 ZF107 + 8 ZF117），一个标签页 | 主项目线（ZF117，已提交） |'''

HAND_JAR_OLD = u'''| **已发布成品** | `release\\PotatoST-0.11.jar` = `90510e18…`（**ZF103 那版**：335 键） | ⚠ **落后 6 轮** |
| 未发布的构建 | `build\\libs\\potato_s_t-0.11.jar` = `11ed01c7…`（4260581 B，ZF112 打的）⚠ 里面**也含第三条线（ZF110）未提交的贴图** —— 打包轮必须重打 | 主项目线 |'''
HAND_JAR_NEW = u'''| **已发布成品** | `release\\PotatoST-0.11.jar` = `303c5d468b96826ef6836b0a4e54ccb8a539557c`（4,298,939 B，**ZF114 打的**：432 键、含 ZF104~ZF114）⚠ `.sha1` 的格式本轮已对账成**纯哈希一行**（§4.92） | ⚠ **不含 ZF116/ZF117** |
| 未发布的构建 | `build\\libs\\potato_s_t-0.11.jar` = `7f0a325002a415a9ee1f0b0a58ce3bc543b389cc`（4,307,139 B，ZF117 打的：448 键 + 35 条进度）⚠ 里面**含 ZF116 尚未提交的三张盔甲贴图** —— 打包轮必须重打 | 主项目线 |'''

HAND_DEBT_OLD = u'''**发布线还欠着**：`ZF104（硬质钛合金/稳定金属块）` + `ZF105/106（盔甲两套 + 盔甲层贴图）` +
`ZF107（27 条进度）` + `ZF108（合金冶炼炉两张贴图 + OBJ 的 UV 复位）` +
`ZF109（采油机 + 运行时改群系）` + `ZF111（星璨钢的合金炉配方：消耗槽第一次放开）`
**一次打包**，作废 `90510e18…`。'''
HAND_DEBT_NEW = u'''**发布线还欠着**：`ZF116（星璨钢胸甲/护腿/靴子三件贴图）` + `ZF117（8 条进度 + 状态文案）`
**一次打包**。⚠ `90510e18…` 已由 ZF114 那次打包作废，现成品是 `303c5d46…`；
下一次打包要作废的是**它**。'''

fails_placeholder = None


def main():
    # ---------- 档案 §5 ----------
    insert_after_prefix(ARCH, u"| ZF114 |", ROW, u"档案 §5 加 ZF117 行")
    # ---------- 档案 §9 ----------
    insert_before_exact(ARCH, u"## 10. 备份策略", SEC9, u"档案 §9 加 ZF117 小节")
    # ---------- 档案 §4 ----------
    insert_before_exact(ARCH, u"## 7. 权威情报来源（怎么查原版行为，别靠记忆）",
                        PITFALLS, u"档案 §4 加 4.90/4.91/4.92")
    # ---------- 交接文档 ----------
    sub_once(HAND, HAND_TABLE_OLD, HAND_TABLE_NEW, u"交接 §1 活体数字表")
    sub_once(HAND, HAND_JAR_OLD, HAND_JAR_NEW, u"交接 §1 成品/构建行")
    sub_once(HAND, HAND_DEBT_OLD, HAND_DEBT_NEW, u"交接 §1 发布欠账段")
    # ---------- 英文公告 ----------
    sub_once(ANN, u"and **27 advancements** walk you from your first machine",
             u"and **35 advancements** walk you from your first machine",
             u"公告 §0 的 27 → 35（第一处）")
    sub_once(ANN, u'One tab ("PotatoS&T"), **27 advancements**, deliberately coarse',
             u'One tab ("PotatoS&T"), **35 advancements**, deliberately coarse',
             u"公告 §7 的 27 → 35")
    raw = read(ANN)
    i = raw.find(u"A New Beginning!        obtain a Micro Crusher")
    j = raw.find(u"```", i)
    if i < 0 or j < 0:
        fails.append(u"公告：找不到那棵树的代码块")
    else:
        write(ANN, raw[:i] + ANN_TREE[4:] + raw[j + 3:])
        if u"Star Steel Suit" in read(ANN):
            notes.append(u"公告 §7 的树补上 8 个新节点")
        else:
            fails.append(u"公告：树没补上")

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
