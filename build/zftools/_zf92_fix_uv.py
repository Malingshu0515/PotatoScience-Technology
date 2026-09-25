# -*- coding: utf-8 -*-
r"""_zf92_fix_uv.py —— 把电力高炉那两根「接线柱」的贴图对调成用户要的样子（ZF92）

用户 2025-ZF92 原话：「第一张这个接线的 顶面和正面贴图对调一下 第二张接线的是高炉贴图
和旁边的接线块改一下 顶部也移」，并在追问里选了 **A 方案**：

    两根柱子都变成   顶面 = 素板(浅灰横纹)   正面(南) = 金框方块   底面 = 带铆钉盖板

模型里那两根柱子（1×1×1，位于塔的 ±X 两侧、y 1..2 格）现在是这样：

    #01（原 上=(147,66) 盖板）  上=盖板  下=金框  南=素板  北=深灰  东/西=格栅
    #02（原 上=(154,117) 金框） 上=金框  下=盖板  南=素板  北=深灰  东/西=素板

同一套画在两个对称零件上装反了（金框一个在顶、一个在底），所以：
    · #02 只需把 **顶面 ↔ 正面** 对调（这正是用户说的「对调」）；
    · #01 要把 上←南、南←下、下←上 转一圈（用户说的「顶部也移」）。

**只改 UV，不改顶点、不改贴图**。做法是"重新基准化"：每个顶点在瓦片内的偏移量 (du,dv) 原样保留，
只把瓦片原点 (x0,y0) 换成新瓦片的 —— 这样每个面各自的 UV 朝向（艺术家定的）不变，
换的只是"取贴图上哪一块"。

用法：
    python _zf92_fix_uv.py            # 预演：只报告
    python _zf92_fix_uv.py --write    # 写补丁后的 .bbmodel 并用 _zf91_bake 重烘四份 OBJ
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BB_ARCHIVE = r"C:\PotatoST救援\zf91_pre\user\electric_blast_furnace.bbmodel"
BB_ATTACH = (r"C:\Users\Administrator\.dsh\attachments\v1\files\15"
             r"\15028bf3d0dc6e7234ea03ec6a697b72858bc12ff7383c401b7c394fd2aab366\电力高炉.bbmodel")
BB_FIXED = os.path.join(HERE, "_zf92_ebf_fixed.bbmodel")

# 五张画（16x16 瓦片原点）—— 名字是给人看的
T_LID = (147, 66)      # 带铆钉 + 内凹方板的"盖板"
T_GOLD = (147, 83)     # 暗底 + 金方框
T_PLAIN = (147, 100)   # 浅灰横纹素板
# #02 那一组（同一张画的副本）
T_LID2 = (154, 134)
T_GOLD2 = (154, 117)
T_PLAIN2 = (154, 151)

TARGET = {"上": u"素板", "南": u"金框", "下": u"盖板"}
NAME = {T_LID: u"盖板", T_GOLD: u"金框", T_PLAIN: u"素板",
        T_LID2: u"盖板", T_GOLD2: u"金框", T_PLAIN2: u"素板"}

# 两根柱子按"顶面当前用的是哪张画"识别（下标不是凭据），再逐面给出**源瓦片**：
#   {顶面瓦片: {目标面: 源面当前用的瓦片}}
# ⚠ 第一版这里把两根柱子的键都写成了第一根的那套瓦片，结果第二根没匹配上（脚本自己 STOP 了，好事）。
POST1_TOP = (147, 66)      # 带铆钉盖板在顶上的那根
POST2_TOP = (154, 117)     # 金框在顶上的那根
PATCH = {
    POST1_TOP: {u"上": (147, 100), u"南": (147, 83), u"下": (147, 66)},
    POST2_TOP: {u"上": (154, 151), u"南": (154, 117), u"下": (154, 134)},
}
TARGET = {"上": u"素板", "南": u"金框", "下": u"盖板"}
NAME = {(147, 66): u"盖板", (147, 83): u"金框", (147, 100): u"素板",
        (154, 134): u"盖板", (154, 117): u"金框", (154, 151): u"素板",
        (149, 0): u"深灰", (47, 161): u"深灰",
        (47, 144): u"格栅", (64, 144): u"格栅",
        (149, 17): u"素板", (149, 34): u"素板"}
fails = []


def tile_of(face):
    uu = [face["uv"][k][0] for k in face["vertices"]]
    vv = [face["uv"][k][1] for k in face["vertices"]]
    return (int(round(min(uu))), int(round(min(vv))),
            int(round(max(uu)) - min(uu)), int(round(max(vv)) - min(vv)))


def main(argv):
    from _zf92_facesheet import pick_faces
    write = "--write" in argv
    src = BB_ARCHIVE if os.path.exists(BB_ARCHIVE) else BB_ATTACH
    print(u"读入工程：%s" % src)
    d = json.loads(io.open(src, encoding="utf-8").read())
    els = d["elements"]

    # ① 找那两根柱子：按"顶面用的是哪张画"定位（不靠数组下标 —— 下标不是凭据）
    posts = {}
    for ei, e in enumerate(els):
        pf = pick_faces(e)
        t = tile_of(pf["上"])[:2]
        if t in PATCH:
            posts[t] = (ei, e, pf)
    print(u"\n== ① 定位两根接柱 ==")
    for key in PATCH:
        if key not in posts:
            fails.append(u"找不到顶面用 %s 的柱子" % (key,))
            continue
        ei, e, pf = posts[key]
        print(u"  顶面 %-10s（%s）⇒ 元素 #%02d origin=%s"
              % (str(key), NAME.get(key, u"?"), ei, e.get("origin")))

    print(u"\n== ② 改之前六面各用的是哪张画 ==")
    before = {}
    for key, (ei, e, pf) in sorted(posts.items()):
        before[key] = {}
        row = []
        for lab in (u"上", u"下", u"南", u"北", u"东", u"西"):
            t = tile_of(pf[lab])
            before[key][lab] = t
            row.append(u"%s=%s%s" % (lab, NAME.get(t[:2], u"?"), u"(%d,%d)" % t[:2]))
        print(u"  #%02d  %s" % (ei, u"  ".join(row)))

    print(u"\n== ③ 逐面重新基准化（瓦片内偏移不动，只换瓦片原点）==")
    for key, (ei, e, pf) in sorted(posts.items()):
        for lab in (u"上", u"南", u"下"):
            srckey = PATCH[key][lab]
            # 源瓦片必须**确实**在这根柱子的某个面上（否则说明我对模型的判断错了，停下来）
            src_tile = None
            for l2, t2 in before[key].items():
                if t2[:2] == srckey:
                    src_tile = t2
                    break
            if src_tile is None:
                fails.append(u"#%02d 上找不到源瓦片 %s（当前六面是 %s）"
                             % (ei, srckey, before[key]))
                continue
            base = before[key][lab]
            dx, dy = src_tile[0] - base[0], src_tile[1] - base[1]
            for k in pf[lab]["vertices"]:
                u, v = pf[lab]["uv"][k]
                pf[lab]["uv"][k] = [u + dx, v + dy]
            print(u"  #%02d %s：%s%s → %s%s（4 个顶点各平移 (%+d,%+d)）"
                  % (ei, lab, NAME.get(base[:2], u"?"), str(base[:2]),
                     NAME.get(src_tile[:2], u"?"), str(src_tile[:2]), dx, dy))

    print(u"\n== ④ 改之后 ==")
    ok = True
    for key, (ei, e, pf) in sorted(posts.items()):
        row = []
        for lab in (u"上", u"下", u"南", u"北", u"东", u"西"):
            t = tile_of(pf[lab])
            row.append(u"%s=%s" % (lab, NAME.get(t[:2], u"?")))
        print(u"  #%02d  %s" % (ei, u"  ".join(row)))
        for lab, want in TARGET.items():
            got = NAME.get(tile_of(pf[lab])[:2], u"?")
            if got != want:
                ok = False
                fails.append(u"#%02d 的%s 是「%s」，要的是「%s」" % (ei, lab, got, want))
    # 尺寸（16x16）必须没变，否则"重新基准化"就不成立
    for key, (ei, e, pf) in sorted(posts.items()):
        for lab in TARGET:
            w, h = tile_of(pf[lab])[2], tile_of(pf[lab])[3]
            if (w, h) != (16, 16):
                ok = False
                fails.append(u"#%02d 的%s 瓦片尺寸变成 %dx%d" % (ei, lab, w, h))
    print(u"  ⇒ 两根柱子的 顶/南/下 = %s ：%s"
          % (u"素板 / 金框 / 盖板", u"对上了" if ok else u"**没对上**"))

    print(u"\n== ⑤ 写盘 ==")
    if fails:
        print(u"  [STOP] %d 条不过 ⇒ 什么都不写" % len(fails))
    elif not write:
        print(u"  预演：没加 --write，未写盘")
    else:
        io.open(BB_FIXED, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(d, ensure_ascii=False, indent=4))
        print(u"  [OK] 补丁后的工程 → %s（%d 字节）"
              % (os.path.basename(BB_FIXED), os.path.getsize(BB_FIXED)))
        import _zf91_bake as B
        B.BB = BB_FIXED          # parse_bbmodel 读的是模块全局，这里换成补丁后的那份
        print(u"  重烘四份 OBJ（沿用 ZF91 那套烘焙，代码路径完全一样）：")
        rc = B.main(["--write"])
        if rc:
            fails.append(u"重烘失败（_zf91_bake 返回 %d）" % rc)
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
