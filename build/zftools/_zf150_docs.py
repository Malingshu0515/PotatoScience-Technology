# -*- coding: utf-8 -*-
"""_zf150_docs.py —— ZF150 文档：贴图清单加一节 + 档案加变更行 + 交接文档活体数字

（本轮不新立雷区号：踩到的都是既有条目 —— §4.111 批量改名、§4.7 汇合点只加行、
  以及"活体数字要一起改"那条。新东西写进 §5 变更行与贴图清单那一节就够。）
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"E:\PotatoST"
LIST = os.path.join(ROOT, "docs", "贴图清单.md")
ARCH = os.path.join(ROOT, "docs", "开发档案.md")
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline="\n").write(t)


def main():
    # ① 贴图清单
    raw = read(LIST)
    sec = read(os.path.join(HERE, "_zf150_section.md"))
    if u"## ZF150（0.12）" in raw:
        print(u"  [幂等] 清单已有 ZF150 小节")
    else:
        if not raw.endswith(u"\n"):
            raw += u"\n"
        write(LIST, raw + sec)
        back = read(LIST)
        print(u"  %s 贴图清单纯追加（%d -> %d 字节）"
              % (u"[OK]" if back.startswith(raw) and u"## ZF150（0.12）" in back else u"[!!]",
                 len(raw.encode()), len(back.encode())))

    # ② 档案变更行
    raw = read(ARCH)
    if u"| ZF150 |" in raw:
        print(u"  [幂等] 档案已有 ZF150 变更行")
    else:
        row = read(os.path.join(HERE, "_zf150_row.txt")).strip()
        lines = raw.split(u"\n")
        idx = None
        for i, ln in enumerate(lines):
            if ln.startswith(u"| ZF"):
                idx = i
        if idx is None:
            print(u"  !! 找不到变更表，停手")
            return 1
        lines.insert(idx + 1, row)
        write(ARCH, u"\n".join(lines))
        print(u"  [OK] 变更表已插入 ZF150 行（追在 %s 之后）" % lines[idx][:12])

    # ③ 交接文档的活体数字：键数 579 -> 583（以及 lzh 的 581 -> 585）
    raw = read(HAND)
    n = 0
    for a, b in ((u"**579 键 × 4**", u"**583 键 × 4**"),
                 (u"579 键 × 4", u"583 键 × 4"),
                 (u"579 键×4", u"583 键×4"),
                 (u"（lzh 581）", u"（lzh 585）"),
                 (u"lzh 581", u"lzh 585")):
        if a in raw:
            raw = raw.replace(a, b)
            n += 1
    if n:
        write(HAND, raw)
        print(u"  [OK] 交接文档活体数字改了 %d 处（579→583 / 581→585）" % n)
    else:
        print(u"  [幂等/跳过] 交接文档里没有要改的活体数字")

    back = read(ARCH)
    ok = (u"| ZF150 |" in back and u"## ZF150（0.12）" in read(LIST))
    print(u"  %s 回读：ZF150 行 / 清单小节 都在" % (u"[OK]" if ok else u"[!!]"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
