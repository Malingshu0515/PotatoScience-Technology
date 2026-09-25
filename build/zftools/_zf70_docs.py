# -*- coding: utf-8 -*-
"""_zf70_docs.py —— 把 ZF70（三个进度/成就）写进《开发档案》

规矩（§4.36）：每处替换都要求**恰好命中 1 次**，命中 0 次或 ≥2 次一律报错退出。
"""
import io
import sys

DOCS = r"E:\PotatoST\docs\开发档案.md"

fails = []
applied = []


def rep(text, old, new, why):
    n = text.count(old)
    if n != 1:
        fails.append(u"%s：命中 %d 次（要求恰好 1 次）" % (why, n))
        return text
    applied.append(why)
    return text.replace(old, new, 1)


def main():
    with io.open(DOCS, encoding="utf-8") as fh:
        text = fh.read()
    before_lines = text.count("\n") + 1

    # ---------- ① §4.42 / §4.43 两条新教训 ----------
    old = u"\n## 5. 版本与 [ZF] 流水线记录\n"
    new = u"""
### 4.42 【数据格式】`requirements` 是**外层 AND / 内层 OR** —— 用户说的「和」要拆成多组（0.10 ZF70）

用户给的第 2 条成就写的是「获得发电机 **和** 动力能源捕获器」。我按"两个判据塞进一组"写成：

```json
"requirements": [ [ "generator", "power_capturer" ] ]
```

**这是「或」，不是「和」。** 探针第一次真触发就报出来了：

```
[FAIL] 只拿发电机（还没拿捕获器）⇒ 更强劲的电源**不**完成（实际 true）
[FAIL] 完成时两个判据都完成（实际 1 / 2，percent=1.0）
```

证据链（两条，都不靠记忆）：

1. **原版数据**：`minecraft:husbandry/plant_seed`（种任意一种作物）的 7 个判据**挤在一组**里 ——
   要是"一组 = 全都要"，这条成就就要求把 7 种作物全种一遍，显然不是它的本意；
2. **字节码**：`AdvancementRequirements.test()` 的循环体里是 `anyMatch(list, predicate)`，
   任何一个不满足就 `return false` ⇒ **每个内层组只要有 1 条判据完成就算这组过（OR），
   所有组都得过（AND）**；`allOf(c)` = 每个判据各成一组、`anyOf(c)` = 全部塞进一组，正好互为镜像。

所以「和」的正确写法是**两组、每组一个**：

```json
"requirements": [ [ "generator" ], [ "power_capturer" ] ]
```

单判据的成就（新的开始！/ 入门清洁能源）两种写法等价，但一律按"每个判据各成一组"写，
免得以后加判据时踩同一颗雷。⚠ 静态校验（JsonCheck 之类）**永远抓不到这条** ——
它只在"真拿物品去触发"的时候才显形，所以 `_zf70_verify.py` 专门把它写成断言
（"2 个判据 ⇒ requirements 必须是 2 组、每组 1 个"），反证跑过：退回 OR 写法 ⇒ 3 条 FAIL。

### 4.43 【探针】无头服务端里的假玩家**必须挂一个没连上的 Connection**（0.10 ZF70）

用 `new ServerPlayer(server, level, profile, ClientInformation.createDefault())` 造玩家来真触发判据时，
第一次跑直接 NPE：

```
java.lang.NullPointerException: Cannot invoke "ServerGamePacketListenerImpl.send(Packet)"
  because "player.connection" is null
    at ServerRecipeBook.sendRecipes → ... → AdvancementRewards.grant → PlayerAdvancements.award
```

根因：完成一个**带配方奖励**的进度时会 `awardRecipesByKey → recipeBook.sendRecipes → player.connection.send`。
原版 `smelt_iron`（拿到铁锭）就有配方奖励，所以"随便拿个铁锭当负向对照"这一下自己先炸了。

两条修法（这轮两条都用了）：

1. **挂一个没连上的 `Connection`**：`player.connection = new ServerGamePacketListenerImpl(server,
   new Connection(PacketFlow.SERVERBOUND), player, CommonListenerCookie.createInitial(profile, false))`
   —— `Connection.isConnected()` 为假时 `send()` 只入队，任何奖励包都打不出去，探针能一路跑到底；
2. 负向对照别用原版物品（铁锭会顺带触发原版成就），改用**本模组里与这三条无关的物品**
   （这轮用微型粉碎机）。

同一节顺带记一句：`Loaded 1402 advancements` = 原版 1399 + 本模组 3 —— **加载数就是账目**。

## 5. 版本与 [ZF] 流水线记录
"""
    text = rep(text, old, new, u"§4.42/§4.43 插入")

    # ---------- ② §5 加 ZF70 行 ----------
    old = u"\n\n> ZF40~ZF44 全是**电力高炉的连续改动**"
    row = (
        u"| ZF70 | **新建 `zf70_pre`**（**动手前**建的，7 个改前件：4 个 lang + `docs/开发档案.md` + "
        u"旧成品 jar 与 `.sha1`；逐份核哈希、失败 0。进度 JSON 是**新增**——`data/potato_s_t/advancement/` "
        u"这个目录本轮才建，没有改前件） | 0.10：**三个进度（成就）**（用户原话：「加几个成就（进度）"
        u"没说默认就是普通成就」）。① **新的开始！**（根）：条件=获得低级发电机、描述「简洁的电力来源 "
        u"方便且够用」、图标=低级发电机；**更强劲的电源**：条件=获得发电机**和**动力能源捕获器、"
        u"前置=新的开始！；**入门清洁能源**：条件=放置一个太阳能板、描述「量变产生质变」、前置=新的开始！；"
        u"② 三条都是 **frame=task**（普通成就）、`show_toast`/`announce_to_chat` = true、`hidden` = false；"
        u"根必须给 `background`（这轮用 `potato_s_t:textures/block/common_metal_block.png`，"
        u"否则 GUI 里那个标签页没有底图）；③ **用户没说的两处我定的**：更强劲的电源图标=发电机、"
        u"入门清洁能源图标=太阳能板（都取该条件里的那个方块）；④ **「和」的写法踩了雷** —— 见 §4.42："
        u"`requirements` 是**外层 AND / 内层 OR**，`[[generator, power_capturer]]` 是「或」，"
        u"要写成 `[[generator], [power_capturer]]`；**探针第一次真触发就抓出来了**（2 项 FAIL）；"
        u"⑤ 四语言各 +6 键（204 → **210**）：中文逐字用用户原话，en/ja/ru 是**我译的**；"
        u"⑥ 探针 `AdvancementCheck` **47 项全 [OK]**（账目 / 树与父指针 / 展示 / 判据类型 / requirements / "
        u"**真触发**：拿无关物品三条都不完成、拿低级发电机只完成第一条、**只拿发电机不算完成**、"
        u"再拿捕获器才完成且 2/2 判据、放一般金属块不算完成、放太阳能板才完成；服务端当场播报三条；"
        u"服务端日志 `Loaded 1402 advancements` = 原版 1399 + 3）；⑦ **反证**：把 requirements 退回「或」写法 ⇒ "
        u"`_zf70_verify.py` **3 条 FAIL**（另加 §4.43 那条假玩家 NPE 的坑）；新写常驻 `_zf70_verify.py`（**87 项**）"
        u" | 见 §4.42 / §4.43 / §6.17 / §9 |"
    )
    text = rep(text, old, u"\n" + row + old, u"§5 ZF70 行")

    # ---------- ③ §6.17 新工具页 ----------
    old = u"\n## 7. 权威情报来源（怎么查原版行为，别靠记忆）\n"
    new = u"""
### 6.17 加一个**进度（成就）**要动哪几处（0.10 ZF70 实例：三条）

| # | 动哪 | 干什么 |
|---|---|---|
| 1 | `data/potato_s_t/advancement/<id>.json` | **目录名是单数** `advancement`（1.21 起；`advancements` 复数在 1.21.1 不识别）。根= 不写 `parent`，**根必须给 `display.background`**（一张贴图路径，整页标签页的底图）；子进度写 `"parent": "potato_s_t:<父id>"` |
| 2 | 图标格式 | 1.21 是 `"icon": { "count": 1, "id": "potato_s_t:xxx" }` —— **不是** 1.20 那种 `{"item": ...}` |
| 3 | 条件 | 拿物品：`minecraft:inventory_changed` + `conditions.items[0].items`（**字符串**，不是数组）；放方块：`minecraft:placed_block` + `conditions.location[0] = { "condition": "minecraft:block_state_property", "block": "..." }`（不写 `properties` = 任意状态都算） |
| 4 | **`requirements`** | ⚠ **外层 AND / 内层 OR**。用户说「和」⇒ 每个判据各成一组 `[["a"],["b"]]`；说「或」⇒ 全塞一组 `[["a","b"]]`。见 §4.42 |
| 5 | `frame` | `task` = 普通成就（默认）、`goal`、`challenge`。普通成就也建议**显式写**出来，别靠默认值 |
| 6 | 四语言 | `advancements.<ns>.<id>.title` / `.description`，4 个文件都要加（LangCheck 会查键集合一致） |
| 7 | 不用注册代码 | 进度是**纯数据**：不需要 `DeferredRegister`、不需要改 `PotatoST`。服务端 `Loaded N advancements` 会 +1/条 |
| 8 | 配方书联动 | 原版"配方解锁"就是**进度的 `rewards.recipes`**。本模组目前一条 `rewards` 都没写 ⇒ **配方书不会自动解锁**（JEI 看得到、手摆能合），要改的话在这里加 |

**验证要点**（这轮立的规矩）：

- **必须真触发**，光看 JSON 不算 —— 探针里用 `CriteriaTriggers.INVENTORY_CHANGED.trigger(...)` /
  `PLACED_BLOCK.trigger(...)` 打一遍，再看 `player.getAdvancements().getOrStartProgress(holder).isDone()`；
- 多判据的成就**一定要测"只满足一半"**：这正是 AND/OR 写反时唯一会露馅的地方；
- 假玩家记得挂 `Connection`（§4.43），负向对照别用原版物品。

## 7. 权威情报来源（怎么查原版行为，别靠记忆）
"""
    text = rep(text, old, new, u"§6.17 新增")

    # ---------- ④ §9 加 ZF70 待验证块 ----------
    old = (u"- [ ] **ZF66 我替你定的三个数**")
    new = (u"- [ ] **ZF70：等你试三个进度**（成品见本轮汇报）。三条都是**普通成就**（会弹提示、会在聊天栏播报）：\n"
           u"      ① **新的开始！** —— 拿到**低级发电机**就该弹（图标=低级发电机）；\n"
           u"      ② **更强劲的电源**（前置=新的开始！）—— **发电机和动力能源捕获器两个都拿到**才弹。\n"
           u"      ⚠ 特意提醒：**只拿发电机不会弹**（这是你那个「和」字的判据，我第一版写成了「或」，被探针抓出来了，见 §4.42）；\n"
           u"      ③ **入门清洁能源**（前置=新的开始！）—— **放下一个太阳能板**就该弹（放别的方块不算）。\n"
           u"      另外请看：进度界面左侧应当多出一个**新的标签页**（图标=低级发电机，底图=一般金属块那张贴图）。\n"
           u"      创造模式拿物品**也会**触发（`inventory_changed` 认的是「背包里有了一件」）。\n"
           u"- [ ] ZF70 说明：**「和」= 两个都要**。如果你想改成「或」（拿到任意一个就算），\n"
           u"      把 `stronger_power.json` 的 `requirements` 从 `[[generator],[power_capturer]]` 改成\n"
           u"      `[[generator, power_capturer]]` 即可（一行，改完跑 `python build/zftools/_zf70_verify.py` 会提醒你语义变了）。\n"
           u"- [ ] ZF70 说明：**英/日/俄三个语言的标题与描述是我译的**（你只给了中文），译文列在汇报里，\n"
           u"      要改哪句直接说。\n"
           u"- [ ] **ZF66 我替你定的三个数**")
    text = rep(text, old, new, u"§9 ZF70 待验证块")

    # ---------- 落盘 ----------
    if fails:
        print(u"**有失败项，未写盘**：")
        for f in fails:
            print(u"  !! " + f)
        return 1
    with io.open(DOCS, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    after_lines = text.count("\n") + 1
    print(u"已改 %d 处：" % len(applied))
    for a in applied:
        print(u"  [OK] " + a)
    print(u"行数 %d -> %d" % (before_lines, after_lines))
    print(u"失败项 = 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
