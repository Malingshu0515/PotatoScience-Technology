# -*- coding: utf-8 -*-
"""_zf63_docs.py —— ZF63 档案落笔（配方耗电 5800 → 800 FE/t）"""
import io
import sys

DOC = r"E:\PotatoST\docs\开发档案.md"

ROW = u'''| ZF63 | **新建 `zf63_pre`**（1 个改前件：`AlloySmelterRecipes.java`） | 0.10：**配方耗电 5800 → 800 FE/t**（用户答复：「行吧改成800 2的话就一次做一份吧」—— 我把"一件 348 万 FE、低级发电机要跑 9.7 小时"这笔账算给他看之后他拍的板；第 2 问"要不要并行"保持**一次一份**）。① `ENERGY_PER_TICK` 一处常量改动（BE 与 JEI 都从它读 ⇒ 只有一个数字要改）；② 一件总耗电 348 万 → **480,000 FE**（800 × 600），机器 32768 的缓冲够跑 **41 tick**（原来只够 5.6 tick）；③ ZF42 静态守卫照样满足（800 ≤ 32768）。探针 `AlloyRecipeCheck` 复跑 **23 项全 [OK]**（`ticks=600 injected=479200 spent=480000`）；**并且把探针里的期望值改成字面量**（800 / 480000 / 600，不再从被测常量抄 —— 抄的话改坏常数探针跟着变，等于没检查，§4.27）；反证：把常量改成 700 ⇒ **4 FAIL**（`per-tick draw is exactly 800 FE/t (got 700)`）。⚠ **记账失误一笔**：我先用 ZF62 那个发布脚本发的（里面写着作废 ZF60 的哈希），而它**先拷文件后报错** ⇒ 等改好脚本再跑时"旧 jar"已经不是 ZF62 那一版了，报了一条虚警。**规矩：发布脚本的 VOID 必须每次跟着改**（本次成品 `b2e60d50…`，作废 `d62a8e42…`） | 见 §9 |
'''

OLD9 = u'''- [ ] **数字待你确认**：5800 FE/t × 30 秒 = **一件 348 万 FE**，而本模组的低级发电机只有 100 FE/t
      （要跑 9.7 小时才够一件），机器自身缓冲 32768 只够 5.6 tick ⇒ 必须**持续**供 5800 FE/t。
      这是照你给的字面值实现的；要是想调小（比如 580），说一声就改一个常数。
- [ ] 配方**一次只做一份**（不并行）。要像电力高炉那样多个输入槽同时开工也行，但得设上限
      保证 `并行数 × 5800 ≤ 32768`（最多 5 路）—— 你要就加。
'''

NEW9 = u'''- [x] ~~5800 FE/t 的数字待确认~~ → **ZF63 用户改成 800 FE/t**（一件 **480,000 FE**，缓冲够跑 41 tick）。
- [x] ~~要不要并行~~ → 用户答复「2的话就一次做一份吧」⇒ **保持一次一份**，不加并行。
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
        if line.startswith(u"| ZF62 |") and not added:
            out.append(ROW.rstrip(u"\n"))
            added = True
    if not added:
        problems.append(u"没找到 ZF62 行")
    text = u"\n".join(out)

    if text.count(OLD9) != 1:
        problems.append(u"§9 里那两条待办没找到（%d 处）" % text.count(OLD9))
    else:
        text = text.replace(OLD9, NEW9, 1)

    if problems:
        print(u"有失败项，**不落盘**：")
        for p in problems:
            print(u"  !! " + p)
        return 1

    io.open(DOC, "w", encoding="utf-8", newline="\n").write(text)
    print(u"字数 %d -> %d（+%d）" % (before, len(text), len(text) - before))
    print(u"§5 ZF63 行 + §9（两条待办结掉）已写入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
