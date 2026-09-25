# -*- coding: utf-8 -*-
"""_zf61_docs.py —— ZF61 档案落笔（贴图工作流 + TextureCheck 第 7 道门）

⚠ 这一轮**没动源码/资源**（只加工具与文档）⇒ 成品 jar 仍是 ZF60 的 `2eda8966…`，**不作废**。
"""
import io
import sys

DOC = r"E:\PotatoST\docs\开发档案.md"

ROW = u'''| ZF61 | 无（**没动任何源码/资源**：只加工具与文档 ⇒ 成品 jar 仍是 ZF60 的 `2eda8966…`，**不作废**） | 0.10：**贴图工作流改成"用户放文件、我出清单与校验"**（用户提议：「以后贴图工作量大的话我和你说 你告诉我各个贴图文件名 我去放到材质文件夹就可以了 貌似png发给你就变成别的格式了」—— 他观察对了：他发的 `.png` 到我这儿是**转过格式的副本**（webp、alpha 被压平），ZF60 那张"花屏底色"就是这么来的，所以"他自己放文件"才是稳的做法）。新增两样：① **`TextureCheck.py`**（**第 7 道门**）：逐个读 `textures/` 下 90 个文件的**文件头**（不是 PNG 直接 FAIL —— 正好挡住"webp 改名叫 .png"这个坑）、查尺寸是不是 2 的幂、物品贴图有没有 alpha（WARN）、并列出**"还在借原版贴图"的模型**；`--plan` 时生成 ② **`docs/贴图清单.md`**（三列：放哪 / 文件名 / 是什么，照着往材质文件夹丢文件即可，另附命名与格式三条规矩）。首跑结果：90 张**没有一张不是真 PNG**、**待画 8 个**（电容←铁粒、创造模式线缆←红石块、碳酸锂/锂矿精粉/氯化钠←糖、测试流体储罐←玻璃+铁块，都是 §9 早记着的占位），另 25 条 WARN（23 张占位色块是 **160×160** 而不是 16×16、2 张物品贴图没有 alpha）。⚠ 这脚本第一版**自己虚报了 60 多个** —— 把模型里的**贴图变量引用** `"particle": "#all"` 当成了"借原版贴图"；修完 70 → 8。又一次"先怀疑期望"（§4.30） | 见 §9 |
'''

SEC9 = u'''- [ ] **贴图工作流（ZF61 起）**：`docs/贴图清单.md` 是你我共用的清单 —— 现在「待画」8 个：
      电容 / 创造模式线缆 / 碳酸锂 / 锂矿精粉 / 氯化钠 / 测试流体储罐。你把 PNG 丢进
      `textures\\item\\` 或 `textures\\block\\`（**ASCII 文件名**、**真 PNG**、方块 16×16、
      物品 16×16 且背景透明），说一声我跑 `TextureCheck.py` 复核。
      另外：项目里 **23 张老占位色块是 160×160**（不是 16×16），换上你的图时顺带就修掉了。
'''


def main():
    text = io.open(DOC, encoding="utf-8").read()
    before = len(text)
    problems = []

    lines = text.split(u"\n")
    out = []
    added = False
    for line in lines:
        out.append(line)
        if line.startswith(u"| ZF60 |") and not added:
            out.append(ROW.rstrip(u"\n"))
            added = True
    if not added:
        problems.append(u"没找到 ZF60 行")
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
    print(u"§5 ZF61 行 + §9 贴图工作流 已写入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
