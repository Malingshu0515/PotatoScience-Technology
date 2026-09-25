# -*- coding: utf-8 -*-
u"""_zf79_verifypatch.py —— 把往轮校验与公告跟到 ZF79 的内容

① `_zf71_verify.py`：液压机配方数 **7 → 8**（原断言写死 `out.add(new Recipe(` 出现 7 次，
   现在多了"12 沥青 → 柏油块"），标签也改准（8 条里 7 条是锭→板、1 条是沥青→柏油块）。
② 公告 §3 那行：液压机一行补上沥青→柏油块。
③ 语言键数 **246 → 248**（`_zf78_verify.py` / `_zf73_verify.py` B11 / `_zf75_verify.py` C2 /
   `_zf71_verify.py` + 公告那行 "(246 keys each)"）。

每条替换断言正好命中 1 次。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
fails = []


def patch(path, old, new, label):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, hits))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def main():
    print(u"== ① _zf71_verify：液压机配方数 ==")
    patch(os.path.join(TOOLS, "_zf71_verify.py"),
          u'''    check(len(re.findall(r"out\\.add\\(new Recipe\\(", press)) == 7,
          u"液压机接受 7 种锭（公告列了 copper/iron/nickel/cobalt/silver/aluminum/steel = %d 种）"
          % len(re.findall(r"out\\.add\\(new Recipe\\(", press)))''',
          u'''    # 0.11 ZF79：多了一条"12 沥青 → 柏油块" ⇒ 8 条（7 条锭→板 + 1 条沥青→柏油块）
    check(len(re.findall(r"out\\.add\\(new Recipe\\(", press)) == 8,
          u"液压机 8 条配方（7 锭→板 + 1 沥青→柏油块），实际 %d 条"
          % len(re.findall(r"out\\.add\\(new Recipe\\(", press)))''',
          u"_zf71 液压机配方数 7 → 8")

    print(u"== ② 公告：液压机那行 ==")
    patch(ANN,
          u"| **Hydraulic Press** | Presses ingots into plates: copper, iron, nickel, cobalt, silver, "
          u"aluminum, steel. | 400 FE/t × 3 s = **24,000 FE per plate**; buffer is exactly one plate |",
          u"| **Hydraulic Press** | Presses ingots into plates: copper, iron, nickel, cobalt, silver, "
          u"aluminum, steel. **12 Bitumen → 1 Asphalt Block** (decorative). | 400 FE/t × 3 s = "
          u"**24,000 FE per plate**; buffer is exactly one plate |",
          u"公告：液压机一行补沥青→柏油块")

    print(u"== ③ 语言键数 246 → 248 ==")
    patch(os.path.join(TOOLS, "_zf78_verify.py"),
          u'check(u"四份语言键数一致且 = 246（219 + 22 + 5）",\n          len(set(counts.values())) == 1 and list(counts.values())[0] == 246)',
          u'check(u"四份语言键数一致且 = 248（219 + 22 + 5 + 2）",\n          len(set(counts.values())) == 1 and list(counts.values())[0] == 248)',
          u"_zf78 键数 → 248")
    patch(os.path.join(TOOLS, "_zf73_verify.py"),
          u'check(u"B11 四语言各 246 键（ZF75 加 biome 名 + ZF78 加 27 键）", all(v == 246 for v in counts.values()), str(counts))',
          u'check(u"B11 四语言各 248 键（ZF75 biome 名 + ZF78 27 键 + ZF79 2 键）", all(v == 248 for v in counts.values()), str(counts))',
          u"_zf73 B11 → 248")
    patch(os.path.join(TOOLS, "_zf75_verify.py"),
          u'check(u"C2 四语言各 246 键（ZF78 起）", all(v == 246 for v in counts.values()), str(counts))',
          u'check(u"C2 四语言各 248 键（ZF79 起）", all(v == 248 for v in counts.values()), str(counts))',
          u"_zf75 C2 → 248")
    patch(os.path.join(TOOLS, "_zf71_verify.py"),
          u'    check(len(keys) == 4 and set(keys.values()) == {246} and u"246 keys each" in doc,',
          u'    check(len(keys) == 4 and set(keys.values()) == {248} and u"248 keys each" in doc,',
          u"_zf71 键数 → 248")
    patch(ANN, u"(246 keys each)", u"(248 keys each)", u"公告 → 248 键")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
