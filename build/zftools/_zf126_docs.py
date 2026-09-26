# -*- coding: utf-8 -*-
u"""_zf126_docs.py —— ZF126 的文档三处（§5 一行 / §9 一节 / 交接 §6 第 18 条）

用户原话（附游戏内截图）：「这个加个fe缓存 18k的fe」

跑法：
    python build\\zftools\\_zf126_docs.py
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs")
ARCHIVE = os.path.join(DOC, u"开发档案.md")
HANDOVER = os.path.join(DOC, u"多会话协作交接.md")

notes, fails = [], []


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def patch(name, path, old, new, marker=None):
    text = read(path)
    nl = u"\r\n" if u"\r\n" in text else u"\n"
    o, n = old.replace(u"\n", nl), new.replace(u"\n", nl)
    if marker is not None and marker in text:
        notes.append(u"%s（已经改过了，本次只核对）" % name)
        return
    if text.count(o) != 1:
        fails.append(u"%s：锚点命中 %d 次（要 1 次）—— 停手" % (name, text.count(o)))
        return
    io.open(path, "w", encoding="utf-8", newline=u"").write(text.replace(o, n, 1))
    if n not in read(path):
        fails.append(u"%s：回读不认" % name)
        return
    if marker is not None and read(path).count(marker) != 1:
        fails.append(u"%s：标记串在回读里出现 %d 次（要 1 次）"
                     % (name, read(path).count(marker)))
        return
    notes.append(u"%s（锚点 1 次命中，回读通过）" % name)


ROW_ANCHOR = (u"⑩ 证据：`_zf125_verify.py` **92 项**、反证 **K187~K198 十二把刀**"
              u"（逐把咬中指定检查）、四语言 **464 → 476 键** | 见 §9 |\n")

ROW_NEW = ROW_ANCHOR + (
    u"| ZF126 | **新建 `zf126_pre`**（**95 份**改前件：`DieselGeneratorBlockEntity` / "
    u"`DieselGeneratorMenu` / `client\\DieselGeneratorScreen` + `_zf125_verify`/`_zf125_falsify` + "
    u"2 份文档 + 旧成品 jar 与 `.sha1` + 全部常驻校验脚本；逐份核哈希 + 回读证明，失败 0。"
    u"⚠ **两次补账**：① 四份 lang（本轮一个键都没加、建备份时判断「不会碰」就没抄，"
    u"后来常驻判据要用 ⇒ 用「工作区未改 + sha1 == HEAD 的 blob」两条证据补进来）；"
    u"② `PotatoST.java`（探针挂载点，**本工程第三次漏**，见 `_补说明2.txt`）） | "
    u"0.11：**大型柴油发电机的 FE 缓冲 7200 → 18000**。用户原话（附游戏内截图：悬浮框标题"
    u"「柴油发电机接线口」、里面一行「柴油 7.49B」）：「这个加个fe缓存 18k的fe」。"
    u"① **从「自定默认」变成「用户给的数」**：ZF125 那版缓冲是 `MAX_ENERGY = ENERGY_PER_TICK`"
    u"（我自定的「正好 1 tick 的产量」7200，当时挂在 §9 待确认）；用户看过界面之后点名 18k ⇒ 改成"
    u"`MAX_ENERGY = 18_000` 并**与产量解耦**（两个数各是各的常量，以后改产量不会再顺手改掉缓冲，"
    u"§4.97 那一课的同类）；② 18k 的含义：缓冲空时能顶 **2 tick** 的产量（2×7200 = 14400 ≤ 18000），"
    u"第 3 tick 起「装不下整整一 tick」就暂停烧油（`hasRoom()` 一字未动）—— 电网短暂抽不动时不白烧油、"
    u"也不扔电；③ **界面上把那个数画出来了**（`EnergyBarPart`，一根 12×52 的竖条）：用户没点名要条，"
    u"但那是个**看不见的内部数字**，「点名 18k」要能自己确认 ⇒ 画出来是唯一的办法（不要的话删一行）；"
    u"柴油罐与工作指示灯**都还在**（加东西不许挤掉原来的）；④ **语言一个键都没加**（能量条的悬停文案"
    u"用的是别的机器早在用的共享键 `gui.potato_s_t.energy`）⇒ 四语言仍 **476 键 ×4**，"
    u"**零份键数耦合的门需要 retarget**；⑤ 证据：真服务端探针 `Zf126Check` **19 项全绿**"
    u"（常量 18000 / 产量仍 7200 / 两者不相等 / 成型 / **空缓冲连跑 3 tick：7200 → 14400 → 第 3 tick 停**"
    u"（状态 OUTPUT_FULL、柴油只烧 2 mB）/ 抽走 7200 后接着发 / **峰值不超 18000** / 抽干后再抽是 0 / "
    u"缓冲只出不进）、`_zf126_verify.py` **31 项**、反证 **K199~K204 六把刀** | 见 §9 |\n")

SECTION = u"""### ZF126（0.11）：大型柴油发电机的 FE 缓冲 7200 → **18000** —— **已完成**

用户原话（附一张游戏内截图：悬浮框标题「柴油发电机接线口」、里面一行「柴油 7.49B」）：

> 这个加个fe缓存 18k的fe

#### 一、做了什么

| # | 东西 | 落点 |
|---|---|---|
| ① | **缓冲 18000 FE** | `DieselGeneratorBlockEntity.MAX_ENERGY = 18_000`（原来是 `= ENERGY_PER_TICK`，即我自定的 7200） |
| ② | **与产量解耦** | 两个数从此各是各的常量：以后改 `ENERGY_PER_TICK` 不会再顺手把缓冲一起改掉（§4.97 那一课的同类坑） |
| ③ | **界面上画出来** | `EnergyBarPart`（12×52 竖条，读 `menu::getEnergy` 与 `MAX_ENERGY`）；柴油罐与工作指示灯都还在 |
| ④ | **不改语言** | 能量条的悬停文案是共享键 `gui.potato_s_t.energy`（别的机器早在用）⇒ 仍 **476 键 ×4**，没有任何键数耦合的门需要动 |

**18k 的语义**：缓冲空的时候能顶 **2 tick** 的产量（2×7200 = 14400 ≤ 18000）；
第 3 tick 起"装不下整整一 tick"就**暂停烧柴油**（`hasRoom()` 的判据一字未动）——
电网短暂抽不动时不白烧油，也不会把已经发出来的电扔掉。

**关于那根能量条（如实记）**：用户只说"加个 fe 缓存"，**没说要画出来**。但那个数原本是
**界面外的内部数字**，玩家没有任何办法确认 18k 生效 ⇒ 本轮顺手画了一根条（部件是现成的，一行）。
不想要的话删 `DieselGeneratorScreen` 里那三行即可。

#### 二、证据

| 项 | 值 |
|---|---|
| 探针 | 真服务端 `Zf126Check`：**19 项全绿** —— 常量 18000 / 产量仍 7200 / **两者不相等**（解耦）/ 照图纸搭 30 格成型 / **空缓冲连跑 3 tick：7200 → 14400 → 第 3 tick 停下**（状态 OUTPUT_FULL、这 3 tick 只烧 2 mB 柴油）/ 抽走 7200 之后又能发一 tick（柴油 98 → 97）/ **全程峰值不超 18000** / 抽 999999 只拿到真实的 14400 / 抽干后再抽是 0 / 缓冲只出不进（`receiveEnergy` 恒 0） |
| 常驻校验 | `_zf126_verify.py` **31 项**：常量与解耦 / 注释里点名用户原话 / **五个逻辑方法逐一逐字节未变**（serverTick / pushEnergy / hasRoom / recheckStructure / applyPort）/ 界面构造器 = 改前件 + 那一段 EnergyBarPart（多一个字符都不许）/ 导入只多一行 / 四语言仍 476 键且**键集合与改前件逐键相同** |
| 反证刀 | **K199~K204 六把**：缓冲改回 7200 / 写回 `ENERGY_PER_TICK` / 删掉能量条 / 删掉工作指示灯 / 往轮判据 B4 改回旧文案 / 只给 zh_cn 加一个键 —— 逐把咬中指定检查 |
| 往轮判据 | `_zf125_verify.py` 的 **B4** 跟着改（原来断言"缓冲 = 1 tick 的产量"，现在断言 18000 且不许再写 `= ENERGY_PER_TICK`）；其它门**一份都不用动**（本轮不加语言键、不动配方、不动贴图） |
| 两次补账（如实记） | ① 四份 lang：建备份时判断"本轮不碰语言"就没抄，后来判据 C5 要用 ⇒ 用「工作区相对 HEAD 未改 + sha1 == HEAD 的 blob」两条证据补进 `zf126_pre`；② `PotatoST.java`：**探针挂载点又漏了清单**（ZF117 / ZF119 之后**第三次**）⇒ 卸完钩子后「盘上 == HEAD 的 blob」逐字节证明后补进 |

**成品**：本轮**没有新成品**（`release\\` 一个字没动）。

"""

HANDOVER_ANCHOR = (u"⑦ 证据：探针 **50 项全绿** + `_zf125_verify.py` **92 项** + "
                   u"反证 **K187~K198 十二把**。\n")

HANDOVER_NEW = HANDOVER_ANCHOR + u"""
18. **ZF126 的账**：① 大型柴油发电机的 **FE 缓冲从 7200 → 18000**（用户原话「这个加个fe缓存
    18k的fe」）—— 它在 ZF125 时是**我自定的默认**（"正好 1 tick 的产量"），现在**出列**，
    归到"用户给的数"里；两个常量从此**解耦**（`MAX_ENERGY` 不再 `= ENERGY_PER_TICK`，
    以后改产量不会再顺手改掉缓冲）；② **界面上多了一根能量条**（`EnergyBarPart`，12×52）——
    用户没点名要条，理由写在 §9：那个数原本看不见；③ **语言键一个都没加**
    （能量条用共享键 `gui.potato_s_t.energy`）⇒ 仍 **476 键 ×4**、零份键数耦合的门要动；
    ④ 证据：探针 **19 项全绿** + `_zf126_verify.py` **31 项** + 反证 **K199~K204 六把**；
    ⑤ ⚠ **探针挂载点第三次漏进备份清单**（`PotatoST.java`，前两次是 ZF117 / ZF119）——
    下次建改前件时**先把 `PotatoST.java` 写进清单**，别等事后补账。
"""


def main():
    patch(u"① §5 加 ZF126 一行", ARCHIVE, ROW_ANCHOR, ROW_NEW, marker=u"| ZF126 |")
    patch(u"② §9 加 ZF126 一节", ARCHIVE, u"## 10. 备份策略\n",
          SECTION + u"## 10. 备份策略\n", marker=u"### ZF126（0.11）")
    patch(u"③ 交接文档加第 18 条", HANDOVER, HANDOVER_ANCHOR, HANDOVER_NEW,
          marker=u"18. **ZF126 的账**")
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改动 %d 处" % len(notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
