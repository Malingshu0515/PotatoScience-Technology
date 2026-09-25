# -*- coding: utf-8 -*-
u"""_zf75_gatefix.py —— 修 ZF75 门里 4 条"老轮次的活体断言"（三类）

① `_zf71_verify.py`：公告里的语言键数 218 → **219**（ZF75 加了 biome 名）；
   顺带把 `ore_n` 的算法打出来看（它现在报 10，而公告写 9 —— 必须搞清楚，不许糊过去）。
② `_zf72_verify.py`：**B15**（"还没有 ocean_oilfield.json"）也是规划轮快照断言，
   我上次漏在 SNAP 名单外 ⇒ 补进 `SNAP_PREFIXES`。
③ `_zf73_verify.py`：四语言键数 218 → **219**。
"""
import io
import re
import sys

Z = r"E:\PotatoST\build\zftools"
Z71 = Z + r"\_zf71_verify.py"
Z72 = Z + r"\_zf72_verify.py"
Z73 = Z + r"\_zf73_verify.py"
ANN = r"E:\PotatoST\docs\UpdateAnnouncement_EN.md"

fails = []


def patch(path, pairs, label):
    t = io.open(path, "r", encoding="utf-8").read()
    for old, new, what in pairs:
        n = t.count(old)
        if n != 1:
            fails.append(u"%s/%s 命中 %d 次" % (label, what, n))
            print(u"  !! %s / %s：命中 %d 次" % (label, what, n))
            return
        t = t.replace(old, new, 1)
        print(u"  [OK] %s / %s" % (label, what))
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t)


def main():
    # ① 公告 + ZF71 期望值：语言键 218 → 219
    t = io.open(ANN, "r", encoding="utf-8").read()
    if t.count(u"(218 keys each)") == 1:
        io.open(ANN, "w", encoding="utf-8", newline=u"\n").write(
            t.replace(u"(218 keys each)", u"(219 keys each)", 1))
        print(u"  [OK] 公告：语言键 218 → 219")
    else:
        fails.append(u"公告里的 218 keys each 命中 %d 次" % t.count(u"(218 keys each)"))
    patch(Z71, [(u'set(keys.values()) == {218} and u"218 keys each" in doc',
                 u'set(keys.values()) == {219} and u"219 keys each" in doc', u"语言键 219")],
          u"_zf71_verify")

    # ② ZF72 的 B15 也是快照断言
    patch(Z72, [(u'SNAP_PREFIXES = (u"B5 ", u"B6 ", u"B12 ", u"B13 ", u"B14 ", u"B16 ", u"D1 ")',
                 u'SNAP_PREFIXES = (u"B5 ", u"B6 ", u"B12 ", u"B13 ", u"B14 ", u"B15 ", u"B16 ", u"D1 ")',
                 u"B15 补进快照名单")], u"_zf72_verify")

    # ③ ZF73 的键数
    patch(Z73, [(u'check(u"B11 四语言各 218 键", all(v == 218 for v in counts.values()), str(counts))',
                 u'check(u"B11 四语言各 219 键（ZF75 加了 biome 名）", all(v == 219 for v in counts.values()), str(counts))',
                 u"语言键 219")], u"_zf73_verify")

    # 诊断：_zf71_verify.py 里 ore_n 是怎么算的
    src = io.open(Z71, "r", encoding="utf-8").read()
    print(u"\n--- _zf71_verify.py 里 ore_n 的来源 ---")
    for i, line in enumerate(src.split(u"\n"), 1):
        if u"ore_n" in line:
            print(u"  L%d: %s" % (i, line.strip()[:160]))
    print(u"\n失败项 = %d" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
