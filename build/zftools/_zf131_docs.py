# -*- coding: utf-8 -*-
# _zf131_docs.py —— ZF131 文档：贴图清单加一节 + 档案加变更行与 4.112 + 交接文档
#
# 正文都在独立 .md/.txt 里，本脚本只负责插入（上一轮把长文本塞进 Python 三引号字面量，
# 末尾一个反斜杠就把结束引号转义掉，连报两次 SyntaxError —— 长文本不要进源码字面量）。
import io
import os
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
    # ---------- ① 贴图清单：纯追加 ----------
    raw = read(LIST)
    sec = read(os.path.join(HERE, "_zf131_section.md"))
    if u"## ZF131（0.11）" in raw:
        print(u"  [幂等] 贴图清单已有 ZF131 小节")
    else:
        if not raw.endswith(u"\n"):
            raw += u"\n"
        write(LIST, raw + sec)
        back = read(LIST)
        print(u"  %s 贴图清单纯追加（%d -> %d 字节）"
              % (u"[OK]" if back.startswith(raw) and u"## ZF131（0.11）" in back else u"[!!]",
                 len(raw.encode()), len(back.encode())))

    # ---------- ② 档案：变更行（追加在最后一行之后）----------
    raw = read(ARCH)
    if u"| ZF131 |" in raw:
        print(u"  [幂等] 档案已有 ZF131 变更行")
    else:
        row = read(os.path.join(HERE, "_zf131_row.txt")).strip()
        lines = raw.split(u"\n")
        idx = None
        for i, ln in enumerate(lines):
            if ln.startswith(u"| ZF"):
                idx = i
        if idx is None:
            print(u"  !! 找不到变更表最后一行，停手")
            return 1
        lines.insert(idx + 1, row)
        write(ARCH, u"\n".join(lines))
        print(u"  [OK] 变更表已插入 ZF131 行（追在最后一行 %s 之后）" % lines[idx][:12])

    # ---------- ③ 档案：4.112 ----------
    raw = read(ARCH)
    if u"### 4.113 " in raw:
        print(u"  [幂等] 档案已有 4.113")
    else:
        anchor = u"### 4.111 "
        if raw.count(anchor) != 1:
            print(u"  !! 4.111 锚点 %d 次，停手" % raw.count(anchor))
            return 1
        idx = raw.index(anchor)
        write(ARCH, raw[:idx] + read(os.path.join(HERE, "_zf131_pitfall.md")) + raw[idx:])
        print(u"  [OK] 已插入 4.113（在 4.111 之前）")

    # ---------- ④ 交接文档：活体数字段补一句 ----------
    raw = read(HAND)
    needle = u"⚠ **谁改这个数，记得这三处 + 清单表头一共四处一起动。**"
    if needle in raw and u"ZF131" not in raw:
        add = (needle + u"\n>\n"
               u"> **ZF131（2026-09-26 13:3x，素材线）**：给**大型柴油发电机**加了工作循环音"
               u"（用户给的音频）。**这个数没动**（13 → 13，音效与\"借原版贴图\"无关），"
               u"但 `SoundCheck.py` 的音效事件从 **8 → 9**；`ModSounds` / `sounds.json` / "
               u"`sounds/` 三处同步。\n")
        write(HAND, raw.replace(needle, add, 1))
        print(u"  [OK] 交接文档活体段已补 ZF131 说明")
    else:
        print(u"  [幂等/跳过] 交接文档")

    back = read(ARCH)
    ok = (u"| ZF131 |" in back and u"### 4.113 " in back and u"### 4.111 " in back
          and u"## ZF131（0.11）" in read(LIST))
    print(u"  %s 回读：ZF131 行 / 4.113 / 4.111 / 清单小节 都在" % (u"[OK]" if ok else u"[!!]"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
