# -*- coding: utf-8 -*-
u"""_zf113_docs.py —— ZF113 的文档：§5 行 + §9 小节（酸性反应室去重叠 + JEI 箭头左移）"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"

ROW5 = (u"| ZF113 | **新建 `zf113_pre`**（82 份改前件：`client/AcidicReactionChamberScreen`/"
        u"`client/jei/MachineRecipeCategory`/`AcidicReactionChamberMenu` + `_zf102_verify.py`"
        u"+ 全部常驻校验脚本 + 2 份文档 + 旧成品 jar 与 `.sha1`） | 0.11：**界面去重叠 + JEI 箭头微调**。"
        u"用户原话（附酸性反应室界面截图）：「这个gui可以改一下 有些重叠 然后合金冶炼炉的jei配方箭头"
        u"也向左移5个像素」。**两处重叠都是算出来的、不是感觉**：① 状态灯 (174,25) 8×8 的框画在 "
        u"173..183，而**硫槽 (160,25)** 的框到 177 ⇒ 压 4 px（截图里槽右上角那个黄方块就是灯）"
        u"⇒ 灯挪到能量条正下方 **(190,62)**；② 「物品栏」标签由基类按 `imageHeight-93` 算 = **123**，"
        u"而四个配方按钮在 y=110..**124** ⇒ 压 1~2 px ⇒ 这台机器的界面把标签单独挪到 **129**"
        u"（`this.inventoryLabelY = HEIGHT - 87`），按钮与背包槽位一个没动。③ JEI 箭头：合金炉现在画 "
        u"**7 个输入**（ZF111 加了 2 个消耗品）⇒ 居中算出来紧贴右边的消耗品槽 ⇒ 新增每机器微调钩子 "
        u"`arrowDx(machineId)`，**只给合金炉 -5**，别的机器一格不动。新写 `_zf113_verify.py`："
        u"把界面里所有摆件矩形**逐对算相交**（含槽位），这才是本轮真正的检查 |")

SEC9 = u"""### ZF113（0.11）酸性反应室界面去重叠 + 合金炉 JEI 箭头左移 5 px —— **未打包**

原话（附界面截图）：「这个gui可以改一下 有些重叠 然后合金冶炼炉的jei配方箭头也向左移5个像素」

**重叠不是我"看着像"，是算出来的**（两处都是矩形相交）：

| # | 谁压谁 | 数字 | 改法 |
|---|---|---|---|
| ① | **状态灯**压住**硫槽** | 灯在 (174,25) 8×8 ⇒ 含边框占 173..183；硫槽在 (160,25) ⇒ 边框到 177 ⇒ **压 4 px**（截图里槽右上角那个黄方块就是这盏灯） | 灯挪到能量条正下方 **(190,62)** —— 右下那一列本来只有能量条，谁也不碰谁 |
| ② | **「物品栏」标签**压住**四个配方按钮** | 标签由 `MachineScreen` 按 `imageHeight - 93` 算 ⇒ 216-93 = **123**；按钮在 y=110..**124** ⇒ 压 1~2 px | 这台机器的界面把标签单独往下挪 6 px（**129**）：`this.inventoryLabelY = HEIGHT - 87`；按钮与背包槽位一个都没动 |

**JEI 箭头**：合金炉现在画 **7 个输入**（5 个锭 + ZF111 那 2 个消耗品）⇒ "输入区与输出区之间居中"
算出来会紧贴右边的消耗品槽。新增一个每机器微调钩子：

```java
private int arrowXFor(Entry recipe) { return arrowXBase(recipe) + arrowDx(recipe.machineId()); }
private static int arrowDx(String machineId) { return "alloy_smelter".equals(machineId) ? -5 : 0; }
```

⇒ **只给合金炉 -5**，其它 11 台机器的 JEI 页面一格不动（要改成全体左移就是把 `arrowDx` 返回 -5）。

**证据**：

- [x] `_zf113_verify.py`：把界面里**所有摆件矩形逐对算相交**（7 罐 + 能量条 + 进度条 + 状态灯 +
      4 按钮 + 2 槽位 = 15 个矩形，105 对全查），另查"标签在按钮下沿之下、在背包第一行之上"、
      "没摆件越出 214×216 面板"、"箭头微调只对合金炉生效"
- [x] 反证刀 K138~K140（灯挪回 174 / 标签挪回基类算法 / 箭头微调删掉 —— 逐把都必须红）
- [x] 往轮的 `_zf101_verify.py`（界面摆件）与 **`_zf102_verify.py`**（它钉着 `new StatusLampPart(174`
      —— 已同步到新坐标）复跑仍绿

**要你实测的**：打开酸性反应室 —— 硫槽右上角**不该再压着那个黄点**（灯现在在右下角能量条底下，
鼠标放上去还是那套状态文案）；「物品栏」四个字与四个配方按钮之间**留出空**。

**成品**：**本轮没有新成品** —— `release\\PotatoST-0.11.jar` 仍是 ZF103 那版 `90510e18…`。

"""


def main():
    fails = []
    text = io.open(DOC, encoding="utf-8", newline="").read()
    if u"| ZF113 |" in text:
        fails.append(u"§5 行已经写过了")
    lines = text.split(u"\n")
    idx_row = [i for i, l in enumerate(lines) if l.startswith(u"| ZF112 |")]
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
    for h in (u"| ZF113 |", u"### ZF113（0.11）"):
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
