# -*- coding: utf-8 -*-
u"""_zf73_docs.py —— ZF73 对 `docs/开发档案.md` 的五处编辑（每处断言「正好命中 1 次」）

① 新增 §4.45：液体方块**不要**设 `.bucket(...)`（原版空桶会白拿 3000 mB）；
② §5 追加 ZF73 流水线行（0.11 第一批：原油 + 油桶 + 两刀白名单；成品 `2a35a9ee…`）；
③ §9 追加 ZF73 的待办与待你复验清单；
④ §6 新增 §6.18「加一个流体 / 液体方块 / 流体容器要动哪几处」；
⑤ §10 记 ZF73 的备份与发布口径（0.10 与 0.11 两个 jar 并存）。
"""
import hashlib
import io
import sys

ARCH = r"E:\PotatoST\docs\开发档案.md"

A_S5 = u"## 5. 版本与 [ZF] 流水线记录"
A_ROW = u"（要恢复就只有把那张图从回收站还原回去），详见 §10 |"
A_S9 = u"要不要把它从回收站**还原**回 `textures\\block\\`（代价：ModelCheck 会再报 2 条孤儿提示），你定。"
A_S6 = u"## 7. 权威情报来源（怎么查原版行为，别靠记忆）"
A_S10 = u"  ⚠ 这条对账**只对本轮有效**：从 ZF73 起源码树要开始变，跟 v0.10 成品比就没意义了。"

SEC_445 = r"""### 4.45 【实现雷】液体方块**不要**设 `.bucket(...)` —— 否则一个原版空桶白拿 3000 mB（0.11 ZF73）

NeoForge 的 `BaseFlowingFluid.Properties.bucket(Supplier<Item>)` 看着无害（"给这种流体配个桶"），
但它会顺着**原版空桶的拾取路径**漏出去：

```
BucketItem.use  →  方块实现 BucketPickup（LiquidBlock 就是）
                →  LiquidBlock.pickupBlock() 返回 new ItemStack(this.fluid.getBucket())
```

于是玩家拿**原版空桶**右键一下原油，直接得到一个**装满 3000 mB** 的油桶（而油桶一次只舀 1000 mB）
—— 白送 3 倍，还绕过了用户规则「原油只能通过油桶舀取」。

核对过的兜底行为（`BaseFlowingFluid.getBucket()`）：**不设 bucket 时返回 `Items.AIR`**，
`pickupBlock` 给出空栈 ⇒ 原版桶什么也舀不走；而 `BucketItem` 只在返回值非空时才消掉源方块，
所以源方块也不会被白白吃掉。探针里两条都钉了断言（`oil.getBucket() == Items.AIR`）。

⇒ 规矩：**自定义流体要"只能被自己的容器装"时，就不要设 `.bucket(...)`**，
舀取逻辑写在自己的物品里（本工程 = `OilBucketItem.scoopAt`，一次一格 1000 mB、装不下就不舀）。

"""

ROW_ZF73 = u"""| ZF73 | **新建 `zf73_pre`**（52 个改前件：`gradle.properties` + 7 个 java + 4 份 lang + 配方目录**整个 34 份**（glob 进来，不凭记忆）+ 生成器表 + `_zf69_repro.py` + 档案 + 贴图清单 + 旧成品 jar 与 `.sha1`；逐份核哈希、失败 0） | 0.11：**石油线第一批**（v0.11 规划 §6 的 ZF73）。① **原油**：流体 `potato_s_t:crude_oil` + 流动变体 + **本工程第一个液体方块** `potato_s_t:crude_oil`（`LiquidBlock`，属性照抄原版水、`MapColor` 换黑）；参数与岩浆同值（探针实测 `tickDelay=30 / slopeFind=2 / dropOff=2`）、`canConvertToSource(false)`（**不无限**）、`canHydrate(false)`（不润湿耕地）；**故意不设 `.bucket(...)`** ⇒ 原版空桶舀不走（见 §4.45）；② **油桶** `potato_s_t:oil_bucket`：不可堆叠、**3000 mB**、**只装一种**液体（异种拒收）、**拒收气体**、白色容量条 + Shift tooltip（与高压气罐同款表现，内容物另写 `OilBucketContents`，不动已发布的气罐语义）、世界右键**舀**任何液体（**一次一格 1000 mB**，装不下就不舀，源方块真被抽掉）；③ **两刀白名单**（ZF72 规划轮抓到的雷，§4.44）：`ModFluids.isGas` 改成**正向列举**那 3 种气体（含流动变体），`TankContents.isGas` / `FillingMachineBlockEntity.isGasFluid` 一律委托它 —— **改前原油会被当成气体灌进高压气罐**；同源第二刀：灌装机界面原按 `ModFluids.idOf` 的 1..3 紧凑编号同步流体（装了原油会显示「空」），改成**流体注册表 id**；④ **灌装机**：新增 `FluidContainerItem` 接口（容量/收不收/灌/空否），槽位、灌装、完成音、菜单 Shift 快移四处从「写死高压气罐」改成认接口；**水箱改成对任何流体开放**（否则油桶在机器里灌不到油；拒收规矩交给容器）；⑤ **配方**：走生成器表（表里 17 条）⇒ `oil_bucket.json`：`CBC / SBS / IAI`（C=`c:ingots/copper`、B=原版铁桶、S=钢板、I=铁板、A=铝锭），**吃 2 个铁桶、出 1 个**（用户 2026-09-24 拍板）；`_zf73_repro.py` 证明**其余 34 份配方逐字节没动**；⑥ **贴图**：用户直接给了原图（16×16 JPEG、近黑 `rgb(16~21)`、sha256 `d8b4c276…`）⇒ 转成真 PNG 落到 `crude_oil_still.png` / `crude_oil_flow.png`（像素逐点不变，仅换容器格式）；油桶贴图按用户要求**先借原版铁锭**；⑦ **四语言各 +8 键**（210 → **218**）：中文用用户口径（原油/油桶），en/ja/ru 是我译的；⑧ **探针 `OilCheck` 105 项全 [OK]**（流体 id/参数/不无限/原版桶舀不走、液体方块与 fluid 互指、正向白名单 11 条、油桶 3000/单流体/拒气体/白条、**气罐拒原油但气体照旧可混装**（回归）、世界舀取 14 条（含「舀异种被拒且源方块还在」「装满后第 4 次不吞方块」）、灌装机 17 条（含 `tryFillSlot` 真灌 5 mB、扣 60 FE、气罐拒油且不扣电、界面 id = 注册 id 11）、**配方照用户原话硬摆**能合成 1 个 + 两条负向对照、四语言键在服务端能解析）；⑨ **发布**：`mod_version` 0.10 → **0.11**，成品 **`release\\PotatoST-0.11.jar` = `2a35a9eeda99b125e59637ceb6bf74be33bd1d16`**（2,225,933 B / 718 条目）；与 v0.10 成品**逐条目对账**：只在 0.10 里的只有用户 2026-09-22 删掉的孤儿贴图 `lv_001.png`，只在 0.11 里的是 6 份新资源 + 5 个新 class，同名变动的 36 项全是本次真碰过的文件 —— **`PotatoST-0.10.jar`（`84d09345…`）原样保留，不作废**（版本升级，不是同版本重打包）| 见 §4.44 / §4.45 / §6.18 / §9 / §10 |"""""

SEC_S9 = u"""- [ ] **ZF73：等你上手试原油与油桶**（成品 `release\\PotatoST-0.11.jar` = `2a35a9ee…`）。要看的：
      ① 创造页里多了一个**油桶**（现在贴图是原版铁锭，你那张真贴图随时能换）；
      ② 拿油桶右键**原油/水/岩浆**都能舀，一次一格；**舀满 3000 后第 4 次点油面，油不会被吞掉**；
      ③ 桶里装了水再去舀油 ⇒ **舀不动**（异种流体拒收，水面也不消失）；
      ④ 高压气罐**装不进原油**（这是本轮最要紧的一条：改之前它会把原油当气体收下）；
      ⑤ 灌装机里放油桶 + 用管道往机器里灌原油 ⇒ 能灌进去，界面左侧的罐子**显示原油而不是"空"**；
      ⑥ 合成：铜锭/铁桶/铜锭 + 钢板/铁桶/钢板 + 铁板/铝锭/铁板 ⇒ **1 个油桶**（吃 2 个铁桶）。
- [ ] ZF73 说明：**油桶本轮不能倒出/放置**（你只要求"舀取"，见 v0.11 规划 §5 待决 2）。
      要倒出、要能像水桶一样放一桶油到地上，说一声，我加一条交互（潜行右键之类）。
- [ ] ZF73 说明：**原油湖（地表油田）与海洋油田群系还没做** —— 那是 ZF74（`mini_oilfield` 特征、
      沙漠/恶地 3 倍、`potato_s_t:ocean_oilfield` 水色 4047AD）。现在原油方块只能在**创造模式**里
      拿到（`/setblock` 或创造物品栏里没有方块物品 —— 故意不给 BlockItem）。
- [ ] ZF73 顺带一条：`_zf69_repro.py`（ZF69 的复现性脚本）**已经失效但又不报错** ——
      它要的备份根 `...\\PotatoST救援_20260917_183054\\zf69_pre` 被删进回收站了，
      脚本只打印"找不到备份目录"就退出 0（**假绿**）。本轮已把 ZF73 的复现性改成
      `_zf73_repro.py`（备份根在新位置、缺目录直接算失败），并把 `_zf69_repro.py` 改成**响的**。
"""

SEC_618 = r"""### 6.18 加一个**流体 / 液体方块 / 流体容器**要动哪几处（0.11 ZF73 实例：原油 + 油桶）

以本轮"加原油 + 油桶"为例，一次要动的全部落点（照这个清单走，别漏）：

| # | 落点 | 干什么 | 漏了会怎样 |
|---|---|---|---|
| 1 | `ModFluids` | 流体类型（贴图/密度/`canConvertToSource`/`canHydrate`）+ 源 + 流动 + `BaseFlowingFluid.Properties`（`tickRate/slopeFindDistance/levelDecreasePerBlock/block`） | 没有方块 ⇒ 泵抽不到、油田湖放不了 |
| 2 | `ModBlocks` | `LiquidBlock`（属性照抄 `Blocks.WATER`，`MapColor` 换色）+ **不注册 BlockItem** | 忘了注册方块 = 流体没有实体；注册了 BlockItem = 玩家能随手放油 |
| 3 | **气体/液体判定** | `ModFluids.isGas` **正向列举**；`isLiquid = !isGas`；所有旧判定改成委托 | 负向判定会把新流体误判成气体（§4.44 的雷） |
| 4 | 容器物品 | 内容物工具类（`CUSTOM_DATA` 存档）+ 物品类（容量条/tooltip/`use`）+ `FluidContainerItem` 实现 | 灌装机不认它 |
| 5 | `ModItems` | 注册 + **创造模式标签页**（`output.accept`） | 创造里拿不到 |
| 6 | 资源 | `models/item/<id>.json`、`textures/item/<id>.png`；液体方块要 `blockstates/<fluid>.json` + `models/block/<fluid>.json`（只有 `particle`）+ `textures/block/<fluid>_still.png` / `_flow.png` | ModelCheck/TextureCheck 报缺，游戏里紫黑格 |
| 7 | 配方 | 改 `build/zftools/_zf45_recipes.py` 的表再 `--write`（**不要手写 JSON**），然后跑 `_zf73_repro.py` 证明别的配方没被改坏 | 手写 JSON 会被下次重跑覆盖 |
| 8 | 语言 | **四份** lang 同步加键（`fluid_type.` / `fluid.` / `block.` / `item.` / tooltip），键数必须一致 | LangCheck 直接红 |
| 9 | 版本 | `gradle.properties` 的 `mod_version`（0.11 线由用户 2026-09-24 定：没提到 0.12 就都是 0.11） | 成品名与档案对不上 |
| 10 | 发布 | `_zf73_publish.py`（先核对后拷贝 + 与上一版**逐条目对账**） | 说不清这一版到底动了哪些文件 |

**两条只属于流体的坑**（都写进了 §4）：① `.bucket(...)` 不要设，否则原版空桶白拿一整桶（§4.45）；
② 判定别用负向写法（§4.44）。

"""

SEC_S10 = u"""- ✅ **ZF73（0.11 石油线第一批）**：**动手前**建 `zf73_pre`，一次抄 **52 份**（`gradle.properties` + 7 个 java +
  4 份 lang + **配方目录整 34 份**（glob 进来，不凭记忆）+ 生成器表 + `_zf69_repro.py` + 档案 + 贴图清单 +
  旧成品 jar 与 `.sha1`），逐份核哈希、**失败 0**。发布走 `_zf73_publish.py`：**先核对后拷贝**，
  拷贝后核哈希并写 `.sha1`；新成品 `PotatoST-0.11.jar` 与 v0.10 成品**逐条目对账**
  （只在旧 jar 里的 1 项 = 用户删掉的孤儿贴图；只在新的 11 项 = 6 资源 + 5 class；同名变动 36 项全是本轮真碰的）。
  ⚠ 口径：**0.10 → 0.11 是版本升级，两个 jar 并存，不作废任何 SHA1**（"作废"只用于同版本重打包）。
"""


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        print(u"  !! %s：锚点命中 %d 次（必须正好 1 次）⇒ 整篇不写" % (label, n))
        return None
    return text.replace(old, new, 1)


def main():
    text = io.open(ARCH, "r", encoding="utf-8").read()
    before = sha1(ARCH)
    print(u"改前 %d 字符  %s" % (len(text), before[:12]))
    steps = [
        (A_S5, SEC_445 + A_S5, u"① §4.45"),
        (A_ROW, A_ROW + u"\n" + ROW_ZF73, u"② §5 ZF73 行"),
        (A_S9, A_S9 + u"\n" + SEC_S9.rstrip(u"\n"), u"③ §9"),
        (A_S6, SEC_618 + A_S6, u"④ §6.18"),
        (A_S10, A_S10 + u"\n" + SEC_S10.rstrip(u"\n"), u"⑤ §10"),
    ]
    for old, new, label in steps:
        out = replace_once(text, old, new, label)
        if out is None:
            return 1
        text = out
    io.open(ARCH, "w", encoding="utf-8", newline=u"\n").write(text)
    print(u"改后 %d 字符  %s" % (len(text), sha1(ARCH)[:12]))
    print(u"五处编辑全部命中 1 次、已写入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
