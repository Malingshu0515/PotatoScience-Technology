# -*- coding: utf-8 -*-
r"""_zf92_convention.py —— 统计"贴图上的每一块被用在了哪个朝向的面上"

思路：用户说某个小方块的"顶面和正面贴图对调了"。模型里 19 个元素是同一套画法，
所以"艺术家把哪一块画成顶面"这件事是**可以从全体用法统计出来**的：
如果某块贴图在别的元素上都当"上"用，唯独这一个元素当"南"用，那它八成就是接错了。

只读。
"""
import io
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _zf92_facesheet import pick_faces, DIRS  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BB = r"C:\PotatoST救援\zf91_pre\user\electric_blast_furnace.bbmodel"
TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png"


def main():
    d = json.loads(io.open(BB, encoding="utf-8").read())
    use = {}
    for ei, e in enumerate(d["elements"]):
        for label, f in pick_faces(e).items():
            uvs = f["uv"]
            uu = [uvs[k][0] for k in f["vertices"]]
            vv = [uvs[k][1] for k in f["vertices"]]
            key = (int(round(min(uu))), int(round(min(vv))),
                   int(round(max(uu)) - min(uu)), int(round(max(vv)) - min(vv)))
            use.setdefault(key, []).append((ei, label))
    print(u"== 贴图矩形 -> 用在哪些元素/朝向 ==")
    for key in sorted(use, key=lambda k: (k[0], k[1])):
        items = use[key]
        dirs = {}
        for _ei, lb in items:
            dirs[lb] = dirs.get(lb, 0) + 1
        print(u"  (%3d,%3d) %2dx%-2d ×%-3d  朝向: %s"
              % (key[0], key[1], key[2], key[3], len(items),
                 u"  ".join(u"%s×%d" % (k, v) for k, v in sorted(dirs.items()))))
        if len(items) <= 6:
            print(u"        用于: %s" % u" ".join(u"#%02d%s" % it for it in items))
        else:
            print(u"        用于: %s …（共 %d 处）"
                  % (u" ".join(u"#%02d%s" % it for it in items[:8]), len(items)))


if __name__ == "__main__":
    main()
