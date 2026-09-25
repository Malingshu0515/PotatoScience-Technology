# -*- coding: utf-8 -*-
u"""_zf94_fix_uv.py —— 让电力高炉两根接线柱的**东/西**也一致（ZF94，用户第 3 条）

用户原话：「**3. 电力高炉 接线方块还是对称一致一下吧**」。

改之前两根柱子的六面（ZF92 之后）：

    #01（原顶=盖板）  上=素板(147,100) 下=盖板(147,66)  南=金框(147,83)  北=深灰(149,0)   东=格栅(47,144) 西=格栅(64,144)
    #02（原顶=金框）  上=素板(154,151) 下=盖板(154,134) 南=金框(154,117) 北=深灰(47,161)  东=素板(149,17) 西=素板(149,34)

`_zf92_tilecmp.py` 逐像素比过：两根柱子**每一面用的都是同一张画**（只是各有一份副本），
**唯一不一致的就是东/西** —— 一根是格栅、一根是素板。

**往哪边一致？** 两条路都说得通，我这里按下面三条证据选「**都用格栅**」：
  ① 格栅那对瓦片（47,144）与（64,144）是**一对专用画**（贴图里只有这两份，另两份副本
     （164,68）/（164,51）归 4 号板用）；而素板那对（149,17）/（149,34）只是**通用素板的第 5、6 份副本**
     —— 让柱子用格栅，贴图里没有任何一张画变成"没人用"；
  ② 用户在 ZF92 的第二张截图里看到的就是 #01 的**格栅**那一面（他把那一格叫「接线的是高炉贴图」），
     说明他心里的"接线块"长相更接近格栅那版；
  ③ 「接线口」上带通风格栅本来就比一块光板更像机器的接口。

⚠ 两条路**都是一行改动**（把东/西换成另一对瓦片即可）—— 用户要另一种，说一声就翻过来。

做法与 ZF92 完全一致：**在"瓦片"这一层重新基准化**（每个顶点在瓦片内的偏移 (du,dv) 原样保留，
只换瓦片原点），**只动 `vt`**；改完两根柱子**每个方向用的都是同一张画**，且东/西用的是**同一个矩形**。

用法：
    python _zf94_fix_uv.py            # 预演
    python _zf94_fix_uv.py --write    # 写补丁工程并用 _zf91_bake 重烘四份 OBJ
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

# 输入 = ZF92 补过的那份工程（链条：用户原件 → ZF92 补丁 → ZF94 补丁 → OBJ）
BB_IN = os.path.join(HERE, "_zf92_ebf_fixed.bbmodel")
BB_ARCHIVE = r"C:\PotatoST救援\zf91_pre\user\electric_blast_furnace.bbmodel"
BB_OUT = os.path.join(HERE, "_zf94_ebf_fixed.bbmodel")

NAME = {(147, 100): u"素板", (147, 83): u"金框", (147, 66): u"盖板",
        (154, 151): u"素板", (154, 117): u"金框", (154, 134): u"盖板",
        (149, 0): u"深灰", (47, 161): u"深灰",
        (47, 144): u"格栅A", (64, 144): u"格栅B",
        (149, 17): u"素板副本1", (149, 34): u"素板副本2"}
# 两根柱子按"顶面当前用哪张画"识别；只改东/西两个面
POST_TOP = {"p1": (147, 100), "p2": (154, 151)}
PATCH = {
    "p1": {},                                    # 第一根已经是格栅，不动
    "p2": {u"东": (47, 144), u"西": (64, 144)},  # 第二根：素板副本 → 与第一根相同的格栅瓦片
}
fails = []


def tile_of(face):
    uu = [face["uv"][k][0] for k in face["vertices"]]
    vv = [face["uv"][k][1] for k in face["vertices"]]
    return (int(round(min(uu))), int(round(min(vv))),
            int(round(max(uu)) - min(uu)), int(round(max(vv)) - min(vv)))


def main(argv):
    from _zf92_facesheet import pick_faces
    write = "--write" in argv
    src = BB_IN if os.path.exists(BB_IN) else BB_ARCHIVE
    print(u"读入工程：%s" % os.path.basename(src))
    d = json.loads(io.open(src, encoding="utf-8").read())

    posts = {}
    for ei, e in enumerate(d["elements"]):
        pf = pick_faces(e)
        t = tile_of(pf["上"])[:2]
        for key, want in POST_TOP.items():
            if t == want:
                posts[key] = (ei, e, pf)
    print(u"\n== ① 定位两根接柱 ==")
    for key in POST_TOP:
        if key not in posts:
            fails.append(u"找不到顶面用 %s 的柱子" % (POST_TOP[key],))
            continue
        ei, e, pf = posts[key]
        row = u"  ".join(u"%s=%s" % (lab, NAME.get(tile_of(pf[lab])[:2], u"?"))
                         for lab in (u"上", u"下", u"南", u"北", u"东", u"西"))
        print(u"  %s（元素 #%02d）  %s" % (key, ei, row))

    print(u"\n== ② 改之前：两根柱子逐面比（每面是不是同一张画）==")
    before = {k: {lab: tile_of(pf[lab]) for lab in (u"上", u"下", u"南", u"北", u"东", u"西")}
              for k, (_ei, _e, pf) in posts.items()}
    if len(before) == 2:
        for lab in (u"上", u"下", u"南", u"北", u"东", u"西"):
            a, b = before["p1"][lab], before["p2"][lab]
            same = (a == b)
            print(u"    %s：p1 %s%-12s  p2 %s%-12s  %s"
                  % (lab, a[:2], NAME.get(a[:2], u"?"), b[:2], NAME.get(b[:2], u"?"),
                     u"一致" if same else u"**不一致**"))

    print(u"\n== ③ 逐面重新基准化（只动东/西，瓦片内偏移不变）==")
    for key, patch in PATCH.items():
        if key not in posts:
            continue
        ei, _e, pf = posts[key]
        for lab, srckey in sorted(patch.items()):
            base = before[key][lab]
            dx, dy = srckey[0] - base[0], srckey[1] - base[1]
            for k in pf[lab]["vertices"]:
                u, v = pf[lab]["uv"][k]
                pf[lab]["uv"][k] = [u + dx, v + dy]
            print(u"  %s（#%02d）%s：%s%s → %s%s（4 个顶点各平移 (%+d,%+d)）"
                  % (key, ei, lab, NAME.get(base[:2], u"?"), str(base[:2]),
                     NAME.get(srckey, u"?"), str(srckey), dx, dy))
    if not any(PATCH.values()):
        print(u"  两根已经一致，无需改动")

    print(u"\n== ④ 改之后：两根柱子逐面比 ==")
    ok = True
    for lab in (u"上", u"下", u"南", u"北", u"东", u"西"):
        a = tile_of(posts["p1"][2][lab])
        b = tile_of(posts["p2"][2][lab])
        same_rect = (a == b)
        # 同一个矩形，或两张矩形里的画**逐像素相同**（艺术家给每面各留了副本）
        same_art = same_rect
        if not same_art:
            import _zf66_png
            w, _h, _c, px = _zf66_png.read_png(
                os.path.join(r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block",
                             "electric_blast_furnace.png"))
            def art(t):
                return [px[(t[1] + y) * w + t[0] + x] for y in range(16) for x in range(16)]
            same_art = art(a) == art(b)
        print(u"    %s：p1 %s%-12s  p2 %s%-12s  %s"
              % (lab, a[:2], NAME.get(a[:2], u"?"), b[:2], NAME.get(b[:2], u"?"),
                 u"同一张画" if same_art else u"**还是不一样**"))
        if not same_art:
            ok = False
            fails.append(u"%s 两根柱子仍不一致" % lab)
        if (a[2], a[3]) != (16, 16) or (b[2], b[3]) != (16, 16):
            fails.append(u"%s 的瓦片尺寸不是 16×16" % lab)
    print(u"  ⇒ 六面**逐面同画**：%s" % (u"是" if ok else u"**否**"))

    print(u"\n== ⑤ 写盘 ==")
    if fails:
        print(u"  [STOP] %d 条不过 ⇒ 什么都不写" % len(fails))
    elif not write:
        print(u"  预演：没加 --write，未写盘")
    else:
        io.open(BB_OUT, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(d, ensure_ascii=False, indent=4))
        print(u"  [OK] 补丁后的工程 → %s（%d 字节）"
              % (os.path.basename(BB_OUT), os.path.getsize(BB_OUT)))
        import _zf91_bake as B
        B.BB = BB_OUT
        print(u"  重烘四份 OBJ（沿用 ZF91 那套烘焙）：")
        rc = B.main(["--write"])
        if rc:
            fails.append(u"重烘失败（_zf91_bake 返回 %d）" % rc)
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
