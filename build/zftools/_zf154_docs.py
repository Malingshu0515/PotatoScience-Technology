# -*- coding: utf-8 -*-
# _zf154_docs.py —— ZF154 文档：贴图清单加一节 + 档案加变更行
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"E:\PotatoST"
LIST = os.path.join(ROOT, "docs", "贴图清单.md")
ARCH = os.path.join(ROOT, "docs", "开发档案.md")


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline="\n").write(t)


def main():
    raw = read(LIST)
    sec = read(os.path.join(HERE, "_zf154_section.md"))
    if u"## ZF154（0.12）" in raw:
        print(u"  [幂等] 清单已有 ZF154 小节")
    else:
        if not raw.endswith(u"\n"):
            raw += u"\n"
        write(LIST, raw + sec)
        back = read(LIST)
        print(u"  %s 贴图清单纯追加（%d -> %d 字节）"
              % (u"[OK]" if back.startswith(raw) and u"## ZF154（0.12）" in back else u"[!!]",
                 len(raw.encode()), len(back.encode())))

    raw = read(ARCH)
    if u"| ZF154 |" in raw:
        print(u"  [幂等] 档案已有 ZF154 变更行")
    else:
        row = read(os.path.join(HERE, "_zf154_row.txt")).strip()
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
        print(u"  [OK] 变更表已插入 ZF154 行（追在 %s 之后）" % lines[idx][:12])

    back = read(ARCH)
    ok = u"| ZF154 |" in back and u"## ZF154（0.12）" in read(LIST)
    print(u"  %s 回读：ZF154 行 / 清单小节 都在" % (u"[OK]" if ok else u"[!!]"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
