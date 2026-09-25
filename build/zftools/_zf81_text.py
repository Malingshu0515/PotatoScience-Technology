# -*- coding: utf-8 -*-
u"""_zf81_text.py —— ZF81 的文案/文档/活体校验：把散落各处的「100 FE」一次改完

为什么写脚本而不是手改：上一轮（ZF80）就是"改一处跑一遍门"，白跑了一整遍门。
这次先把**活体数字**（会跟着代码走、且有校验在盯的）一次扫全：
  · 四份 lang 的电解器 tooltip（zh/ja/ru 各 2 处、en 1 处）
  · 英文公告电解器那一行（`_zf71_verify.py` 会活体核对这串字面量）
  · `_zf71_verify.py` 自己的两条期望（常量 = 100、tooltip 含 100 FE）
  · `MachineRecipes.java` 的 javadoc
每处都断言锚点命中次数，改完立刻回读核对。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
ZF71 = os.path.join(ROOT, "build", "zftools", "_zf71_verify.py")
RECIPES = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", "MachineRecipes.java")

fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def patch(path, old, new, label, expect=1):
    t = read(path)
    hits = t.count(old)
    if hits != expect:
        fails.append(u"%s：锚点命中 %d 次（期望 %d）" % (label, hits, expect))
        return
    write(path, t.replace(old, new, expect))
    print(u"  [OK]   %s（%d 处）" % (label, hits))


def patch_tooltip(lang, expect):
    u"""只改电解器 tooltip 那一行里的 100 FE（别的行一个字节不动）。"""
    p = os.path.join(LANG, lang + u".json")
    t = read(p)
    out = []
    n = 0
    for line in t.split(u"\n"):
        if u"tooltip.potato_s_t.electrolyzer" in line:
            n = line.count(u"100 FE")
            line = line.replace(u"100 FE", u"1000 FE")
        out.append(line)
    if n != expect:
        fails.append(u"%s：tooltip 里 100 FE 命中 %d 处（期望 %d）" % (lang, n, expect))
        return
    write(p, u"\n".join(out))
    print(u"  [OK]   %s tooltip：100 FE → 1000 FE（%d 处）" % (lang, n))


def main():
    print(u"== ① 四份 lang ==")
    for lang, expect in [(u"zh_cn", 2), (u"en_us", 1), (u"ja_jp", 2), (u"ru_ru", 2)]:
        patch_tooltip(lang, expect)

    print(u"== ② 英文公告 ==")
    patch(ANN, u"100 FE/t + 10 mB water/t", u"1,000 FE/t + 10 mB water/t",
          u"公告电解器行：100 → 1,000 FE/t")

    print(u"== ③ 活体校验 _zf71_verify.py ==")
    patch(ZF71, u'check(u"100 FE/t + 10 mB water/t" in doc '
                u'and re.search(r"ENERGY_PER_TICK_OXYGEN\\s*=\\s*100", el) is not None,\n'
                u'          u"电解器：100 FE/t（ENERGY_PER_TICK_OXYGEN = 100）")',
          u'check(u"1,000 FE/t + 10 mB water/t" in doc '
          u'and re.search(r"ENERGY_PER_TICK_OXYGEN\\s*=\\s*1000", el) is not None,\n'
          u'          u"电解器：1000 FE/t（ENERGY_PER_TICK_OXYGEN = 1000，ZF81 抬的）")',
          u"ZF71：电解器能耗期望 100 → 1000")
    patch(ZF71, u'(u"tooltip.potato_s_t.electrolyzer", [u"100 FE", u"10 mB water"',
          u'(u"tooltip.potato_s_t.electrolyzer", [u"1000 FE", u"10 mB water"',
          u"ZF71：tooltip 字面量 100 FE → 1000 FE")

    print(u"== ④ MachineRecipes javadoc ==")
    patch(RECIPES, u"水 10 mB/t → 氧气 3 + 氢气 6，100 FE/t。",
          u"水 10 mB/t → 氧气 3 + 氢气 6，1000 FE/t。", u"JEI 说明注释（氧）")
    patch(RECIPES, u"海盐（每 500 mB 水耗 1 个）→ 氯气 3 + 氢气 6，100 FE/t。",
          u"海盐（每 500 mB 水耗 1 个）→ 氯气 3 + 氢气 6，1000 FE/t。", u"JEI 说明注释（氯）")

    print(u"\n== 回读核对 ==")
    leftovers = []
    for lang in [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]:
        for line in read(os.path.join(LANG, lang + u".json")).split(u"\n"):
            if u"tooltip.potato_s_t.electrolyzer" in line and u"100 FE" in line:
                leftovers.append(lang)
    if leftovers:
        fails.append(u"还有语言文件留着 100 FE：%s" % leftovers)
    if u"100 FE/t + 10 mB water/t" in read(ANN):
        fails.append(u"公告里还留着 100 FE/t")
    print(u"四份 lang + 公告已无 100 FE 残留：%s" % (u"是 ✓" if not leftovers else u"否"))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
