# -*- coding: utf-8 -*-
u"""_zf115_docs.py —— ZF115 的文档：§5 行 + §9 小节（锂电池构造间硫酸砍到十分之一）"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"

ROW5 = (u"| ZF115 | **新建 `zf115_pre`**（83 份改前件：`LithiumBatteryPlantBlockEntity` + 四份 lang "
        u"+ 探针存档 `check/Zf112Check.java` + `_zf112_verify`/`_zf112_falsify` + 全部常驻校验脚本 "
        u"+ 文档 + 旧成品）｜⚠ **ZF114 这个号被另一条线占了**（「星轨坠」道具，`zf114_pre` 727 份），"
        u"本轮顺延为 ZF115 | 0.11：**锂电池构造间硫酸砍到十分之一**。用户原话：「锂电池构造间 "
        u"硫酸消耗和储罐容量都先改成原来的十分之一吧」⇒ `ACID_PER_TICK` 10 → **1**、"
        u"`TANK_CAPACITY` 8000 → **800**；一炉 = 1 × 600 = **600 mB**，罐 800 照样**装得下一炉**"
        u"（这条性质两次改数都保住了）。连带改：四语言介绍里的三个数字、探针里那几条**字面量**"
        u"（§4.27：探针期望值不从被测常量抄，所以改数必须手改探针）、`_zf112_verify.py` 的断言、"
        u"`_zf112_falsify.py` 的 K133/K134 锚点；探针**重跑一遍 50 项全绿**（罐满 800 跑完剩 200） |")

SEC9 = u"""### ZF115（0.11）锂电池构造间：硫酸砍到十分之一 —— **未打包**

原话：「锂电池构造间 硫酸消耗和储罐容量都先改成原来的十分之一吧」

| | 改前（ZF112） | 改后（ZF115） |
|---|---|---|
| 每 tick 硫酸 | 10 mB | **1 mB** |
| 罐容量 | 8000 mB | **800 mB** |
| 一炉（30 秒 = 600 tick） | 6000 mB | **600 mB** |
| 罐装得下一炉吗 | 8000 ≥ 6000 ✓ | 800 ≥ 600 ✓（**性质没变，还是"装满一罐够跑完一炉"**） |

**连带改的地方**（一个数在工程里被引用的所有处）：

1. 四语言介绍的三个数字（`tooltip.potato_s_t.lithium_battery_plant`）—— 顺手补了一笔旧账：
   ja/ru 那两份当时只把「罐 2000」留在了原地（ZF112 只补了 zh/en），这次四份一起对齐；
2. **探针里的字面量**（`Zf112Check.java`）—— §4.27 那条规矩的直接后果：探针期望值不许从被测
   常量抄，所以改数**必须手改探针**，否则探针跟着常量一起变、等于没检查；
3. `_zf112_verify.py` 的断言与 `_zf112_falsify.py` 的 K133/K134 锚点（原来钉 10 / 8000）。

**⚠ 编号说明**：**ZF114 被另一条线占了**（「星轨坠」道具那一轮，`zf114_pre` 里 727 份快照），
本轮顺延为 **ZF115** —— 备份根 `zf115_pre`（83 份）。

**证据**：

- [x] **探针重跑：50 项全绿**（`build\\zftools\\_zf112_probe_utf8.txt`）——
      现在验的是：每 tick **1 mB** / 一炉 **600 mB** / 罐 **800** 装得下一炉 /
      满罐 800 跑完一炉**剩 200**；存档已更新（14065 B，sha1 `7c8c19ed…`）
- [x] `_zf112_verify.py` **158 项 0 失败**；反证刀 **K133~K137 五把全咬住**
      （K133 改成"1 mB/t 改回 10"、K134 改成"罐 800 改回 8000"）
- [x] 键数**仍是 432**（ZF114 星轨坠 +15 键之后）（只改值，一个键没加/删）⇒ 19 份键数耦合的校验器一份都没动

**要你实测的**：给构造间灌硫酸 —— 现在**一桶（1000 mB）能灌满 800 的罐还多**，
跑一炉只吃掉 600；这样一瓶硫酸能撑一炉多。

**成品**：**本轮没有新成品** —— `release\\PotatoST-0.11.jar` 仍是 ZF103 那版 `90510e18…`。

"""


def main():
    fails = []
    text = io.open(DOC, encoding="utf-8", newline="").read()
    if u"| ZF115 |" in text:
        fails.append(u"§5 行已经写过了")
    lines = text.split(u"\n")
    idx_row = [i for i, l in enumerate(lines) if l.startswith(u"| ZF113 |")]
    idx_sec = [i for i, l in enumerate(lines) if l.startswith(u"## 10. 备份策略")]
    if len(idx_row) != 1 or len(idx_sec) != 1:
        fails.append(u"锚点命中 §5=%d §9=%d" % (len(idx_row), len(idx_sec)))
    if fails:
        for f in fails:
            print(u"  !! " + f)
        return 1
    sec = SEC9.split(u"\n")
    if sec and sec[-1] == u"":
        sec = sec[:-1]
    out = u"\n".join(lines[:idx_row[0] + 1] + [ROW5] + lines[idx_row[0] + 1: idx_sec[0]]
                     + sec + [u""] + lines[idx_sec[0]:])
    if u"\r" in out:
        fails.append(u"有 CR")
    for h in (u"| ZF115 |", u"### ZF115（0.11）"):
        if out.count(h) != 1:
            fails.append(u"%r 出现 %d 次" % (h, out.count(h)))
    if fails:
        print(u"失败项 = %d（没落盘）" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    io.open(DOC, "w", encoding="utf-8", newline=u"\n").write(out)
    print(u"档案：%d 行 → %d 行" % (len(lines), len(out.split(u"\n"))))
    print(u"失败项 = 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
