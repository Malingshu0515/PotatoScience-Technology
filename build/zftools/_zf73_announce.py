# -*- coding: utf-8 -*-
u"""_zf73_announce.py —— 把 `docs/UpdateAnnouncement_EN.md` 从 0.10 升到 0.11

为什么非改不可：`_zf71_verify.py` 是**活体事实核对**（公告里的数必须等于当前代码/资源），
ZF73 一加原油它就跳闸 4 条 —— 这正是当初设计它的目的（公告跟不上 mod 就自己挂）。
本轮把公告升到 0.11：改版本号、补原油/油桶一节、把 4 个数字改成实测值、把"没做的"写进 known gaps。
每处替换都断言「正好命中 1 次」。
"""
import hashlib
import io
import sys

DOC = r"E:\PotatoST\docs\UpdateAnnouncement_EN.md"

EDITS = [
    (u"# PotatoS&T — 0.10 Content Overview & Update Notes",
     u"# PotatoS&T — 0.11 Content Overview & Update Notes",
     u"标题版本号"),
    (u"Everything listed below is implemented and shipped in 0.10.",
     u"Everything listed below is implemented and shipped in 0.11.",
     u"正文版本号"),
    (u"- **Fluids:** oxygen, hydrogen, chlorine. High-Pressure Gas Tanks store them",
     u"- **Fluids:** oxygen, hydrogen, chlorine, plus **crude oil** (new in 0.11, see below). "
     u"High-Pressure Gas Tanks store them",
     u"流体清单加原油"),
    (u"- **4 languages:** English, 中文, 日本語, Русский (210 keys each)",
     u"- **4 languages:** English, 中文, 日本語, Русский (218 keys each)",
     u"语言键数 210 → 218"),
    (u"borrowed from vanilla (8 models still do this).",
     u"borrowed from vanilla (9 models still do this).",
     u"借贴图数量 8 → 9"),
    (u"*Version 0.10 · mod id `potato_s_t` · built for NeoForge 21.1.235 on Minecraft 1.21.1*",
     u"*Version 0.11 · mod id `potato_s_t` · built for NeoForge 21.1.235 on Minecraft 1.21.1*",
     u"页脚版本号"),
    (u"- **Recipes do not auto-unlock** in the recipe book.",
     u"""- **Crude oil is currently a creative-only fluid.** The fluid, the liquid block and the Oil
  Bucket all work, but the surface oilfields (`mini_oilfield`) and the ocean-oilfield biome are
  **not generated yet** — they arrive in the next update. Until then, place oil with
  `/setblock <pos> potato_s_t:crude_oil` (it spreads like lava and never becomes infinite).
- **The Oil Bucket only scoops.** It cannot pour oil back out or place a source block yet.
- **Recipes do not auto-unlock** in the recipe book.""",
     u"known gaps 补原油两条"),

    # 新增一节：紧跟在 §5 的流体那行后面
    (u"- **Fluids:** oxygen, hydrogen, chlorine, plus **crude oil** (new in 0.11, see below). "
     u"High-Pressure Gas Tanks store them — and yes, the hydrogen",
     u"""- **Fluids:** oxygen, hydrogen, chlorine, plus **crude oil** (new in 0.11, see below).
  High-Pressure Gas Tanks store them — and yes, the hydrogen""",
     u"（占位：把流体行折成两行，供下一处插入锚定）"),
]

OIL_SECTION = u"""
### Crude oil and the Oil Bucket (new in 0.11)

**Crude oil** is a dark, viscous liquid. It is deliberately *not* water-like:

- it **never multiplies** — flowing oil does not turn back into a source block, so a pool you
  scoop out stays empty;
- it spreads at **lava's pace** (30 ticks per step, slope distance 2, level drop 2);
- it does not wet farmland, does not put out fires, and no vanilla bucket can pick it up.

The **Oil Bucket** holds **3000 mB** and is the only container that can take oil:

| | |
|---|---|
| Scooping | right-click a source block: **1000 mB per click** (three clicks fill it) |
| Contents | **one liquid only** — a different fluid, or any gas, simply will not go in |
| Also works on | water and lava (any liquid except the three process gases) |
| Bar | the same white fill bar as the High-Pressure Gas Tank |
| Recipe | copper ingot / bucket / copper ingot, steel plate / bucket / steel plate, iron plate / aluminium ingot / iron plate → **1 Oil Bucket (eats two iron buckets)** |

Oil can also be **pumped** with the Fluid Pump and moved through Fluid Pipes — that is how the
distillation tower will be fed once it exists.
"""


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    text = io.open(DOC, "r", encoding="utf-8").read()
    before = sha1(DOC)
    print(u"改前 %d 字符  %s" % (len(text), before[:12]))
    for old, new, label in EDITS:
        n = text.count(old)
        if n != 1:
            print(u"  !! %s：锚点命中 %d 次（必须正好 1 次）⇒ 整篇不写" % (label, n))
            return 1
        text = text.replace(old, new, 1)
        print(u"  [OK] %s" % label)

    # 新节插在 §5 那条流体行之后。⚠ 第一次锚点写成跨行的
    # "the hydrogen warning is real."（原文在这中间换行）⇒ 命中 0 次；
    # 改成最后一行的尾巴（单行内唯一）
    anchor = u"warning is real."
    if text.count(anchor) != 1:
        print(u"  !! 新节锚点命中 %d 次 ⇒ 整篇不写" % text.count(anchor))
        return 1
    idx = text.index(anchor) + len(anchor)
    text = text[:idx] + u"\n" + OIL_SECTION + text[idx:]
    print(u"  [OK] 新增「Crude oil and the Oil Bucket」一节")

    io.open(DOC, "w", encoding="utf-8", newline=u"\n").write(text)
    print(u"改后 %d 字符  %s" % (len(text), sha1(DOC)[:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
