# -*- coding: utf-8 -*-
u"""_zf139_docs.py —— ZF139 的三份文档（数据 + 落盘逻辑）

  ① `docs\\开发档案.md`：§5 变更行（插在 ZF136 那一行后面）+ 六条 §4 新雷区（插在 §4 区末尾）
     + §9 新小节（追加到文件末尾）；
  ② `docs\\多会话协作交接.md`：§1 的两个活体数字（语言键 478 → **483**、配方 68 → **69**）
     + §6 两条（本轮的账 / 我 22:31 那次误伤另一条线的**事故记录**）；
  ③ `docs\\UpdateAnnouncement_EN.md`：末尾补一条振金套加强的英文条目。

⚠ 锚点全部用**整行精确匹配**（不是前缀）—— §4.112 就是"按段首匹配"踩出来的。
⚠ 长的中文块一律用三引号（`u'''...'''`），中文里需要引号的地方用「」。
⚠ 幂等：第二次跑会报"已经在了"并跳过。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, u"docs", u"开发档案.md")
HAND = os.path.join(ROOT, u"docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, u"docs", u"UpdateAnnouncement_EN.md")

notes, fails = [], []

# ------------------------------------------------------------------ §4 六条
LESSONS = u'''
### 4.127 【陷阱】`ServerPlayer` 有**两个** tick：`tick()` 不调 `super.tick()`，真玩家逻辑在 `doTick()`（0.11 ZF139）

写「振金套穿满就该有抗性提升 I」的真服务端探针时，ARMOR 属性死活是 0、套装效果一帧都不跑。
根因在 `ServerPlayer.java`：

```
510  public void tick() {          // ← 覆写了 Player.tick()，而且**不调 super.tick()**
511      this.gameMode.tick(); this.wardenSpawnTracker.tick();
513      this.spawnInvulnerableTime--;   // ← 出生保护在这里减
518      this.containerMenu.broadcastChanges();  ... 相机 / CriteriaTriggers.TICK / 交互距离属性
546  }
568  public void doTick() {          // ← 真玩家那一 tick（由 ServerGamePacketListenerImpl.tick() 调）
571      super.tick();               //    Player.tick() → PlayerTickEvent + LivingEntity.tick()
```

⇒ **只调 `tick()`**：不触发 `PlayerTickEvent`、也不走 `LivingEntity.tick()` 里的
`detectEquipmentUpdates()`（`LivingEntity.java:2482`）⇒ **装备属性永远挂不上**（`getArmorValue()` 恒 0）。
服务端是**两个都调**的（连接 tick 调 `doTick()`，关卡实体循环调 `tick()`）——
探针里要模拟「玩家入场」，就得 `p.tick(); p.doTick();` 成对跑。

### 4.128 【陷阱】假玩家有 **60 tick 出生保护**，而且它**只挡摔落以外的伤害**（0.11 ZF139）

`ServerPlayer.hurt` 第 793-795 行：

```java
boolean flag = this.server.isDedicatedServer() && this.isPvpAllowed() && source.is(DamageTypeTags.IS_FALL);
if (!flag && this.spawnInvulnerableTime > 0 && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) return false;
```

`spawnInvulnerableTime` 初值 **60**，而且是 **private**。于是伤害源矩阵一跑就现原形：
**只有 fall 打得进去**（dev 服务端 isDedicatedServer + pvp 都为真 ⇒ 那个 `flag` 放行），
`generic` / `playerAttack` / `mobAttack` / `magic` **一律返回 false，连 `LivingIncomingDamageEvent` 都不触发**。

症状披着「功能没生效」的皮：反伤统计 **0/2000**，看着像自己写的判据错了，实际是**一下都没打进去**。

**规矩两条**：① 探针里造成伤害前，先用 `ServerPlayer.tick()` 跑满 61 帧把保护烧掉（见 §4.127，只有那个方法减它）；
② **负向用例必须配「这一下真打进去了」的灵敏度对照** —— 否则「反了 0 次」是假绿。
本轮第一版 13 条红里有一半来自这两条。

### 4.129 【陷阱】`CombatTracker.getDeathMessage()` 只能在**死亡那一刻**问（0.11 ZF139）

想验「被反伤打死的人文案是踢到了铁板」，很自然会写：

```java
attacker.hurt(reflectSource, 100.0F);                          // 死了
Component m = attacker.getCombatTracker().getDeathMessage();    // ← 恒为 death.attack.generic
```

因为 `LivingEntity.die` 里会调 `CombatTracker.recheckStatus()`，而它在 `!mob.isAlive()` 时
**把 entries 清空**（`if (this.takingDamage && (!this.mob.isAlive() || ...)) { ... this.entries.clear(); }`）。
`ServerPlayer.die` 的真实顺序是「先 `CommonHooks.onLivingDeath`（= `LivingDeathEvent`）→ 再读文案 → 最后 `super.die`」。

⇒ 探针要**挂 `LivingDeathEvent`**，在事件里把文案抓下来（本轮就是这么改的，改完这条立刻绿）。

### 4.130 【陷阱】`check()` 不返回值 ⇒ `if not check(...)` 恒真（§4.96 重演，0.11 ZF139）

`_zf103_verify.py` 的 `check()` 只记账、返回 `None`。本轮我自己新写的常驻校验里写了

```python
if not check(os.path.isfile(dt), u"...存在"):
    return finish()
```

`not None` 恒为 True ⇒ **后面 ⑤⑥⑦ 三组 20+ 条断言一条都没跑**，而汇总照样打印
「断言数 = 39　失败项 = 0　结论: 通过」。**假绿灯比红灯坏得多**（§4.96 已经写过一次，本轮我又犯）。

**规矩**：需要拿返回值的地方一律用薄包装 `check_ok()`（`_zf120_verify.py` 就是这么写的）；
另外**汇总行里的"断言数"要与预期条数对得上** —— 39 条明显少于自己写的组数，那本身就是信号。

### 4.131 【陷阱】`0.0F` 不进常量池（钛合金那条「反向」判据的假红）（0.11 ZF139）

本轮「反向」判据要钉「另外两套盔甲的数字一个都没动」，照源码抄了
`TITANIUM_ALLOY = [25, 0.0, 2, 8, 6, 4]` ⇒ 假红。`javap -constants` 实际读到的是
**`[25, 2, 8, 6, 4]`**：`0.0F` 走字节码 `fconst_0`，**不是**常量池条目。

⇒ 同 §4.103 那条（`0.0/1.0` 是 `dconst_*`、小整数是 `bipush/sipush`）：
**期望值要照「编出来的常量池」写，不是照源码字面写**。星璨钢那串里 `0.5F` 是真常量池条目，所以 6 个数都在。

### 4.132 【流程雷】改轮号**必须先查有没有人占**，而且**改名脚本不许扫目录通配**（0.11 ZF139，§4.111 重演）

我开工时盘上最新是 ZF135 ⇒ 取了 **ZF136**。做到一半另一条线提交了 `8ed549a`，
那一笔**同时**往档案 §5 塞了 `| ZF136 |`（换 `star_steel_ingot.png` 那件事）⇒ 我的号被占了。
为了改号，我写了个脚本：「**凡是 `build/zftools` 里名字带 `zf136` 的一律改名成 `zf138`、内容里 136 换 138**」。结果：

* 那条线自己**已经在用 `_zf138_*`** 这个名字（`_zf138_look.txt` 22:14、`_zf138_diff.png` 22:16 就是它的产物）；
* `shutil.move` 在 Windows 上目标存在时**会覆盖** ⇒ 他们的 `_zf138_*.py` 被我换成了他们自己的 `_zf136_*.py` 旧稿。

补救：**逐个查过他们那 9 个件里的 `138` 全在号码位置（没有数据值被误伤）⇒ 逐字节还原成 `_zf136_*`**，
`zf138_pre/` 也还原成 `zf136_pre/`；救不回的是他们 `_zf138_*.py` 里可能比旧稿新的部分 ——
**已写进交接 §6 请他们核对**。

⚠ 这**正是 §4.111 那一条**（ZF130 那次「按前缀批量改名把别人 25 个文件一起改了」）⇒ 同一个坑第二次踩。
**规矩三条**：
1. 取轮号前先 `grep` 一遍档案 §5 **与** `build/zftools` 的**实际文件名**，两个都空才用；
2. **改名只对自己点名的清单动手**，绝不用 `*zfNNN*` 通配扫目录；
3. 改完立刻 `git status` 看有没有碰到别人的路径 —— 本次就是先看到一堆 `??` 才停手的。
'''

ROW = u'''| ZF139 | **新建 `zf139_pre`**（**144 份**改前件：`ModArmorMaterials` / `ModVibraniumSet` / `ModArmorItems` / **`PotatoST.java`（探针挂载点）** + 四份 lang + `_zf120_verify.py` + 四门清单 + 全部 `_zf*_verify/_falsify/_gatesnap` + 3 份文档 + 旧成品与 `.sha1`；逐份核哈希 + 回读证明 144/144，失败 0） | 0.11：**振金套加强**（用户原话「振金套你看看能不能略微加强一下 现在地位太尴尬了 比星璨麻烦很多 却大大不如晚上的星璨 简直就是个白板」）。① **先按原版公式把两套摆平**（`CombatRules.getDamageAfterAbsorb` + `LivingEntity.getDamageAfterMagicAbsorb`）：振金原来的 20 护甲 / 12 韧性**就是下界合金那一行**，10 点伤害吃 **2.80**；星璨钢**白天**（28 护甲）吃 2.00、**夜晚**（+抗性 II）只吃 **1.20** ⇒「白板」是事实不是情绪；② 用户拍板「乙方案 + 一条新套装效果」：护甲值 **3/8/6/3 → 4/9/7/4**（各 +1；韧性 12 / 击退抗性 0.4 / 附魔权重 2 一个不动）⇒ 6/10/20 三个档**恒 16%**；满套**常驻抗性提升 I**（不挑昼夜与维度，`PlayerTickEvent.Post`，与星璨钢那套同一个口子）、满套**免疫摔落伤害**（取消 `LivingFallEvent` ⇒ 连摔落音效都不放）、满套**10% 反伤**（反的是**这一击的原始伤害**，挂 `LivingDamageEvent.Post`）；③ 反伤用了**本工程第一个自定义伤害类型** `potato_s_t:vibranium_reflect`（数据包 `damage_type`；`effects=thorns` ⇒ 挨打那一声是「打铁板」；`message_id` ⇒ 死亡文案键 `death.attack.potato_s_t.vibranium_reflect` =「%1$s踢到了铁板」，`%1$s` 是**先动手那位**的名字）；④ 四语言 **482 → 483** 键（28 份往轮门 + 英文公告跟平）；⑤ 证据：真服务端探针 **52 项全绿**（含 2000 次真受击反伤 175 次、四条排除名单各 400 次全 0 且配灵敏度对照、死亡那一刻的文案键）、`_zf139_verify.py` **90 项 0 失败**、反证 **K227~K250 二十四把**全咬住；⑥ ⚠ 本轮轮号改了两次（ZF136 → ZF138 → **ZF139**），第二次改号误伤了另一条线的同名文件、已逐字节还原 —— 见交接 §6 与 §4.132 | 见 §4.127~§4.132 / §9 |'''

SECTION = u'''

### ZF139（0.11）振金套加强：护甲 24 / 常驻抗性 I / 免摔落 / 10% 反伤「踢到了铁板」—— **待你实测**

用户原话：「振金套你看看能不能略微加强一下 现在地位太尴尬了 比星璨麻烦很多 却大大不如晚上的星璨 简直就是个白板」

我没有直接改，先把两套的**实吃伤害**按原版公式逐格算出来摆给你看
（`CombatRules.getDamageAfterAbsorb`：先护甲 `min(max(护甲 − 伤害/(2+韧性/4), 护甲×0.2), 20)/25`，
再 `LivingEntity.getDamageAfterMagicAbsorb`：抗性每级 ×0.8）：

| 满套 | 护甲/韧性 | 小怪 6 | 普通 10 | 重击 20 |
|---|---|---|---|---|
| 下界合金 | 20 / 12 | 1.49（25%） | 2.80（28%） | 7.20（36%） |
| 星璨钢·白天 | 28 / 2.5 | 1.20（20%） | 2.00（20%） | 4.00（20%） |
| 星璨钢·夜晚主世界 | 28 / 2.5 + 抗性 II | 0.72（12%） | 1.20（12%） | 2.40（12%） |
| **振金·改前** | 20 / 12 | 1.49（25%） | **2.80（28%）** | 7.20（36%） |
| **振金·改后** | **24 / 12 + 抗性 I** | **0.96（16%）** | **1.60（16%）** | **3.20（16%）** |

⇒ 改前的振金**连白天的星璨都不如**，而它比星璨贵得多（12 金锭 + 8 热力金属 + 3 银锭 + 2 高碳钢 +
1 硬质钛合金，再各加 1 粗振金 + 2 下界合金碎片，14500 FE/t）。你拍板的是**乙方案 + 一条新效果**。

#### 一、改了什么（四条，都在「穿满四件」那一档）

| # | 内容 | 落点 | 与星璨钢的关系 |
|---|---|---|---|
| ① | 护甲值 **3/8/6/3 → 4/9/7/4**（各 +1，满套 24；韧性 12、击退抗性 0.4、附魔权重 2 一个不动） | `ModArmorMaterials.VIBRANIUM` | 白天稳压星璨 |
| ② | 满套**常驻抗性提升 I**（不挑昼夜、不挑维度，图标一直亮） | `ModVibraniumSet.onPlayerTick` | 与星璨的「夜晚每件抗性 I」同一个口子（`PlayerTickEvent.Post`） |
| ③ | 满套**免疫摔落伤害** | `ModVibraniumSet.onFall`（取消 `LivingFallEvent`） | 星璨只有虚空救援时给缓降 |
| ④ | 满套：挨打 **10%** 概率把**这一击的原始伤害**还给攻击者 | `ModVibraniumSet.onDamagePost` | 星璨没有 |

④ 的细节：反伤用**本工程第一个自定义伤害类型** `potato_s_t:vibranium_reflect`
（`data/potato_s_t/damage_type/vibranium_reflect.json`，照原版 `thorns.json` 的格式与键序）：

* `effects = thorns` ⇒ 挨这一下的人听到的是「打铁板」那一声（`Player.getHurtSound` 读的就是 `type().effects().sound()`）；
* `message_id = potato_s_t.vibranium_reflect` ⇒ 死亡文案键 `death.attack.potato_s_t.vibranium_reflect`，
  中文是 **`%1$s踢到了铁板`**，而按 `DamageSource.getLocalizedDeathMessage` 的规则 `%1$s` 是**受害者** ——
  也就是**先动手的那位**，所以名字天然对，不需要我们再拼字符串。

#### 二、四条判断是怎么定的（都查了源码，不是凭手感）

| 问题 | 结论 | 依据 |
|---|---|---|
| 反伤挂哪个事件？ | **`LivingDamageEvent.Post`**（不是「伤害之前」那个） | `LivingIncomingDamageEvent` 比**无敌帧判定**更早（`LivingEntity.java:1152` vs `:1190`）⇒ 挂那里会在「根本没掉血」的那一下掷骰子；探针专门验了这条（无敌帧里的第二下：`incoming +1`、`post +0`） |
| 反多少？ | **`getOriginalDamage()`**（进护甲前） | 用户说「返还 **100% 的伤害**」；按「我掉了多少血」反的话，攻击者挨的还不到他自己出手的零头，「踢到铁板」就不成立了 |
| 哪些不算？ | 弹射物（已被整条免疫）/ 爆炸（已减半）/ **反伤本身**（递归保护）/ 被盾牌或伤害吸收全吃掉那一下（`getNewDamage() <= 0`） | `Post` 事件是**无条件**触发的（`LivingEntity.java:1805` 那句在 `if (f1 != 0.0F)` 块**外面**） |
| 摔落为什么不用伤害标签？ | 用 `LivingFallEvent` 取消 | 取消之后 `causeFallDamage` 直接 return false，**连摔落音效都不放**；按 `#is_fall` 取消伤害会留下音效与粒子 |

#### 三、证据

| 项 | 值 |
|---|---|
| 真服务端探针 | **52 项全绿**（`Zf139Check`：跑完已摘除、留档在 `build/zftools/check/`）：伤害类型四个字段 / 护甲 24（对照下界合金 20）/ 抗性 I 320 tick 且不覆盖已有的抗性 III / 摔落 100 点不掉血而破套照掉 / **2000 次真受击反伤 175 次**（≈8.75%）/ 四条排除名单各 400 次**全 0** 且配「同口径普通攻击 400 次反了 36 次」的**灵敏度对照** / 反伤数值 = 原始伤害（裸装挨 4.0 掉 4.0）/ **死亡那一刻**的文案键与名字 / 星璨钢与裸装对照 / 无敌帧那一下的架构证据 |
| 常驻校验 | `_zf139_verify.py` **90 项 0 失败**（材料数值 / 七处满套判据 / 三条新效果的字节码与源码句式 / 数据包逐字段与原版 thorns 对照 / 四语言 483 键与插键位置 / 与改前件比老键值 / 跟平与反向） |
| 反证刀 | **K227~K250（24 把）**：护甲值抄错 / 韧性 / 击退抗性 / 顺手改星璨 / 抗性时长 / 不判满套 / 覆盖规则取反 / 图标不可见 / 摔落不取消 / 概率改 0.5 / 删「没掉血不掷骰」 / 删递归保护 / 删两条排除 / 反成「我掉了多少血」 / 还手对象写反 / 伤害源实体换人 / `message_id` 改名 / `effects` 改掉 / 文案丢 `%1$s` / 往轮键数改回 482 / 交接活体数字改回 482 |
| 全门快照 | 见 `_zf139_gatesnap.txt`（与 `_zf139_gatesnap_before.txt` 逐条比） |
| 活体数字 | 四语言 **482 → 483** 键（+1：死亡文案）；贴图 / 模型 / 配方 / 进度**一行没动** |

#### 四、⚠ 本轮的两件事要你知道

1. **轮号改了两次**（ZF136 → ZF138 → **ZF139**）。原因：开工时盘上最新是 ZF135，我取了 ZF136；
   做到一半另一条线提交了 `8ed549a`，那一笔同时往档案 §5 塞了 `| ZF136 |`（换 `star_steel_ingot.png` 那件事），
   而 ZF137 也是他们的、ZF138 是他们在用的文件名 ⇒ 本轮最终用 **ZF139**。
2. **改号时我误伤了另一条线的文件**：改号脚本「凡 `build/zftools` 里名字带 `zf136` 的一律改名成 `zf138`」
   把他们**已经在用的** `_zf138_*.py` 覆盖成了他们自己的 `_zf136_*.py` 旧稿。
   已逐个查过（`138` 全在号码位置、没有数据值被误伤）并**逐字节还原**成 `_zf136_*` / `zf136_pre/`；
   救不回的是他们 `_zf138_*.py` 里可能更新的部分 —— 已写进交接 §6 请他们核对。
   **这是 §4.111 的重演**（同一个坑第二次），规矩已加固成三条写在 §4.132。

#### 五、要你实测的（进游戏）

1. 穿上振金四件：护甲条应当是 **24**（比下界合金多 4 点）；屏幕右上角**一直**挂着「抗性提升 I」的图标
   （白天、夜里、下界、末地都在）。
2. 从高处跳下来：**不掉血、也没有「砰」的落地声**（摘掉任意一件再跳，照常掉血 + 有声）。
3. 让骷髅射你：**照样免疫 + 弹回去**（老效果没坏）。
4. 让僵尸 / 苦力怕打你：十下里大约**一下**会把伤害原样弹回给它 —— 打你多少，它掉多少。
   如果它被这一下打死，聊天栏那条死亡提示应当是「**XXX踢到了铁板**」，而且 XXX 是**它的名字**。
5. Shift 看振金套说明：四条新内容都写在里面（四语言都改了）。
'''


def read(p):
    return io.open(p, encoding=u"utf-8", newline=u"").read()


def write(p, t):
    io.open(p, u"w", encoding=u"utf-8", newline=u"").write(t)


def insert_after_exact(text, anchor_line, block, label):
    lines = text.split(u"\n")
    hits = [i for i, l in enumerate(lines) if l == anchor_line]
    if len(hits) != 1:
        fails.append(u"%s：锚点行命中 %d 次" % (label, len(hits)))
        return text
    lines[hits[0] + 1:hits[0] + 1] = block.split(u"\n")
    notes.append(u"  [插] %s" % label)
    return u"\n".join(lines)


def main():
    # ---------------------------------------------------------- 开发档案
    doc = read(DOC)
    if u"| ZF139 |" in doc:
        notes.append(u"  [已做过] 档案 §5 已有 ZF139 行")
    else:
        anchor_row = [l for l in doc.split(u"\n") if l.startswith(u"| ZF136 |")]
        if len(anchor_row) != 1:
            fails.append(u"§5：ZF136 那一行命中 %d 次" % len(anchor_row))
        else:
            doc = insert_after_exact(doc, anchor_row[0], ROW, u"档案 §5：ZF139 变更行")
    if u"### 4.127" not in doc:
        # §4 区末尾 = `## 7.` 那个标题**之前**（盘上是 §4.112 块之后、§7 之前）
        lines = doc.split(u"\n")
        i7 = [i for i, l in enumerate(lines) if l.startswith(u"## 7. ")]
        if not i7:
            fails.append(u"档案：找不到 §7 标题，没法定位 §4 区末尾")
        else:
            k = i7[0]
            lines[k:k] = LESSONS.split(u"\n")
            doc = u"\n".join(lines)
            notes.append(u"  [插] 档案 §4：4.127~4.132 六条（插在 §7 之前）")
    else:
        notes.append(u"  [已做过] 档案已有 §4.127")
    if u"### ZF139（0.11）振金套加强" not in doc:
        doc = doc.rstrip(u"\n") + u"\n" + SECTION
        notes.append(u"  [追加] 档案 §9：ZF139 小节")
    else:
        notes.append(u"  [已做过] 档案已有 ZF139 小节")
    write(DOC, doc)

    # ---------------------------------------------------------- 交接文档
    hand = read(HAND)
    old_keys = u"| 语言键数 | **478 键 × 4**"
    if old_keys in hand:
        hand = hand.replace(
            old_keys,
            u"| 语言键数 | **483 键 × 4**", 1)
        hand = hand.replace(
            u"→ **478**（ZF127 银线 / 银线轴 +2）。",
            u"→ **478**（ZF127 银线 / 银线轴 +2）→ **482**（ZF133 星璨钢斧 +4）"
            u"→ **483**（ZF139 振金套：死亡文案 +1）。", 1)
        notes.append(u"  [改] 交接 §1：语言键数 478 → 483（含链子）")
    elif u"| 语言键数 | **483 键 × 4**" in hand:
        notes.append(u"  [已做过] 交接 §1 的键数已是 483")
    else:
        fails.append(u"交接 §1：没找到「478 键 × 4」那一行")
    if u"`crafting_shaped` **58** 条" in hand:
        hand = hand.replace(u"**68 份**（其中 `crafting_shaped` **58** 条）",
                            u"**69 份**（其中 `crafting_shaped` **59** 条）", 1)
        notes.append(u"  [改] 交接 §1：配方 68 → 69（活体数字，别线加过一份）")
    else:
        notes.append(u"  [跳过] 交接 §1 的配方数字已经改过或格式不同")

    ITEM21 = u'''
21. **ZF139 的账（振金套加强）**：① 用户原话「振金套你看看能不能略微加强一下 现在地位太尴尬了
    比星璨麻烦很多 却大大不如晚上的星璨 简直就是个白板」。**先把数摆平再动手**：按原版
    `CombatRules.getDamageAfterAbsorb` + `LivingEntity.getDamageAfterMagicAbsorb` 逐格算，
    振金改前的 20 护甲 / 12 韧性**就是下界合金那一行**（10 点伤害吃 2.80），而星璨钢**白天**吃 2.00、
    **夜晚**只吃 1.20 ⇒「白板」是事实。② 用户拍板「乙方案 + 一条新套装效果」⇒ 改四处：
    **护甲值 3/8/6/3 → 4/9/7/4**（各 +1；韧性/击退抗性/附魔权重一个不动）、满套**常驻抗性提升 I**
    （`PlayerTickEvent.Post`，与星璨钢同一个口子）、满套**免疫摔落**（取消 `LivingFallEvent`）、
    满套 **10% 反伤**（反**这一击的原始伤害**，挂 `LivingDamageEvent.Post`）。
    ③ ⚠ **本工程第一个自定义伤害类型**：`data/potato_s_t/damage_type/vibranium_reflect.json`
    （照原版 `thorns.json` 的格式与键序；`effects=thorns` ⇒ 挨打那一声是「打铁板」；
    `message_id` ⇒ 死亡文案键 `death.attack.potato_s_t.vibranium_reflect`，中文「%1$s踢到了铁板」，
    `%1$s` 是**先动手那位**）。**谁以后再动死亡文案，先看这个文件与那条键。**
    ④ 四语言 **482 → 483** 键 ⇒ 28 份往轮门 + 英文公告跟平（`_zf139_gatefix.py`，逐份命中次数在它输出里）。
    ⑤ 证据：探针 **52 项全绿** + `_zf139_verify.py` **90 项 0 失败** + 反证 **K227~K250 二十四把**。
    ⑥ ⚠ **`_rzh_armor_tips.py`（润色线的装备说明生成器）里的振金说明是 ZF133 之前的底稿** ——
    谁重跑它都会把这四条新说明打回原样；本轮的文案在 `zf139_pre` 里有改前件、在 §9 里有全文。
    '''
    ITEM22 = u'''
22. **⚠ 我（ZF139 那条线）22:31 误伤了另一条线的文件 —— 请核对**：
    ① 事故：为了把本轮从 ZF136 改号，我写了个脚本「**凡 `build/zftools` 里名字带 `zf136` 的一律改名成
    `zf138`、内容里 136 换 138**」。而你们那时**已经在用 `_zf138_*`**（`_zf138_look.txt` 22:14、
    `_zf138_diff.png` 22:16 就是你们的产物）⇒ Windows 上 `shutil.move` 目标存在时**会覆盖**，
    于是你们的 `_zf138_*.py` 被换成了你们自己的 `_zf136_*.py` 旧稿。
    ② 已做的补救：逐个查过你们那 9 个件里的 `138` **全在号码位置**（`ZF138`/`zf138`/`_zf138`，
    没有数据值被误伤）⇒ **逐字节还原成 `_zf136_*`**（apply / diff.py / diff.png / docs / look.py /
    look.txt / row.txt / section.md / shape.py），`zf138_pre/` 也还原成 `zf136_pre/`。
    ③ **救不回的**：你们 `_zf138_*.py` 里若比 `_zf136_*` 旧稿更新，那部分内容已经丢了 ——
    请按需重生成/复核（那几张产物 `.txt`/`.png` 都还在，脚本都是可重跑的）。
    ④ 本轮定号 **ZF139**（136 被你们档案行占了、137 是你们的提交、138 是你们在用的文件名）。
    ⑤ 这条已立成 §4.132（**§4.111 的重演**）：改名**只对自己点名的清单**动手，不许用 `*zfNNN*` 通配扫目录。
    '''
    if u"21. **ZF139 的账" not in hand:
        hand = hand.rstrip(u"\n") + u"\n" + ITEM21 + ITEM22
        notes.append(u"  [追加] 交接 §6：第 21/22 条")
    else:
        notes.append(u"  [已做过] 交接 §6 已有第 21 条")
    if u"最后更新**：2026-09-25" in hand:
        hand = hand.replace(u"**最后更新**：2026-09-25 21:5x", u"**最后更新**：2026-09-26 22:5x", 1)
        notes.append(u"  [改] 交接抬头日期")
    write(HAND, hand)

    # ---------------------------------------------------------- 英文公告
    ann = read(ANN)
    ENTRY = u'''
- **Vibranium set buffed (0.11 ZF139)** - the top-tier set was a plain netherite clone before this: **20 armour / 12 toughness**, i.e. 2.80 damage taken out of a 10-damage hit, while Star Steel already took only 2.00 in **daylight** and 1.20 at night - despite vibranium costing far more. Four changes, all on the full set: (1) armour values go **3/8/6/3 -> 4/9/7/4** (24 total; toughness 12, knockback resistance 0.4 and enchantment weight 2 unchanged), which flattens incoming damage to **16%** at every hit size; (2) **Resistance I at all times** - any hour, any dimension, icon always up; (3) **immunity to fall damage** (the fall is cancelled before damage, so not even the landing thud plays); (4) **10% of incoming hits are returned in full to the attacker** - the raw damage of the blow, before your own armour. That reflected hit uses a **new custom damage type** (`potato_s_t:vibranium_reflect`, the mod's first), so anyone killed by it gets the death message **"... kicked a steel plate"** - the name shown is the attacker's own. Projectiles, explosions and other reflected hits are excluded (the first two are already fully handled, the third stops two wearers from bouncing damage forever).
'''
    if u"ZF139)" not in ann:
        ann = ann.rstrip(u"\n") + u"\n" + ENTRY
        notes.append(u"  [追加] 英文公告：振金套加强条目")
    else:
        notes.append(u"  [已做过] 英文公告已有 ZF139 条目")
    write(ANN, ann)

    print(u"\n".join(notes))
    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
