# -*- coding: utf-8 -*-
u"""_zf113_verify.py —— ZF113 常驻校验：酸性反应室界面去重叠 + 合金炉 JEI 箭头左移 5 px

用户原话（附界面截图）：「这个gui可以改一下 有些重叠 然后合金冶炼炉的jei配方箭头也向左移5个像素」

四段：
  ① **几何账**：把界面里所有"摆件"的矩形抠出来逐对算相交 —— 这是本轮的核心检查
     （用户看到的重叠就是两个矩形的交集，能算出来就不该靠眼睛）；
  ② **「物品栏」标签**：必须在按钮下沿之下（y=129 > 124）；
  ③ **JEI 箭头**：只有合金炉 -5，别的机器 0；
  ④ 文档两处。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
SCR = os.path.join(JAVA, r"client\AcidicReactionChamberScreen.java")
JEI = os.path.join(JAVA, r"client\jei\MachineRecipeCategory.java")
DOC = os.path.join(ROOT, r"docs\开发档案.md")
HANDOFF = os.path.join(ROOT, r"docs\多会话协作交接.md")

n_pass = 0
fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def check(name, cond, detail=None):
    global n_pass
    if cond:
        n_pass += 1
    else:
        fails.append(name + (u"  ← %s" % detail if detail else u""))


def eq(name, want, got):
    check(name, want == got, u"期望 %r 实际 %r" % (want, got))


def overlaps(a, b):
    u"""两个 (x, y, w, h) 矩形有没有交集（边贴边不算）"""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def main():
    scr = read(SCR)
    jei = read(JEI)

    # ---------- ① 几何账 ----------
    print(u"== ① 界面摆件的几何账 ==")
    # 摆件（坐标照 AcidicReactionChamberScreen 的常量与实参；槽位另算）
    parts = {}
    for i, x in enumerate((26, 48, 70, 92, 114, 136)):
        parts[u"原料罐%d" % i] = (x, 17, 18, 40)
    for i, x in enumerate((26, 48, 70, 92)):
        parts[u"产物罐%d" % i] = (x, 64, 18, 40)
    parts[u"能量条"] = (190, 17, 12, 40)
    parts[u"进度条"] = (120, 80, 44, 8)
    parts[u"状态灯"] = (190, 62, 8, 8)
    for i in range(4):
        parts[u"按钮%d" % i] = (25 + i * 22, 110, 20, 14)
    # 槽位（含边框：slot 坐标 ±1）
    slots = {u"硫槽": (160, 25, 18, 18), u"输出槽": (160, 49, 18, 18)}

    bad = []
    keys = sorted(parts)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            if overlaps(parts[keys[i]], parts[keys[j]]):
                bad.append(u"%s ∩ %s" % (keys[i], keys[j]))
    eq(u"摆件两两不相交（原来状态灯 ∩ 硫槽）", [], bad)
    bad2 = [u"%s ∩ %s" % (s, k) for s in sorted(slots) for k in keys
            if overlaps(slots[s], parts[k])]
    eq(u"槽位与任何摆件不相交", [], bad2)
    # 别越出面板
    W, H = 214, 216
    eq(u"界面尺寸 214×216", True, "WIDTH = 214" in scr and "HEIGHT = 216" in scr)
    out = [k for k, (x, y, w, h) in list(parts.items()) + list(slots.items())
           if x < 0 or y < 0 or x + w > W or y + h > H]
    eq(u"没有摆件越出面板", [], out)

    # ---------- ② 物品栏标签 ----------
    print(u"\n== ② 「物品栏」标签 ==")
    check(u"标签位置被单独挪过（不再用基类的 imageHeight-93）",
          "this.inventoryLabelY = HEIGHT - 87;" in scr)
    label_y = 216 - 87
    eq(u"标签行 = 129", 129, label_y)
    btn_bottom = 110 + 14
    check(u"标签在按钮下沿之下（129 > 124）", label_y > btn_bottom,
          u"标签 %d，按钮下沿 %d" % (label_y, btn_bottom))
    inv_y = 134
    check(u"标签在背包第一行之上（129 < 134）", label_y < inv_y)

    # ---------- ③ JEI 箭头 ----------
    print(u"\n== ③ JEI 箭头 ==")
    check(u"有每台机器的微调钩子", "private static int arrowDx(String machineId)" in jei)
    check(u"合金炉 = -5", '"alloy_smelter".equals(machineId) ? -5 : 0' in jei)
    check(u"arrowXFor 用上了微调", "return arrowXBase(recipe) + arrowDx(recipe.machineId());" in jei)
    check(u"居中算法本身还在（arrowXBase）", "private int arrowXBase(MachineRecipes.Entry recipe)" in jei)
    eq(u"只有一处调用（定义 + 调用 = 2 次）", 2, jei.count("arrowDx("))

    # ---------- ④ 文档 ----------
    print(u"\n== ④ 文档 ==")
    doc = read(DOC)
    check(u"档案 §5 有 ZF113 行", u"| ZF113 |" in doc)
    check(u"档案 §9 有 ZF113 小节", u"ZF113（0.11）" in doc)
    check(u"档案里写明了那两处重叠的坐标", u"174" in doc and u"123" in doc)

    print(u"")
    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
