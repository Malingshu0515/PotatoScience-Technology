# -*- coding: utf-8 -*-
u"""_zf77_gatefix.py —— 校验与档案对齐 ZF77（海洋油田改成浅海近岸）"""
import io
import sys

Z = r"E:\PotatoST\build\zftools"
VERIFY = Z + r"\_zf75_verify.py"
ARCH = r"E:\PotatoST\docs\开发档案.md"

OLD_B4 = u'    check(u"B4 石岸 → 油田分支存在", u"original.is(Biomes.STONY_SHORE)" in src)'
NEW_B4 = (u'    # ZF77：改成"靠岸的浅海"（用户：「还是放在海里吧 靠近岸边就行」）\n'
          u'    check(u"B4 浅海 → 油田分支存在", u"original.is(Biomes.OCEAN)" in src)\n'
          u'    check(u"B4b 近岸判定（四邻至少一个不是海，用 #minecraft:is_ocean）",\n'
          u'          u"isCoastalOcean" in src and u"is_ocean" in src and u"NEIGHBOUR_OFFSETS" in src)\n'
          u'    check(u"B4c 没再动石岸（旧的 STONY_SHORE 分支已删）", u"Biomes.STONY_SHORE" not in src)')

OLD_S9_TAIL = u"      嫌多/嫌少改 `_zf75` 之后那个默认值或世界预设里的 `\"oil_chance\"`（三个预设都在）。"
NEW_S9_TAIL = OLD_S9_TAIL + u"""
- [x] **ZF77：海洋油田挪到海里了**（用户：「海洋油田还是放在海里吧 靠近岸边就行 概率较低」）。
      判定从"替换**石岸**"改成"替换**靠岸的浅海**"：原版 `minecraft:ocean` 且**四个正方向相邻 quart 格
      至少有一个不在 `#minecraft:is_ocean` 里**（= 贴着陆地/石岸/沙滩）；概率仍是 0.15（`oil_chance`）。
      地貌不动（地形由 multi_noise 决定，换群系只换水色/植被），群系植被步骤也换成海洋风格
      （发光地衣/海草/短海草/海带）。**实测**：新世界正常生成 `Done (6.263s)!`，
      探针 14 项全 [OK] —— 含"靠岸浅海 → 油田（chance 1.0）""远海**不**替换""chance 0.0 全不换"，
      以及注入份数 `plains=1 desert=1+1 ocean=1 oilfield=1`（**无重复注入**）。"""


def main():
    fails = []
    t = io.open(VERIFY, "r", encoding="utf-8").read()
    if t.count(OLD_B4) != 1:
        fails.append(u"verify B4 命中 %d 次" % t.count(OLD_B4))
    else:
        io.open(VERIFY, "w", encoding="utf-8", newline=u"\n").write(t.replace(OLD_B4, NEW_B4, 1))
        print(u"  [OK] _zf75_verify.py：B4 改成浅海近岸 + 加 B4b/B4c")
    a = io.open(ARCH, "r", encoding="utf-8").read()
    if a.count(OLD_S9_TAIL) != 1:
        fails.append(u"档案 §9 尾锚点命中 %d 次" % a.count(OLD_S9_TAIL))
    else:
        io.open(ARCH, "w", encoding="utf-8", newline=u"\n").write(a.replace(OLD_S9_TAIL, NEW_S9_TAIL, 1))
        print(u"  [OK] 档案 §9 记录 ZF77")
    print(u"失败项 = %d" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
