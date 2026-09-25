# -*- coding: utf-8 -*-
u"""_zf79_docs.py —— ZF79 的文档（§5 行 / §6.21 新章节 / §9 待验 / 贴图清单）

四件事：
  ① `docs/开发档案.md` §5 加 ZF79 行（插在 ZF78 行之后、表格末尾）
  ② §6.21 新章节：给液压机**加一条配方**要动哪几处（0.11 ZF79 立的规矩）
  ③ §9 加用户侧验证条目（含成品哈希占位 __NEWSHA__，发布后由 republish 脚本填）
  ④ `docs/贴图清单.md` 追加"ZF79 的占位/新贴图"一节（柏油块借煤炭块；电力高炉已是用户手绘）
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
TEXLIST = os.path.join(ROOT, "docs", u"贴图清单.md")
fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)


def insert_after_line(path, anchor, block, label):
    t = read(path)
    hits = t.count(anchor)
    if hits != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, hits))
        return
    i = t.index(anchor)
    eol = t.index(u"\n", i) + 1
    write(path, t[:eol] + block + t[eol:])
    print(u"  [OK]   %s" % label)


def insert_before(path, anchor, block, label):
    t = read(path)
    hits = t.count(anchor)
    if hits != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, hits))
        return
    write(path, t.replace(anchor, block + anchor, 1))
    print(u"  [OK]   %s" % label)


def append(path, block, label):
    t = read(path)
    if not t.endswith(u"\n"):
        t += u"\n"
    write(path, t + block)
    print(u"  [OK]   %s" % label)


ROW = u"""| ZF79 | **新建 `zf79_pre`**（22 个改前件：`PressRecipes` / `HydraulicPressBlockEntity` / `client/HydraulicPressScreen` / `ModBlocks` / `ModItems` / 4 份 lang / `mineable/pickaxe.json` / 旧的 `electric_blast_furnace.png` / **用户原图 `电力高炉.png`** / 4 份文档 / 4 个往轮校验脚本 / 旧成品 jar 与 `.sha1`；逐份核哈希、失败 0。**这次记得先抄了** —— ZF78 漏过一次，见那一行的自述） | 0.11：**两件**（用户原话：「12个沥青 可以在液压机压成一个柏油块（纯建筑方块 先用煤炭块材质）**然后我把电力高炉材质放进方块材质文件夹里了**」）。① **液压机配方表扩成"带输入数量"**：`PressRecipes.Recipe` 加 `inputCount`（原先是写死的"一次吃 1 个"）+ **允许 `inputTag` 为 null**（沥青属于"其他物品"，按长期规则不挂 `c:` 标签）+ 字段正名（`ingotTag`→`inputTag`、`plate`→`result`，因为表里不再只有"锭→板"）+ 新增 `hasEnough()`（**数量够不够**与**物品对不对**分开判）；7 条老配方原样不动（走 1 个的便利构造器）。② **柏油块** `potato_s_t:asphalt_block`：纯装饰方块（无方块实体），性质照原版煤炭块（`strength 5.0/6.0` + 石头音 + `requiresCorrectToolForDrops`），贴图**先借原版煤炭块**（4 位调色板 PNG ⇒ 解成 8 位 RGBA 落进本工程命名空间 + 来源凭据），进 `mineable/pickaxe`（**不进** `needs_stone_tool` —— 与煤炭块一致，木镐也能挖），**没有合成台配方**（只能压出来）。③ **液压机行为**：新增状态码 **6 = 材料数量不够**（黄灯，与新文案 `...status.material`）——语义与"输入槽空"不同：那是**没东西、进度清零**，这是**有东西但不够、进度保留**（跟断电一样）；数量检查**排在"满进度结算"之前**（否则 11 个沥青也能出货）；结算按 `recipe.inputCount()` 扣料。④ **JEI 跟着改**：`MachineRecipes.buildHydraulicPress` 支持无标签输入（退回兜底物品）并让输入图标带数量 ⇒ JEI 上直接看到"沥青 ×12 → 柏油块"。⑤ **电力高炉新材质**：用户把 `textures/block/电力高炉.png`（**256×256 / 8 位 / RGBA**，不是改名 webp）放进来了 ⇒ 按 §4.24 改成 ASCII 名 `electric_blast_furnace.png` 覆盖旧的 **16×16 生成器占位**（原名件留档为 `电力高炉.原名件`，改名前后逐字节相同）；**MTL 一行没动**（它本来就指向这个路径）⇒ OBJ 与 UV 全部不变。⚠ **记一笔**：`MakeBlastFurnaceModel.py` 会把这张贴图盖回单色，**以后不要再跑它**。⑥ 四语言 246 → **248** 键（柏油块名字 + 液压机新状态文案），液压机 tooltip 四语言各补一行"沥青 ×12 → 柏油块"；英文公告 §3 那行同步。⑦ **探针 `AsphaltCheck` 33 项全 [OK]**：注册与标签、配方表 8 条、沥青要 12 个、11 个不开工且不吃料（状态 6、进度 0）、12 个跑 60 tick 出 1 块且**电正好扣光 24000**、24 个连跑两轮出 2 块、**铁锭老配方回归（1 个进 1 个出、只吃 1 个）**、输出满时卡住不吃料。⑧ 发布见 §9 | 见 §6.21 / §9 |

"""

SEC_621 = u"""### 6.21 给**液压机**加一条配方要动哪几处（0.11 ZF79 立的规矩）

液压机的配方表在 `PressRecipes.java`（**Java 表，不是 JSON**），加一条要动的地方：

| # | 动什么 | 注意 |
|---|---|---|
| 1 | `PressRecipes` 的 `all()` 里加一条 | 输入**有 `c:` 标签**就传标签 + 兜底物品；**没有标签**（例如沥青）就传 `null` + 物品 |
| 2 | 一次吃几个 | 第 4 个参数是 `inputCount`：不写就是 1（老配方都走这个便利构造器）；写 12 才是"12 个换 1 个" |
| 3 | 产物是不是方块 | 方块产物传 `ModBlocks.XXX_ITEM.get()`（**物品**，不是方块本体） |
| 4 | 时间与耗电 | 全机器统一 **60 tick / 400 FE·t**（`DURATION_TICKS` / `ENERGY_PER_TICK`）；要单独给这条改速率得给 `Recipe` 再加字段 |
| 5 | 材料不够的提示 | 已经有了：`STATUS_MATERIAL`（黄灯）+ `gui.potato_s_t.hydraulic_press.status.material`；**四语言都要有** |
| 6 | JEI | **不用动** —— `MachineRecipes.buildHydraulicPress` 是遍历 `PressRecipes.all()` 生成的，输入图标会自动带上数量 |
| 7 | 工具提示 | `tooltip.potato_s_t.hydraulic_press` 里有"可加工：…"一行，**四语言都要补**（ZF71 那次就因为漏了一行被记成 bug） |
| 8 | 公告 | `docs/UpdateAnnouncement_EN.md` §3 的液压机一行 |
| 9 | 语言键数 | 只加名字/文案才会涨；`_zf73/_zf75/_zf71/_zf78` 四个校验里的**活体键数**要跟着改 |
| 10 | 探针 | 新写一个（或扩 `AsphaltCheck`）：**至少验"数量不够不开工、正好够时吃掉的个数、1:1 老配方回归"** |

**一条口径**：`Recipe.matches()` 只看**物品对不对**，`hasEnough()` 才看**数量够不够** ——
两者分开是有意的（"放错了"要报"不可锻压"，"放少了"要报"材料不够"，混在一起玩家看不懂）。
"""

SEC_9 = u"""- [ ] **ZF79：等你试两件**（成品 `release\\PotatoST-0.11.jar` = `__NEWSHA__`）。要看的：
      ① **12 个沥青 → 1 个柏油块**：把 12 个沥青丢进液压机输入槽 ⇒ 60 秒内出 1 个柏油块
      （耗电与压板一样 400 FE/t，一块共 24000 FE）。**先放 11 个看状态灯**：应当是**黄灯** +
      悬停写「材料不够：沥青要 12 个」，而且**一个沥青都不会被吃掉**；补到 12 个才开工。
      ② **柏油块**：创造页里能拿到，挖下来会掉（木镐就能挖，和煤炭块一样）；贴图现在是**原版煤炭块**
      那张（你说"先用煤炭块材质"）—— 要换你自己的图就把 `textures/block/asphalt_block.png` 覆盖掉。
      ③ **电力高炉新材质**：把新 jar 装进游戏，成型一台电力高炉看外观 —— 贴图是你放进来的那张
      256×256（我按 §4.24 改名成 `electric_blast_furnace.png`，原名件留了档）；**模型/UV 一个字节没动**，
      所以只有贴图变了。看不清哪面对就发截图，我按需要调 MTL 或 UV。
- [ ] ZF79 说明：**柏油块除了建筑暂时没别的用途**（你只说了"纯建筑方块"）；要给它加配方/当燃料/压回去，说一声。
- [ ] ZF79 说明：**柏油块没有合成台配方**，只能靠液压机压（12 沥青 → 1）；创造页里可以直接拿。
- [ ] ZF79 提醒：`MakeBlastFurnaceModel.py`（ZF39 那个 OBJ/MTL 生成器）**会把电力高炉贴图盖回单色**
      —— 现在那张是你手绘的，**别再跑那个脚本**；要动模型另说（`_zf68_obj.py` 是合金炉的，两码事）。
"""

TEXLIST_ADD = u"""
---

## ZF79 的贴图变动

> ⚠ 这一节是**手写**的：`TextureCheck.py --plan` 只按模型推名字，认不出"这张是占位/这张是手绘"。
> 下次重跑 `--plan` 会把它冲掉，我再补回来。

| 放哪 | 文件名 | 是什么 | 现在是什么 |
|---|---|---|---|
| `textures/block/` | `asphalt_block.png` | 柏油块 | **原版煤炭块那张图的副本**（你要求「先用煤炭块材质」），要换就把这个文件覆盖掉 |
| `textures/block/` | `electric_blast_furnace.png` | 电力高炉 | ✅ **已经是你的手绘 256×256**（原名件 `电力高炉.png` 已按 §4.24 改成 ASCII 名，原图留档为 `电力高炉.原名件`） |

柏油块的方块模型是 `cube_all`（一张图铺六面），所以**只有这一个 png 要画**。
"""


def main():
    print(u"== ① §5 加 ZF79 行 ==")
    insert_after_line(DOC, u"| ZF78 | **补建 `zf78_pre`**", ROW, u"§5 ZF79 行")

    print(u"== ② §6.21 新章节 ==")
    insert_before(DOC, u"## 7. 权威情报来源（怎么查原版行为，别靠记忆）", SEC_621, u"§6.21 液压机配方清单")

    print(u"== ③ §9 用户侧验证 ==")
    insert_after_line(DOC, u"      详见 `C:\\PotatoST救援\\zf78_pre\\MANIFEST.md`。",
                      SEC_9, u"§9 ZF79 条目")
    # ZF78 那条"沥青没有任何用途"已经被本轮推翻 ⇒ 就地改成"已定"，不能留一句假话
    t = read(DOC)
    old = (u"- [ ] ZF78 说明：**沥青目前没有任何用途** —— 你只说了\"产出来、满 64 停机\"，没说能干什么，\n"
           u"      所以我**故意没给它挂任何原版功能标签**（当燃料烧、当合成材料都要你点名）。")
    new = (u"- [x] ~~ZF78 说明：**沥青目前没有任何用途**~~ ⇒ **ZF79 已定**：**12 个沥青在液压机里压成 1 个柏油块**\n"
           u"      （纯建筑方块，见 §6.21 与 §9 的 ZF79 条目）。它**仍然没有**原版功能标签（不是燃料）。")
    if t.count(old) != 1:
        fails.append(u"沥青用途那条锚点命中 %d 次" % t.count(old))
    else:
        write(DOC, t.replace(old, new, 1))
        print(u"  [OK]   §9：把「沥青没有用途」改成 ZF79 已定（不留假话）")

    print(u"== ④ 贴图清单 ==")
    append(TEXLIST, TEXLIST_ADD, u"贴图清单追加 ZF79 一节")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
