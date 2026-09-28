# -*- coding: utf-8 -*-
u"""_zf155_retarget.py —— ZF155 活体数字跟平：**语言键数 587 → 594、lzh 589 → 596**。

为什么必须动别人写的门：全工程有 ~25 道常驻门把"四语言键数"**写死**（历史沿革：
448→454→464→476→478→482→483→487→492→508→579→583→**587**→**594**）。
本轮通用升级模板加了 **7 个键 × 5 份**，所以那批门必须一起跟到 594（lzh 596）——
这是 ZF150/ZF153 都做过的同一件事（`_zf150_retarget.py` / `_zf153_retarget.py`）。

口径（**只动钥匙数的写法，不碰任何别的数字**）：
  · 只改"这一行里既有旧数、又看得出是钥匙数"的行（含 `键` / `KEYS` / `KEY_NEW` / `KEY_OLD` /
    `EXPECT_KEYS` / `keys each` / `locale` / `LANG` 这些标记）；
  · `592`（`_zf120` 的胸甲耐久）、`74/82/89`（配方份数，另算）、哈希串里的数字**一律不碰**；
  · 历史叙述（`508 → 579` 这种链、老公告条目里的 579/587）**保持原样**（§4.159）；
  · 改完逐行打印，`--write` 才落盘。

跑法：python build\\zftools\\_zf155_retarget.py [--write]
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

OLD4, NEW4 = u"587", u"594"
OLD5, NEW5 = u"589", u"596"

# 这些行虽然带旧数，但属于**历史叙述**或**别的量**，一律不碰（逐条写明理由）
SKIP_LINE_MARKERS = [
    u"508 → 579",            # 档案里的键数链（历史）
    u"Language files grew",  # 老公告条目（历史）
    u"508 to",               # 老公告条目（历史）
    u"508 each",             # 老公告条目（历史）
    u"579 keys each",        # 老公告条目（历史）
    u"literary",             # 老公告条目里的 lzh 历史数
    u"Literary",             # 同上
    u"NETHERITE_DURABILITY",  # _zf120 的耐久数（另一个量）
    u"482 →",
]

KEY_MARKERS = [u"键", u"KEYS", u"KEY_NEW", u"KEY_OLD", u"EXPECT_KEYS", u"keys each",
               u"locale", u"LANG", u"KEY_", u"table", u"want = {"]

TARGETS = sorted(f for f in os.listdir(ZT)
                 if re.match(r"^_zf\d+_(verify|guard|repro|audit|langaudit|tabaudit|recipe_guard|jar)\.py$",
                             f) and f != u"_zf155_verify.py")

changes, touched, skipped_lines = [], [], []


def retarget_line(line):
    """返回 (新行, 说明) —— 不动就返回 (原行, None)。"""
    if OLD4 not in line and OLD5 not in line:
        return line, None
    for s in SKIP_LINE_MARKERS:
        if s in line:
            return line, u"跳过（%s）" % s
    if not any(k in line for k in KEY_MARKERS):
        return line, u"跳过（看不出是钥匙数）"
    # 只替换**独立的**四位数字，别咬到哈希/长串里的片段
    new = re.sub(r"(?<![0-9a-fA-F])" + OLD4 + r"(?![0-9a-fA-F])", NEW4, line)
    new = re.sub(r"(?<![0-9a-fA-F])" + OLD5 + r"(?![0-9a-fA-F])", NEW5, new)
    if new == line:
        return line, u"跳过（数字被哈希包着）"
    return new, u"改"


def main(argv):
    write = u"--write" in argv
    for fn in TARGETS:
        p = os.path.join(ZT, fn)
        text = io.open(p, encoding="utf-8", errors="replace").read()
        lines = text.split(u"\n")
        out, local = [], []
        for i, l in enumerate(lines):
            nl, note = retarget_line(l)
            if note == u"改":
                local.append((i + 1, l.strip()[:120], nl.strip()[:120]))
            elif note and note != u"跳过（看不出是钥匙数）":
                skipped_lines.append((fn, i + 1, note, l.strip()[:90]))
            out.append(nl)
        if local:
            touched.append(fn)
            changes.extend([(fn,) + c for c in local])
            if write:
                io.open(p, u"w", encoding="utf-8", newline=u"").write(u"\n".join(out))

    # 英文公告：**常驻那条**（四语言 bullet）跟到 594；老条目一律不动（§4.159）
    ann = io.open(ANN, encoding="utf-8", newline=u"").read()
    ann2 = ann
    live = u"(587 keys each)"
    if live in ann2:
        ann2 = ann2.replace(live, u"(594 keys each)", 1)
        changes.append((u"UpdateAnnouncement_EN.md", 0, live, u"(594 keys each)"))
        if write:
            io.open(ANN, u"w", encoding="utf-8", newline=u"").write(ann2)

    print(u"================ ZF155 活体数字跟平（587→594 / 589→596） ================")
    for fn, ln, old, new in changes:
        print(u"  %-26s %4s | %s" % (fn, ln if ln else u"-", old))
        print(u"  %-26s %4s → %s" % (u"", u"", new))
    print(u"\n改动 %d 处，涉及 %d 份文件" % (len(changes), len(set([c[0] for c in changes]))))
    if skipped_lines:
        print(u"\n刻意跳过的行（历史叙述 / 别的量）：")
        for fn, ln, note, text in skipped_lines:
            print(u"  %-26s %4d %s | %s" % (fn, ln, note, text))
    print(u"\n%s" % (u"已落盘" if write else u"（没加 --write，只算不写）"))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
