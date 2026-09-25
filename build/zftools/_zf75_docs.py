# -*- coding: utf-8 -*-
u"""_zf75_docs.py —— ZF75 四处文档编辑（地表油田 + 海洋油田群系）"""
import io
import sys

ARCH = r"E:\PotatoST\docs\开发档案.md"
PLAN = r"E:\PotatoST\docs\v0.11规划.md"
ANN = r"E:\PotatoST\docs\UpdateAnnouncement_EN.md"

A_ROW = u"| 见 §6.19 / §9 |"
A_S9 = u"      要验的话：跟柴油动力（`createdieselgenerators`）一起装，看它的 `#c:crude_oil` 配方认不认我们的原油。"
A_PLAN = u"> `PotatoST-0.10.jar` **原样并存**（不是作废关系）。"
A_ANN = u"""- **Crude oil is currently a creative-only fluid.** The fluid, the liquid block and the Oil
  Bucket all work, but the surface oilfields (`mini_oilfield`) and the ocean-oilfield biome are
  **not generated yet** — they arrive in the next update. Until then, place oil with
  `/setblock <pos> potato_s_t:crude_oil` (it spreads like lava and never becomes infinite)."""

NEW_ANN = u"""- **Crude oil now generates in the world.** Small surface oil lakes (`mini_oilfield`) appear
  anywhere in the overworld at roughly the same rarity as vanilla lava lakes — and **three times
  as often in deserts and badlands**. The **Ocean Oilfield** biome (dark blue water, `#4047AD`)
  shows up along stony shores at a deliberately low rate. **Existing worlds get it too**: the
  biome source falls back to the registry when an old save has no oil-biome entry."""

ROW = u"""| ZF75 | **新建 `zf75_pre`**（13 个改前件：`SaltyRiverBiomeSource.java` + 3 份世界预设 + `is_overworld` 标签 + 4 份 lang + 档案 + 贴图清单 + 旧成品 jar 与 `.sha1`；逐份核哈希、失败 0） | 0.11：**世界生成**（用户反馈：「locate指令只能查到咸水河 无论是查生物群系或者结构都找不到海底油田 和微型油田」—— 这不是 bug：ZF73 报告里写明世界生成留到下一轮，而那一轮被标签问题占了）。① **地表油田** `potato_s_t:mini_oilfield`：配置特征=`minecraft:lake`（barrier=石头、fluid=原油 level 0，与原版 `lake_lava` 逐字对齐）+ 放置特征（`rarity_filter 200` / `in_square` / `WORLD_SURFACE_WG` / biome 过滤，与原版地表岩浆湖同参数）；② **沙漠恶地 3 倍**：基础注入器挂 `#minecraft:is_overworld`，另两份挂自定义标签 `#potato_s_t:oilfield_dense` ⇒ 探针实测**平原 1 份 / 沙漠 3 份 / 恶地 3 份**；③ **海洋油田群系** `potato_s_t:ocean_oilfield`（水色 `4212653` = 4047AD、以石岸为底 + 海草海带、补 cod/squid 权重）；④ **群系源改造**（`SaltyRiverBiomeSource`）：新增**可选**字段 `oil_biome`/`oil_chance`（默认 0.15），把 `minecraft:stony_shore` 按位置哈希替换成油田 —— **旧存档兼容靠 `Holder.Reference#unwrapLookup()` 兜底**：老 level.dat 没这个字段时从注册表反查默认群系，**不用开新世界**（探针钉了这条断言）；⚠ **咸水河的哈希公式一个字节没改**（改了旧存档群系边界会错开），油田用另一套常数 `0x5EED`；⑤ **两个真错误是探针抓出来的**：(a) `neoforge:add_features` 的 `biomes` **数组形式只吃群系 id、不吃 tag** ⇒ 改成单值 tag；(b) **`#minecraft:is_desert` 在 1.21.1 根本不存在**（只有 `is_badlands`）—— 我 ZF72 规划里那个标签是凭空写的，探针一连串 FAIL 把它逼出来了 ⇒ 自建 `#potato_s_t:oilfield_dense` = `[#minecraft:is_badlands, minecraft:desert]`；⑥ **探针 `OilfieldCheck` 20 项全 [OK]**（群系注册/水色/名字/`#is_overworld`、注入器份数 1/3/3/1、**用合成 delegate 做的确定性规则测试**（oil_chance=1.0 全替换 400/400、0.0 全不换、咸水河规则未受影响、旧存档兜底解析）、`/place feature` 真放出 **60 块原油且全是源方块**）；⑦ **测试方法上的教训**：第一次 `/place feature` 放不出油 —— 原版 `LakeFeature` 作用区是 **origin 起 +15 格**、且下半透镜必须是固体方块，我铺的 16×16 平台不够宽 ⇒ 特征直接 `return false`；平台放大到 -2..26 才成；⑧ 同版本重打包 ⇒ 上一版 `39e66beb…` 作废，新成品 **`4528ed53cbdef41d952e8707e05c4424bd49cc41`**（2,231,500 B / 731 条目）| 见 §9 |"""

SEC_S9 = u"""- [ ] **ZF75：世界生成做好了，等你跑图确认**（成品 `release\\PotatoST-0.11.jar` = `4528ed53cbdef41d952e8707e05c4424bd49cc41`；**同版本重打包 ⇒ 上一版 `39e66beb…` 作废**）。要看的：
      ① `/locate biome potato_s_t:ocean_oilfield` —— **旧存档也能查到**（群系源会自动兜底；如果你在旧存档里查不到，
         把世界的创建方式告诉我：`FixedBiomeSource` 那种"单一群系"世界本来就不会有海洋油田）；
      ② 地表找**原油湖**：跟原版岩浆湖差不多稀有，**沙漠/恶地是别处的 3 倍**；
      ③ ⚠ **`/locate structure` 永远找不到微型油田** —— 它是 **feature** 不是结构，`/locate` 不搜 feature；
         想立刻看一个就用 `/place feature potato_s_t:mini_oilfield ~ ~ ~`（放在实心地面表层）；
      ④ 油田里的原油是**源方块**、能舀、舀干不会自己长回来。
- [ ] ZF75 提醒：**海洋油田群系只在"石岸"位置替换**（你说的"石岸群系和海洋群系之间过渡"）。探针实测替换率 0.15；
      嫌多/嫌少改 `_zf75` 之后那个默认值或世界预设里的 `"oil_chance"`（三个预设都在）。
"""


def main():
    fails = []

    def patch(path, old, new, label):
        t = io.open(path, "r", encoding="utf-8").read()
        n = t.count(old)
        if n != 1:
            fails.append(u"%s：命中 %d 次" % (label, n))
            print(u"  !! %s：命中 %d 次" % (label, n))
            return
        io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
        print(u"  [OK] %s" % label)

    patch(ARCH, A_ROW, A_ROW + u"\n" + ROW, u"档案 §5 ZF75 行")
    patch(ARCH, A_S9, A_S9 + u"\n" + SEC_S9.rstrip(u"\n"), u"档案 §9 ZF75 待办")
    patch(PLAN, A_PLAN, A_PLAN + u"\n>\n> **2026-09-24 ZF75 已完成**：地表油田 `mini_oilfield`（沙漠/恶地 3 倍）与"
                              u"海洋油田群系 `ocean_oilfield`（水色 4047AD）已实现，成品 `4528ed53…`；"
                              u"旧存档靠群系源的注册表兜底也能吃到新群系。",
          u"规划文档记 ZF75 完成")
    patch(ANN, A_ANN, NEW_ANN, u"公告：原油不再只是创造模式流体")
    print(u"\n失败项 = %d" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
