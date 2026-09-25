# -*- coding: utf-8 -*-
u"""_zf114_textures.py —— ZF114「星轨坠」与「粗振金」两张物品贴图（16×16，程序生成）

用户原话：星轨坠是「一个道具」、粗振金是「15 以上固定产出 3 个」的那种原矿 ——
两张都是**程序生成的占位**（用户没给素材），配色按本工程既有的器物风格来。

画法：ASCII 像素图 + 调色板。
  · 好处：每个像素都能逐行数、能断言（本脚本对每行长度、字符是否在调色板里都断言），
    而不是"用一堆画圆公式拼出来再看命"。
  · 落盘前必须 `read_image` 亲眼看（档案 §4.35）：只看尺寸和不透明比例会被花屏骗过去。

跑法：
    python build\\zftools\\_zf114_textures.py            # 只写 build\\zftools\\_zf114_out\\ 预览
    python build\\zftools\\_zf114_textures.py --write     # 同时写进 src\\main\\resources\\...
"""
import io
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from _zf66_png import write_png, read_png   # noqa: E402  （项目自带的 PNG 读写，ZF66 起就带校验）

ROOT = r"E:\PotatoST"
OUT = os.path.join(ROOT, "build", "zftools", "_zf114_out")
DEST = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "textures", "item")

# ----------------------------------------------------------------------------
# 调色板：键 = ASCII 图里用的字符，值 = RGBA
# ----------------------------------------------------------------------------
PALETTE = {
    u".": (0, 0, 0, 0),          # 透明

    # 金链环（星轨坠顶部那个挂环）
    u"g": (109, 79, 26, 255),    # 暗金（描边）
    u"G": (226, 178, 74, 255),   # 金
    u"h": (255, 232, 160, 255),  # 金高光

    # 紫水晶主体（星轨坠）
    u"v": (44, 20, 74, 255),     # 深紫（描边）
    u"V": (124, 77, 232, 255),   # 紫
    u"c": (167, 139, 250, 255),  # 浅紫

    # 星光
    u"w": (238, 240, 255, 255),  # 星芯（近白）
    u"s": (176, 168, 255, 255),  # 星芒 / 轨道碎光

    # 粗振金（深紫金属块）
    u"d": (26, 20, 44, 255),     # 暗描边
    u"D": (62, 52, 100, 255),    # 金属底色
    u"m": (104, 84, 180, 255),   # 中间调
    u"l": (168, 150, 255, 255),  # 高光
    u"H": (222, 214, 255, 255),  # 镜面点
}

# ----------------------------------------------------------------------------
# 拼行工具：每行由若干 (起始列, 片段) 组成，**同一行内不许重叠**（写错当场炸）。
# 这样就不必手数 16 个点 —— 数错正是这套图最容易被糊弄过去的地方。
# ----------------------------------------------------------------------------
def row(*segs):
    line = [u"."] * 16
    for x0, seg in segs:
        for i, ch in enumerate(seg):
            assert line[x0 + i] == u".", u"第 %d 列被写了两次（片段 %r）" % (x0 + i, seg)
            line[x0 + i] = ch
    assert len(line) == 16
    return u"".join(line)


def art(*rows):
    assert len(rows) == 16, u"必须正好 16 行，现在 %d 行" % len(rows)
    return list(rows)


# ----------------------------------------------------------------------------
# 图 1：星轨坠 —— 顶部金环 + 紫水晶坠体 + 里面一颗四芒星 + 两侧轨道碎光
# ----------------------------------------------------------------------------
PENDANT = art(
    row(),
    row((6, u"gGGg")),
    row((5, u"gGhhGg")),
    row((5, u"gG"), (8, u"Gg")),          # 环孔透明
    row((6, u"gGGg")),
    row((5, u"vvVVvv")),
    row((4, u"vVVccVVv")),
    row((3, u"vVVccccVVv")),
    row((3, u"vVccwwccVv")),
    row((3, u"vVcwwwwcVv")),
    row((4, u"vVcwwcVv")),
    row((4, u"vVVccVVv")),
    row((5, u"vVVVVv"), (13, u"s")),     # 右侧轨道碎光
    row((6, u"vVVv")),
    row((2, u"s"), (11, u"s")),          # 坠体下方的星尘
    row(),
)

# ----------------------------------------------------------------------------
# 图 2：粗振金 —— 一簇三块深紫金属原矿（照原版"粗矿"那种碎块手感）
#   全部收在 2..13 列内：贴边的像素在物品栏里会被裁掉，看着像缺角。
# ----------------------------------------------------------------------------
RAW_VIBRANIUM = art(
    row(),
    row(),
    row((5, u"dddd")),
    row((4, u"dDmmDd")),
    row((3, u"dDmllmDDd")),
    row((3, u"dDmHlmmDDd")),
    row((3, u"dDDmmmmDDd")),
    row((4, u"dDDmmmmDd")),
    row((5, u"dddddddd")),                        # 上块收口
    row((2, u"ddd"), (8, u"dDmllD")),             # 左下小块起 + 右下块起
    row((2, u"dDmHd"), (8, u"dDmHlD")),
    row((3, u"dDDd"), (8, u"dDmmmD")),
    row((3, u"dd"), (8, u"dDDDDd")),
    row((10, u"dddd")),
    row(),
    row(),
)


def build(art, name):
    u"""ASCII 图 -> RGBA 像素列表，带两条**会失败的**断言"""
    h = len(art)
    assert h == 16, u"%s: 行数 %d != 16" % (name, h)
    px = []
    for y, row in enumerate(art):
        if len(row) != 16:
            raise ValueError(u"%s 第 %d 行长度 %d != 16：%r" % (name, y, len(row), row))
        for x, ch in enumerate(row):
            if ch not in PALETTE:
                raise ValueError(u"%s 第 %d 行第 %d 列出现调色板外的字符 %r" % (name, y, x, ch))
            px.append(PALETTE[ch])
    assert len(px) == 256, u"%s: 像素数 %d != 256" % (name, len(px))
    return px


def describe(path, name):
    w, h, ctype, px = read_png(path)
    opaque = sum(1 for p in px if p[3] == 255)
    clear = sum(1 for p in px if p[3] == 0)
    colors = len(set(p[:3] for p in px if p[3] > 0))
    print(u"   %-22s %dx%d colorType=%d 不透明 %d (%.1f%%) 全透明 %d 颜色数 %d"
          % (name, w, h, ctype, opaque, 100.0 * opaque / (w * h), clear, colors))
    # 物品贴图必须有透明底（TextureCheck 的口径），也是本图"没画满"的证据
    assert 0 < opaque < 256, u"%s: 不透明像素 %d 不合法（物品图必须有透明底）" % (name, opaque)


def preview(path, name):
    u"""16×16 直接看太小 —— 出 10 倍最近邻预览（档案 §6.8 的做法）"""
    w, h, ctype, px = read_png(path)
    scale = 10
    big = []
    for y in range(h):
        row = []
        for x in range(w):
            row += [px[y * w + x]] * scale
        for _ in range(scale):
            big += row
    out = os.path.join(OUT, name + u"_x10.png")
    write_png(out, w * scale, h * scale, big)
    print(u"   预览：%s" % out)
    return out


def main(argv):
    do_write = "--write" in argv
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    jobs = [(u"starfall_pendant", PENDANT), (u"raw_vibranium", RAW_VIBRANIUM)]
    for name, art in jobs:
        print(u"[%s]" % name)
        px = build(art, name)
        tmp = os.path.join(OUT, name + u".png")
        write_png(tmp, 16, 16, px)
        describe(tmp, name)
        preview(tmp, name)
        if do_write:
            if not os.path.isdir(DEST):
                raise SystemExit(u"目标目录不存在：%s" % DEST)
            dst = os.path.join(DEST, name + u".png")
            write_png(dst, 16, 16, px)
            print(u"   >>> 已写入 %s" % dst)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
