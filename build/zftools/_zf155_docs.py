# -*- coding: utf-8 -*-
u"""_zf155_docs.py —— ZF155 文档落地（幂等，默认 dry-run）。

  ① 档案 **§4.163**：运行期加宽配方表的五条实证；
  ② 档案 **§5** 加 ZF155 行；
  ③ 档案 **§9** 加 ZF155 小节（**待用户实测**）；
  ④ 交接 **§1** 活体数字（语言键数 / 配方份数）+ **§6** 加第 31 条；
  ⑤ 英文公告末尾加一条（§4.150 日志纪律）。

跑法：python build\\zftools\\_zf155_docs.py [--write]
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", "开发档案.md")
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

notes, fails, plan = [], [], []


def want(text, old, new, label):
    if new in text:
        notes.append(u"  [跳过] %s（已经在，幂等）" % label)
        return text
    if text.count(old) != 1:
        fails.append(u"%s：锚点命中 %d 次（应为 1）" % (label, text.count(old)))
        return text
    notes.append(u"  [改] %s" % label)
    return text.replace(old, new, 1)


D4_TITLE = (u"### 4.163 【工具雷】运行期加宽配方表：官方口子 / 挂点先后 / 纹饰为何不可能 / "
            u"包私有字段怎么绕 / 锚点要吃掉空行（0.12 ZF155）")
D4 = D4_TITLE + u"""

用户原话：「**能不能加个通用升级模板 所有mod需要升级模板升级都可以用它 如果有冲突则不可以使用**」，
并拍板要**真·通用**（含原版下界合金）。做法不是改别人的数据文件，而是**在服务端把配方表装好之后原地加宽**：
凡模板槽要东西的 `minecraft:smithing_transform` 升级，模板槽一律由「原模板」加宽成「原模板 **或** 通用模板」，
**id 一个字不变**（不加副本 ⇒ JEI 里不会出现两条一模一样的升级）。五条实证，条条有出血点：

**① 换表有官方口子，一行反射都不需要。**
`RecipeManager.replaceRecipes(Iterable<RecipeHolder<?>>)` 是 **NeoForge 加的 public 方法**
（`RecipeManager.java:165`，本轮从 sources.jar 现读）：它就地重建 `byType`/`byName` 两张表。
⚠ 那两个字段本身是 `private` **且是 `Immutable*`**（第 40-41 行），自己动手既改不动也没必要 ——
`setAccessible` 那套在本轮**零出现**（常驻门 D4 专门盯着"引擎源码里不许出现反射"）。

**② 挂点必须在「配方包发出去」之前；而 `/reload` 会换掉整个 RecipeManager。**
`OnDatapackSyncEvent` 的 javadoc 原文就是「Fires when a player joins the server or when the reload
command is ran, **before tags and crafting recipes are sent to the client**」；两条路径都实读过：
登录 `PlayerList.java:208-209`、`/reload` `PlayerList.java:916-921` —— 事件先发、配方包后发
⇒ 在这里换表，客户端（含 JEI）拿到的是**换过之后**的表。
② 的后半段更要命：`/reload` 走 `MinecraftServer.reloadResources`（第 1504 行），
第 1532 行 `this.resources = p_335203_` 把 **RecipeManager 整个换成新实例**，第 1540 行才调
`getPlayerList().reloadResources()` 去发事件 ⇒ 加宽**必须每次重装**，而且要幂等
（本轮用「管理器实例 + 配方 id 内容签名」做键缓存，探针 F1/F2 用**真跑一次 `/reload`** 验的）。

**③ 盔甲纹饰**注定**不可能通用 —— 图案与模板物品是绑死的。**
`TrimPatterns.getFromTemplate` 的实现是 `template.is(pattern.templateItem())`（`TrimPatterns.java:59`），
而 `TrimPattern` 是个 record，字段里就有 `Holder<Item> templateItem`（`TrimPattern.java:18`）
⇒ 通用模板不属于任何图案，`SmithingTrimRecipe.assemble` 里的两个 `Optional` 必有一个是空、
**必返 `ItemStack.EMPTY`**。给纹饰加宽只会造出"界面匹配得上、产物是空"的假配方 ⇒ 一律跳过
（理由码 `trim-pattern-bound`，原版 18 条纹饰全在里面）。

**④ 三个槽是包私有 final ⇒ 走官方编解码器往返，而且**必须**逐物品复核。**
`SmithingTransformRecipe` 的 `template/base/addition/result` 全是**包私有 final**（本类在
`com.potatost.mod`，拿不到），所以用 `RecipeSerializer.SMITHING_TRANSFORM.codec()` 编码成 JSON、
再用 `Ingredient.CODEC` 解回来，最后 {@code new SmithingTransformRecipe(...)} 造加宽副本。
往返**一定**要复核：对注册表里**每一件物品**逐一比对「原件判定」与「解回来的判定」同真同假
（三个槽都比），任何一处不一致就整条放弃（`fidelity-template` / `fidelity-base` / `fidelity-addition`）。
⚠ 只认**恰好**是 `SmithingTransformRecipe` 这个类的配方：子类走的是别的序列化器，
按原版序列化器编码会**丢字段**（记 `foreign-serializer`，宁可不加宽）。
本轮的现场数据（探针报告 `_zf155_probe_utf8.txt`，28 项全绿）：
表里锻造配方 **38** 条 ⇒ 加宽 **15** 条 = 原版下界合金 **9** + **Create 6**（它的下界合金潜水装备，
其中 3 条附加物是 **tag** `c:ingots/netherite` —— 保真复核对 tag 也没红）；
跳过 18 条纹饰；冲突 **0**；**表里的锻造配方总数装前装后都是 38**（原地换，不是加副本）。

**⑤ 探针挂载块必须把前导空行一起吃掉（这是本轮踩到的、也是纠了 ZF151 那笔账）。**
上一版锚点写的是 `    }\\n\\n    private void registerCapabilities(`，而插入块自带一个前导 `\\n`
⇒ 挂载后 `    }` 前多一行，摘除只删块本身 ⇒ **摘完比改前多 2 行空白**。
（ZF151 那条线的卸载脚本当时看到这个差异，把它记成"别人这几分钟改的"——其实是我这套锚点的必然产物。）
改法：把 `\\n\\n` 放进锚点、再由替换原样写回去，挂载/卸载就**严格互逆**。
本轮实测：摘完后 `PotatoST.java` 的 sha1 = 改前件的 `995fa43862986a70f1f2072b92e2742975d1f55a`，
**逐字节相同**。

**⑥ 冲突判据取「双槽重合」而不是「配方签名相等」。**
两条升级若**底物能对上同一件、附加物也能对上同一件、结果却不同**，玩家把通用模板放进去时
游戏没法判断他要哪一个 —— 这就是「有冲突则不可以使用」。本轮取**物品级重合**（底物集合相交 ∩
附加物集合相交 ∩ 结果不同），比"签名完全相等"更严：宁可保守，也不放一条会出错的进去。
探针 D1/D2/D3 直接喂**合成配方**给生产代码 `plan()` 验：同底同料不同结果的两条**都**进 `conflicts`
且都不加宽；只有底物重合、材料不同的第三条**能**加宽。
"""

D5_ROW = (u"| ZF155 | **新建 `zf155_pre`**（**108 份**：`ModItems.java` / `PotatoST.java`（⚠ 探针挂载点，"
          u"动手前就在清单里）/ 五份 lang / 4 份振金护甲 smithing 配方 / 三份文档 / 全部常驻门 / "
          u"成品 0.12 + `.sha1` + `build\\libs` 那份；逐份核 sha1 + 回读，失败 0。"
          u"⚠ 开工前查过轮号：`_zf155_*` 没人占、救援目录里没有 `zf155_pre`（§4.147））"
          u" | 0.12：**通用升级模板**（用户原话「能不能加个通用升级模板 所有mod需要升级模板升级都可以用它 "
          u"如果有冲突则不可以使用（然后给振金剑加个配方 钛合金剑用这个和振金升级 之前所有的振金装备"
          u"下界合金模板也改成这个）获取方式；下界合金升级模板 围一圈铝锭」）。① 新增物品 "
          u"`potato_s_t:universal_upgrade_template`（原版 `SmithingTemplateItem` 子类，tooltip 原版三段式 + "
          u"一行规则）+ 16x16 贴图（脚本画的占位）+ 5 语 7 键。② 获取方式：**八块铝锭围一圈 + 中间一张"
          u"下界合金升级模板**（`crafting_shaped`，与原版那张复制配方形状不同、不打架）。"
          u"③ **真·通用**：`UniversalUpgradeTemplate` 在 `ServerStartedEvent` + `OnDatapackSyncEvent`（登录 / "
          u"`/reload`）把每条 `smithing_transform` 的模板槽**原地**加宽成「原模板 ∪ 通用模板」"
          u"（`RecipeManager.replaceRecipes`，零反射；id 不变 ⇒ 表里数量不变）。"
          u"④ 纹饰一律跳过（图案与模板物品绑死，§4.163③）；子类序列化器 / 保真复核不过的一律跳过并记原因码。"
          u"⑤ **冲突即禁用**：底物 ∩ 附加物都重合而结果不同的两条，**都不许**用通用模板（探针 D1-D3 验）。"
          u"⑥ 振金剑配方 + 4 件振金护甲换模板（下界合金模板不再能升振金 —— 用户要求「也改成这个」）。"
          u"⑦ 探针 `Zf155Check`（真开服，**含真跑一次 `/reload`**）**28 项 ALL OK**："
          u"加宽 15 条（原版 9 + Create 6，含 3 条 tag 原料）/ 纹饰 18 条全跳过 / 冲突 0 / "
          u"锻造配方总数不变 / 真查表真 assemble（下界合金与振金剑都出得来）/ 负对照（下界合金模板不再升振金、"
          u"纹饰不吃通用模板）/ `/reload` 之后加宽自己回来 | 见 §9 ｜ 见 §4.163 |\n")

D9_ANCHOR = u"## 10. 备份策略"
D9 = u"""### ZF155（0.12）通用升级模板：**全游戏所有升级都能用它** + 冲突即禁用 —— **待你实测**

用户原话：「**能不能加个通用升级模板 所有mod需要升级模板升级都可以用它 如果有冲突则不可以使用
（然后给振金剑加个配方 钛合金剑用这个和振金升级 之前所有的振金装备下界合金模板也改成这个）
获取方式；下界合金升级模板 围一圈铝锭**」。拍板：**真·通用**（含原版下界合金）。

**你手上要试的七件事**

| # | 怎么试 | 应该看到 |
|---|---|---|
| 1 | 3×3 里**八块铝锭围一圈**、中间放**一张下界合金升级模板** | 出 **1 个通用升级模板**（模板本身会被消耗掉） |
| 2 | 锻造台：钻石头盔 + 下界合金锭 + **通用升级模板** | 出下界合金头盔（**原版下界合金模板照旧能用**，两条路都通） |
| 3 | 锻造台：**钛合金剑** + 振金锭 + **通用升级模板** | 出**振金剑**（这是本轮新加的配方；之前它只能创造模式拿） |
| 4 | 锻造台：钛合金头盔/胸甲/护腿/靴子 + 振金锭 + **通用升级模板** | 出对应振金件（4 件都改用它了） |
| 5 | ⚠ 锻造台：钛合金头盔 + 振金锭 + **下界合金模板** | **不出东西**（你要求"也改成这个"，所以下界合金模板对振金升级**不再生效**） |
| 6 | 装了 Create 的话：铜制潜水头盔/靴子/背罐 + 下界合金锭 + **通用升级模板** | 出 Create 的下界合金潜水装备（**别的 mod 的升级也一并认它** —— 现场实测到 6 条） |
| 7 | 盔甲纹饰：钻石胸甲 + 金锭 + **通用升级模板** | **不出东西**。纹饰的图案与模板物品是**绑死**的（§4.163③），所以它吃不了通用模板；原来的纹饰模板照旧能用 |

**关于「有冲突则不可以使用」**：两条升级如果**底物与材料完全对得上同两件东西、结果却不同**，
那两条**都不认**通用模板（照旧只认各自的模板）。判别口径与实测见 §4.163⑥（探针 D1-D3）。
本轮你装的那一堆 mod（原版 + Create）里**冲突数 = 0**，所以日常用不到这条。

**`/reload` 安全**：`/reload` 会把配方表整张重建，本轮的挂点在**配方包发出去之前**重装一次
（探针 F1/F2 是真跑了一次 `/reload` 验的）。

**已知边界**：① 只对 `minecraft:smithing_transform` 生效；`smithing_trim`（纹饰）与**自定义序列化器**的
锻造配方不管（有日志，理由码 `trim-pattern-bound` / `foreign-serializer`）；
② 三个槽的保真复核用的是"每件物品的默认堆"，按组件区分的花式原料只能验到物品级；
③ 贴图是我按"下界合金框 + 铝白面板 + 向上箭头"脚本画的**占位**（你没给素材），要换直接换
`textures/item/universal_upgrade_template.png`，记得同步改 `_zf155_verify.py` 里的哈希。

---

"""

H6_ANCHOR = u"""    ③ 谁要拿 ZF139 的探针源码复核那轮结论，**以报告 `_zf139_probe_utf8.txt` 为准**（52 项全绿那份）。"""
H6_NEW = H6_ANCHOR + u"""

31. **ZF155 的账（通用升级模板）**：① 用户原话见档案 §9。做的是**一件新物品 + 一台"运行期加宽器"**：
    `universal_upgrade_template`（原版 `SmithingTemplateItem` 子类）+ `UniversalUpgradeTemplate`
    （`ServerStartedEvent` / `OnDatapackSyncEvent` 两个挂点，用 `RecipeManager.replaceRecipes`
    **原地**把每条 `smithing_transform` 的模板槽加宽成「原模板 ∪ 通用模板」）。
    ② **我定的、用户没说的**（改都是一处）：加宽只在**服务端运行期**做（数据文件一个字没动别人的）；
    只认**恰好**是 `SmithingTransformRecipe` 的配方；纹饰一律跳过；冲突判据取"底物 ∩ 附加物都重合
    且结果不同"；保真复核用"每件物品的默认堆"；生成的新表 id 形如
    `potato_s_t:universal/<命名空间>/<原路径>`（本轮因为**原地换 id**，实际没有新增 id）。
    ③ **贴图是占位**（用户没给素材）：脚本画的 16x16，哈希钉在 `_zf155_verify.py` 的 `TEX_SHA1`；
    用户给素材后换图 + 改哈希 + 跑 `_zf155_verify.py` 一遍即可。
    ④ ⚠ **本轮顺手纠了 ZF151 的一笔账**：那轮的探针挂载块把前导空行吃掉了，摘完 `PotatoST.java`
    比改前**多 2 行空白**，它当时记成"别人这几分钟改的"——其实是锚点的必然产物。本轮把 `\\n\\n`
    放进锚点，摘完与改前件**逐字节相同**（§4.163⑤）。"""

ANN_ADD = u"""
## New in 0.12 ZF155 - Universal Upgrade Template

- **New item: Universal Upgrade Template** (`potato_s_t:universal_upgrade_template`).
  Craft it in a 3x3 grid: **one Netherite Upgrade Smithing Template in the centre, eight
  Aluminium Ingots around it**.
- **It works for every upgrade that needs a template - including vanilla netherite and other mods.**
  At runtime the server widens every `minecraft:smithing_transform` recipe so its template slot
  accepts **either the original template or the Universal Upgrade Template**. Recipes are replaced
  **in place** (same ids), so JEI will not show duplicate entries.
  Measured on this pack: 9 vanilla netherite upgrades + 6 Create netherite diving upgrades were
  widened; the original templates keep working exactly as before.
- **Vibranium gear now uses it**: the vibranium sword is craftable at last
  (Titanium Alloy Sword + Vibranium Ingot + Universal Upgrade Template), and the four vibranium
  armour pieces were switched over. The netherite template **no longer** upgrades vibranium gear.
- **Conflicts are refused**: if two upgrades accept the same base *and* the same material while
  producing different results, neither of them accepts the Universal Upgrade Template.
- **Armour trims do not take it**: a trim pattern is bound to one specific template item, so the
  Universal Upgrade Template cannot stand in for a trim template.
- Works across `/reload` (the table is re-widened before recipes are sent to clients).
"""


def main(argv):
    write = u"--write" in argv

    doc = io.open(DOC, encoding=u"utf-8", newline=u"").read()
    nums = [int(m.group(1)) for m in re.finditer(u"(?m)^#{3,4} 4\\.([0-9]+)", doc)]
    mx = max(nums)
    already = D4_TITLE in doc
    print(u"档案 §4 最大编号 = %d（目标 §4.163；已写入 = %s）" % (mx, already))
    if not already and mx != 162:
        fails.append(u"§4 编号不是 163（实测 max=%d）—— 停手先看清" % mx)

    doc2 = want(doc, D9_ANCHOR, D9 + D9_ANCHOR, u"档案 §9 加 ZF155 小节")
    if D4_TITLE not in doc2:
        j = doc2.find(u"\n| ZF15")
        if j < 0:
            fails.append(u"档案：找不到 §5 的 ZF15x 行，没处插 §4.163")
        else:
            k = doc2.rfind(u"\n", 0, j)
            doc2 = doc2[:k] + u"\n" + D4 + doc2[k:]
            notes.append(u"  [改] 档案 §4.163")
    if u"| ZF155 |" in doc2:
        notes.append(u"  [跳过] 档案 §5 的 ZF155 行（已经在，幂等）")
    else:
        rows = [m.start() for m in re.finditer(u"(?m)^\\| ZF15", doc2)]
        if not rows:
            fails.append(u"档案：§5 里一行 ZF15x 都没有")
        else:
            last = rows[-1]
            j = doc2.find(u"\n", last)
            doc2 = doc2[:j + 1] + D5_ROW + doc2[j + 1:]
            notes.append(u"  [改] 档案 §5 加 ZF155 行（接在最后一行 ZF15x 之后）")
    if doc2 != doc:
        plan.append((DOC, doc, doc2))

    hand = io.open(HAND, encoding=u"utf-8", newline=u"").read()
    h2 = hand
    old_keys = u"| 语言键数 | **587 键 × 4**"
    new_keys = u"| 语言键数 | **594 键 × 4**"
    if new_keys in h2:
        notes.append(u"  [跳过] 交接 §1 语言键数（已经是 594）")
    elif h2.count(old_keys) == 1:
        h2 = h2.replace(old_keys, new_keys, 1)
        h2 = h2.replace(u"（lzh = 589 = 四份 + `language.name` / `language.region`）",
                        u"（lzh = 596 = 四份 + `language.name` / `language.region`）", 1)
        h2 = h2.replace(u"→ **587**（ZF153 振金剑：物品名 + 三行说明 = **+4**）",
                        u"→ **587**（ZF153 振金剑：物品名 + 三行说明 = **+4**）"
                        u"→ **594**（ZF155 通用升级模板：物品名 / 升级 / 适用于 / 原料 / 底物槽 / 材料槽 / "
                        u"规则 = **+7**）", 1)
        notes.append(u"  [改] 交接 §1 语言键数 587 → 594（lzh 589 → 596）")
    else:
        fails.append(u"交接 §1 语言键数锚点命中 %d 次" % h2.count(old_keys))

    old_rec = u"`data\\potato_s_t\\recipe\\` **74 份**"
    new_rec = (u"`data\\potato_s_t\\recipe\\` **91 份**（递归数，含 `pressing/` 子目录 7 条；"
               u"按类型：`crafting_shaped` 68 / `crafting_shapeless` 5 / **`smithing_transform` 5** / "
               u"`blasting` 4 / `smelting` 2 / `create:pressing` 7）")
    if old_rec in h2:
        h2 = h2.replace(old_rec, new_rec, 1)
        notes.append(u"  [改] 交接 §1 配方份数 74 → 91（顺带写清类型分布）")
    elif new_rec in h2:
        notes.append(u"  [跳过] 交接 §1 配方份数（已经是 91）")
    else:
        notes.append(u"  ⚠ 交接 §1 配方份数那行的措辞变了，本轮不动它（别人的口径）")

    h2 = want(h2, H6_ANCHOR, H6_NEW, u"交接 §6 加第 31 条")
    if h2 != hand:
        plan.append((HAND, hand, h2))

    ann = io.open(ANN, encoding=u"utf-8", newline=u"").read()
    if u"## New in 0.12 ZF155" in ann:
        notes.append(u"  [跳过] 公告 ZF155 那一条（已经在，幂等）")
    else:
        plan.append((ANN, ann, ann.rstrip(u"\n") + u"\n" + ANN_ADD))
        notes.append(u"  [改] 公告末尾加 ZF155 那一条")

    print(u"\n".join(notes))
    print(u"")
    print(u"计划写盘 %d 份" % len(plan))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    if fails or not write:
        if not write:
            print(u"（没加 --write，只算不写）")
        return 1 if fails else 0
    for path, _old, new in plan:
        io.open(path, u"w", encoding=u"utf-8", newline=u"").write(new)
        print(u"  已写 %s" % os.path.relpath(path, ROOT))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
