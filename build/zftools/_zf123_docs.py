# -*- coding: utf-8 -*-
u"""_zf123_docs.py —— ZF123 的文档三件套（锚点替换，逐处断言"原文只出现一次"）

① `docs\\开发档案.md` §4 新增 **4.101**（客户端插件注册没有探针 ⇒ JEI 一崩全没），插在 `## 7.` 之前；
② 同文件 §5 表格追加 **ZF123** 行（接在 ZF122 行后面）；
③ 同文件 §9 追加 **ZF123** 小节（插在 `## 10. 备份策略` 之前）；
④ `docs\\多会话协作交接.md`：§6 追加第 15 条欠账。

跑法：
    python build\\zftools\\_zf123_docs.py            # 只校验
    python build\\zftools\\_zf123_docs.py --write    # 落盘
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, r"docs\开发档案.md")
HAND = os.path.join(ROOT, r"docs\多会话协作交接.md")

A4_OLD = u'''## 7. 权威情报来源（怎么查原版行为，别靠记忆）'''

A4_NEW = u'''### 4.101 【客户端雷】JEI 的插件注册**没有探针**：一台机器漏个 case，整个模组的配方页全没（0.11 ZF123，用户实测）

用户报「jei看不到合金冶炼炉的配方了」。查 `run\\client\\logs\\` 捞到现场：

```
[ERROR] [mezz.jei.library.load.PluginCaller/]: Caught an error from mod plugin:
        class com.potatost.mod.client.jei.PotatoSTJeiPlugin potato_s_t:jei_plugin
java.lang.IllegalArgumentException: Ingredient is invalid and cannot be used as a drawable ingredient:
        0 minecraft:air minecraft:air components:{}
    at mezz.jei.library.gui.helpers.GuiHelper.createDrawableIngredient(GuiHelper.java:128)
    at com.potatost.mod.client.jei.PotatoSTJeiPlugin.registerCategories(PotatoSTJeiPlugin.java:133)
java.lang.IllegalArgumentException: Recipe catalyst must be a valid ingredient
    at com.potatost.mod.client.jei.PotatoSTJeiPlugin.registerRecipeCatalysts(PotatoSTJeiPlugin.java:160)
java.lang.IllegalStateException: There is no recipe category registered for:
        RecipeType[uid=potato_s_t:micro_crusher, ...]
```

**病根就一行**：`MACHINES` 里 12 台机器，`iconFor()` 的 switch 只有 **11 个 `case`** ——
ZF112（`0a286b8`，2026-09-25 22:19）往 `MACHINES` 里加了 `lithium_battery_plant`，
**忘了在 `iconFor` 里加对应的 `case`** ⇒ 返回 `ItemStack.EMPTY` ⇒ JEI 在
`createDrawableItemStack` 抛异常 ⇒ `PluginCaller` 捕获后**把这一次注册的结果整个丢掉**
⇒ **12 台机器的 JEI 页面一台都没有**（用户看到的"合金炉配方没了"只是他顺手点的那台）。

**时间线是用日志切出来的**：`2026-09-25-1`（22:24 那场）**绿**，
`2026-09-25-2`（22:30 那场）起**每场都红** —— 正好卡在那个 22:19 的提交上；
红的那场里最后一个注册成功的分类是 `ammonia_synthesis_chamber`（= MACHINES 里锂电前面那台），
`lithium_battery_plant` 那条**从来没出现过** ⇒ 就是它。

**为什么整整一天没被发现**（三条叠加）：

1. 本工程的探针**全是服务端**的（`runServer`），而 **JEI 是纯客户端**；
2. 常驻校验只看"源码里 MACHINES 有几台 / JEI 分类数是不是 12"—— 那两个数**一直是对的**；
3. 崩的结果是"**少了一整块 UI**"，不崩溃、不弹窗，只有真的打开 JEI 才看得见。

**规矩**：

1. **凡是"列表 A 与 switch B 必须一一对应"的地方，两处都要有常驻检查**：
   本轮把 `MACHINES ↔ iconFor` 的逐一对应钉进 `_zf123_verify.py`（含"不许有多余 case"），
   反证刀 K178 **专门把那个 case 删掉复现用户那一场**。
2. **注册回调里绝不让一个坏元素带走整批**：icon 为空 ⇒ **记 ERROR + 跳过这一台**，
   而不是把空物品交给第三方（JEI 的选择是"整批作废"）。ZF123 起 `registerCategories` 与
   `registerRecipeCatalysts` 两处都有这道兜底，收尾还会打印"跳过了谁"。
3. **客户端行为只能靠用户的眼睛当最后一关**：这次是用户报的、不是门报的。
   以后加机器 / 加 JEI 分类，自测清单里必须有一条：**打开 JEI 搜一下这台机器**。

## 7. 权威情报来源（怎么查原版行为，别靠记忆）'''

A5_TAIL = u'''| 见 §9 |



> ZF40~ZF44 全是**电力高炉的连续改动**'''

ROW = u'''| ZF123 | **新建 `zf123_pre`**（**106 份**改前件：`client\\jei\\PotatoSTJeiPlugin` / `MachineRecipeCategory` / `MachineRecipes` / `PotatoST` + 四份 lang + 全部常驻校验脚本 + 3 份文档 + 旧成品 jar 与 `.sha1` + **两份取证客户端日志**（`2026-09-25-1/-2`，怕日志轮转把现场冲掉）；逐份核哈希 + **回读证明**、失败 0） | 0.11：**修 JEI 那个"一崩全没"的客户端雷**（用户实测：「jei看不到合金冶炼炉的配方了」）。① **病根一行**：`PotatoSTJeiPlugin.MACHINES` 12 台，`iconFor()` 的 switch 只有 11 个 case —— **ZF112（`0a286b8`，09-25 22:19）加 `lithium_battery_plant` 时漏了 case** ⇒ 返回 `ItemStack.EMPTY` ⇒ JEI 在 `createDrawableItemStack` 抛 `Ingredient is invalid … 0 minecraft:air` ⇒ `PluginCaller` 把**整次注册**丢掉 ⇒ **12 台机器一台的 JEI 页面都没有**（用户点的合金炉只是其中一台）；② **时间线靠日志切出来**：`2026-09-25-1`（22:24 那场）绿 / `2026-09-25-2`（22:30）起每场都红，正好卡那个提交；红场里最后一个成功分类是 `ammonia_synthesis_chamber`（锂电前一台），`lithium_battery_plant` **从未出现**；③ **修法**：补 case + **两处注册各加一道兜底**（空 icon ⇒ 记 ERROR + **只跳过这一台**，不再让一个坏元素带走整批）+ 收尾横幅打印"跳过了谁"；④ **新雷 §4.101**：本工程探针全是服务端的，**JEI 是纯客户端**，静态检查看的是"源码里的台数"（一直是对的）⇒ 这类雷只能靠"用户打开 JEI 看一眼"，所以把 `MACHINES ↔ iconFor` 的逐一对应钉成常驻检查；⑤ 用户报的第二件事「星璨钢貌似还只有英文名称了」—— **盘上查不出问题**：写了 `_zf123_langaudit.py` 做四项体检（四语言键集合一致 / zh 值与 en 值相同 = 没翻译 / **重复键**（后一个赢，能把中文静默顶成英文）/ 92 个注册 id 有没有语言键），**四项全绿**，`item.potato_s_t.star_steel_ingot` 在 zh_cn 就是「星璨钢锭」⇒ **不瞎改**，等用户补线索（在哪看到、同一处别的物品是不是中文）；⑥ 证据：探针 `Zf123Check` **不适用**（本轮改的是纯客户端 JEI 注册，无头服务端跑不到那段代码）⇒ 证据换成**客户端日志 + 源码逐一对应 + 反证刀**；`_zf123_verify.py`（**34 项**）、反证 **K178~K182 五把刀** | 见 §9 |'''

A9_ANCHOR = u'''## 10. 备份策略'''

A9_NEW = u'''### ZF123（0.11）修 JEI：一台机器漏个 case，整个模组的配方页全没 —— **待你实测**

你报的两件事，一件查清了、一件没查出来（如实说）：

#### 一、「jei看不到合金冶炼炉的配方了」= **真的坏了，而且不止合金炉**

| | |
|---|---|
| 现场 | `run\\client\\logs\\2026-09-25-2.log.gz` 起每一场都报 `IllegalArgumentException: Ingredient is invalid and cannot be used as a drawable ingredient: 0 minecraft:air`，栈顶是 `PotatoSTJeiPlugin.registerCategories(:133)` 与 `registerRecipeCatalysts(:160)`；紧接着 JEI 抱怨 `There is no recipe category registered for: RecipeType[uid=potato_s_t:micro_crusher…]` |
| 病根 | `MACHINES` 里 **12 台**机器，`iconFor()` 的 switch 只有 **11 个 case** —— ZF112（`0a286b8`，**2026-09-25 22:19**）加「锂电池构造间」时，把它加进了 `MACHINES` 却**没加进 `iconFor`** ⇒ 返回空物品 ⇒ JEI 抛异常 ⇒ **整个插件这一次注册的结果全被丢掉** |
| 影响面 | **不是合金炉一台**：12 台机器的 JEI 页面**一台都没有**（你点的合金炉只是顺手那台） |
| 多久了 | 从 **09-25 22:19** 起，整整一天。日志边界切得很干净：`2026-09-25-1`（22:24 那场）绿，`2026-09-25-2`（22:30 那场）起全红 |
| 为什么没早发现 | 我们的探针**全是服务端的**（`runServer`），JEI 是**纯客户端**；常驻校验只看"源码里 MACHINES 有几台"——**那个数一直是对的**；崩的表现是"少了一整块 UI"，不崩溃不弹窗 |

**修法（三处）**：

1. 补上 `case "lithium_battery_plant"`；
2. `registerCategories` 与 `registerRecipeCatalysts` **各加一道兜底**：icon 为空就
   **记 ERROR + 只跳过这一台**，不再把空物品交给 JEI（它的选择是"整批作废"）
   —— 以后再有人加机器忘了加 case，坏的只是那一台；
3. 收尾横幅打印"注册了几台 / 跳过了谁"，让"JEI 到底活没活"在日志里一眼可见。

**要你做的**：**重启客户端**（dev 客户端要重启才会加载新类），然后打开 JEI 搜一下
「合金冶炼炉 / 锂电池构造间 / 微型粉碎机」—— 12 台机器都应该有配方页了。
日志里应当出现 `JEI: registered 12 machine recipe categories [...]`（以前是 `11` + 一条 ERROR）。

#### 二、「星璨钢貌似还只有英文名称了」= **盘上查不出问题**（等你补一条线索）

我用新写的 `build\\zftools\\_zf123_langaudit.py` 把"名字为什么是英文"的四种可能逐条查了：

| 查什么 | 结果 |
|---|---|
| 四份 lang 的键集合是否一致 | **一致**（464 键 ×4） |
| 有没有"中文值 == 英文值"（= 没翻译） | **没有**（白名单只有 `itemGroup.potato_s_t` = 商标名） |
| 有没有**重复键**（JSON 后一个赢，能把中文静默顶成英文） | **没有** |
| 92 个注册 id 是不是都有语言键 | **都有** |
| `item.potato_s_t.star_steel_ingot` 在 zh_cn 是什么 | **星璨钢锭**（与 en 的 Star Steel Ingot 不同） |

⇒ 所以**不是**语言文件的问题，我也**没有瞎改**。麻烦你补一句：**在哪儿看到的**（JEI 物品列表 /
背包 tooltip / 成就界面 / 机器界面 / 创造页）、**同一处别的物品是不是中文**、当时客户端语言是不是中文
（`run\\client\\options.txt` 里现在是 `lang:zh_cn`）。有截图最好。

#### 三、证据

| 项 | 值 |
|---|---|
| 探针 | **本轮没有探针**（如实说）：改的是**纯客户端**的 JEI 注册回调，无头服务端根本跑不到那段代码 |
| 证据换成 | ① 客户端日志的**前后对照**（`2026-09-25-1` 绿 / `2026-09-25-2` 红，两份都拷进改前件留档）；② `MACHINES` 与 `iconFor` 的 case **逐一对应**（12 ↔ 12，本轮前是 12 ↔ 11）；③ `_zf123_verify.py` **34 项**；④ 反证刀 **K178~K182 五把**（K178 就是"把那个 case 再删掉"，复现你今天遇到的那一场） |
| 实测 | **要你重启客户端看一眼**（JEI 是客户端行为，我们验不到） |

**成品**：**本轮没有新成品** —— `release\\PotatoST-0.11.jar` 仍是 ZF114 打的 **`303c5d468b96826ef6836b0a4e54ccb8a539557c`**（432 键，**不含 ZF116~ZF123**）。

## 10. 备份策略'''

H15_OLD = u'''    ⑤ 我**撤掉的菜单那层门**改变了 ZF49 的一条老行为（「消耗槽目前放不了东西」）——
    如果你认为那两格就该只让自动化塞，说一声，撤回来是一处（删掉那段 override 即可）。'''
H15_NEW = u'''    ⑤ 我**撤掉的菜单那层门**改变了 ZF49 的一条老行为（「消耗槽目前放不了东西」）——
    如果你认为那两格就该只让自动化塞，说一声，撤回来是一处（删掉那段 override 即可）。
15. **ZF123 的账（JEI 这口锅是 ZF112 的，主项目线本轮修掉）**：① **`PotatoSTJeiPlugin.MACHINES`
    与 `iconFor` 的 case 必须一一对应** —— ZF112 漏了一个 `case "lithium_battery_plant"`，
    结果从 09-25 22:19 起**整个模组的 JEI 页面全没了**（12 台机器一台不剩），
    用户 09-26 才报上来；`_zf123_verify.py` 现在钉着这条（K178 复现）。
    ② **以后加机器**：`MACHINES` + `iconFor` + `MachineRecipes` + `ModBlocks` 四处一起加，
    加完**打开 JEI 搜一下这台机器**（客户端行为没有探针，见 §4.101）。
    ③ 用户报的「星璨钢只有英文名」在盘上查不出问题（`_zf123_langaudit.py` 四项全绿），
    等用户补线索 —— **别瞎改语言**。
    ④ 本轮**没有探针**（改的是纯客户端代码），证据是客户端日志前后对照 + 源码逐一对应 + 5 把反证刀。'''

EDITS = [(DOC, A4_OLD, A4_NEW, u"§4.101 新雷"),
         (DOC, A9_ANCHOR, A9_NEW, u"§9 ZF123 小节"),
         (HAND, H15_OLD, H15_NEW, u"交接 §6 第 15 条")]


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)


def main(argv):
    do_write = "--write" in argv
    fails, done, cache = [], 0, {}
    for path, old, new, label in EDITS:
        if path not in cache:
            cache[path] = read(path)
        txt = cache[path]
        if new.strip()[:40] in txt and old not in txt:
            print(u"  [跳过] %-24s %s（幂等）" % (label, os.path.basename(path)))
            done += 1
            continue
        n = txt.count(old)
        if n != 1:
            fails.append(u"%s 的锚点「%s」命中 %d 次（应为 1）" % (os.path.basename(path), label, n))
            continue
        cache[path] = txt.replace(old, new, 1)
        print(u"  [改]   %-24s %s" % (label, os.path.basename(path)))
        done += 1

    doc = cache[DOC]
    if u"| ZF123 |" not in doc:
        n = doc.count(A5_TAIL)
        if n != 1:
            fails.append(u"§5 表格尾锚点命中 %d 次（应为 1）" % n)
        else:
            doc = doc.replace(A5_TAIL, u"| 见 §9 |\n" + ROW +
                              u"\n\n\n\n> ZF40~ZF44 全是**电力高炉的连续改动**", 1)
            print(u"  [改]   §5 表格追加 ZF123 行")
            done += 1
    else:
        print(u"  [跳过] §5 表格 ZF123 行（已加过，幂等）")
        done += 1
    cache[DOC] = doc

    if fails:
        print(u"")
        print(u"锚点对不上，**一个字节都没写**：")
        for f in fails:
            print(u"  !! " + f)
        return 1
    if do_write:
        for p, txt in cache.items():
            write(p, txt)
        print(u"\n落盘：%d 个文件" % len(cache))
    else:
        print(u"\n（只校验，没落盘；加 --write 才写）")
    print(u"通过 = %d   失败 = 0" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
