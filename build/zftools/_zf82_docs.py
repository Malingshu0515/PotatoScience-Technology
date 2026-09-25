# -*- coding: utf-8 -*-
u"""_zf82_docs.py —— ZF82 四份文档：档案（§4.54/§4.55 两条雷 + §5 ZF82 行 + §9 验收）+ 贴图清单

占位 `__NEWSHA__` / `__NEWSIZE__` / `__NEWENTRIES__` 由 `_zf82_publish.py` 打包后填真值。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOCS = r"E:\PotatoST\docs"
fails = []


def read(p):
    if not os.path.exists(p):
        fails.append(u"缺文件：%s" % p)
        return u""
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)


def insert_after(text, anchor, block, label):
    if text.count(anchor) != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, text.count(anchor)))
        return text
    at = text.find(anchor)
    eol = text.find(u"\n", at)
    return text[:eol + 1] + block + text[eol + 1:]


TRAP1 = u"""
### 4.54 【实现雷】NeoForge 的 `can*` 开关长在 **FluidType.Properties** 上，写到"流动参数链"上就是「找不到符号」（0.11 ZF82）

给柴油/汽油加桶与液体方块时，我照着水/岩浆的直觉这样写：

```java
new BaseFlowingFluid.Properties(DIESEL_TYPE, DIESEL, FLOWING_DIESEL)
        .block(ModBlocks.DIESEL)
        .canConvertToSource(false)   // ← 编译错误：找不到符号
```

`canConvertToSource / canHydrate / canExtinguish / supportsBoating` 全都是
**`FluidType.Properties`**（流体"种类"的属性）上的开关 —— 本工程的 `ModFluids.liquidType(...)`
**早就设过了**；而 `BaseFlowingFluid.Properties`（流动"参数"）上只有
`block / tickRate / slopeFindDistance / levelDecreasePerBlock / explosionResistance / bucket`。

**规矩**：
1. 加一种流体时看清楚**两条链**：种类开关进 `FluidType.Properties`，流动参数进 `BaseFlowingFluid.Properties`；
2. `.bucket(...)` 放**链尾**（它返回原版 `FlowingFluid.Properties`，后面再点 neo 扩展方法同样会挂）；
3. 编译器的「找不到符号」+「位置: 类 Properties」= 十有八九是**点错了那条链**。
"""

TRAP2 = u"""
### 4.55 【排查雷】"机器错了"的直觉会挡住"探针错了" —— 探针也要留**逐 tick 轨迹**（0.11 ZF82）

容器换流器第一次探针跑出 5 条 FAIL（第 60 tick 右槽没变桶）。我第一反应是"机器 off-by-one"，
把结算从"下一 tick"改成"加满即结算"（这一改本身是对的，与液压机对齐）；结果第二次跑变成
**"比预期早一格"**（第 59 tick 就成了）。再加**逐 tick 轨迹**才看清真相：

```
t1=进度1/左3000  t2=进度2/左3000  …  t58=进度58/左3000  t59=进度59/左3000  t60=进度0/左2000
```

⇒ **机器从头到尾都是对的**：正好第 60 tick 结算、正好扣 1000。错的是我探针里**没跟着改的两条旧断言**
（标签写着"第 59 tick"，读的却是 62 次 tick 之后的状态）。

**规矩**：
1. 探针里凡是"第 N tick 应该怎样"，要么在循环里**采下那一 tick 的值**再断言，要么别把 tick 数写进标签；
2. 出现"比预期早/晚一格"这种**只差一格**的现象时，**先打轨迹再改代码** —— 一格之差最常见的来源是
   探针与机器**各数了一次**，而不是逻辑错；
3. 轨迹要进报告（本工程的 UTF-8 报告机制），这样复查时不用重跑。
"""

ROW = (u"| ZF82 | **新建 `zf82_pre`**（27 个改前件：`ModFluids` / `ModBlocks` / `ModItems` / `ModMenus` / "
       u"`PotatoST` / `PotatoSTClient` / `StatusLampPart` / 4 份 lang / 原油的 blockstate+model（当模板）/ "
       u"7 个往轮校验脚本 / `_zf78_falsify.py` / 4 份文档 / 旧成品 jar 与 `.sha1`；逐份核哈希、失败 0） | "
       u"0.11：**两件**（用户原话：「新进 柴油桶 汽油桶（先用水桶贴图）和原版水桶一致 可以倒出相应的流体"
       u"返回空桶 并可以被空桶收回源头液体」+「再加一个【容器换流器】… 3s后 消耗油罐内1000mb的液体 "
       u"把桶变成相应的流体桶（别的mod的流体也可以，前提是流体有对应桶的形式）流体泵也可以把液体泵出 "
       u"这个是直接消耗油罐的流体容量 然后泵出 有多少泵多少（取决于泵的速率）」）。"
       u"① **柴油桶 / 汽油桶**：两个原版 `BucketItem`（放置/舀取/返还空桶全走原版那套），"
       u"贴图按用户吩咐**先借原版水桶**；为了让「倒得出来、舀得回去」成立，柴油/汽油第一次有了"
       u"**液体方块**（性质照原油）与 **`.bucket(...)`** —— 原版空桶能舀正是因为 "
       u"`LiquidBlock#pickupBlock` 返回 `fluid.getBucket()`。⚠ **原油/石脑油/液化石油气仍然没有桶**"
       u"（ZF73 那条「一个原版空桶 = 3000 mB 会白送三倍」的老规矩不许被带坏，探针里有负向断言）。"
       u"② **容器换流器**：左槽放装流体的容器、右槽放**刚好 1 个**空桶，3 秒（60 tick）取 1000 mB，"
       u"把空桶换成**那种流体的官方桶**；官方桶就是 NeoForge 的 `Fluid#getBucket()` ⇒ "
       u"水→水桶、柴油→柴油桶、别的 mod 的流体→那个 mod 自己的桶，**没有桶形式的流体直接拒绝并说明**"
       u"（用户那句「前提是流体有对应桶的形式」不需要按名字/标签猜，API 已经把这层映射做好了）。"
       u"③ **泵接口**：`getFluidHandler()` 暴露的**不是机器自己的罐，而是左槽那件容器**"
       u"（「直接消耗油罐的流体容量」）⇒ 泵抽多少容器少多少，`SIMULATE` 只算不取；气体也走这条路"
       u"（「高压气罐必须接泵泵出」），界面遇到气体则明确让玩家接泵。"
       u"④ 探针 `FluidExchangerCheck` 真服务端 **48 项全 [OK]**（含逐 tick 轨迹、泵的 SIMULATE/EXECUTE、"
       u"气体走泵、用户的九宫格配方用 `CraftingInput` 真跑一遍认出来）。"
       u"⑤ 四语言 257 → **270** 键；合成配方 29 → **30** 条；两个坑记进 §4.54 / §4.55。 |\n")

VERIFY = u"""
### ZF82（0.11）柴油桶/汽油桶 + 容器换流器 —— 待你实测

- [ ] **柴油桶 / 汽油桶**：拿空桶右键柴油（源）⇒ 得到柴油桶；拿柴油桶右键地面 ⇒ 放出柴油源 + 返回空桶
      （与水的桶完全一致）；贴图现在是**借的原版水桶**，等你画
- [ ] **容器换流器**：左槽放装了液体的油桶、右槽放**1 个**空桶 ⇒ 3 秒后右槽变成那种流体的桶、
      左槽少 1000 mB；水 ⇒ 原版水桶、柴油 ⇒ 柴油桶
- [ ] 用**别的 mod 的流体**灌进油桶再换 ⇒ 应当产出**那个 mod 自己的桶**（前提是它有桶）
- [ ] 拿**原油**去换 ⇒ 应当**拒绝**并提示「这种流体没有对应的桶」（原油没有官方桶）
- [ ] 左槽放**高压气罐**（气体）⇒ 界面拒绝并提示接泵；把**流体泵**接在换流器上 ⇒ 能抽走，
      **抽的是左槽那件容器**（泵速率决定快慢，抽到容器空为止）
- [ ] ⚠ **四个我替你定的决策**（不合口味说一声，都是一行的事）：
      ① 这台机器**不耗电**（你没给能耗数，本轮没编）；
      ② 右槽只认**原版空桶**（不认油桶/别的 mod 的空容器）；
      ③ 右槽要**刚好 1 个**空桶（桶是原地变成流体桶的，堆叠会分不开；要"能一次塞一叠"就得再加一个输出槽）；
      ④ 气体**只能走泵**（按你说的），界面不做气体

**成品**：`release\\PotatoST-0.11.jar` = `__NEWSHA__`（__NEWSIZE__ B / __NEWENTRIES__ 条目），
**作废上一版 `257ff4b79635f7764bd241d1e7fc17d387188efe`**（ZF81）；0.10 成品 `84d09345…` 原样保留。
"""

TEX = u"""
## ZF82（0.11）：柴油桶 / 汽油桶 + 容器换流器

| 文件 | 状态 | 说明 |
|---|---|---|
| `models/item/diesel_bucket.json` | **借贴图** | `layer0 = minecraft:item/water_bucket`（用户原话「先用水桶贴图」） |
| `models/item/gasoline_bucket.json` | **借贴图** | 同上 |
| `textures/block/fluid_exchanger.png` | **占位（我生成）** | 16×16 / 8 位 RGBA：金属灰底 + 上下两个青色口 + 中间横缝 |
| `textures/block/diesel_still.png` / `_flow.png` | 已有 | ZF78 用户给的贴图，本轮起被**液体方块**用上了 |
| `textures/block/gasoline_still.png` / `_flow.png` | 已有 | 同上 |
"""


def main():
    arch_p = os.path.join(DOCS, u"开发档案.md")
    arch = read(arch_p)
    if u"### 4.54" not in arch:
        anchor = u"\n\n| 版本 | 内容 |"
        if arch.count(anchor) != 1:
            fails.append(u"§4.54 插入点命中 %d 次" % arch.count(anchor))
        else:
            arch = arch.replace(anchor, u"\n" + TRAP1 + TRAP2 + anchor, 1)
    if u"| ZF82 |" not in arch:
        arch = insert_after(arch, u"| ZF81 | **新建 `zf81_pre`**", ROW, u"档案 §5：ZF82 行")
    if u"### ZF82（0.11）柴油桶/汽油桶" not in arch:
        if arch.count(u"\n## 10. 备份策略") != 1:
            fails.append(u"档案 §9：锚点命中 %d 次" % arch.count(u"\n## 10. 备份策略"))
        else:
            arch = arch.replace(u"\n## 10. 备份策略", u"\n" + VERIFY + u"\n## 10. 备份策略", 1)
    write(arch_p, arch)

    tex_p = os.path.join(DOCS, u"贴图清单.md")
    tex = read(tex_p)
    if u"## ZF82（0.11）" not in tex:
        write(tex_p, tex.rstrip(u"\n") + u"\n" + TEX)
        print(u"贴图清单：追加 ZF82 一节")

    print(u"文档改完，失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
