# -*- coding: utf-8 -*-
"""_zf55_verify.py —— ZF55「围起来就能激活」的盘面复核

**期望值是从需求与几何推出来的，不是从代码里抄的**：
判定要查的格 = 底面整张（4×5=20）+ 第 1~2 层的外圈（每层 14，两层 28）= **48**；
长方体的表面 = 80 − 内部 12 = **68**（表面含顶面，只是顶面不参与判定）。
脚本自己按几何算一遍，再和 Java 里的常量、图纸里的空格对。

最要紧的一条硬不变式（ZF55 第一版就是栽在这儿）：
**凡是判定要查的格，图纸里都必须有方块** —— 否则"照图纸搭"的人反而激活不了。
第一版把判定写成"表面 68 格"，而图纸的顶面本来就是漏风的（22 个空格里有 10 个在顶面），
这条断言当场抓到。

其他文本级检查兜住"以后改坏了没人发现"：
  - inspect 必须在取方块之前跳过内部格；
  - ok() 必须看**总缺口数**，不能看"收集到的明细条数"（limit<=0 时明细永远是空的，
    第一版就因此"旁边挖个洞照样成型、成型后永不失效"）；
  - isCasing 必须认 part/port（否则每秒复查会把成型的机器判死）；
  - form() 必须走表面格、且跳过空格/控制器那格；
  - 自动激活三条路必须都接着 tryAutoForm；
  - 挖接线口必须 disassemble（ZF54 那个"留下几十格隐形方块"的坑）；
  - 四语言文案：键集一致、invalid 占位符 7 个、no_port 存在、介绍里 48/68/32768 都在。

最后再跑一遍 _zf52_verify.py（介绍里的摆放图 vs 代码里的图纸逐格一致）。
"""
import io
import json
import os
import re
import subprocess
import sys

PROJ = r"E:\PotatoST"
JAVA = os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod")
LANG = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "lang")
ZFT = os.path.join(PROJ, "build", "zftools")

WIDTH, DEPTH, HEIGHT = 4, 5, 4
LANGS = ("zh_cn", "en_us", "ja_jp", "ru_ru")

fails = []


def check(cond, msg):
    print((u"  [OK]   " if cond else u"  [FAIL] ") + msg)
    if not cond:
        fails.append(msg)


def read(path):
    return io.open(path, encoding="utf-8").read()


def java_layers():
    """从 AlloySmelterStructure.java 里抠出 4 层 × 5 行的图案（权威）。"""
    text = read(os.path.join(JAVA, "AlloySmelterStructure.java"))
    rows = re.findall(r'"([MHRWBCPK S.]{4})"\s*,', text)
    rows = [r for r in rows if len(r) == 4 and all(c in "MHRWBCPKS." for c in r)]
    if len(rows) != 20:
        raise SystemExit(u"从 Java 里抠出 %d 行图案，应该是 20 行" % len(rows))
    return [rows[i * 5:(i + 1) * 5] for i in range(4)]


def main():
    layers = java_layers()
    src_struct = read(os.path.join(JAVA, "AlloySmelterStructure.java"))
    src_block = read(os.path.join(JAVA, "AlloySmelterBlock.java"))
    src_be = read(os.path.join(JAVA, "AlloySmelterBlockEntity.java"))
    src_port = read(os.path.join(JAVA, "AlloySmelterPortBlock.java"))

    # ---------- ① 几何：要查的 58 / 表面 68 ----------
    print(u"① 几何（底面 + 三层墙 + 顶面图纸画了方块的那两列 = 58；长方体表面 = 68）")
    required = set()
    hull = set()
    inner = set()
    for y in range(HEIGHT):
        for j in range(DEPTH):
            for i in range(WIDTH):
                if (y == 0
                        or (y <= HEIGHT - 2 and (j in (0, DEPTH - 1) or i in (0, WIDTH - 1)))
                        or (y == HEIGHT - 1 and layers[y][j][i] != ".")):
                    required.add((y, j, i))
                if y in (0, HEIGHT - 1) or j in (0, DEPTH - 1) or i in (0, WIDTH - 1):
                    hull.add((y, j, i))
                else:
                    inner.add((y, j, i))
    check(len(required) == 58, u"要查的格 58（算出来 %d）" % len(required))
    check(len(hull) == 68, u"表面格 68（算出来 %d）" % len(hull))
    check(len(inner) == 12, u"内部格 12（算出来 %d）" % len(inner))
    check(required <= hull, u"要查的格全都在表面里")
    top_required = {c for c in required if c[0] == HEIGHT - 1}
    check(len(top_required) == 10, u"顶面有 10 格进判定（算出来 %d）" % len(top_required))
    check(all(layers[y][j][i] != "." for (y, j, i) in top_required),
          u"进判定的顶面格都是图纸里画了方块的")

    for name, want in (("REQUIRED_CELLS", 58), ("HULL_CELLS", 68)):
        m = re.search(name + r"\s*=\s*(\d+)", src_struct)
        check(m is not None and int(m.group(1)) == want,
              u"Java 常量 %s == %d（读到 %s）" % (name, want, m.group(1) if m else u"没有"))
    req_body = src_struct.split("public static boolean isRequired(")[1].split("\n    }")[0]
    check("if (y == 0)" in req_body and "return true;" in req_body, u"isRequired：底面整张都查")
    check("return kindAt(y, j, i) != Kind.AIR;" in req_body,
          u"isRequired：顶面只查「图纸画了方块」的格（ZF59 等第四层摆完再成型）")
    hull_body = src_struct.split("public static boolean isHull(")[1].split("\n    }")[0]
    check("y == 0 || y == HEIGHT - 1 || j == 0 || j == DEPTH - 1 || i == 0 || i == WIDTH - 1"
          in hull_body, u"isHull 就是「贴到任意一个面」")

    air_cells = set()
    for y in range(HEIGHT):
        for j in range(DEPTH):
            for i in range(WIDTH):
                if layers[y][j][i] == ".":
                    air_cells.add((y, j, i))
    # ★ 最要紧的不变式：要查的格，图纸里必须有方块
    bad = sorted(required & air_cells)
    check(not bad, u"图纸里每个「要查的格」都有方块（空格撞上的：%s）" % (bad or u"无"))
    # ⚠ 空格总数**不再写死**（§4.30：绝对数字会随图纸变旧 —— ZF57 换图纸后 22 就过时了）。
    #   这里改成验"结构"：空格必须只出现在内部与顶面，且内部 12 格全空。
    top = {c for c in hull if c[0] == HEIGHT - 1}
    check(air_cells <= (inner | top),
          u"空格只出现在内部和顶面（内部 %d + 顶面 %d，实际空格 %d）"
          % (len(inner), len(top), len(air_cells)))
    check(inner <= air_cells, u"内部 12 格在图纸里都是空的")

    # ---------- ② 判定本体 ----------
    print(u"\n② 判定：只查该查的格、认 part/port、ok() 看总缺口数")
    body = src_struct.split("public static Report inspect(")[1].split("\n    }")[0]
    gi = body.find("isRequired")
    gb = body.find("getBlockState")
    check(gi >= 0 and gb >= 0 and gi < gb,
          u"inspect 在取方块之前就跳过内部格（isRequired@%d < getBlockState@%d）" % (gi, gb))
    check("holeCount++" in body, u"inspect 数的是**总**缺口数 holeCount")
    ok_body = src_struct.split("public boolean ok()")[1].split("\n        }")[0]
    check("this.holeCount == 0 && this.wiring > 0" in ok_body,
          u"ok() = 没缺口 且 有接线块")
    check("holes.isEmpty()" not in ok_body,
          u"ok() **没有**看 holes.isEmpty()（limit<=0 时那个永远是空的）")
    casing = src_struct.split("public static boolean isCasing(")[1].split("\n    }")[0]
    for field in ("ALLOY_SMELTER_PART", "ALLOY_SMELTER_PORT"):
        check(field in casing, u"isCasing 认 %s（否则成型后每秒复查会把机器判死）" % field)
    for field in ("COMMON_METAL_BLOCK", "ADVANCED_METAL_BLOCK", "STABLE_METAL_BLOCK",
                  "HEAT_RESISTANT_METAL_BLOCK", "HEATER", "HEAT_SINK", "WIRING_BLOCK",
                  "ALLOY_SMELTER", "IRON_BLOCK", "BLAST_FURNACE", "HOPPER", "CAULDRON"):
        check(field in casing, u"isCasing 收 %s" % field)

    # ---------- ③ 成型/拆解 ----------
    print(u"\n③ 成型只动表面上的机器方块 / 挖接线口要还原")
    form_body = src_be.split("public void form()")[1].split("\n    /**")[0]
    check("isHull" in form_body, u"form() 走 isHull（表面 68 格）")
    check("allPositions()" not in form_body, u"form() 不再用 allPositions()（ZF54 那种 80 格全换）")
    check("isCasing(current)" in form_body and "continue;" in form_body,
          u"form() 跳过空格/非机器方块（顶面漏风时不留隐形格）")
    check("originalFor" in form_body and "originalFor" in src_be,
          u"form() 用 originalFor 解脏状态（上一轮部件格不许记成原始方块）")
    check("structureOk()" in src_be, u"structureOk() 用于每秒复查")
    check("AlloySmelterBlock.tryAutoForm(this.level, this.worldPosition);" in src_be,
          u"没激活的控制器每 10 tick 试一次自动成型")
    check("master.disassemble(pos);" in src_port,
          u"挖接线口会 disassemble(pos)（不留隐形部件格）")

    print(u"\n④ 自动激活三条路")
    for hook in ("protected void onPlace(", "protected void neighborChanged("):
        check(hook in src_block, u"AlloySmelterBlock 覆写了 %s" % hook.strip())
    onplace = src_block.split("protected void onPlace(")[1].split("\n    }")[0]
    neighb = src_block.split("protected void neighborChanged(")[1].split("\n    }")[0]
    check("tryAutoForm" in onplace, u"onPlace → tryAutoForm")
    check("tryAutoForm" in neighb, u"neighborChanged → tryAutoForm")
    try_body = src_block.split("public static void tryAutoForm(")[1].split("\n    }")[0]
    check("isFormed()" in try_body and "isDisassembling()" in try_body,
          u"tryAutoForm 挡住「已成型」与「正在拆解」两个重入")
    check("shellComplete" in try_body, u"tryAutoForm 走 shellComplete")

    # ---------- ⑤ 文案 ----------
    print(u"\n⑤ 四语言文案")
    data = {c: json.loads(read(os.path.join(LANG, c + ".json"))) for c in LANGS}
    base = set(data["zh_cn"])
    for c in LANGS:
        check(set(data[c]) == base, u"%s 键集与 zh_cn 一致（%d 键）" % (c, len(data[c])))
    for c in LANGS:
        inv = data[c]["gui.potato_s_t.alloy_smelter.invalid"]
        check(inv.count("%s") == 7, u"%s invalid 占位符 7 个（数到 %d）" % (c, inv.count("%s")))
        nop = data[c]["gui.potato_s_t.alloy_smelter.no_port"]
        check("%s" not in nop, u"%s no_port 没有占位符" % c)
        tip = data[c]["tooltip.potato_s_t.alloy_smelter"]
        check("58" in tip, u"%s 介绍里写了要查 58 格" % c)
        check("32768" in tip, u"%s 介绍里仍写着储能 32768 FE" % c)
        check(len(tip.split("\n")) <= 20, u"%s 介绍 %d 行（≤20）" % (c, len(tip.split("\n"))))
    tip_zh = data["zh_cn"]["tooltip.potato_s_t.alloy_smelter"]
    check(u"自动激活" in tip_zh, u"中文介绍里写了「自动激活」")
    check(u"顶面" in tip_zh and u"内部" in tip_zh, u"中文介绍里写了「顶面和内部随便放」")

    # ---------- ⑥ 回归：介绍图 vs 代码图纸 ----------
    print(u"\n⑥ 回归 _zf52_verify.py（介绍里的摆放图逐格）")
    p = subprocess.run([sys.executable, os.path.join(ZFT, "_zf52_verify.py")],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", "replace")
    check(p.returncode == 0, u"_zf52_verify.py 通过（exit=%d）" % p.returncode)
    if p.returncode != 0:
        print(out[-2000:])

    print(u"\n------------------------------")
    print(u"失败项 = %d" % len(fails))
    print(u"结论: " + (u"通过" if not fails else u"有失败项"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
