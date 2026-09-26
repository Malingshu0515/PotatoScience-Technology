# -*- coding: utf-8 -*-
r'''_zf141_docs.py —— ZF141 的文档 / 凭据落盘（纯插入 + 定点替换；锚点唯一性先验）

碰五处：
  A `docs\开发档案.md`
      A1 §5 表加 `| ZF141 |`（锚点 = ZF140 那一行，插在它**之后**）
      A2 §4 加 §4.139~§4.145 七条（锚点 = `## 7.`，插在它**之前**）
      A3 §9 加 ZF141 小节（锚点 = `## 10.`，插在它**之前**）
  B `docs\多会话协作交接.md`：§1 三行活体数字 + §6 加第 23 / 24 条
  C `docs\UpdateAnnouncement_EN.md`：末尾补一条英文条目
  D `build\用户素材\_来源凭据.json`：登记四张素材（三新 + 斧子换的那张）

⚠ §4.6：每个锚点**必须恰好命中一次**，否则当场停手、一个字节都不写。
⚠ §4.8：换行风格照原文件（这几份都是 LF）。
⚠ 本文件里凡是含 ASCII 双引号的整段文案，一律用 **三单引号** 包住 ——
   这条是被自己咬出来的：上一版把中文说明写在 u"..." 里，中间夹了 ASCII 引号 ⇒ 语法错
   （与 §4.53 那条同源：中文字符串里引用别人的话用「」）。

跑法：
    python build\zftools\_zf141_docs.py            # 只算不写
    python build\zftools\_zf141_docs.py --write
'''
import glob
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

fails, notes, plan = [], [], []


def read(p):
    return io.open(p, encoding="utf-8", newline="").read()


def insert_after(text, anchor, block, label):
    if text.count(anchor) != 1:
        fails.append(u"%s：锚点命中 %d 次（应为 1）" % (label, text.count(anchor)))
        return text
    notes.append(u"  [插] " + label)
    return text.replace(anchor, anchor + block, 1)


def insert_before(text, anchor, block, label):
    if text.count(anchor) != 1:
        fails.append(u"%s：锚点命中 %d 次（应为 1）" % (label, text.count(anchor)))
        return text
    notes.append(u"  [插] " + label)
    return text.replace(anchor, block + anchor, 1)


def replace_once(text, old, new, label):
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

# ==================================================================== A1
ROW = u'''| ZF141 | **新建 `zf141_pre`**（**137 份**改前件：`ModTiers` / `ModItems` / `PotatoST`（探针挂载点）/ **被顶掉的斧子贴图** / 四份 lang / 凭据 / 四份文档 / 门清单与计数器 / **全部 `_zf*_verify/_check/_chain/_falsify` 常驻门**；逐份核哈希 + 回读，137/137 一致、失败 0） | 0.11：**星璨钢工具补齐**（用户原话见 §9）。① **剑 / 镐 / 锄与斧子共用同一档位**：耐久 **1192** / 挖掘速度 **9.0** / 伤害加成 **8.0** / **挖掘等级钻石**（`INCORRECT_FOR_DIAMOND_TOOL`）/ 附魔权重 **22**，探针里三份 `getTier()` 是**同一个对象**；② 伤害按「剑和斧子差不多、其他略低」：**剑 16.0**（1.6 次/秒）、**镐 13.0**（1.2）、**锄 12.0**（1.0），**斧子 17.0（0.9）一个字没动**；③ 技能「**与夜同频**」＝夜晚（主世界 `dayTime%24000 ∈ [13000,23000)`）**采掘与攻击都不消耗耐久**，判据**转调**斧子那个 `isNight`（不复制第二份）；④ ⚠ **剑的采掘磨损是 2 点**（1.21.1 的 `Item.mineBlock` 读 `DataComponents.TOOL`，剑的 `damagePerBlock = 2`）⇒ 白天一律走 `super.mineBlock`，**没有**照抄斧子那三行硬编码 `hurtAndBreak(1)`（照抄会把剑从 2 悄悄改成 1）；⑤ 锄的攻速**有意偏离原版**（原版锄那套刻度配上 8.0 的档位加成会得到 24 DPS 的最强武器）⇒ 取 `-3.0F`（1.0 次/秒）；⑥ 配方 = **原版图纸只换材料**（探针在**真合成网格**里摆了一遍，并用「同图纸换原版钻石 ⇒ 出原版钻石工具」做正对照）；⑦ 斧子贴图换成用户新给的 `星璨钢斧子新贴图.png`（旧素材 `星璨钢斧.png` 已被用户删掉）⇒ 顺手把 `_zf133_verify.py` 那条**已经静默跳过**的贴图判据挪回新素材、判据重新生效；⑧ 四语言 **483 → 487** 键 ⇒ **32 份**门跟平（含 `_zf139_verify.py` 与 `_zf117_verify.py`） | 见 §9 ｜ 见 §4.139~§4.145 |
'''

# ==================================================================== A2
SEC4 = u'''> 下面 4.139~4.145 是 ZF141（星璨钢工具补齐）这一轮换来的：四条属于「**印象与源码不符**」，
> 一条是「**加东西时怎么不复制实现**」，一条是「**改已在用产物**」的流程，一条是**如实记账**。

### 4.139 【陷阱】1.21.1 的 `mineBlock` 写在 **`Item`** 上、读 **`DataComponents.TOOL`** —— 「抄斧子那三行」会把剑的 2 点改成 1 点（0.11 ZF141）

本轮要给三把新工具加「夜晚不消耗耐久」，最省事的写法是**把斧子 ZF133 那三行照抄**：

```java
if (!level.isClientSide && isNight(level)) { return true; }
if (state.getDestroySpeed(level, pos) != 0.0F) { stack.hurtAndBreak(1, entity, EquipmentSlot.MAINHAND); }
return true;
```

**这写法对斧子是对的，对剑是错的。** 从 `sources.jar` 现抠出来的事实（`Item.java:230`）：

```java
public boolean mineBlock(ItemStack stack, Level level, BlockState state, BlockPos pos, LivingEntity miningEntity) {
    Tool tool = stack.get(DataComponents.TOOL);
    if (tool == null) return false;                       // ← 没有组件 ⇒ 返回 false、一点都不扣
    if (!level.isClientSide && state.getDestroySpeed(level, pos) != 0.0F && tool.damagePerBlock() > 0)
        stack.hurtAndBreak(tool.damagePerBlock(), ...);   // ← 扣多少由**组件**说了算
    return true;
}
```

`damagePerBlock` 是**每件工具自己带的**：`SwordItem.createToolProperties()` 最后那个参数就是 **2**
（`new Tool(List.of(...), 1.0F, 2)`），`DiggerItem` 走 `tier.createToolProperties(blocks)` 是 **1**。
⇒ 硬编码 `hurtAndBreak(1)` 会把剑的采掘磨损**减半**，还顺手抹掉「没有 TOOL 组件」那条分支。

**正确写法**：白天 `return super.mineBlock(...)`（原样，含 `damagePerBlock` 与 null 分支），
只有夜晚那一支自己给返回值（同口径：`stack.get(DataComponents.TOOL) != null`）。
探针把这条钉死了：四件工具的 `damagePerBlock` 实测 **2 / 1 / 1 / 1**，白天采掘实测掉 **2 / 1 / 1 / 1**。

⚠ 同源一条：`SwordItem extends TieredItem`（**不**经 `DiggerItem`），而 `mineBlock` / `postHurtEnemy`
两个耐久入口都定义在 `Item` 上 ⇒ 四个子类各自 `@Override` 都生效，`super.xxx()` 也都落到 `Item` 那一份。
顺带记下**攻击磨损**：`SwordItem.postHurtEnemy` 扣 **1**、`DiggerItem.postHurtEnemy` 扣 **2**。

### 4.140 【陷阱】`LivingEntity.detectEquipmentUpdates()` 是 **private** —— 公开入口是 `ServerPlayer.doTick()`（0.11 ZF141）

探针要在真服务端上读「换了主手物品之后玩家的攻击力/攻速」，第一版直接写：

```java
p.setItemSlot(EquipmentSlot.MAINHAND, stack);
p.detectEquipmentUpdates();     // ← 编译不过：找不到符号
```

现查 `sources.jar`：`detectEquipmentUpdates()` 是 **private**（`LivingEntity.java:2581`），
只在 `LivingEntity.tick()` 里被调（`:2482`）。公开入口是 **`ServerPlayer.doTick()`**
（`ServerPlayer.java:568`，public；`ServerPlayer.tick()` 不调 `super.tick()`，真玩家逻辑全在 `doTick` 里 —— §4.127）。
⇒ 换成 `p.doTick();` 即可。**与 ZF139 同一个结论，这次是从编译期又撞了一遍** ——
凡是「改了装备却读不到新属性」，第一反应就该是「那一 tick 还没跑」。

### 4.141 【陷阱】服务端的 `getResourceManager()` **只查 `data/`** —— 想核 `assets/**` 走类路径（0.11 ZF141）

探针想证「四语言的新键真的进了构建产物」，第一版写：

```java
server.getResourceManager().getResource(ResourceLocation.fromNamespaceAndPath(NS, "lang/en_us.json"))
```

**永远 `Optional.empty()`**，可同一份探针里 `Component.translatable("item.potato_s_t.star_steel_sword").getString()`
却能正常翻译出来 —— 两条判据互相打架，说明「取不到」不是文件缺失。
根因：服务端那个 ResourceManager 是按 **`PackType.SERVER_DATA`** 建的（该类型的目录是 `data`），
`assets/` **根本不在这棵树里**。⇒ 核 `assets/**` 用**类路径**：

```java
Zf141Check.class.getResourceAsStream("/assets/potato_s_t/lang/en_us.json")
```

还多一层好处：类路径里那份是**过了 `processResources` 的产物**，比「源目录里有」更强
（源文件在、构建没带上，照样是坏）。

### 4.142 【陷阱】急迫（Haste）给 **+10% 攻击速度** —— 量「装备裸值」前先清效果，而且**清完不能再 tick**（0.11 ZF141）

探针读「装备本身的攻速」时假红两条：**斧子读到 0.99（期望 0.9）、空手读到 4.4（期望 4.0）**。
`0.9 × 1.1 = 0.99`、`4.0 × 1.1 = 4.4` —— 一个 **×1.1** 的乘子；而剑/镐/锄三条都是精确值。
为什么**只有斧子**中招？因为斧子自带技能：**手持就续 1 秒急迫 I**
（`StarSteelAxeItem.applyHoldEffect`，挂 `PlayerTickEvent.Post`），而原版**急迫每级附加 +10% 攻击速度**
（药水效果自带 `ADD_MULTIPLIED_TOTAL 0.1` 的属性修饰符）。第 5 次读「空手」时那 20 tick 的急迫还没到期 ⇒ 4.4。

修的时候又踩了第二层，而且**只差一次调用**：

```java
p.doTick();             // ① 装备属性进表（顺带挂上急迫）
p.removeAllEffects();   // ② 清掉急迫
p.doTick();             // ③ ← 这次 tick 里 applyHoldEffect **又**把急迫挂回来了（手还拿着斧子）
```

⇒ 还是 0.99。**正确顺序**是「tick 一次让装备属性进表 → 清效果 → **直接读**」：
装备修饰符是第 ① 步挂上去的，清效果不会动它；急迫那 +10% 会随效果一起消失。

⚠ 方法论：探针里「读装备裸值」必须先把身上会改属性的效果清干净，否则测的是「装备 + 当前药水」。
本轮顺手把这个假红变成了**正向判据**：手持斧子 tick 一下 ⇒ 断言拿到急迫 I **且**攻速被顶到 0.99
（一条判据同时证了 ZF133 的技能没被碰坏）。

### 4.143 【方法论】给已有档位加「共用的那一档」：**加参数**，不复制匿名类（0.11 ZF141）

三把新工具要共用一个档位，而它与斧子那一档**只差一个字段**（修理材料：斧子走共用的轻质钛合金，
新的走星璨钢锭）。直觉写法是再复制一份匿名 `Tier` —— 但 `_zf133_verify.py` 的 A4 判据盯着
`tiers.count("public int getUses()") == 1`（**全文件只准有一份匿名 Tier**），当场就会被顶红。
⇒ 给 `build(...)` **加第六个参数**（`Supplier<Ingredient> repairIngredient`），旧的五参重载转调它、
默认仍是 `ModTiers::repair` ⇒ **钛合金那两把的字节级行为一个都没变**（探针实测五个字段全同）。

**这也说明「判据写在对的地方」值钱**：那条 A4 不是好看，它是**结构约束** ——
在「想偷懒复制一份」的时候先把人拦下来。

### 4.144 【流程雷】「换贴图」是**改已在用产物**：动手前先核「要顶掉的那张 == 上一轮上线的那张」（0.11 ZF141）

用户这次的素材里有一张 `星璨钢斧子新贴图.png` —— 它不是新物品的图，是**给已有斧子换皮**。
这类改动有两条与「新增一张图」不同的风险：

1. **拿错图**：顶掉的若是别的东西的贴图，游戏里会莫名其妙变样 ⇒ 脚本先算盘上那张的 sha1，
   与上一轮上线的（ZF133 的 `8f5de358857e…`）**对上才动手**，对不上就停；
2. **旧素材被删**：用户已经把 `星璨钢斧.png` 从素材区删掉 ⇒ 原来那条「在用贴图 == 用户素材（逐字节）」
   的判据变成 `if os.path.isfile(src)` 不成立 ⇒ **D2~D5 一条都不跑，「绿」是空的**。
   本轮把靶子改指新素材，判据重新生效。

⚠ **「条件为假就跳过」的判据会静默失效**：凡是写了 `if 文件在:` 才断言，就必须配一条
「文件必须在」的前置断言（本轮补的就是它）。

### 4.145 【证据雷】归档的探针源码必须与它产出的报告**自洽**（TAG / 类名 / 报告路径）—— ZF139 那份对不上（0.11 ZF141 发现）

本轮开工时顺手核了上一轮的归档件：

| 件 | 里面写的是 |
|---|---|
| `build\\zftools\\check\\Zf139Check.java`（已提交） | `public final class Zf138Check` / `TAG = "[A138] "` / `REPORT_PATH = …_zf138_probe_utf8.txt` |
| `build\\zftools\\_zf139_probe_utf8.txt`（它产出的报告） | 通篇 `[A139] ` |

也就是说**归档的那份源码与它产出的报告不是同一版**（起因是那轮中途改过轮号，改名脚本只扫了 `_zf139_*`，
`check\` 下那份没跟着走）。**本轮不伪造、不改写历史**：那份留原样，另立本条 + 交接 §6 第 24 条如实记着；
同时给**本轮的**卸载脚本加一条自检 —— 归档时断言「归档件的 TAG / 类名 / 报告路径」与报告里实际出现的
TAG 一致，不一致就报错。

**通用规矩**：归档步骤要有「归档物与产物自洽」的断言，不能只看「文件存在」。

'''

# ==================================================================== A3
SEC9 = u'''### ZF141（0.11）星璨钢工具补齐（剑 / 镐 / 锄 + 斧子换贴图）—— **待你实测**

用户原话：「还有几个星璨钢的工具你自己写一下呗（耐久 挖掘等级 技能...）剑和斧子差不多强度
其他的略低（要不要技能都无所谓）你参考一下斧子和星璨钢套 你随便搞 配方就是原版工具一样
（原材料换成星璨钢）谢谢了宝宝」+「贴图在用户素材 刚才忘说了」。

素材区当时有四张跟本轮有关的图。**先把「这张图画的是什么」钉死再动手**（判据是形状，不是文件名）：
把每张的 alpha 掩码与**原版六档 × 五种工具**的 30 张图逐个算 IoU（`_zf141_recon.txt` ①）：

| 素材 | 非空像素 | 最像的原版 | IoU | 与文件名推断 |
|---|---|---|---|---|
| `星璨钢剑.png` | 98 | `*_sword`（六档同形） | **0.857** | 剑 ✓ |
| `星镐子_001.png` | 80 | `*_pickaxe` | **0.682** | 镐 ✓ |
| `星锄子_001.png` | 51 | `*_hoe` | **0.962** | 锄 ✓ |
| `星璨钢斧子新贴图.png` | 62 | `*_axe` | **0.968** | 斧（**换皮**）✓ |

#### 一、四个数怎么定的

| 工具 | 显示伤害 | 攻速 | DPS | 依据 |
|---|---|---|---|---|
| 斧（ZF133） | **17.0** | 0.9 | 15.3 | 你给的档位 —— **本轮一个字没动** |
| **剑** | **16.0** | 1.6 | 25.6 | 「剑和斧子差不多强度」⇒ **每击只差 1 点**；挥得快是原版剑/斧本来的关系（原版钻石剑 7@1.6 对钻石斧 9@1.0） |
| **镐** | **13.0** | 1.2 | 15.6 | 「其他的略低」 |
| **锄** | **12.0** | 1.0 | 12.0 | 同上，三把里最低 |

档位（三把新工具**共用同一个对象**，探针里 `==` 成立）：**耐久 1192 / 挖掘速度 9.0 / 伤害加成 8.0 /
挖掘等级钻石 / 附魔权重 22** —— 与斧子那一档**逐字相同**（这是「参考斧子」最直白的读法）。
对照：原版钻石档是 1561 / 8.0 / 3.0 / 钻石 / 10。

#### 二、技能：「与夜同频」（夜晚采掘与攻击都不磨损）

跟斧子**同一条判据**（转调 `StarSteelAxeItem.isNight`，没有第二份实现）：主世界 `dayTime % 24000`
落在 `[13000, 23000)` 时 —— **采掘与攻击都不消耗耐久**。为什么两个入口都要覆写、为什么白天不能用
斧子那种「硬编码扣 1」的写法，见 §4.139（**剑的 `damagePerBlock` 是 2**）。

#### 三、⚠ 我替你定的六件事（都是你没说的；改都是一处）

1. **三把统一 1192 耐久 / 钻石级 / 附魔 22** —— 「参考斧子」+ 原版「一个材料一个档」的读法。
2. **技能选了「夜晚不磨损」**（你说「要不要技能都无所谓」）—— 它就是斧子已有的那条，三把共用一句说明。
   **没做**的是斧子另外两条（手持急迫 I、Shift 右键冲击波）：想让**镐**也带手持急迫，
   只是把 `StarSteelAxeItem.applyHoldEffect` 里那个 `instanceof` 放宽一行，说一声就加。
3. **锄地（右键开地）那一下照原版扣 1 点耐久**，没管 —— 它走 `HoeItem.useOn` 里独立的一次
   `hurtAndBreak`，要覆盖就得把原版那段「查 `toolModifiedState` + `Predicate`/`Consumer`」整段抄一遍，
   抄错的风险大于收益。说明文案写的是「采掘与攻击」，**与实际一致、没有多吹**。
4. **锄的攻速取 1.0 次/秒**（`-3.0F`），**不是**原版钻石锄的 4.0 次/秒 —— 原版那套刻度靠「参数随档位
   一路变负」把总伤害钉在 1，配上本档位 8.0 的加成会得到 **6 伤害 × 4 次/秒 = 24 DPS 的全模组最强武器**，
   与「其他的略低」直接矛盾。
5. **没有做铲子** —— 你给的四张图是剑 / 镐 / 锄 / 斧，**没有锹**。要的话给张图，我补上
   （配方照原版锹：1 锭 + 2 棍）。
6. **斧子那张按「给现有斧子换皮」理解**（文件名就是「斧子新贴图」，而且旧素材 `星璨钢斧.png`
   已经被你从素材区删掉了）。若你本意是「再做一把新斧子」，说一声我改回来 ——
   旧图在 `zf141_pre` 里有逐字节备份（`8f5de358857e…`）。

#### 四、证据

| 项 | 值 |
|---|---|
| 配方 | 三条 shaped，**图纸与原版逐格相同**（剑 `X/X/#`、镐 `XXX/ # / # `、锄 `XX/ #/ #`），只把材料换成星璨钢锭 ⇒ 盘上配方 69 → **72** 份（`crafting_shaped` 59 → **62**） |
| 探针 | `_zf141_probe_utf8.txt` **70 项全绿**：档位五字段与斧子逐字相同 / 三份 `getTier()` 同一对象 / 属性实测 16·1.6、13·1.2、12·1.0、斧 17·0.9、空手 1·4.0 / 黑曜石与古代残骸挖得动（对照石镐挖不动）/ 修理材料只认星璨钢锭（斧子两者都认）/ **夜晚采掘与攻击四件全 0，白天采掘 2·1·1·1、白天攻击 1·2·2·2** / **真合成网格**三条出我们的、同图纸换钻石出原版的三把 / 类路径里四语言键值与 487 键 / 顺手复核 ZF133 的手持急迫（攻速被顶到 0.99） |
| 常驻校验 | `_zf141_verify.py`（项数与失败数见它自己的输出） |
| 反证刀 | `_zf141_falsify.py`（刀数与咬住数见它自己的输出） |
| 活体数字 | 四语言 **483 → 487** 键；配方 **69 → 72**（shaped **59 → 62**）；Java **+4**（`StarSteelTools` + 三个物品类）；资源 **+10**（3 配方 + 3 模型 + 4 贴图） |
| 门 | `_zf104_gates.ps1` 加两段；32 份常驻门跟平键数（含上一轮的 `_zf139_verify.py` 与 `_zf117_verify.py`）；`_zf133_verify.py` 的贴图靶子换到新素材 |
| 未打包 | ⚠ **本轮没有重新打包** `release\\PotatoST-0.11.jar`（用户没要求）⇒ 成品仍是旧的那份、`RELEASE_KEYS = 482` 不用动；下次打包的人要把成品哈希与键数一起对账 |

#### 五、要你实测

1. 工作台照原版摆法摆：**剑** 竖着 2 锭 + 1 棍；**镐** 上排 3 锭 + 中间竖 2 棍；**锄** 上排 2 锭 + 右列竖 2 棍
   ⇒ 各出一把（三条都是原版图纸，只是材料换成星璨钢锭）；
2. 拿剑/镐/锄按 **Shift** 看说明：三把都应写「夜晚采掘与攻击不消耗耐久。1192 耐久，挖掘等级钻石」；
3. **白天**挖方块 / 砍怪 ⇒ 耐久照掉（砍方块：剑 **2**、镐锄 1；打怪：剑 1、镐锄 **2**）；
   **夜里**同样操作 ⇒ **一点不掉**（主世界 13000~23000；下界 / 末地不属于这条，那边照常磨损）；
4. 镐挖**黑曜石 / 古代残骸**应当挖得动（钻石级）；耐久上限应是 **1192**；
5. 铁砧上修：**星璨钢锭**能修三把新的（斧子仍是「星璨钢锭与轻质钛合金都能修」，那是它的老写法）；
6. 斧子的贴图应换成你新给的那张（旧的那张已逐字节备份）。

'''

# ==================================================================== B
def patch_hand(text):
    text = replace_once(
        text,
        u"| 语言键数 | **483 键 × 4**（zh_cn / en_us / ja_jp / ru_ru，四份键集合必须完全一致） | "
        u"键数的活体数字：… → 448（ZF117）→ 449（ZF119 振金锭）→ **454**（ZF120 振金套 +5）"
        u"→ **464**（ZF122 星仪图之章 +10）→ **476**（ZF125 大型柴油发电机 +12）"
        u"→ **478**（ZF127 银线 / 银线轴 +2）→ **482**（ZF133 星璨钢斧 +4）"
        u"→ **483**（ZF139 振金套：死亡文案 +1）。",
        u"| 语言键数 | **487 键 × 4**（zh_cn / en_us / ja_jp / ru_ru，四份键集合必须完全一致） | "
        u"键数的活体数字：… → 448（ZF117）→ 449（ZF119 振金锭）→ **454**（ZF120 振金套 +5）"
        u"→ **464**（ZF122 星仪图之章 +10）→ **476**（ZF125 大型柴油发电机 +12）"
        u"→ **478**（ZF127 银线 / 银线轴 +2）→ **482**（ZF133 星璨钢斧 +4）"
        u"→ **483**（ZF139 振金套：死亡文案 +1）→ **487**（ZF141 星璨钢剑/镐/锄："
        u"三件工具名 + 一句共用的技能说明 +4）。",
        u"交接 §1：键数 483 → 487 + 链条补一环")

    text = replace_once(
        text,
        u"| 配方 | `data\\potato_s_t\\recipe\\` **69 份**（其中 `crafting_shaped` **59** 条）；"
        u"生成器表 `_zf45_recipes.py` 定形 **34** 条 + 锻造台 **4** 条 |",
        u"| 配方 | `data\\potato_s_t\\recipe\\` **72 份**（其中 `crafting_shaped` **62** 条）；"
        u"生成器表 `_zf45_recipes.py` 定形 **34** 条 + 锻造台 **4** 条；"
        u"⚠ ZF141 那三条（星璨钢剑/镐/锄）**只写了 JSON、没进那张表**，"
        u"谁下次重跑生成器先看 §6 第 23 条 |",
        u"交接 §1：配方 69 → 72")

    text = replace_once(
        text,
        u"| Java / 资源 | **156** 个 java / **642** 个资源文件 | — |",
        u"| Java / 资源 | **%d** 个 java（不含临时探针）/ **%d** 个资源文件 | — |"
        % (L["java"], L["res"]),
        u"交接 §1：Java/资源计数跟到现数（%d / %d）" % (L["java"], L["res"]))

    text = insert_after(
        text,
        u"    ⑤ 这条已立成 §4.132（**§4.111 的重演**）：改名**只对自己点名的清单**动手，"
        u"不许用 `*zfNNN*` 通配扫目录。\n",
        u"""
23. **ZF141 的账（星璨钢工具补齐）**：① 用户原话见档案 §9。做的是**剑 / 镐 / 锄**三把新工具
    + **斧子换贴图**（素材 `星璨钢斧子新贴图.png` 顶掉 `star_steel_axe.png`；旧图 sha1 `8f5de358857e…`
    在 `zf141_pre` 里有逐字节备份）。② 三把与斧子**共用同一档位**（1192 / 9.0 / 8.0 / 钻石 / 22），
    伤害 **16 / 13 / 12**（斧子 17 没动）；技能是「夜晚采掘与攻击都不消耗耐久」，
    判据**转调** `StarSteelAxeItem.isNight`。③ **六件我替他定的**（三把统一耐久 / 技能选夜晚不磨损 /
    锄地那一下没管 / 锄的攻速有意取 1.0 而不是原版的 4.0 / **没做铲子**（他没给锹的图）/
    斧子那张按「换皮」理解）—— 全文在档案 §9，改都是一处。
    ④ ⚠ **三条新配方只写了 JSON、没有进生成器表 `_zf45_recipes.py`**：那张表是「定形配方」的表，
    重跑 `--write` 会不会把这三条删掉取决于它的清理口径 —— **谁下次碰那个生成器，先跑一遍
    `_zf141_verify.py` 看配方数是不是 72**（§4.93「表与盘脱钩」那条老账；本轮按「先不动表」处理，
    它本来就已经是打包轮的欠账）。
    ⑤ 四语言 **483 → 487** 键 ⇒ 32 份门跟平（`_zf141_gatefix.py`）。
    ⑥ 证据：探针 **70 项全绿**；常驻校验与反证刀的项数见它们自己的输出。
    ⑦ 本轮**没有重新打包**（用户没要求）⇒ `release\\PotatoST-0.11.jar` 与 `RELEASE_KEYS = 482` 都不用动。

24. **⚠ ZF139 的归档探针与它自己的报告对不上（我这条线自己欠的，如实记着）**：
    `build\\\\zftools\\\\check\\\\Zf139Check.java`（已提交）里面写的是
    `class Zf138Check` / `TAG = "[A138] "` / 报告路径 `_zf138_probe_utf8.txt`，
    而它产出的 `_zf139_probe_utf8.txt` 通篇是 `[A139] ` —— **归档的那份源码不是最终那一版**
    （那轮中途改过轮号，改名脚本只扫了 `_zf139_*`，`check\\` 下那份没跟着走）。
    ① **本轮不伪造也不改写历史**：那份留原样，报告与判据都没动；
    ② 已立 §4.145，并给**本轮**的卸载脚本加了自检（归档时断言归档件的 TAG / 类名 / 报告路径
    与报告里实际出现的 TAG 一致）；
    ③ 谁要拿 ZF139 的探针源码复核那轮结论，**以报告 `_zf139_probe_utf8.txt` 为准**（52 项全绿那份）。
""",
        u"交接 §6：加第 23 / 24 条")
    return text


# ==================================================================== C
ANN_ENTRY = u'''
- **Star Steel tools completed (0.11 ZF141)** - the axe is no longer the only Star Steel tool: **a sword, a pickaxe and a hoe join it, and all four share one tier** - **1192 durability**, mining speed **9.0**, **diamond mining level**, enchantment weight **22** (the axe's own numbers, untouched). Attack damage follows the request "sword about as strong as the axe, the rest a little lower": **sword 16.0** (1.6 hits/s), **pickaxe 13.0** (1.2), **hoe 12.0** (1.0); the axe stays at **17.0** (0.9). All three carry the axe's skill, **"in tune with the night"**: in the Overworld between dayTime 13000 and 23000, **mining and attacking cost no durability at all**. Two design notes: the hoe deliberately swings at **1.0 hits/s** rather than the vanilla diamond hoe's 4.0 (the vanilla hoe scale pins total damage at 1, and this tier's +8 bonus would have turned it into a **24 DPS** weapon - the strongest in the mod), and tilling soil still costs 1 durability exactly like vanilla (the tooltip says "mining and attacking", which is precisely what it does). All three recipes are the **vanilla patterns with Star Steel Ingots swapped in** - sword `X / X / #`, pickaxe `XXX / " # " / " # "`, hoe `XX / " #" / " #"` - so the ghost recipe looks exactly like the iron and diamond ones. The axe also got the **new texture** you dropped in. There is **no shovel yet** (no shovel texture was provided).
'''


# ==================================================================== D
USER_DIR = os.path.join(ROOT, "build", u"用户素材")
# (素材名, 落盘名, 说明)
CRED_JOBS = [
    (u"星璨钢剑.png", u"star_steel_sword.png",
     u"用户 ZF141 给的星璨钢剑贴图（16x16 RGBA，可直接用）。身份核实：alpha 掩码与原版"
     u"六档剑的 IoU 均为 **0.857**（对镐/斧/锄都 ≤0.55）⇒ 与文件名一致。"
     u"原字节复制成 textures/item/star_steel_sword.png"),
    (u"星镐子_001.png", u"star_steel_pickaxe.png",
     u"用户 ZF141 给的星璨钢镐贴图（16x16 RGBA）。形状 IoU 0.682 vs 原版镐 ⇒ 与文件名一致。"
     u"原字节复制成 textures/item/star_steel_pickaxe.png"),
    (u"星锄子_001.png", u"star_steel_hoe.png",
     u"用户 ZF141 给的星璨钢锄贴图（16x16 RGBA）。形状 IoU **0.962** vs 原版锄（四张里最高）。"
     u"原字节复制成 textures/item/star_steel_hoe.png"),
    (u"星璨钢斧子新贴图.png", u"star_steel_axe.png",
     u"用户 ZF141 给的**斧子新贴图**（16x16 RGBA）—— 注意它是**换皮**不是新物品："
     u"原字节复制成 textures/item/star_steel_axe.png，**顶掉 ZF133 那张**"
     u"（旧 sha1 8f5de358857e… / 3235 B）。用户同时把旧素材 `星璨钢斧.png` 从素材区删掉了 ⇒ "
     u"凭据里那条旧记录**保留**（它是历史），但那条「在用贴图 == 用户素材」的判据靶子"
     u"已由本轮改指本文件（见 `_zf141_gatefix.py` 的 B 段）。"
     u"旧图有逐字节备份：`zf141_pre/src/main/resources/assets/potato_s_t/textures/item/star_steel_axe.png`"),
]


def patch_cred(text):
    data = json.loads(text)
    before = len(data)
    for src_name, dst_name, why in CRED_JOBS:
        src = os.path.join(USER_DIR, src_name)
        if not os.path.isfile(src):
            fails.append(u"凭据：素材不在 %s" % src)
            continue
        raw = open(src, "rb").read()
        sha = __import__("hashlib").sha1(raw).hexdigest()
        # ⚠ **不许编哈希**：这里现算，并顺手核"它是不是真落到了目标路径上（同哈希）"
        dst = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t",
                           "textures", "item", dst_name)
        if not os.path.isfile(dst) or \
                __import__("hashlib").sha1(open(dst, "rb").read()).hexdigest() != sha:
            fails.append(u"凭据：%s 与在用贴图 %s 不同哈希" % (src_name, dst_name))
            continue
        if src_name in data:
            fails.append(u"凭据里已经有 %s 了" % src_name)
            continue
        data[src_name] = {
            "原名": src_name,
            "sha1": sha,
            "bytes": len(raw),
            "轮次": u"ZF141",
            "说明": why,
        }
    body = json.dumps(data, ensure_ascii=False, indent=2) + u"\n"
    notes.append(u"  [改] 凭据 %d → %d 条（sha1 现算，不写死）" % (before, len(data)))
    return body


def main(argv):
    write = u"--write" in argv

    doc = read(DOC)
    doc = insert_after(doc, u"| ZF140 |", u"", u"（占位：ZF140 行存在性）") if False else doc
    # A1：锚点是 ZF140 那一整行 ⇒ 先取出它
    lines = doc.split(u"\n")
    idx140 = [i for i, l in enumerate(lines) if l.startswith(u"| ZF140 |")]
    if len(idx140) != 1:
        fails.append(u"§5 里 `| ZF140 |` 命中 %d 行（应为 1）" % len(idx140))
    else:
        lines.insert(idx140[0] + 1, ROW.rstrip(u"\n"))
        notes.append(u"  [插] 档案 §5 加 ZF141 行")
        doc = u"\n".join(lines)
    doc = insert_before(doc, u"## 7. 权威情报来源", SEC4, u"档案 §4 加 4.139~4.145")
    doc = insert_before(doc, u"## 10. 备份策略", SEC9, u"档案 §9 加 ZF141 小节")
    plan.append((DOC, read(DOC), doc))

    hand = patch_hand(read(HAND))
    plan.append((HAND, read(HAND), hand))

    ann = read(ANN)
    if u"ZF141" in ann:
        notes.append(u"  [跳过] 英文公告里已经有 ZF141 了（幂等）")
    else:
        ann2 = ann.rstrip(u"\n") + u"\n" + ANN_ENTRY
        notes.append(u"  [插] 英文公告补 ZF141 条目")
        plan.append((ANN, ann, ann2))

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
