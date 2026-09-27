# -*- coding: utf-8 -*-
u"""_zf148_docs.py —— ZF148 文档四处落地（幂等，默认 dry-run）。

  ① 档案 **§4.151**：帕秋莉手册这一轮踩到的四个坑（工具雷 / 判据雷）；
  ② 档案 **§5** 加 ZF148 行；
  ③ 档案 **§9** 加 ZF148 小节（**待用户实测**）；
  ④ 交接 **§1** 活体数字跟平（键数 579 / 配方 74 / java+资源 / 成品行）+ 新增「硬依赖」行；
  ⑤ 交接 **§6** 加第 29 条（本轮账 + 打包轮要做的三件事）；
  ⑥ 英文公告末尾加一条（§4.150 日志纪律要求）。

跑法：python build\\zftools\\_zf148_docs.py [--write]
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

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


# ---------------------------------------------------------------- ① §4.151
D4151_ANCHOR = u"`303c5d46…` / `2c738238…` 那些老哈希链。\n"
D4151 = D4151_ANCHOR + u"""
### 4.151 【工具雷】**联动帕秋莉**这一轮踩到的四个坑（0.12 ZF148）

帕秋莉（Patchouli）的书是**数据驱动**的，能踩的坑全在"文档没写、字节码才知道"的地方。
四条都当场被抓（前三条被探针 `Zf148Check` 抓，第四条让判据改了写法）：

1. ⚠ **`book.json` 的 `model` 键会被帕秋莉无条件加 `item/` 前缀**。
   字节码（`Book` 构造器）：`SerializationUtil.getAsResourceLocation(json, "model", DEFAULT_MODEL)`
   之后**直接** `ResourceLocation.withPrefix("item/")`。
   ⇒ 写 `"potato_s_t:item/guide_book"` 会解析成 `potato_s_t:item/item/guide_book`（贴图永远找不到），
   **正确的写法是不带前缀的 `"potato_s_t:guide_book"`**。文档里那句 `foo:bar → /assets/foo/models/item/bar.json`
   是"最终效果"，不是"该填什么"。探针 B11 两行（写字面量 / 读解析结果）就是钉这个的。
2. ⚠ **`PatchouliAPI.get().getBookStack(id)` 不查注册表**（`PatchouliAPIImpl → ItemModBook.forBook`：
   只把 id 塞进 `patchouli:book` 组件）。所以"瞎编一个书 id ⇒ 书堆应该为空"这条**负对照是错的**：
   真正的废书形态是"**堆造得出来、`BookRegistry.books` 里没有它**"。
3. ⚠ **专服上读不到创造模式物品栏的内容**：`CreativeModeTabs.tryRebuildTabContents` 只被
   `CreativeModeInventoryScreen`（**客户端**）调用 ⇒ 服务端探针里 `tab.getDisplayItems()` 恒空。
   帕秋莉进物品栏走的是 `BuildCreativeModeTabContentsEvent`（`NeoForgeModInitializer.processCreativeTabs`）。
   ⇒ 探针能验的只有"`book.creativeTab` 这个 `ResourceLocation` 写对了没有"，
   **"书真的出现在我们的物品栏里"只能靠客户端眼验**（已写进 §9 的实测清单）。
4. ⚠ **正文只认 `en_us` 目录**：`BookContentResourceListenerLoader.findFiles` 里写死
   `"en_us".equals(matcher.group("lang"))`（其余语言目录由 `BookContentsBuilder.loadLocalizedJson`
   按"先试当前语言、再回退基路径"处理）。⇒ 多语言**不要**复制五份 JSON 目录，
   而是 `i18n: true` + 把正文写成**语言键**（本轮 71 键 × 5 语言）。

附带一条**没能离线定论**的：书的默认字体是 `minecraft:uniform`，
而 1.21.1 客户端 jar 里 `assets/minecraft/font/include/unifont.json` 是 **`{"providers":[]}`（空的）**，
真正的 CJK 字形不在那个 jar 里 ⇒ 无法离线判断中文会不会掉字。
按"最稳"选：`use_blocky_font: true`（正文走原版默认字体，与全游戏中文渲染一致）。
若用户实测发现更想要帕秋莉的细体，把它改回 `false` 即可（book.json 一个字段）。
"""

# ---------------------------------------------------------------- ② §5 行
D5_ANCHOR_HEAD = u"| ZF147 |"
D5_ROW = (u"| ZF148 | **新建 `zf148_pre`**（**178 份**改前件：`build.gradle` / `neoforge.mods.toml` / "
          u"`PotatoST.java`（探针挂载点）/ 五份 `lang` / 三份文档 / **全部常驻门**（`_zf*_verify.py` + "
          u"`_zf100_recipe_guard.py` + `_zf104_gates.*`）/ `_zf94_gatecount.py`；逐份核 sha1 + 回读，失败 0。"
          u"⚠ 开工前查过轮号：`build\\zftools` 下没有别的 `_zf148_*`、救援目录下没有 `zf148_pre`（§4.147）"
          u" | 0.12：**联动帕秋莉手册做一本教程书**（用户原话「你看看能不能联动帕秋莉手册或者自己做个书 "
          u"教程向的 开局给一个 或者一本书+一个铁锭合成」；拍板：**联动帕秋莉** + 开局送一本 + 书+铁锭可再合）。"
          u"① 依赖：帕秋莉 `1.21.1-93-NEOFORGE` 进 `libs/`（离线用本地 jar，`compileOnly`），"
          u"`neoforge.mods.toml` 加 **`type=\u0022required\u0022` 硬依赖**（玩家不装帕秋莉开不了游戏 —— 用户拍板）；"
          u"② 书数据：`data/potato_s_t/patchouli_books/guide/book.json` + "
          u"`assets/.../patchouli_books/guide/en_us/{categories×6,entries×18}`，"
          u"`i18n: true` ⇒ 正文全是**语言键**（71 键 × 5 语言，键数 **508 → 579**、lzh 510 → 581）；"
          u"③ 物品用帕秋莉自己注册的 `patchouli:guide_book` + 组件 `patchouli:book=potato_s_t:guide`"
          u"（**不新增物品类**），模型 + 脚本生成的 16×16 贴图；"
          u"④ 配方 `guide_book.json`：书 + 铁锭（shapeless）⇒ 配方 **73 → 74**（`shaped` 仍 63）；"
          u"⑤ Java 只多一个 `GuideBook.java`（登录送一本，标记走玩家持久化数据，拿不到书**不打标记**）；"
          u"⑥ 探针 `Zf148Check` **92 项 ALL OK**；⑦ 门跟平 **43 份**：35 份键数/配方、5 份拆 `RELEASE_KEYS`、"
          u"2 份「后续轮次加的键」、1 份配方白名单 | 见 §9 ｜ 见 §4.151 |\n")

# ---------------------------------------------------------------- ③ §9 小节
D9_ANCHOR = u"### 翻译线（0.12）跟做用户手改的中文 —— 81 条铺到四语"
D9 = u"""### ZF148（0.12）联动帕秋莉：一本教程手册 —— **待你实测**

用户原话：「**你看看能不能联动帕秋莉手册或者自己做个书 教程向的 开局给一个 或者一本书+一个铁锭合成**」。
拍板（用户在选择题里点的）：**联动帕秋莉**（接受"玩家必须另装帕秋莉"这条硬依赖）+ **开局送一本** +
**书 + 铁锭可再合成**。

**做法**
- **依赖**：`libs/Patchouli-1.21.1-93-NEOFORGE.jar`（Modrinth 上那一份，646,777 B）——
  与 JEI 同套路（`compileOnly` 本地 jar，工程一直 `--offline` 构建）；
  `neoforge.mods.toml` 里 `type="required"`、`versionRange="[1.21.1-93,)"`、`ordering="AFTER"`。
  ⚠ 开发实例 `run/client/mods` 与 `run/server/mods` 也各放了一份（探针服务器要能起来）。
- **书**：`data/potato_s_t/patchouli_books/guide/book.json`（书定义，`use_resource_pack` + `i18n` +
  `use_blocky_font` + `show_progress: false`）+ `assets/potato_s_t/patchouli_books/guide/en_us/`
  下 **6 个分类 / 18 个条目 / 37 个文本页 + 3 个配方页**（配方页直接嵌 JEI 里那三条配方）。
- **多语言**：正文一个汉字都没写进 JSON —— 全是键 `potato_s_t.guide.*`，五份 `lang` 各 **+71 键**
  （键数 **508 → 579**、lzh **510 → 581**）。
- **物品**：用帕秋莉自己注册的 `patchouli:guide_book`，靠组件 `patchouli:book = potato_s_t:guide` 区分
  ⇒ **没有新增物品类**；模型 `assets/.../models/item/guide_book.json` + 脚本生成的 16×16 RGBA 贴图
  （`_zf148_book.py` 里那张 16×16 像素图是**占位**，随时可换，用户要是画了新的丢 `build\\用户素材\\`）。
- **配方**：`data/potato_s_t/recipe/guide_book.json` —— `minecraft:book` + `minecraft:iron_ingot`，
  shapeless，产物带 `components: {patchouli:book: potato_s_t:guide}`（不带组件就是一本废书）。
- **开局送一本**：`GuideBook.java` 监听 `PlayerEvent.PlayerLoggedInEvent`（服务端），
  标记写在**玩家持久化数据**里（随存档走）；⚠ **拿不到书堆就直接返回、不打标记**，
  下次登录还能再试。老存档在这条上线后也会补一本（标记一开始是空的）。

**证据**
- 探针 `Zf148Check`（真 `runServer`，帕秋莉已加载）：**92 项 ALL OK** —— 书被 `BookRegistry` 认下来、
  13 个字段逐条对、书堆/组件、配方产物与原料（含"石头不是原料"负对照）、
  26 个资源文件、图标/配方页/分类三处交叉引用、五语言 71 键一条不缺。
  报告 `build\\zftools\\_zf148_probe_utf8.txt`；归档件 `build\\zftools\\check\\Zf148Check.java`。
- 常驻门 `_zf148_verify.py`（静态，只读盘）：书定义逐字段、18 份条目结构与三处交叉引用、
  配方/模型/贴图、五语言与生成器表**逐字一致**、`GuideBook.java` 关键片段、文档、活体数字跟平。
- 反证：`_zf148_falsify.py` —— 逐把刀都要"改一处 ⇒ 指定的那一项必须变红 ⇒ 还原后必须回绿"。

**要你实测的（服务端探针看不到的部分）**
1. 进世界时**收到一本手册**（聊天栏还有一句提示）；② 右键能打开，分类/条目能点；
2. **中文会不会掉字/显示成方块** —— 这条我离线定不了论（见 §4.151 第 5 条），
   真掉字就把 `book.json` 的 `use_blocky_font` 改成 `false` 再试（帕秋莉的细体）；
3. 书里那 3 个配方页能不能正常渲染（`micro_crusher` / `hydraulic_press` / `star_chart_tome`）；
4. **创造模式物品栏里有没有这本书**（专服读不到，只能眼看）；
5. 书 + 铁锭能不能合出一本，丢了能不能补。

**本轮没做的（说清楚）**
- 正文只覆盖 **「起步 / 电力 / 材料 / 石油 / 星陨 / 疑难」六类 18 条**，**没有写满全 mod**
  （化工细类、机器总览、成就线还没写）；后续可以按类一轮一类地补，键数链条与门都已留好位置。
- 贴图是脚本占位图，不是美术。

**边界**
- `release\\PotatoST-0.12.jar`（12:56 打的，`45c061df…`）**早于本轮** ⇒ 里面没有手册、
  还是 508 键 / 73 配方；**打包轮要重打**（详见交接 §6 第 29 条）。
- 帕秋莉那 40 多份"成品 jar 键数"的门本轮拆出了 `RELEASE_KEYS = 508`（成品还是老数字），
  **打包轮把它跟 `EXPECT_KEYS` 一起抬**。

""" + D9_ANCHOR

# ---------------------------------------------------------------- ④ 交接 §1
H_KEYROW_OLD_HEAD = u"| 语言键数 | **508 键 × 4**"
H_KEYROW_NEW = (u"| 语言键数 | **579 键 × 4**（zh_cn / en_us / ja_jp / ru_ru，四份键集合必须完全一致；"
                u"lzh = 581 = 四份 + `language.name` / `language.region`）")
H_CHAIN_OLD = u"→ **508**（ZF145 成就树补线：8 条进度 × 标题/说明 = +16）。"
H_CHAIN_NEW = (u"→ **508**（ZF145 成就树补线：8 条进度 × 标题/说明 = +16）→ **579**"
               u"（ZF148 帕秋莉教程手册：书字段 3 + 分类名/说明 12 + 条目名 18 + 正文 37 + 赠书提示 1 = **+71**）。")
H_RECIPE_OLD = u"`data\\potato_s_t\\recipe\\` **73 份**（其中 `crafting_shaped` **63** 条）"
H_RECIPE_NEW = (u"`data\\potato_s_t\\recipe\\` **74 份**（其中 `crafting_shaped` **63** 条；"
                u"ZF148 那本是 **shapeless**：书 + 铁锭）")
H_JAVA_OLD = u"| Java / 资源 | **185** 个 java（不含临时探针）/ **745** 个资源文件 | — |"
H_JAVA_NEW = (u"| Java / 资源 | **187** 个 java（不含临时探针；ZF148 加了 `GuideBook.java`）/ "
              u"**787** 个资源文件（ZF148 加了 28：书定义 1 + 分类 6 + 条目 18 + 模型 1 + 贴图 1 + 配方 1） | — |")
H_DEP_NEW = (u"| **模组依赖** | **硬依赖帕秋莉（Patchouli）`1.21.1-93+`**（ZF148 起）—— 教程手册靠它渲染；"
             u"`neoforge.mods.toml` 里 `type=\"required\"`。⚠ 发行说明必须写明这条（玩家不装开不了游戏） | 主项目线 |\n")
H_JAR_OLD = (u"| **已发布成品** | `release\\PotatoST-0.11.jar` = "
             u"`303c5d468b96826ef6836b0a4e54ccb8a539557c`（4,298,939 B，**ZF114 打的**：432 键、含 ZF104~ZF114）"
             u"⚠ `.sha1` 的格式已对账成**纯哈希一行**（§4.92） | ⚠ **不含 ZF116~ZF121** |")
H_JAR_NEW = (u"| **已发布成品** | `release\\PotatoST-0.12.jar` = `45c061dfc9c171aeea783b64c05ca0e3d884871b`"
             u"（5,769,926 B，**12:56 打的**：508 键 / 73 配方 / 357 类，五语言齐全）"
             u"⚠ 它**早于 ZF148** ⇒ 里面**没有手册**、也没有那条硬依赖；旧成品 `PotatoST-0.11.jar` = "
             u"`a26d33633b7e791da7888477404a78c8cbbb61c4`（12:13 重打） | ⚠ **打包轮要重打 0.12**（§6 第 29 条） |")

H6_ANCHOR = u"28. **ZF147 的账（版本线 0.11 → 0.12）**"
H6_NEW = u"""29. **ZF148 的账（帕秋莉教程手册）**：① 用户原话「你看看能不能联动帕秋莉手册或者自己做个书
    教程向的 开局给一个 或者一本书+一个铁锭合成」⇒ **联动帕秋莉** + 开局送一本 + 书+铁锭可再合。
    ② 键数 **508 → 579**（+71）、配方 **73 → 74**、Java **+1 个类**（`GuideBook`）、
    资源 **+28 份**、**新增硬依赖 `patchouli`**（`neoforge.mods.toml` + `libs/` 那份 jar + 两个 run 实例的 mods）。
    ③ ⚠ **打包轮要做的三件事**：(a) 重打 `release\\PotatoST-0.12.jar`（现在那份 12:56 的**早于本轮**）；
    (b) 把本轮拆出来的 `RELEASE_KEYS = 508`（`_zf73/_zf75/_zf78/_zf79/_zf80/_zf81/_zf82/_zf93/_zf100/
    _zf101/_zf102/_zf117` 等门里的成品键数靶子）**跟 `EXPECT_KEYS = 579` 一起抬**，并作废
    `45c061df…` / `a26d3363…` 两条哈希链；(c) 公告 "Download" 那一段的
    "508 keys / 73 recipes / 357 classes" 三个数改成 **579 / 74 / 358**。
    ④ 本条也是 §4.150 日志纪律生效后的第二条（`_zf148_*` 全套脚本 + §5 行 + 公告那条）。
"""
H6 = H6_NEW + H6_ANCHOR

# ---------------------------------------------------------------- ⑥ 公告
ANN_ADD = u"""

## New in 0.12 ZF148 — an in-game guide book (Patchouli)

**PotatoS&T now requires [Patchouli](https://modrinth.com/mod/patchouli) `1.21.1-93` or newer.**
The guide book is rendered by Patchouli, so the mod will not start without it. This is a deliberate
choice: the book gets categories, an index, page turning and embedded recipe pages for free, and it
stays in sync with the mod version.

What you get:

- **A tutorial book, handed to you on your first login** (a marker is stored per player per world,
  so existing worlds get one too). Right-click to open it.
- **Lost it? Craft another one from one vanilla book plus one iron ingot.**
- Six categories and 18 entries, all with in-book text in **all five languages**:
  Getting Started, Power, Materials, Oil and Chemistry, Starfall, and Troubleshooting.
  Three of the entries embed real JEI recipe pages.
- Language files grew from 508 to **579 keys each** (Literary Chinese: 581).

⚠ The book currently covers the early and mid game path in depth (first machine, first power,
materials, oil, starfall). The chemistry sub-machines, a machine overview and the advancement line
are planned for later updates.
"""


def main(argv):
    write = u"--write" in argv

    doc = io.open(DOC, encoding=u"utf-8", newline=u"").read()
    doc2 = want(doc, D4151_ANCHOR, D4151, u"档案 §4.151")
    # §5：插在 ZF147 那行之后（那一行以 "| ZF147 |" 开头，行尾是指到 §9/§4 的收尾）
    i = doc2.find(D5_ANCHOR_HEAD)
    if i < 0:
        fails.append(u"档案 §5 找不到 ZF147 行")
    else:
        j = doc2.find(u"\n", i)
        if u"| ZF148 |" in doc2:
            notes.append(u"  [跳过] 档案 §5 的 ZF148 行（已经在，幂等）")
        else:
            doc2 = doc2[:j + 1] + D5_ROW + doc2[j + 1:]
            notes.append(u"  [改] 档案 §5 加 ZF148 行")
    doc2 = want(doc2, D9_ANCHOR, D9, u"档案 §9 加 ZF148 小节")
    if doc2 != doc:
        plan.append((DOC, doc, doc2))

    hand = io.open(HAND, encoding=u"utf-8", newline=u"").read()
    h2 = want(hand, H_KEYROW_OLD_HEAD, H_KEYROW_NEW, u"交接 §1 键数行")
    h2 = want(h2, H_CHAIN_OLD, H_CHAIN_NEW, u"交接 §1 键数链条补一环")
    h2 = want(h2, H_RECIPE_OLD, H_RECIPE_NEW, u"交接 §1 配方行")
    h2 = want(h2, H_JAVA_OLD, H_JAVA_NEW, u"交接 §1 Java/资源行")
    h2 = want(h2, H_JAR_OLD, H_JAR_NEW, u"交接 §1 成品行")
    # 新增「模组依赖」行：插在「版本线」那行之后
    if u"| **模组依赖** |" in h2:
        notes.append(u"  [跳过] 交接 §1 模组依赖行（已经在，幂等）")
    else:
        k = h2.find(u"| **版本线** |")
        if k < 0:
            fails.append(u"交接 §1 找不到版本线行")
        else:
            e = h2.find(u"\n", k)
            h2 = h2[:e + 1] + H_DEP_NEW + h2[e + 1:]
            notes.append(u"  [改] 交接 §1 加「模组依赖」行")
    h2 = want(h2, H6_ANCHOR, H6, u"交接 §6 加第 29 条")
    if h2 != hand:
        plan.append((HAND, hand, h2))

    ann = io.open(ANN, encoding=u"utf-8", newline=u"").read()
    if u"## New in 0.12 ZF148" in ann:
        notes.append(u"  [跳过] 公告 ZF148 那一条（已经在，幂等）")
    else:
        plan.append((ANN, ann, ann.rstrip(u"\n") + u"\n" + ANN_ADD))
        notes.append(u"  [改] 公告末尾加 ZF148 那一条")

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
    for p, old, new in plan:
        io.open(p, u"w", encoding=u"utf-8", newline=u"").write(new)
        assert io.open(p, encoding=u"utf-8", newline=u"").read() == new, p
    print(u"已写盘 %d 份" % len(plan))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
