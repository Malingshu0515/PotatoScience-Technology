# -*- coding: utf-8 -*-
# _zf136_docs.py —— ZF136 文档：贴图清单加一节 + 档案加变更行
# （本轮没有新雷区要立：判断依据走的是既有方法，疏漏也是既有 §4.73 那一族，不新开号）
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
    sec = read(os.path.join(HERE, "_zf136_section.md"))
    if u"## ZF136（0.11）" in raw:
        print(u"  [幂等] 贴图清单已有 ZF136 小节")
    else:
        if not raw.endswith(u"\n"):
            raw += u"\n"
        write(LIST, raw + sec)
        back = read(LIST)
        print(u"  %s 贴图清单纯追加（%d -> %d 字节）"
              % (u"[OK]" if back.startswith(raw) and u"## ZF136（0.11）" in back else u"[!!]",
                 len(raw.encode()), len(back.encode())))

    raw = read(ARCH)
    if u"| ZF136 |" in raw:
        print(u"  [幂等] 档案已有 ZF136 变更行")
    else:
        row = read(os.path.join(HERE, "_zf136_row.txt")).strip()
        lines = raw.split(u"\n")
        idx = None
        for i, ln in enumerate(lines):
            if ln.startswith(u"| ZF135 |"):
                idx = i
        if idx is None:
            for i, ln in enumerate(lines):
                if ln.startswith(u"| ZF"):
                    idx = i
        if idx is None:
            print(u"  !! 找不到变更表，停手")
            return 1
        lines.insert(idx + 1, row)
        write(ARCH, u"\n".join(lines))
        print(u"  [OK] 变更表已插入 ZF136 行")

    back = read(ARCH)
    ok = u"| ZF136 |" in back and u"## ZF136（0.11）" in read(LIST)
    print(u"  %s 回读：ZF136 行 / 清单小节 都在" % (u"[OK]" if ok else u"[!!]"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
