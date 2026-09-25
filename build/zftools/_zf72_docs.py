# -*- coding: utf-8 -*-
u"""_zf72_docs.py —— ZF72 对 `docs/开发档案.md` 的四处编辑（每处断言「正好命中 1 次」）

① §4 新增 **4.44**：负向判定（非水非岩浆 ⇒ 气体）是给未来埋的雷；
② §5 追加 **ZF72** 流水线行（v0.11 石油线规划轮）；
③ §9 追加 ZF72 的待办（规划文档位置 / 头号雷 / 11 条待拍板 / 备份根换了地方）；
④ §10 记「备份根被删进回收站 + 换根」这条事故与对策。

规矩（ToolLint ③）：替换前必须 `count == 1`，否则**整篇不写**、直接报错 —— 宁可不动，
也不要把档案改花。
"""
import hashlib
import io
import os
import sys

ARCH = r"E:\PotatoST\docs\开发档案.md"

fails = []

ANCHOR_S5 = r"## 5. 版本与 [ZF] 流水线记录"
ANCHOR_ROW = u"这张**拼错名的孤儿贴图**当成了第 8 个） | 见 §9 |"
ANCHOR_S9 = u"后者的话我补方块+世界生成。"
ANCHOR_S10 = r"## 10. 备份策略"
ANCHOR_S11 = r"## 11. 代码标准（0.09 起执行）"

SEC_444 = r"""### 4.44 【设计雷】负向判定（「非水非岩浆 ⇒ 气体」）是给未来埋的雷 —— 加液体前必须改成正向白名单（0.11 ZF72 规划轮）

`TankContents.isGas()`（`TankContents.java:151`）与 `FillingMachineBlockEntity.isGasFluid()`（`:134`）
都写成同一种形状：

```java
return fluid != Fluids.WATER && fluid != Fluids.FLOWING_WATER
        && fluid != Fluids.LAVA && fluid != Fluids.FLOWING_LAVA;
```

当初这么写**没错**：世界里只有水与岩浆两种原版液体，本模组的 3 种流体全是气体，
「排掉水和岩浆」恰好等价于「是气体」，两行搞定、还不用维护名单。

**但 v0.11 一加原油，它当场变成错的**：原油既不是水也不是岩浆 ⇒ `isGas(crude_oil) == true`
⇒ `TankContents.fill()` 会**把原油灌进高压气罐**（tooltip 还会照样显示「· 原油：1000 mB」），
灌装机的五个「气体」水箱也会把原油当气体收 —— 直接违反用户原话「不可以罐装气体」。
这条雷是 ZF72 **规划轮、没写一行代码**就抓到的：把新规格逐条落到现有代码上「对一遍」，
比对完了再去实现，成本差一个数量级。

⇒ 立三条规矩：

1. **新增流体/新类别时，判定一律正向列举**：`ModFluids.isGas(fluid)` 只认 OXYGEN / HYDROGEN /
   CHLORINE 及其 flowing 变体。**负向判定（「除了 X 都是 Y」）一律视为待还的债**，加新东西时先还。
2. 同源的第二处（同一轮抓到）：`ModFluids.idOf()/byId()` 只认那 3 种气体，而灌装机界面就是靠
   这个整数 id 同步的 ⇒ 水箱里装了原油，界面显示「空」（看着像机器坏了）。
   ⇒ 加流体时**必须同时审「哪些地方按 id / 按枚举认流体」**，不只是审类型判定。
3. 更一般的教训：**「现在世界上只有 X」这种前提一旦写进判定，就等于给未来埋雷。**
   每加一类新东西，回头把所有「排除式 / 负向式」判定过一遍。

"""

ROW_ZF72 = "| ZF72 | **新建 `zf72_pre`**（1 个改前件：`docs/开发档案.md`，逐份核哈希、失败 0。**备份根换地方了** —— 一直用的桌面根已被删进回收站，见 §10 ⇒ 新根 `C:\\PotatoST救援\\zf72_pre`） | 0.11：**石油线规划轮**（用户原话：「PotatoS＆T v0.11规划（石油相关）第一部分」）⇒ 新增 `docs/v0.11规划.md`（**纯文档，不动 jar**：成品仍是 ZF70 的 `84d09345…`、`mod_version` 仍 `0.10`、**不作废**；v0.11 线由用户 2026-09-20 宣布开启，v0.10 成品继续挂着，两者是**版本关系不是作废关系**）。① 文档 = 你给的**逐字规格** + 20 行「规格→落点」对照 + **10 个侦察出来的雷** + **11 条待你拍板** + 分轮建议（ZF73 石油本体/油桶、ZF74 油田特征/海洋油田群系）+ 3 张待画贴图 + 验收思路；② **头号雷（已立 §4.44）**：现有气体判定是**负向**的（`非水非岩浆 ⇒ 气体`）⇒ 一注册原油，**高压气罐就会把原油当气体收下**，直接违反你的「不可以罐装气体」⇒ ZF73 第一刀改成正向白名单；同源第二雷：灌装机界面按整数 id 同步流体、`ModFluids.idOf/byId` 只认 3 种气体 ⇒ 水箱里装了原油界面显示「空」；③ 其它雷：本工程**从没注册**过液体方块（原油是第一个 `LiquidBlock`，而**流体泵只认液体方块实例** ⇒ 不做成方块泵就永远抽不到）、群系源 codec 已写进 3 个世界预设 JSON 且**旧存档把配置存进 level.dat**（只能加带默认值的可选字段，否则旧存档开图即崩）、`data/minecraft/.../is_overworld.json` 是同工程覆盖的（新群系要追加）、原版 placed_feature **没有**「排除某群系」写法（沙漠/恶地 3 倍要拆成 1 份基础 + 2 份额外）；④ **原版事实不靠记忆**：新写 `_zf72_vanilla_evidence.py`，每次从 `client-extra.jar` 与 NeoForge `sources.jar` 现抠（地表岩浆湖 `rarity_filter chance = 200`、lake 的 `barrier=minecraft:stone` / `fluid=minecraft:lava` / `level=0`、NeoForge `Tags.java` 里**没有**原油通用 `c:` 标签 ⇒ 本轮不加标签），落成 `_zf72_vanilla_evidence.json`，校验再拿文档与它逐条对齐；⑤ 你给的三行配方材料逐项核过：铜锭/铁桶是原版，铁板/钢板/铝锭都在本工程（钢板走 `#c:ingots/steel`，本工程=高碳钢 ⇒ 压板机可产）⇒ **生存可获得**；⑥ 新写常驻 `_zf72_verify.py`（**57 项**：A 规格逐字 / B 文档 vs 代码 / C 文档 vs 原版证据 / D 冻结状态 / E 档案已记录 / F 文档完整）；⑦ **校验抓到我自己写错一处**：文档初稿写「工程里从没出现过 `LiquidBlock`」，实际 `FluidPumpBlockEntity:400` 的泵判定就是 `instanceof LiquidBlock` —— 断言写得太粗（抓字面而非抓注册）才会先 FAIL，收窄成「没有 `new LiquidBlock(` 注册」后过，并把「泵认液体方块」这条**升级成待决 11**（泵到底允不允许抽原油） | 见 §4.44 / §9 / §10 |"""

SEC_S9 = u"""- [ ] **ZF72（v0.11 石油线规划轮）：规格已存档 ⇒ `docs\\v0.11规划.md`**（纯文档，**不动 jar**；成品仍是 `84d09345…`）。
      里面有你给的**逐字规格**、20 行「规格→落点」对照、**10 个侦察出来的雷**、**11 条待你拍板**、
      分轮建议（ZF73 石油本体 + 油桶 / ZF74 地表油田特征 + 海洋油田群系）、3 张待画贴图、验收思路。
- [ ] **ZF72 头号雷（已立 §4.44）**：现有气体判定是**负向**的 —— `TankContents.isGas` 与
      `FillingMachineBlockEntity.isGasFluid` 都写成「非水非岩浆 ⇒ 气体」⇒ **一注册原油，
      高压气罐就会把原油当气体收下**，直接违反你的「不可以罐装气体」。ZF73 第一刀 = 改成正向白名单
      （只列氧气/氢气/氯气 + 流动变体）。同源第二雷：灌装机界面按整数 id 同步流体，而
      `ModFluids.idOf/byId` 只认那 3 种气体 ⇒ 机器里装了原油，界面显示成「空」。
- [ ] **ZF72 待你拍板 11 条**（默认值写在文档 §5，你不回我就按默认走）：① 一次舀 1000 还是 3000；
      ② 油桶能不能倒出液体；③ 「任何液体」含不含原版水/岩浆；④ 灌装机五个水箱是否对任何液体开放；
      ⑤ 油桶配方产出 1 个还是 2 个；⑥ 海洋油田里要不要海底油苗；⑦ 它算不算「海洋」；
      ⑧ 群系源怎么扩（我拟加带默认值的可选字段 —— **不能改名、不能加必填字段**，否则旧存档开图即崩）；
      ⑨ 原油烧不烧/爆不爆；⑩ `mod_version` 何时提到 0.11；⑪ **流体泵允不允许抽原油**
      （你说「原油**只能**通过油桶舀取」，而泵天生认液体方块 ⇒ 这条必须你定）。
- [ ] **ZF72 备份根换地方了**：上一轮的桌面备份根已被删进回收站（取证见 §10），
      本轮起改在 `C:\\PotatoST救援\\zf72_pre\\`。
"""

SEC_S10 = r"""- **⚠ ZF72 备份根换地方（并把事故记档）**：一直用的桌面根
  `C:\Users\Administrator\Desktop\PotatoST救援_<yyyyMMdd_HHmmss>\` 里那份
  `..._20260917_183054`（记录大小 **424,191,790 B**，装着 zf68_pre…zf71_pre 与各轮的 `新增文件\`）
  **已经被删进回收站**（删除时间 **2026-09-19 13:36:29**；`$R` 实体仍在 ⇒ **可以还原**。
  取证脚本 `build/zftools/_zf72_recycle_list.py`，**只读**，不解包、不动回收站）。
  ⇒ 新根源改到 **`C:\PotatoST救援\<阶段名>\`**（C 盘、**不进桌面**，不再被「清桌面」带走）：
  ZF72 起先建 `zf72_pre`（1 个改前件 `docs\开发档案.md`，逐份核哈希、失败 0）。
  桌面那份**要不要还原由用户定**，我不动回收站里的任何东西。
"""


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        fails.append(u"%s：锚点命中 %d 次（必须正好 1 次）" % (label, n))
        return text
    return text.replace(old, new, 1)


def main():
    with io.open(ARCH, "r", encoding="utf-8") as fh:
        text = fh.read()
    before_len = len(text)
    before_sha = sha1(ARCH)
    print(u"改前: %d 字符  %s" % (before_len, before_sha[:12]))

    text = replace_once(text, ANCHOR_S5, SEC_444 + ANCHOR_S5, u"§4.44 插入点（§5 标题前）")
    text = replace_once(text, ANCHOR_ROW, ANCHOR_ROW + u"\n" + ROW_ZF72, u"§5 ZF72 行（ZF71 行之后）")
    text = replace_once(text, ANCHOR_S9, ANCHOR_S9 + u"\n" + SEC_S9.rstrip(u"\n"), u"§9 插入点（ZF71 条目之后）")
    text = replace_once(text, ANCHOR_S10, SEC_S10.rstrip(u"\n") + u"\n" + ANCHOR_S10, u"§10 插入点（§10 标题前）")

    if fails:
        print(u"\n锚点有问题，**整篇不写**：")
        for f in fails:
            print(u"  !! " + f)
        return 1

    with io.open(ARCH, "w", encoding="utf-8", newline=u"\n") as fh:
        fh.write(text)
    after_sha = sha1(ARCH)
    print(u"改后: %d 字符（+%d）  %s" % (len(text), len(text) - before_len, after_sha[:12]))
    print(u"四处编辑全部命中 1 次、已写入")
    for f in fails:
        print(u"  !! " + f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
