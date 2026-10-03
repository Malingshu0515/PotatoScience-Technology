# -*- coding: utf-8 -*-
u"""_zf186_docs.py —— ZF186 文档落笔（§4.186 + §5 行 + §9 段 + 交接第 45 条 + 英文公告 +
中英双语公告）+ 哈希三处联动。

主题：配置系统 + 配置界面（零新依赖）。版本线 0.14。
跑法：python build\\zftools\\_zf186_docs.py [--write]
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
BIL = os.path.join(ROOT, "docs", u"0.13_0.14更新公告与介绍_中英.md")
V149 = os.path.join(ROOT, "build", "zftools", u"_zf149_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")

S4 = u"""### 4.186 【配置雷】配置取值三件事：没加载会抛、别缓存、界面不是工厂（0.14 ZF186）

用户原话：「**联动一下配置界面（做成不是必须依赖项）使本mod可以接受配置** 目前我指定的配置项为
黑洞是否为一次性（false则做成只消耗完电力条，不损坏）以及引力装置蓄力时长（默认30s 5-60s可调）
还有单块锂电池容量（1m-20mfe）现在的值为默认值 还想加其它的你自己发挥」。

**① `ConfigValue.get()` 在配置没加载时会抛异常。** NeoForge `ModConfigSpec` 第 1235 行就是
`Preconditions.checkState(loadedConfig != null, "Cannot get config value before config is loaded.")`。
而注册表填充 / 物品栏 / 客户端 tooltip 都可能比配置加载**早** ⇒ 取值器必须
`SPEC.isLoaded() ? v.get() : v.getDefault()`（本工程封成 `b()` / `i()` 两个助手，
门 A2 钉住「代码里 `.get()` 只许出现 2 次，都在这两个助手里」）。

**② 别把配置值缓存进 `static final`。** `GravityDeviceItem.CAPACITY` / `BlackHoleManager.LIFETIME` /
`LithiumBatteryBlockEntity.PER_BLOCK` 这一类常量必须**删掉、改成方法**：配置界面点一下就能改，
`ConfigValue.set()` 在 `restartType == NONE` 时会**立刻**刷新缓存，而我们的 static 常量永远停在
类加载那一刻 ⇒ 现象是「界面改了、物品条/机器不动」（假生效）。探针 B2 量的就是这个：**同一块电池**，
配置一改当场从 4M 变 12M。

**③ `ConfigurationScreen` 不是 `IConfigScreenFactory`。** 它是
`public final class ConfigurationScreen extends OptionsSubScreen` ⇒
`registerExtensionPoint(IConfigScreenFactory.class, ConfigurationScreen::new)` **编译不过**；
要写 lambda `(container, parent) -> new ConfigurationScreen(container, parent)`。注册必须放在
**客户端专用**类里（`value = Dist.CLIENT`），否则服务端也要去加载 GUI 类；
`ModContainer.registerExtensionPoint` 本体只是一句 `Map.put`（javap 核过，没有时机限制）
⇒ 放在 `FMLClientSetupEvent` 那一拍完全安全。

**④ ⚠ `@EventBusSubscriber(bus = ...)` 在 21.1.235 已标记「过时待删」**（编译会出 `[removal]` 警告）。
不写 bus 时 `IModBusEvent` 照样落在 mod 总线上（`PotatoSTClient` 一直这么干）⇒ 新类别抄那个参数。

**⑤ 配置项之间不许有隐式耦合。** 第一版把「视界虚空伤害」写在「吸引生物」的 early-return **后面**
⇒ 关掉「吸引生物」会**顺手把伤害也关掉**。探针 G2 当场抓住（关伤害的 G2a 绿、开伤害的 G2b 红）；
现在两个开关各管各的（门 B5 钉住 `if (!pull && !hurt)` 与 `if (hurt && dist <= VOID_RADIUS …)`）。

**⑥ 判据别被自己的注释误伤。** 门的第一版 A2/A5/B1/B4 一起红，红的是**注释**里写的
`{@code ConfigurationScreen}`、`PER_BLOCK = 4_000_000L`（我在类注释里解释「老常量是什么」）
⇒ 凡「某字面量不该再出现」的判据都要跑在**去注释**的代码体上。反证刀 K5 也栽在同一处：
`value = Dist.CLIENT` 在注释里也有一份 ⇒ 砍掉注解参数、门却不红。

**⑦ 改默认值要连静态文案一起改。** 用户把蓄力从 25 秒改成默认 30 秒，而五语种的
`tooltip.potato_s_t.gravity_device` **根本没写蓄力时长**（只写了一次性 / 8M FE / 副手 / Shift+左键）
⇒ 不是「改数字」而是「补一句」（并说明这些都能在配置里改）；物品 tooltip 里那三行数字改成
**现算**（`appendHoverText`），否则配置一改文案就骗人。

**⑧ 老存档的容量只会「封顶」不会「没收」。** 单块容量调小时，已经充进去的电**不偷偷扣掉**
（`canReceive` 变 false、顶部那一面慢慢放出去即可）；只有多方块重新成型时才按新容量 `Math.min` 封顶。

"""

ROW = u"""| ZF186 | **新建 `zf186_pre`**（**122 份**改前件：6 份将改源码 + `neoforge.mods.toml` + 五份 lang + 四份文档 + `_zf149_verify.py` + `gradle.properties`/`build.gradle` + 旧成品与 `.sha1` + **全部常驻门 101 份**；逐份核 sha1 + 回读，失败 0。⚠ 轮号 `_zf186_*` / §4.186 查过没人占（§4.147）） | **0.14：配置系统 + 配置界面（零新依赖）**（用户原话见 §9）。① 新增 `PotatoSTConfig`（NeoForge `ModConfigSpec`，`COMMON` ⇒ `config/potato_s_t-common.toml`）**11 项**：点名三项 = 黑洞是否一次性（默认 true）/ 引力装置蓄力 **30 秒**（5~60）/ 单块锂电池 **4M FE**（1M~20M）；我加的八项 = 黑洞存活 20s（5~120）、单次搬运上限 1500（100~5000）、扫描半径 40 格（8~80）、吸引生物、视界虚空伤害、引力装置储能 8M（1M~64M）、锂电池每面速率 65536（1024~1048576）、多方块块数上限 800（27~800）。② 配置界面走 NeoForge 自带 `ConfigurationScreen`，注册在**客户端专用**类 `client/PotatoSTConfigScreen`；`neoforge.mods.toml` **一个依赖都没加**（门 A4/D3 与改前逐字节比对）。③ `GravityDeviceItem.CAPACITY`/`CHARGE_TICKS`、`BlackHoleManager.LIFETIME`/`MAX_BLOCKS`/`HALF`、`LithiumBatteryBlockEntity.PER_BLOCK`/`TRANSFER_RATE`/`MAX_BLOCKS` **全部删除**改成现取配置（§4.186②）。④ **真服务端探针 `Zf186Check` 20/0**：同一块电池 4M→12M 当场生效、一次只收 4096 FE、蓄力 5s/60s→100/1200 tick、一次性 true 坏 / false 不坏且电力条抽干、半电开火什么都不发生（反面自证）、寿命 5s 坍缩 / 10s 还在、半径 8 吸不到 15 格外 / 40 吸得到、吸生物与虚空伤害两个开关各自生效。⑤ 门 `_zf186_verify.py` **19/0**、反证刀 **11/11**。⑥ 五语种各补 **34** 键（655→689、lzh 657→691）+ 静态 tooltip 补上蓄力时长。⑦ **重打**：`release\\PotatoST-0.14.jar` = **{size} 字节 / sha1 `{sha}`**（class {cls}；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.186 |
"""

S9 = u"""### ZF186（0.14）本模组现在**有配置了**（配置界面 · 零新依赖）

按你点名做的三件事 + 我自己加的八件，全在**一个文件**里：`config/potato_s_t-common.toml`
（首次启动自动生成；游戏里也能改：**模组列表 → PotatoS&T → 配置**）。

| 段 | 配置项 | 默认 | 可调范围 | 干什么的 |
| --- | --- | --- | --- | --- |
| 黑洞 | `one_shot` **（你点名）** | `true` | 开/关 | **关掉 = 放完只抽干电力条，装置不损坏**（充上电还能再放）；开着 = 老行为（用一次就坏） |
| 黑洞 | `lifetime_seconds` | `20` | 5 ~ 120 | 黑洞活多久 |
| 黑洞 | `max_blocks` | `1500` | 100 ~ 5000 | 一次最多搬多少方块 |
| 黑洞 | `scan_radius_blocks` | `40` | 8 ~ 80 | 扫描半径（格）；默认 40 = 5×5×5 区块 |
| 黑洞 | `pull_entities` | `true` | 开/关 | 吸不吸生物（含玩家） |
| 黑洞 | `void_damage` | `true` | 开/关 | 视界内是否持续吃虚空伤害 |
| 引力装置 | `charge_seconds` **（你点名）** | **`30`** | 5 ~ 60 | 长按右键蓄力多久放黑洞（**注意：老版本是 25 秒，按你说的默认改成 30 秒**） |
| 引力装置 | `capacity_fe` | `8,000,000` | 1M ~ 64M | 装置储能上限 |
| 锂电池 | `per_block_fe` **（你点名）** | **`4,000,000`** | 1M ~ 20M | **单块容量**；多方块总容量 = 块数 × 本值 |
| 锂电池 | `transfer_rate_fe` | `65,536` | 1024 ~ 1,048,576 | 每 tick 每面进出上限 |
| 锂电池 | `max_size_blocks` | `800` | 27 ~ 800 | 一座电池最多拼几块 |

**配置界面不是必须依赖项**：界面用的是 **NeoForge 自带**的 `ConfigurationScreen`，所以
**一个依赖都没加**（`neoforge.mods.toml` 跟上一版逐字节一样，门 A4/D3 钉着）；
装了 Configured / Cloth Config 这类读 `ModConfigSpec` 的模组也读**同一份**配置，不冲突；
不想用界面就直接改 TOML，改完即时生效（不用重启）。

**实测（真服务端，探针 20/0）**：同一块锂电池，配置一改**当场**从 4,000,000 变 12,000,000；
把每面速率改成 4,096 之后，一次要 1,000,000 FE 也只收得进 4,096；蓄力设 5 秒 / 60 秒 = 100 / 1200 tick；
一次性关掉之后装置放完**完好无损**、电力条清零；**只有一半电时开火什么都不会发生**（闸门没被绕过）；
寿命设 5 秒的黑洞跑满 100 tick 就坍缩、设 10 秒的还在；半径 8 时 15 格外的方块一根汗毛没动、半径 40 时被搬走；
「吸引生物」关掉牛一动不动、「虚空伤害」关掉牛站在奇点边上也不掉血。
"""

HAND45 = u"""45. **ZF186 的账（0.14：配置系统 + 配置界面，零新依赖）**：① 用户原话见档案 §9；三条设计决定见 §4.186
    —— **取值器必须 `SPEC.isLoaded()` 兜底**（`ConfigValue.get()` 没加载会抛，ModConfigSpec:1235）、
    **配置值不许缓存进 `static final`**（界面改完即时生效，缓存 = 假生效）、
    **`ConfigurationScreen` 不是 `IConfigScreenFactory`**（要写 lambda，且注册类必须 `Dist.CLIENT`）。
    ② 探针 `Zf186Check` **20/0**（真服务端量行为：4M→12M 当场生效、速率 4096 只收 4096、蓄力 100/1200 tick、
    一次性 true/false 各自表现、半电开火没反应、寿命 5s/10s 对照、半径 8/40 对照、两个开关独立）；
    门 `_zf186_verify.py` **19/0**、反证刀 **11/11**。③ ⚠ **改默认值 25s → 30s 是用户明说的**：
    五份 lang 里那句静态 tooltip **原来根本没写蓄力时长** ⇒ 是「补一句」不是「改数字」；
    物品 tooltip 的三行数字改成 `appendHoverText` **现算**，否则配置一改文案就骗人。
    ④ ⚠ **判据别被注释误伤**：门的 A2/A5/B1/B4 第一版全红，红在**类注释**里提到的
    `{@code ConfigurationScreen}` / `PER_BLOCK = 4_000_000L` ⇒ 「字面量不该再出现」类判据要跑在去注释的代码体上
    （反证刀 K5 同一坑）。⑤ 老存档容量**只会封顶不会没收**（调小不偷偷扣电，重新成型时才 `Math.min`）。
"""


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


BIL_ZH = u"""
**0.14 追加：整个模组现在可配置（配置界面 · 零新依赖）。**

- **一个文件管全部**：`config/potato_s_t-common.toml`（首次启动生成）。游戏里也能改 ——
  **模组列表 → PotatoS&T → 配置**（NeoForge 自带界面，五语种都有翻译）。
- **你点名的三项**：① **黑洞是否一次性**（默认开）：关掉之后放完黑洞**只抽干电力条、装置不损坏**；
  ② **引力装置蓄力时长**：默认 **30 秒**（5~60 可调，**老版本是 25 秒**）；
  ③ **单块锂电池容量**：默认 **4,000,000 FE**（1M~20M 可调，多方块总容量 = 块数 × 本值）。
- **另外 8 项**（我加的）：黑洞存活 20 秒 / 一次最多搬 1500 块 / 扫描半径 40 格 / 是否吸生物 /
  视界是否虚空伤害；引力装置储能 8M FE；锂电池每面速率 65,536 FE/t、一座最多 800 块。
- **不是必须依赖项**：配置界面用的是 NeoForge 自带的，`neoforge.mods.toml` 依赖清单与上一版
  **一字不差**；装了 Configured / Cloth Config 之类也读同一份配置，不装照样能改。
- 改完**即时生效**（不用重启）：实测同一块电池 4M→12M 当场变，蓄力 5 秒 = 100 tick。
"""

BIL_EN = u"""
**0.14 addition: the whole mod is configurable now (with an in-game screen and zero new dependencies).**

- **One file for everything:** `config/potato_s_t-common.toml` (created on first launch). You can also
  edit it in game via **Mods -> PotatoS&T -> Config** (NeoForge's built-in screen, translated into all
  five languages the mod ships).
- **The three you asked for:** (1) **one-shot black hole** (default on) - turn it off and firing only
  drains the energy bar, the device survives; (2) **gravity device charge-up time** - default **30 s**
  (5-60 s; the old version was 25 s); (3) **lithium battery capacity per block** - default
  **4,000,000 FE** (1M-20M; total = blocks x this value).
- **Eight more (my pick):** black hole lifetime 20 s / 1500 blocks per hole / 40-block scan radius /
  pull entities / void damage; gravity device buffer 8M FE; battery transfer rate 65,536 FE/t and
  800 blocks per multiblock.
- **Not a required dependency:** the screen is NeoForge's own, and the dependency list in
  `neoforge.mods.toml` is byte-identical to the previous release. Configured / Cloth Config read the
  same spec if you have them; if you do not, editing the TOML still works.
- **Applies live** (no restart): a battery block went 4M -> 12M the moment the value changed, and a
  5 s charge-up is 100 ticks.
"""


def main(argv):
    write = u"--write" in argv
    size, h = os.path.getsize(JAR), sha(JAR)
    z = zipfile.ZipFile(JAR)
    names = z.namelist()
    cls = len([n for n in names if n.endswith(u".class")])
    recipes = len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")])
    adv = len([n for n in names if n.startswith(u"data/potato_s_t/advancement/") and n.endswith(u".json")])
    keys_zh = len(json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))
    keys_lzh = len(json.loads(z.read(u"assets/potato_s_t/lang/lzh.json").decode("utf-8")))
    z.close()
    print(u"成品：%d 字节 / sha1 %s / class %d / 配方 %d / 进度 %d / 键 %d+%d"
          % (size, h, cls, recipes, adv, keys_zh, keys_lzh))

    v149 = read(V149)
    m = re.search(u'WANT_SHA = u?"([0-9a-f]{40})"', v149)
    old_sha = m.group(1) if m else u""
    m = re.search(u"WANT_SIZE = (\\d+)", v149)
    old_size = u"{:,}".format(int(m.group(1))) if m else u""
    fails = []

    def refresh(text):
        if old_sha:
            text = text.replace(old_sha, h)
        if old_size:
            for unit in (u" 字节", u" bytes", u" B"):
                text = text.replace(old_size + unit, u"{:,}{}".format(size, unit))
        text = re.sub(u"\\*\\*\\d+ classes, \\d+ advancements, \\d+ recipes\\*\\*",
                      u"**%d classes, %d advancements, %d recipes**" % (cls, adv, recipes), text)
        text = re.sub(u"\\*\\*(\\d+) 键 × 4\\*\\*", u"**%d 键 × 4**" % keys_zh, text)
        return text

    doc = read(DOC)
    if u"### 4.186 " not in doc:
        a = u"| ZF147 |"
        if doc.count(a) != 1:
            fails.append(u"档案 §5 表头锚点 %d 次" % doc.count(a))
        else:
            doc = doc.replace(a, S4 + a, 1)
    if u"| ZF186 |" not in doc:
        a2 = u"（阶段一改文件、阶段二读新成品跟平文档）。 | 见 §9 ｜ 见 §4.150 |\n"
        if doc.count(a2) != 1:
            fails.append(u"档案 ZF181 行尾锚点 %d 次" % doc.count(a2))
        else:
            row = ROW.replace(u"{size}", u"{:,}".format(size)).replace(u"{sha}", h).replace(u"{cls}", str(cls))
            doc = doc.replace(a2, a2 + row + u"\n", 1)
    if u"### ZF186（0.14）" not in doc:
        a3 = u"## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案 §10 锚点 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, S9 + u"\n" + a3, 1)
    doc = refresh(doc)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"45. **ZF186 的账" not in hand:
        a4 = u"## 7. ZF146 这一轮的交接"
        if hand.count(a4) != 1:
            fails.append(u"交接 §7 锚点 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, HAND45 + u"\n" + a4, 1)
    hand = refresh(hand)
    if write and not fails:
        io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)

    vn = re.sub(u'WANT_SHA = u?"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, v149, count=1)
    vn = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, vn, count=1)
    # ⚠ C7 跟平：`_zf149_verify.py` 里那条「公告 Download 段**整句**」的靶子是**写死**的字符串
    #   （上一轮是 `**408 classes, 43 advancements, 114 recipes**`）。本轮 class 408→410、
    #   进度 43→46（别的线加的），公告那句由 refresh() 改了 ⇒ 靶子必须跟着改，否则门必红、
    #   而且红的是**判据**不是公告。判据强度不动：仍是「逐字比那一整句」。
    vn = re.sub(u"\\*\\*\\d+ classes, \\d+ advancements, \\d+ recipes\\*\\*",
                u"**%d classes, %d advancements, %d recipes**" % (cls, adv, recipes), vn)
    vn = re.sub(u"跟到 \\d+ / \\d+", u"跟到 %d / %d" % (cls, recipes), vn)
    if vn == v149:
        if (u'WANT_SHA = u"%s"' % h) in v149:
            print(u"  （_zf149_verify.py 的靶子已经就是这份成品，跳过）")
        else:
            fails.append(u"_zf149_verify.py：靶子没换到")
    elif write and not fails:
        io.open(V149, "w", encoding="utf-8", newline=u"").write(vn)

    ann = read(ANN)
    if u"## New in 0.14 ZF186" not in ann:
        a5 = u"## New in 0.14 ZF184 - The ground slam now scales with your real attack damage"
        if ann.count(a5) != 1:
            fails.append(u"公告 ZF184 段锚点 %d 次" % ann.count(a5))
        else:
            block = (u"## New in 0.14 ZF186 - Config support: an in-game config screen with zero new dependencies\n\n"
                     u"- **The mod is configurable now.** One `config/potato_s_t-common.toml` (created on\n"
                     u"  first launch) holds **11 options**, and the mod list screen gets a **Config** button\n"
                     u"  that opens an auto-generated GUI (NeoForge's built-in `ConfigurationScreen`),\n"
                     u"  translated into all five languages the mod ships.\n"
                     u"- **Not a required dependency:** the dependency list in `neoforge.mods.toml` is\n"
                     u"  byte-identical to the previous release. Configured / Cloth Config read the same\n"
                     u"  config spec if you have them; if you do not, the built-in screen and plain TOML both work.\n"
                     u"- The three options you asked for:\n"
                     u"  - **One-shot black hole** (default on): turn it off and firing only drains the energy\n"
                     u"    bar - the device survives, so you can recharge it and fire again.\n"
                     u"  - **Gravity device charge-up time** (default **30 s**, adjustable 5-60 s).\n"
                     u"  - **Lithium battery capacity per block** (default **4,000,000 FE**, adjustable\n"
                     u"    1,000,000-20,000,000 FE).\n"
                     u"- Eight more options in the same file: black hole lifetime (20 s), blocks moved per\n"
                     u"  hole (1500), scan radius (40 blocks), pull entities, void damage at the horizon,\n"
                     u"  gravity device energy buffer (8M FE), battery transfer rate per side (65,536 FE/t)\n"
                     u"  and max blocks per battery multiblock (800).\n"
                     u"- Measured on a real server: a battery block goes 4M -> 12M FE the moment the value\n"
                     u"  changes, a 1,000,000 FE request only pulls in the configured 4,096 FE rate, 5 s / 60 s\n"
                     u"  charge-up becomes 100 / 1200 ticks, a one-shot device breaks while a reusable one\n"
                     u"  keeps working with the energy bar drained, a 5 s black hole collapses after 100 ticks\n"
                     u"  while a 10 s one is still eating, an 8-block scan radius leaves a block 15 blocks away\n"
                     u"  alone while a 40-block radius moves it, and the two entity switches (pull / void\n"
                     u"  damage) work independently.\n"
                     u"- **Download:** `release/PotatoST-0.14.jar` - **{size} bytes**, sha1 **`{sha}`**.\n\n"
                     ).format(size=u"{:,}".format(size), sha=h)
            ann = ann.replace(a5, block + a5, 1)
    ann = refresh(ann)
    if write and not fails:
        io.open(ANN, "w", encoding="utf-8", newline=u"").write(ann)

    bil = read(BIL)
    if u"0.14 追加：整个模组现在可配置" not in bil:
        az = u"亡灵杀手 V 打僵尸 25.09 / 打牛 13.0（= 无附魔）；锋利 V 打牛 16.0。\n"
        ae = u"  enchantment); Sharpness V 16.0 on a cow.\n"
        if bil.count(az) != 1 or bil.count(ae) != 1:
            fails.append(u"双语公告锚点 zh=%d en=%d" % (bil.count(az), bil.count(ae)))
        else:
            bil = bil.replace(az, az + BIL_ZH, 1)
            bil = bil.replace(ae, ae + BIL_EN, 1)
    bil = refresh(bil)
    if write and not fails:
        io.open(BIL, "w", encoding="utf-8", newline=u"").write(bil)

    print(u"模式：%s ｜ 失败 = %d" % (u"落盘" if write else u"干跑", len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
