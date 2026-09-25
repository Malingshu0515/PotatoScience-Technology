# -*- coding: utf-8 -*-
"""_zf69_docs.py —— 把 ZF69（散热装置配方）写进《开发档案》

规矩（§4.36）：每处替换都要求**恰好命中 1 次**，命中 0 次或 ≥2 次一律报错退出，
绝不"模糊匹配顺手改了别处"。改完打印每处的前后行数。
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

    # ---------- ① §4.41 新教训 ----------
    old = u"\n## 5. 版本与 [ZF] 流水线记录\n"
    new = u"""
### 4.41 【方法论】拿配方自己的材料表摆一遍 = 循环论证 —— 要照**用户原话**硬摆（0.10 ZF69）

ZF47 那次探针 `RecipeProbe` 验耐热金属块配方，做法是读 `recipe.getIngredients()`，
再把每格的第一种材料摆进 `CraftingInput` 去 `assemble()`。看着很硬，其实是**循环论证**：
配方里 `key` 要是写反了（中心与外圈对调），摆出来的材料**跟着一起反**，探针照样打印 `[OK]`。
「读配方 → 摆配方 → 配方通过」三步里，没有任何一步引入**配方之外**的信息。

ZF69 补散热装置配方时改成：

1. **照着用户那句话硬摆**：原话是「加热装置围一圈青金石」⇒ 手写九格（中心放加热装置、
   外圈 8 个青金石），材料表一个字都不从被测配方里读；
2. **逐格双向断言**：九格每一格都要「**接受**对的那种物品」**且**「**不接受**错的那种」
   （中心必须接受加热装置、且必须不接受青金石；外圈反之）。只写「接受」那一半的话，
   `key` 全填同一个万能标签也照样过；
3. **负向摆法**：5 种错摆（中心外围对调 / 少一个角 / 中心空 / 9 个青金石 / 9 个加热装置）
   一律不许出成品。其中「9 个青金石」会命中**原版**青金石块配方 —— 正好说明
   「没命中原版配方」不是判据，「**产物不是散热装置**」才是。

反证：把 `key` 里两个物品对调 ⇒ **9 条逐格断言全挂 + 合成台那条路挂**（共 10 项 FAIL），
而「加载得到 / 3×3 / 产物是散热装置」这些**结构**断言**全过** —— 结构对、内容反，
正是最像「能过」的那种坏法。

**顺带两条同源规矩**：

- 配方 JSON 由生成器表 `_zf45_recipes.py` **生成**，就别手改 JSON：这一轮把新图纸加进表里重跑，
  顺手证明「另外 33 份配方哈希一字未动」（`_zf69_repro.py`，33/33 SAME）；
- 文档里「还剩 N 个没有配方」这种**逐条清点**的话会随开发腐坏（§4.36 的同类），
  所以 `_zf69_verify.py` 把它当断言查：数字必须是 2、名单里不许再有 `heat_sink`。
  ⚠ 这条断言**先失败过**（改档案前跑：3 项 FAIL），改完档案才转 OK —— 它确实会挂。

## 5. 版本与 [ZF] 流水线记录
"""
    text = rep(text, old, new, u"§4.41 插入")

    # ---------- ② §5 加 ZF69 行 ----------
    old = u"\n\n> ZF40~ZF44 全是**电力高炉的连续改动**"
    row = (
        u"| ZF69 | **新建 `zf69_pre`**（**动手前**建的，**37 个改前件**：配方生成器 `_zf45_recipes.py`"
        u" + `docs/开发档案.md` + `recipe/` 下**全部 33 份 JSON** + 旧成品 jar 与 `.sha1`；"
        u"逐份核哈希、失败 0） | 0.10：**给散热装置加配方**（用户原话：「给散热装置加一个配方 "
        u"加热装置围一圈青金石」）。① 新写 `heat_sink.json`：`LLL / LHL / LLL`（L=青金石、H=加热装置）"
        u"⇒ 1 个散热装置、`category: misc`（与另外 15 条生成器配方同档）；这块方块 **ZF34 就注册了、"
        u"一直没有配方** ⇒ 装饰方块里没配方的从 3 个减到 **2 个**；② **走生成器表、不手写 JSON**："
        u"把图纸加进 `_zf45_recipes.py` 的表（表里现在 **16** 条）再 `--write`，白拿"
        u"「id 真实存在 / 每格字符都在 key 里 / key 无冗余」的机械核对；`_zf69_repro.py` 接着证明"
        u"**可复现**：另外 **33 份配方 JSON 与改前备份逐份 SHA1 相同（33/33）**；"
        u"③ 探针 `HeatSinkRecipeCheck` **28 项全 [OK]**（物品 id / 配方加载且 3×3 / **九格逐格双向断言**"
        u" / **照用户原话硬摆的九格**走 `getRecipeFor` 真合成出 1 个散热装置、无返还物、同摆法只命中 1 条"
        u" / 5 种错摆法一律不出散热装置 / 本模组合成配方 **28 条**一条不少；服务端日志 `Loaded 1324 recipes`，"
        u"比 ZF67 的 1323 **正好 +1**）；④ **反证**：把 `key` 两个物品对调 ⇒ **10 项 FAIL**"
        u"（9 条逐格 + 合成台那条），而结构类断言全过（§4.41）；⑤ 顺手核出一条既有事实并**没改**："
        u"本模组 `advancement` = **0** ⇒ **配方书不会自动解锁**（JEI 看得到、工作台手摆也能合，"
        u"与另外 27 条配方同状态）；⑥ 本轮**用户自己**往 `textures/item/` 放了新的 `photovoltaic_component.png`"
        u"（17:15，**真 PNG 16×16**，不是改名 webp）⇒ 构建顺手带上（旧的是 **160×160** 占位色块），"
        u"`TextureCheck` 警告 25→**24**、160×160 老占位 23→**22**；新写常驻 `_zf69_verify.py`（**34 项**）"
        u" | 见 §4.41 / §9 |"
    )
    text = rep(text, old, u"\n" + row + old, u"§5 ZF69 行")

    # ---------- ③ §9 加 ZF69 待验证块 ----------
    old = (u"      `python build/zftools/_zf68_obj.py --write`（映射规则写在脚本头部注释里）。\n"
           u"- [ ] **ZF66 我替你定的三个数**")
    new = (u"      `python build/zftools/_zf68_obj.py --write`（映射规则写在脚本头部注释里）。\n"
           u"- [ ] **ZF69：等你试散热装置的配方**（成品见本轮汇报）。工作台摆 **外圈 8 个青金石 + 正中间 1 个加热装置**\n"
           u"      ⇒ 出 **1 个散热装置**。要看的：① 九格**必须摆满**（少一个角、中心空着都不出）；\n"
           u"      ② JEI 里应当能搜到这条（本模组的配方**没挂 advancement** ⇒ 配方书不会自动解锁，\n"
           u"      但这与另外 27 条一样，手动摆完全能合）；③ 8 个青金石 = 8 个，**不是**染料那种少量。\n"
           u"- [ ] ZF69 说明：**散热装置换配方改一处就够** —— 图纸写在 `build/zftools/_zf45_recipes.py` 的表里，\n"
           u"      改完跑 `python build/zftools/_zf45_recipes.py --write`（那条命令会把表里 16 份 JSON 一起重写，\n"
           u"      所以别手改 `recipe/*.json`，会被下次重跑覆盖）。\n"
           u"- [ ] **ZF69 顺带带上的一张图**：你 17:15 把 `photovoltaic_component.png`（光伏原件）\n"
           u"      换成了 16×16 手绘（旧的是 160×160 占位色块，面积平均过的那版）⇒ 本轮 jar 里已经是新的。\n"
           u"      要退回旧的说一声；接着画别的也行（`docs/贴图清单.md` 里还剩 8 个待画）。\n"
           u"- [ ] **ZF66 我替你定的三个数**")
    text = rep(text, old, new, u"§9 ZF69 待验证块")

    # ---------- ④ §9 「还剩 N 个没有配方」跟着改 ----------
    old = (u"- [ ] **ZF47（耐热金属块配方）之后，装饰方块还剩 3 个没有配方**：\n"
           u"      `advanced_metal_block` 高级金属块、`stable_metal_block` 稳定金属块、`heat_sink` 散热装置。\n"
           u"      已有配方的：`common_metal_block`（ZF37）、`wiring_block`（ZF37）、`heater`（ZF45）、\n"
           u"      `heat_resistant_metal_block`（ZF47）。要哪个的配方直接给图纸就行（一个 JSON 的事）")
    new = (u"- [ ] **装饰方块还剩 2 个没有配方**：\n"
           u"      `advanced_metal_block` 高级金属块、`stable_metal_block` 稳定金属块。\n"
           u"      已有配方的：`common_metal_block`（ZF37）、`wiring_block`（ZF37）、`heater`（ZF45）、\n"
           u"      `heat_resistant_metal_block`（ZF47）、**`heat_sink` 散热装置（ZF69：加热装置围一圈青金石）**。\n"
           u"      要哪个的配方直接给图纸就行（一个 JSON 的事）")
    text = rep(text, old, new, u"§9 无配方清点 3→2")

    # ---------- ⑤ §9 老占位色块张数 ----------
    old = u"      另外：项目里 **23 张老占位色块是 160×160**（不是 16×16），换上你的图时顺带就修掉了。"
    new = (u"      另外：项目里 **22 张老占位色块是 160×160**（不是 16×16），换上你的图时顺带就修掉了\n"
           u"      （ZF69 你换掉的**光伏原件**就是第一张：160×160 → 16×16，编号见 `_zf69_texcount.py` 的输出）。")
    text = rep(text, old, new, u"§9 160x160 计数 23→22")

    # ---------- ⑥ §11.1 门清单补 TextureCheck ----------
    old = (u"| `GroupEnergyCheck.java` | **纯算法验算**（只覆盖 `GroupEnergy`：共享储能池的补/扣/总量/容量/速率分摊）"
           u" | 退出码 0（14 条断言全过） |")
    new = (u"| `TextureCheck.py` | 贴图文件头是不是**真 PNG**（挡住「webp 改名叫 .png」）、尺寸、物品贴图有无 alpha、"
           u"还在**借原版贴图**的模型清单 | 失败项 = 0 |\n"
           u"| `GroupEnergyCheck.java` | **纯算法验算**（只覆盖 `GroupEnergy`：共享储能池的补/扣/总量/容量/速率分摊）"
           u" | 退出码 0（14 条断言全过） |")
    text = rep(text, old, new, u"§11.1 补 TextureCheck 行")

    old = u"> `SoundCheck.py` 是 **0.10 ZF36 新增**的第 7 项。"
    new = (u"> `TextureCheck.py` 是 **0.10 ZF61 新增**的第 8 项 —— ⚠ 当时只在 §5 的 ZF61 行里说了"
           u"「第 7 道门」，**这张表漏了它**（ZF69 补上）。它挡的是「用户丢进来的 `.png` 其实是 webp」这个坑："
           u"只读文件头，不解码。\n"
           u">\n"
           u"> 每轮还会跑**当轮与往轮的常驻校验** `build\\zftools\\_zfNN_verify.py`（由 `_zfNN_gates.ps1` 统一调用），"
           u"它们查的是「口径类」断言（工具提示里的图纸 vs 代码、模型朝向、配方语义…），都要求失败项 = 0。\n"
           u"\n"
           u"> `SoundCheck.py` 是 **0.10 ZF36 新增**的第 7 项。")
    text = rep(text, old, new, u"§11.1 门清单说明")

    # ---------- ⑦ §10 备份记录 ----------
    old = u"- 换装启动器实例时的铁律：**先 sha256 比对实例内旧 jar 与 `release\\` 内的同名副本**，"
    new = (u"- ✅ **ZF69（散热装置配方）**：**动手前**建 `zf69_pre`，一次抄 **37 份**（生成器表 + 档案 + "
           u"`recipe/` 下全部 33 份 JSON + 旧成品 jar 与 `.sha1`），逐份核哈希、**失败 0**，中间不夹任何写操作。"
           u"这一轮之所以要把 **33 份配方 JSON 全抄**（其实只会重写 16 份）：为了拿到"
           u"「除新增的那一份，其余文件一个字节都没动」这条**复现性证据**（`_zf69_repro.py`：33/33 SAME）。\n"
           u"- 换装启动器实例时的铁律：**先 sha256 比对实例内旧 jar 与 `release\\` 内的同名副本**，")
    text = rep(text, old, new, u"§10 ZF69 备份记录")

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
