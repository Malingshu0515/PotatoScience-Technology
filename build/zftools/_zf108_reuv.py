# -*- coding: utf-8 -*-
u"""_zf108_reuv.py —— ZF108：把成型后的合金冶炼炉从"4×4 像素被放大铺满整机"里救出来

**病灶（ZF68 用户模型带进来的，今天才量出来）**：`alloy_smelter_{north,east,south,west}.obj`
每个 112 顶点 / 84 面，却只有 **4 个唯一 `vt`**：

    vt 0.0000 0.7500     vt 0.0000 1.0000
    vt 0.2500 0.7500     vt 0.2500 1.0000

四个点正好是贴图上 **4×4 像素**的一个小方格（u 0~0.25、v 0.75~1.0）⇒ 每个面都只采这一小块，
被**放大**铺满整面（不是平铺！）。所以这支模型"借谁的贴图都一样糊"，也是用户说它丑的一半原因
（另一半是 `alloy_smelter.mtl` 借的是 `heat_resistant_metal_block`，机体根本没有自己的画）。

**改法**：把这 4 个点**等比放大到整张贴图**（u 0.25→1.0、v 0.75→0.0），
`vt` 之外的**一个字节都不动**（v / vn / f / usemtl / 注释全留），
再把 MTL 的 `map_Kd` 指到新画的 `alloy_smelter_formed.png`。

⚠ 朝向：老模型借的是均色贴图 ⇒ 它到底是正着还是反着**从无证据**。本轮的机体贴图
   **做成上下镜像对称**，"翻不翻"因此不成问题（`_zf108_verify.py` 有一条断言盯它）。

用法：
    python build/zftools/_zf108_reuv.py            # 只打印计划 + 逐行核对，不写
    python build/zftools/_zf108_reuv.py --write    # 真写
"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
MDIR = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\block")
OBJS = [u"alloy_smelter_north.obj", u"alloy_smelter_east.obj",
        u"alloy_smelter_south.obj", u"alloy_smelter_west.obj"]
MTL = u"alloy_smelter.mtl"
OLD_TEX = u"potato_s_t:block/heat_resistant_metal_block"
NEW_TEX = u"potato_s_t:block/alloy_smelter_formed"

# 4 个唯一 vt → 整张贴图（保持"哪个角对哪个角"的配对关系不变，只做等比缩放）
VT_MAP = {
    u"vt 0.2500 1.0000": u"vt 1.0000 1.0000",
    u"vt 0.0000 1.0000": u"vt 0.0000 1.0000",     # 不动（已经在角上）
    u"vt 0.0000 0.7500": u"vt 0.0000 0.0000",
    u"vt 0.2500 0.7500": u"vt 1.0000 0.0000",
}


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def patch_obj(name, text):
    u"""返回（新文本, 改了几行, 逐类行数统计）"""
    lines = text.split(u"\n")
    changed = 0
    stats = {}
    for i, l in enumerate(lines):
        key = l.strip()
        kind = key.split(u" ")[0] if key else u""
        stats[kind] = stats.get(kind, 0) + 1
        if key in VT_MAP:
            new = VT_MAP[key]
            if new != key:
                lines[i] = l.replace(key, new)
                changed += 1
    return u"\n".join(lines), changed, stats


def main():
    do_write = "--write" in sys.argv
    fails = []
    print(u"目标目录：%s" % MDIR)
    for name in OBJS:
        p = os.path.join(MDIR, name)
        if not os.path.exists(p):
            fails.append(u"缺文件：%s" % name)
            continue
        text = read(p)
        before_sha = hashlib.sha1(text.encode("utf-8")).hexdigest()
        new, changed, stats = patch_obj(name, text)
        vb = sum(1 for l in text.split(u"\n") if l.strip().startswith(u"vt "))
        va = sum(1 for l in new.split(u"\n") if l.strip().startswith(u"vt "))
        vset_b = sorted(set(l.strip() for l in text.split(u"\n") if l.strip().startswith(u"vt ")))
        vset_a = sorted(set(l.strip() for l in new.split(u"\n") if l.strip().startswith(u"vt ")))
        # 逐类核对：只有 vt 行可以变
        diff_kinds = set()
        for a, b in zip(text.split(u"\n"), new.split(u"\n")):
            if a != b:
                diff_kinds.add((a.strip().split(u" ")[0] if a.strip() else u""))
        ok = (vb == va and diff_kinds <= set([u"vt"]) and len(vset_b) == 4 and len(vset_a) == 4)
        print(u"  [%s] %-28s vt 行 %d→%d，唯一值 %d→%d，改动只落在 %s"
              % (u"OK" if ok else u"FAIL", name, vb, va, len(vset_b), len(vset_a),
                 sorted(diff_kinds) or u"（无）"))
        if not ok:
            fails.append(u"%s：改动的行类型越界 %s" % (name, sorted(diff_kinds)))
        if do_write:
            write(p, new)
            back = read(p)
            if back != new:
                fails.append(u"%s：写回读不一致" % name)
            else:
                print(u"        [写出] %d 行里改了 %d 行；sha1 %s → %s"
                      % (len(new.split(u"\n")), changed, before_sha[:10],
                         hashlib.sha1(back.encode("utf-8")).hexdigest()[:10]))
    # ---- MTL ----
    p = os.path.join(MDIR, MTL)
    if not os.path.exists(p):
        fails.append(u"缺文件：%s" % MTL)
    else:
        text = read(p)
        if OLD_TEX not in text:
            fails.append(u"%s 里找不到旧贴图引用 %s" % (MTL, OLD_TEX))
        else:
            new = text.replace(OLD_TEX, NEW_TEX)
            new = new.replace(
                u"# ZF68：用户模型暂时没有贴图，按用户要求先用**耐热金属块**那张（Kd 拉满，免得被漫反射色压暗）",
                u"# ZF68：用户模型当时没贴图，先用耐热金属块那张；\n"
                u"# ZF108：机体有自己的画了（alloy_smelter_formed.png，16×16 上下镜像对称），\n"
                u"#        同时把那 4 个唯一 vt 等比放大到整张贴图（原来只有 4×4 像素被放大铺满整面）。\n"
                u"#        Kd 仍是拉满，免得被漫反射色压暗。")
            print(u"  [%s] %-28s map_Kd：%s → %s"
                  % (u"OK" if NEW_TEX in new else u"FAIL", MTL, OLD_TEX.split(u"/")[-1],
                     NEW_TEX.split(u"/")[-1]))
            if do_write:
                write(p, new)
                if NEW_TEX not in read(p):
                    fails.append(u"%s：写回读里没有新贴图引用" % MTL)
    print(u"")
    if not do_write:
        print(u"（没写任何字节；加 --write 才落盘）")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
