# -*- coding: utf-8 -*-
"""_zf60_docs.py —— ZF60 档案落笔（7 张贴图 + webp 的 alpha 坑）

三处动：① 新增 §4.35（方法论：webp 的 alpha / 先看图落盘 / 引号诊断）
        ② §5 加 ZF60 行   ③ §9 加待办
"""
import io
import sys

DOC = r"E:\PotatoST\docs\开发档案.md"

S435 = u'''### 4.35 【方法论】webp 的 alpha：WPF 解码器会**悄悄丢掉**，透明区底下是花屏（0.10 ZF60）

用户给了 7 张贴图（文件名都是 `.png`，**实际全是 webp** —— §4.23「扩展名骗人」第 3 次）。
按老流程用 WPF 解，出来的图**底色是粉色噪点 / 灰白棋盘格**。查下去是两件事叠在一起：

| 现象 | 根因 | 正解 |
|---|---|---|
`BitmapDecoder.Create($uri,'None','OnLoad')` 拿到的帧格式是 **Bgr32**（alpha 全 255），透明区底下的 RGB 是编码器留的垃圾 | WPF 的 webp 解码器**不吐 alpha** —— 可文件里其实**有** `ALPH` 块（RIFF 块清单里看得见：`VP8X(10) ALPH(58) VP8(390)`） | 换个入口：**`BitmapImage` + `CreateOptions='PreservePixelFormat'` + `CacheOption='OnLoad'`**，再 `FormatConvertedBitmap(..., Bgra32, ...)` ⇒ alpha 就出来了（钛锭实测 484 个全透明像素）。`BitmapDecoder` / `BitmapFrame.Create` 走同一条路都拿不到 |
两张矿的贴图**没有** ALPH 块 | 方块贴图本来就不该透明 | 校验按**类型**判：物品贴图要求"有透明底"（不透明比例 5%~99.5%），方块贴图要求"整张不透明"≥99.9% |

**顺带两条**：

- **落盘前先看图**。这一轮是靠 `read_image` 直接看解出来的 PNG 才发现"底色是花屏"的 ——
  只看"尺寸对不对、有没有内容"的话，那 7 张（连花屏一起）会被判成全部合格。
- `_zf60_qcheck.py`：PowerShell 报「哈希字面量不完整」这类**莫名其妙**的解析错时，
  先数一数每行 ASCII 双引号是不是成对（这次就是收尾的 `"` 打成了 `'`，从那一行起连环报错）。

> 待用户确认：磁铁 / 粗钛 / 钛粉 / 钛锭这 4 张是 **32×32**（铁粉与两张矿是 16×16）。
> 游戏里物品按 16×16 的格子渲染，32×32 会被**压掉一半细节**（不会报错，只是糊一点）。
> 想要标准像素材质就导出成 16×16 再发一次；想保留高清也可以就这么放着。

'''

ROW = u'''| ZF60 | **新建 `zf60_pre`**（9 个改前件：2 张占位贴图 + 5 个物品模型 + 2 个方块模型） | 0.10：**用户给的 7 张贴图**（按他给的顺序：磁铁 / 铁粉 / 钛矿石 / 深层钛矿石 / 粗钛 / 钛粉 / 钛锭；他还提醒"文件名可能打错" —— 第 5 张文件名写的是"粗振金"，按顺序当"粗钛"处理）。① 7 个文件**名字都是 .png、实际全是 webp**（§4.23 第 3 次）⇒ 走 WPF 解码；② **webp 的 alpha 差点丢光**：`BitmapDecoder` 给的是 Bgr32、透明区底下是花屏/棋盘格，改用 `BitmapImage + PreservePixelFormat` 才拿到 alpha（详见 §4.35）；③ 尺寸：磁铁/粗钛/钛粉/钛锭 **32×32**，铁粉/两张矿 **16×16**（**待用户确认**要不要统一 16×16）；④ 装进资源树：`textures/item/{magnet,iron_powder,raw_titanium,titanium_powder,titanium_ingot}.png` + `textures/block/{titanium_ore,deepslate_titanium_ore}.png`（后 5 张**新建**，前 2 张覆盖旧占位图）；⑤ **5 个模型改成指向自己的贴图** —— 之前钛那 5 样全在借原版：钛矿→`minecraft:block/iron_ore`、深层钛矿→`minecraft:block/deepslate_iron_ore`、粗钛→`minecraft:item/raw_iron`、钛粉→`minecraft:item/gunpowder`、钛锭→`minecraft:item/iron_ingot`。新写 `_zf60_verify.py`（**常驻**）：7 张都是 8 位 RGBA + 尺寸对 + 物品有透明底/方块整张不透明 + 7 个模型都指向自己的贴图 + **不许再出现那 5 个原版占位串**，实测 0 失败（jar 里也复核了一遍）。门全绿（ModelCheck 的孤儿贴图仍只有那 2 张老占位图） | 见 §9 |
'''

SEC9 = u'''- [ ] **ZF60：等用户看贴图**（成品 `2eda8966…`）。7 张都装好了（磁铁/铁粉覆盖旧占位图，钛那 5 张新建）。
      要看的：① 物品栏里磁铁/铁粉/粗钛/钛粉/钛锭有没有**透明底**（不是花屏方块）；
      ② 钛矿/深层钛矿两块石头贴图；③ **32×32 的那 4 张会不会显得糊**（游戏按 16×16 渲染）——
      想要标准像素材质就导出 16×16 再发一次。
'''


def main():
    text = io.open(DOC, encoding="utf-8").read()
    before = len(text)
    problems = []

    anchor5 = u"## 5. 版本与 [ZF] 流水线记录"
    if text.count(anchor5) != 1:
        problems.append(u"§5 标题不唯一")
    else:
        text = text.replace(anchor5, S435 + anchor5, 1)

    lines = text.split(u"\n")
    out = []
    added = False
    for line in lines:
        out.append(line)
        if line.startswith(u"| ZF59 |") and not added:
            out.append(ROW.rstrip(u"\n"))
            added = True
    if not added:
        problems.append(u"没找到 ZF59 行")
    text = u"\n".join(out)

    anchor9 = u"## 9. 待办与已知限制\n\n"
    if text.count(anchor9) != 1:
        problems.append(u"§9 标题不唯一")
    else:
        text = text.replace(anchor9, anchor9 + SEC9, 1)

    if problems:
        print(u"有失败项，**不落盘**：")
        for p in problems:
            print(u"  !! " + p)
        return 1

    io.open(DOC, "w", encoding="utf-8", newline="\n").write(text)
    print(u"字数 %d -> %d（+%d）" % (before, len(text), len(text) - before))
    print(u"§4.35 / ZF60 行 / §9 全部写入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
