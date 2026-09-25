# -*- coding: utf-8 -*-
u"""_zf78_uifix.py —— 按用户 2026-09-24 实测反馈微调版式，并把证据链同步

用户原话：「储罐ui和沥青槽稍微往上提几个像素 有点挡住物品栏字样了」

改了什么：
  · `DistillationOperatorScreen.ROW_Y` 58 → **50**、`DistillationOperatorMenu.SLOT_Y` 92 → **84**
    （已经在源码里改好了；这个脚本只同步"校验脚本 + 文档"）
  · `_zf78_verify.py`：期望值 92 → 84，并**新增 2 条几何回归断言**（罐底 / 沥青槽都必须落在
    「物品栏」那行字上方 —— 算账：原版把标签画在 `imageHeight-93`，高 9 px）
  · 开发档案：§5 那行改为 (158,84) 并记一句改动；§9 补一条 `[x]` 反馈记录 + 新成品哈希

每条替换断言正好命中 1 次。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
VER = os.path.join(ROOT, "build", "zftools", "_zf78_verify.py")
fails = []


def patch(path, old, new, label):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, hits))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def main():
    print(u"== ① 校验脚本：期望值 + 几何回归 ==")
    patch(VER, u'eq(u"沥青槽 y", 92, mc.get("SLOT_Y"))',
          u'eq(u"沥青槽 y（2026-09-24 上提 8 px 后）", 84, mc.get("SLOT_Y"))',
          u"SLOT_Y 92 → 84")
    patch(VER,
          u'    check(u"能量条是竖直的（EnergyBarPart 默认竖直）", "EnergyBarPart" in screen)',
          u'''    check(u"能量条是竖直的（EnergyBarPart 默认竖直）", "EnergyBarPart" in screen)
    # ⚠ 2026-09-24 用户实测：「储罐ui和沥青槽挡住物品栏字样了」
    #   原版把「物品栏」那行字画在 HEIGHT-93（9 px 高）⇒ 机器内容必须落在它上面
    label_y = (sc.get("HEIGHT") or 0) - 93
    check(u"罐底在「物品栏」那行字上方（y=%s，标签在 %d）" % (
        (sc.get("ROW_Y") or 0) + (sc.get("TANK_H") or 0), label_y),
        (sc.get("ROW_Y") or 0) + (sc.get("TANK_H") or 0) <= label_y - 2)
    check(u"沥青槽（+进度条）也在那行字上方（槽底 %s < %d）" % (
        (mc.get("SLOT_Y") or 0) + 18 + 4, label_y),
        (mc.get("SLOT_Y") or 0) + 18 + 4 <= label_y - 1)''',
          u"新增 2 条几何回归断言")

    print(u"== ② 开发档案：§5 那行 ==")
    patch(DOC, u"(158,92)", u"(158,**84**)", u"§5 行的沥青槽坐标")
    patch(DOC,
          u"玩家背包 y=118，左上两行字显示「分馏塔：N / 4 座」",
          u"玩家背包 y=118（⚠ 2026-09-24 你实测「挡住物品栏字样了」⇒ 整排**上提 8 px**："
          u"`ROW_Y` 58→50、`SLOT_Y` 92→84），左上两行字显示「分馏塔：N / 4 座」",
          u"§5 行记一句版式改动")

    print(u"== ③ 开发档案：§9 补一条反馈记录（含新哈希）==")
    patch(DOC,
          u"- [ ] ZF78 说明：**这两个新方块现在都没有合成配方**",
          u"""- [x] **ZF78 版式微调（你 2026-09-24 反馈）**：「储罐ui和沥青槽稍微往上提几个像素
      有点挡住物品栏字样了」⇒ 整排（5 个罐 + 能量条 + 沥青槽 + 进度条）**上提 8 px**
      （`ROW_Y` 58→50、`SLOT_Y` 92→84）：罐底从 110 挪到 **102**。算账：原版把「物品栏」
      那行字画在 `imageHeight - 93`（本面板 = 109，9 px 高占 109~118）⇒ 原来 110 的底边
      正好压住它，现在留 3 px 余量。**顺带钉了一条几何回归断言**（`_zf78_verify.py`：
      罐底与沥青槽都必须 ≤ `HEIGHT-93-2`），下次谁再往下挪会被门拦住。
      这一版成品 = `__NEWSHA__`（同版本重打包 ⇒ 上一版 `2bf27d2c…` 作废）。
      另外你截图里界面写的是「分馏塔：**2 / 4 座**」⇒ **检测这条路是通的**
      （认出 2 座塔），那时停着是因为「石油不足」——原油要先用**流体泵 + 流体管道**打进
      **石油罐**（只有石油罐收料），罐里有油 + 有红石信号才会开始分馏。
- [ ] ZF78 说明：**这两个新方块现在都没有合成配方**""",
          u"§9 补反馈记录")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
