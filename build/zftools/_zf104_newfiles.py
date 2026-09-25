# -*- coding: utf-8 -*-
u"""_zf104_newfiles.py —— **动完手之后**记"本轮新增了哪些路径"（回退清单）

由来（我自己的 slip，记在 ZF104 那一行）：`_zf104_backup.py` 里把这份清单写成
"**开始前**的存在性基线"，可它是**跟备份同一次运行**跑的 —— 而备份是"动手前"、
这份清单却是"动手后"才有意义。结果 `_zf104_newfiles.txt` 里 16 条全被标成
`存在(异常)`，是一份**自己骗自己**的清单。
⇒ 拆成独立脚本，**动手之后**跑，语义写死在输出里：列表里的路径 = 回退时要删的。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf104_pre"
JAVA = r"src\main\java\com\potatost\mod"
RES = r"src\main\resources"

NEW = [
    JAVA + r"\ModArmorMaterials.java",
    JAVA + r"\ModArmorItems.java",
    JAVA + r"\ModArmorPiece.java",
    JAVA + r"\ModArmorSet.java",
    RES + r"\assets\potato_s_t\textures\item\star_steel_ingot.png",
    RES + r"\data\c\tags\item\ingots\star_steel.json",
    RES + r"\data\c\tags\item\star_steel_ingots.json",
]
NEW += [RES + r"\assets\potato_s_t\models\item\%s.json" % n for n in (
    "star_steel_ingot", "titanium_alloy_helmet", "titanium_alloy_chestplate",
    "titanium_alloy_leggings", "titanium_alloy_boots",
    "star_steel_helmet", "star_steel_chestplate", "star_steel_leggings", "star_steel_boots")]


def main():
    lines = [u"ZF104 本轮**新增**的路径（16 条）。",
             u"回退办法：下面这些路径**一律删除**；其余被改过的文件用 zf104_pre 里的改前件覆盖。",
             u"（这份清单是动手**之后**由 _zf104_newfiles.py 生成的，语义就是「新增」，不是「存在性基线」）",
             u""]
    missing = []
    for p in NEW:
        exists = os.path.exists(os.path.join(ROOT, p))
        if not exists:
            missing.append(p)
        lines.append(u"%s  %s" % (u"OK  " if exists else u"缺失", p))
    io.open(os.path.join(BK, u"_zf104_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"新增路径 %d 条，实际存在 %d 条 → %s" % (len(NEW), len(NEW) - len(missing), BK))
    for m in missing:
        print(u"  !! 缺：%s" % m)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
