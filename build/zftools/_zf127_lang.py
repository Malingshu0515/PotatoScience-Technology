# -*- coding: utf-8 -*-
u"""_zf127_lang.py —— ZF127 的四语言 +2 键（476 → **478**）

两个物品各一个名字（`silver_wire` / `silver_wire_spool`），四份语言**插在同一个位置**
（紧跟 `item.potato_s_t.power_cable_spool` 那行之后）⇒ 四份的键序仍然逐位相同
（`_zf109_verify.py` / `_zf112_verify.py` 都在盯键序）。

跑法：
    python build\\zftools\\_zf127_lang.py
"""
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")

ANCHOR = u"item.potato_s_t.power_cable_spool"

VALUES = {
    u"zh_cn": [(u"silver_wire", u"银线"), (u"silver_wire_spool", u"银线轴")],
    u"en_us": [(u"silver_wire", u"Silver Wire"), (u"silver_wire_spool", u"Silver Wire Spool")],
    u"ja_jp": [(u"silver_wire", u"銀線"), (u"silver_wire_spool", u"銀線のスプール")],
    u"ru_ru": [(u"silver_wire", u"Серебряный провод"),
               (u"silver_wire_spool", u"Катушка с серебряным проводом")],
}

OLD_KEYS, NEW_KEYS = 476, 478

notes, fails = [], []


def main():
    for loc, pairs in VALUES.items():
        p = os.path.join(LANG, loc + u".json")
        text = io.open(p, encoding="utf-8", newline=u"").read()
        nl = u"\r\n" if u"\r\n" in text else u"\n"
        before = json.loads(text)
        if len(before) == NEW_KEYS and all(u"item.potato_s_t." + k in before for k, _ in pairs):
            notes.append(u"%s：已经是 %d 键（幂等跳过）" % (loc, NEW_KEYS))
            continue
        if len(before) != OLD_KEYS:
            fails.append(u"%s：改前是 %d 键（预期 %d）—— 停手" % (loc, len(before), OLD_KEYS))
            continue
        pat = re.compile(u"^([ \\t]*\"%s\":.*)$" % re.escape(ANCHOR), re.M)
        hits = pat.findall(text)
        if len(hits) != 1:
            fails.append(u"%s：锚点 %s 命中 %d 次（要 1 次）" % (loc, ANCHOR, len(hits)))
            continue
        add = u"".join(nl + u"    \"item.potato_s_t.%s\":  \"%s\"," % (k, v) for k, v in pairs)
        text = text.replace(hits[0], hits[0] + add, 1)
        io.open(p, "w", encoding="utf-8", newline=u"").write(text)
        after = json.loads(io.open(p, encoding="utf-8").read())
        if len(after) != NEW_KEYS:
            fails.append(u"%s：写完是 %d 键（预期 %d）" % (loc, len(after), NEW_KEYS))
            continue
        restored = {k: v for k, v in after.items() if not k.startswith(u"item.potato_s_t.silver_wire")}
        if restored != before:
            fails.append(u"%s：除了新加的两个键，别的键被动过了" % loc)
            continue
        notes.append(u"%s：%d -> %d 键（新增 %s）" % (loc, len(before), len(after),
                                              u"、".join(after[u"item.potato_s_t." + k] for k, _ in pairs)))

    # 四份键序必须逐位相同（键序是别的门在盯的活体属性）
    seqs = {}
    for loc in VALUES:
        seqs[loc] = list(json.loads(io.open(os.path.join(LANG, loc + u".json"),
                                            encoding="utf-8").read()).keys())
    base = seqs[u"zh_cn"]
    for loc, seq in seqs.items():
        if seq != base:
            diff = [i for i, (a, b) in enumerate(zip(seq, base)) if a != b]
            fails.append(u"%s 的键序与 zh_cn 不一致（第一处不同在第 %s 位）" % (loc, diff[:1]))
    if all(seq == base for seq in seqs.values()):
        notes.append(u"四份键序逐位相同（%d 键）" % len(base))

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
