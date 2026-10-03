# -*- coding: utf-8 -*-
r"""_rzh_guide_verify.py —— 手册去 AI 味的收口验证（五语）。

判据分四组，全部按 key 作用域：

  G1 键数 / 键集合：五份对齐（lzh 多 language.name / language.region）
  G2 风格：按语言各自的禁词表扫 69 条 guide 键 + 31 条配置键
       （感叹号 / 破折号 / 省略号 / 废话词 / 口语 / 抒情）
  G3 结构：`$(br2)` 数与中文逐键相同；占位符与中文一致；无 BOM/CR；无空值/首尾空白
  G4 机制事实：**手册改写最容易删坏的就是数字**。下面钉一批"手册里必须还在"的事实，
       按语言给出各自写法（中文语序换到四语会变，不能照抄中文串）
  G5 数字对账：逐键把中文里的数字组归一化后与译文比，**缺失过半**才算失败（不到即提示）

用法：`python build/zftools/_rzh_guide_verify.py`
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(HERE, u"_rzh_guide_verify.txt")
LOCS = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]

from _rzh_guide_merge import BANNED, nums                   # noqa: E402
import _rzh_guide_zh as GZ                                   # noqa: E402

PH = re.compile(u"%\\d+\\$s|%s|%%")

G = u"potato_s_t.guide."
M = u"potato_s_t.guide.entry.materials."
P = u"potato_s_t.guide.entry.power."
O = u"potato_s_t.guide.entry.oil."
S = u"potato_s_t.guide.entry.starfall."
C = u"potato_s_t.guide.entry.getting_started."
F = u"potato_s_t.guide.entry.faq."

# ---------------------------------------------------------------------------
# G4：手册里必须还在的机制事实（语言 -> [(key, 片段, 说明)]）
# ---------------------------------------------------------------------------
FACTS = []
def add(key, why, **per):
    for loc, needle in per.items():
        FACTS.append((loc, key, needle, why))

add(C + u"first_line.p1", u"沥青一次 12 个",
    zh_cn=u"12 个", en_us=u"12", ja_jp=u"12", ru_ru=u"12", lzh=u"12")
add(M + u"blast_alloy.p1", u"电力高炉 3×3×3 / 12 输入 / 32 输出 / 10 秒 / 800 FE",
    zh_cn=u"3×3×3", en_us=u"3x3x3", ja_jp=u"3×3×3", ru_ru=u"3×3×3", lzh=u"3×3×3")
add(M + u"blast_alloy.p1", u"12 输入槽",
    zh_cn=u"12 个输入槽", en_us=u"12 input slots", ja_jp=u"12 スロット", ru_ru=u"12 входных слотов",
    lzh=u"12 入槽")
add(M + u"blast_alloy.p1", u"32 输出槽",
    zh_cn=u"32 个输出槽", en_us=u"32 output slots", ja_jp=u"出力 32", ru_ru=u"32 выходных слота",
    lzh=u"32 出槽")
add(M + u"blast_alloy.p1", u"每槽 10 秒 / 每件 800 FE",
    zh_cn=u"800 FE", en_us=u"800 FE", ja_jp=u"800 FE", ru_ru=u"800 FE", lzh=u"800 FE")
add(M + u"blast_alloy.p2", u"合金炉 4 层 58 格 / 储能 32768 FE",
    zh_cn=u"58 格", en_us=u"58", ja_jp=u"58", ru_ru=u"58", lzh=u"58")
add(M + u"blast_alloy.p2", u"32768 FE",
    zh_cn=u"32768 FE", en_us=u"32768 FE", ja_jp=u"32768 FE", ru_ru=u"32768 FE", lzh=u"32768 FE")
add(M + u"salt.p1", u"晒盐机 Y 0~64 / 120 秒 / 20 秒",
    zh_cn=u"120 秒", en_us=u"120 seconds", ja_jp=u"120 秒", ru_ru=u"120 секунд", lzh=u"120 秒")
add(M + u"salt.p2", u"盐分解器 64 个 / 40 秒 / 六成 / 5% / 500 mB",
    zh_cn=u"5%", en_us=u"5%", ja_jp=u"5%", ru_ru=u"5%", lzh=u"5%")
add(M + u"salt.p2", u"每 500 mB 水多耗 1 个海盐",
    zh_cn=u"500 mB", en_us=u"500 mB", ja_jp=u"500 mB", ru_ru=u"500 mB", lzh=u"500 mB")
add(P + u"wiring.p1", u"端子远程输电",
    zh_cn=u"接线端子", en_us=u"Terminal", ja_jp=u"端子", ru_ru=u"клемм", lzh=u"接線端子")
add(P + u"wiring.p2", u"铜线 2048 / 银线 16134 FE/t、16 格、32 点耐久",
    zh_cn=u"16134 FE/t", en_us=u"16134 FE/t", ja_jp=u"16134 FE/t", ru_ru=u"16134 FE/t", lzh=u"16134 FE/t")
add(P + u"wiring.p2", u"2048 FE/t",
    zh_cn=u"2048 FE/t", en_us=u"2048 FE/t", ja_jp=u"2048 FE/t", ru_ru=u"2048 FE/t", lzh=u"2048 FE/t")
add(P + u"generation.p2", u"太阳能板白天 / 六成 / 两成",
    zh_cn=u"六成", en_us=u"60%", ja_jp=u"六割", ru_ru=u"60%", lzh=u"六成")
add(P + u"generation.p3", u"每点动力 2 FE/t",
    zh_cn=u"2 FE/t", en_us=u"2 FE/t", ja_jp=u"2 FE/t", ru_ru=u"2 FE/t", lzh=u"2 FE/t")
add(P + u"storage.p1", u"锂电池 4M FE / 层数 6/12/32 / 六种底面",
    zh_cn=u"4M FE", en_us=u"4M FE", ja_jp=u"4M FE", ru_ru=u"4M FE", lzh=u"4M FE")
add(P + u"storage.p1", u"最高 32 层",
    zh_cn=u"32 层", en_us=u"32 layers", ja_jp=u"32", ru_ru=u"32", lzh=u"32 層")
add(P + u"storage.p2", u"构造间 30 秒一件",
    zh_cn=u"30 秒", en_us=u"30 seconds", ja_jp=u"30 秒", ru_ru=u"30 секунд", lzh=u"30 秒")
add(P + u"fluids.p1", u"灌装机 5000 mB / 5 mB/t / 60 FE/t",
    zh_cn=u"60 FE/t", en_us=u"60 FE/t", ja_jp=u"60 FE/t", ru_ru=u"60 FE/t", lzh=u"60 FE/t")
add(P + u"fluids.p3", u"流体泵 0% 到 800%",
    zh_cn=u"800%", en_us=u"800%", ja_jp=u"800%", ru_ru=u"800%", lzh=u"800%")
add(O + u"crude.p2", u"采油机 8n²+80n / 10n mB/s / 25 桶",
    zh_cn=u"8n²", en_us=u"8n²", ja_jp=u"8n²", ru_ru=u"8n²", lzh=u"8n²")
add(O + u"crude.p2", u"10n mB/s",
    zh_cn=u"10n mB/s", en_us=u"10n mB/s", ja_jp=u"10n mB/s", ru_ru=u"10n mB/s", lzh=u"10n mB/s")
add(O + u"distillation.p2", u"每座塔 12 桶 / 每种产品 2.5 桶",
    zh_cn=u"2.5 桶", en_us=u"2.5", ja_jp=u"2.5", ru_ru=u"2,5", lzh=u"2.5")
add(O + u"chemistry.p1", u"燃烧反应室 800 / 1200 / 1000 动力",
    zh_cn=u"1200", en_us=u"1200", ja_jp=u"1200", ru_ru=u"1200", lzh=u"1200")
add(O + u"chemistry.p2", u"空气分离器 200 FE/t",
    zh_cn=u"200 FE", en_us=u"200 FE", ja_jp=u"200 FE", ru_ru=u"200 FE", lzh=u"200 FE")
add(O + u"chemistry.p3", u"加氢脱硫 16 沥青 / 1000 mB 氢气 / 酸性反应室 500 FE/t",
    zh_cn=u"500 FE", en_us=u"500 FE", ja_jp=u"500 FE", ru_ru=u"500 FE", lzh=u"500 FE")
add(O + u"diesel_gen.p1", u"柴油机 3×5×2 / 30 格",
    zh_cn=u"30 格", en_us=u"30 cells", ja_jp=u"30", ru_ru=u"30", lzh=u"30 格")
add(O + u"diesel_gen.p2", u"8000 mB 柴油罐 / 7200 FE",
    zh_cn=u"7200 FE", en_us=u"7200 FE", ja_jp=u"7200 FE", ru_ru=u"7200 FE", lzh=u"7200 FE")
add(S + u"sky_and_star.p2", u"星轨坠 30 秒 / y=200 / 前 10 秒 / 7~20 威力",
    zh_cn=u"200", en_us=u"200", ja_jp=u"200", ru_ru=u"200", lzh=u"200")
add(S + u"sky_and_star.p2", u"15 以上加 3 个粗振金",
    zh_cn=u"3 个", en_us=u"3", ja_jp=u"3", ru_ru=u"3", lzh=u"3")
add(S + u"star_steel.p1", u"星璨钢 20×20",
    zh_cn=u"20×20", en_us=u"20x20", ja_jp=u"20×20", ru_ru=u"20×20", lzh=u"20×20")
add(S + u"star_steel.p2", u"剑气 100 耐久 / 8 格 / 12 点 / 5 秒 / 斧 6 格宽",
    zh_cn=u"12 点", en_us=u"12", ja_jp=u"12", ru_ru=u"12", lzh=u"12")


def read(loc):
    p = os.path.join(LANGDIR, loc + u".json")
    raw = io.open(p, u"rb").read()
    return p, raw, json.loads(raw.decode(u"utf-8"))


def main():
    data, raws = {}, {}
    for loc in LOCS:
        p, raw, d = read(loc)
        data[loc], raws[loc] = d, (p, raw)
    zh = data[u"zh_cn"]
    bad = 0
    L = []

    L.append(u"===== G1 键数 / 键集合 =====")
    for loc in LOCS:
        L.append(u"  %-6s keys=%d" % (loc, len(data[loc])))
    base = set(zh)
    for loc in (u"en_us", u"ja_jp", u"ru_ru"):
        if base != set(data[loc]):
            bad += 1
            L.append(u"  [错] %s 键集合不一致" % loc)
    extra = set(data[u"lzh"]) - base
    if extra != {u"language.name", u"language.region"}:
        bad += 1
        L.append(u"  [错] lzh 多出的键异常：%s" % sorted(extra))
    else:
        L.append(u"  OK   键集合对齐（lzh 只多语言元数据）")

    guide_keys = sorted(k for k in zh if k.startswith(u"potato_s_t.guide"))
    cfg_keys = sorted(k for k in zh if k.startswith(u"potato_s_t.configuration"))

    L.append(u"")
    L.append(u"===== G2 风格禁词（%d guide + %d 配置）=====" % (len(guide_keys), len(cfg_keys)))
    for loc in LOCS:
        hits = []
        for k in guide_keys + cfg_keys:
            v = data[loc].get(k, u"")
            for rule, needles in BANNED.get(loc, []):
                h = [n for n in needles if n in v]
                if h:
                    hits.append((rule, k, h))
        if hits:
            bad += 1
            L.append(u"  [错] %s：%d 处" % (loc, len(hits)))
            for rule, k, h in hits[:14]:
                L.append(u"       %s %s %s" % (rule, k, u",".join(h)))
        else:
            L.append(u"  OK   %s 无禁词" % loc)

    L.append(u"")
    L.append(u"===== G3 结构（$(br2) / 占位符 / BOM / CR）=====")
    for loc in LOCS:
        p, raw = raws[loc]
        probs = []
        if raw.startswith(b"\xef\xbb\xbf"):
            probs.append(u"BOM")
        if b"\r" in raw:
            probs.append(u"CR")
        for k in guide_keys:
            a, b = data[loc].get(k, u""), zh.get(k, u"")
            if a.count(u"$(br2)") != b.count(u"$(br2)"):
                probs.append(u"$(br2) %s: %d != %d" % (k, a.count(u"$(br2)"), b.count(u"$(br2)")))
            if sorted(PH.findall(a)) != sorted(PH.findall(b)):
                probs.append(u"占位符 %s" % k)
            if a.strip() == u"" and b.strip() != u"":
                probs.append(u"空值 %s" % k)
            if a != a.rstrip():
                probs.append(u"行尾空白 %s" % k)
        if probs:
            bad += 1
            L.append(u"  [错] %s：%d 处" % (loc, len(probs)))
            for s in probs[:10]:
                L.append(u"       %s" % s)
        else:
            L.append(u"  OK   %s 结构一致" % loc)

    L.append(u"")
    L.append(u"===== G4 手册机制事实（%d 项）=====" % len(FACTS))
    n = 0
    for loc, key, needle, why in FACTS:
        v = data[loc].get(key, u"")
        if needle not in v:
            bad += 1
            L.append(u"  [错] %s / %s 缺「%s」（%s）" % (loc, key.split(u".")[-2:], needle, why))
        else:
            n += 1
    L.append(u"  %s（%d / %d）" % (u"OK   全部在" if n == len(FACTS) else u"有缺失",
                                  n, len(FACTS)))

    L.append(u"")
    L.append(u"===== G5 数字对账（缺失过半才判错）=====")
    soft = 0
    for loc in (u"en_us", u"ja_jp", u"ru_ru", u"lzh"):
        for k in guide_keys + cfg_keys:
            src, v = zh.get(k, u""), data[loc].get(k, u"")
            ss = nums(src)
            if not ss:
                continue
            miss = [x for x in ss if x not in nums(v)]
            if miss and len(miss) > max(1, len(ss) // 2):
                bad += 1
                L.append(u"  [错] %s / %s 缺 %s" % (loc, k, miss[:8]))
            elif miss:
                soft += 1
                L.append(u"  [提示] %s / %s 少 %s" % (loc, k, miss[:6]))
    L.append(u"  提示 %d 条（不到半数，多为千分位写法差异）" % soft)

    L.append(u"")
    L.append(u"===== 结论 =====")
    L.append(u"  全部通过" if bad == 0 else u"  有 %d 处问题" % bad)
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
    print(u"bad=%d facts=%d/%d -> %s" % (bad, n, len(FACTS), OUT))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
