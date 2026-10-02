# -*- coding: utf-8 -*-
"""run_checks3.py —— 跑父代理给的自检，外加字形/术语/编码的旁证。输出写 UTF-8 文件，便于原样贴回。"""
from __future__ import print_function
import io
import json
import re

HERE = r"E:\PotatoST\build\zftools"
IN = HERE + r"\_rzh_lzh_in3.json"
OUT = HERE + r"\_rzh_lzh_out3.json"
LOG = HERE + r"\_rzh_lzh_out3_check.txt"

buf = []


def p(s):
    buf.append(s)


# ---------------- 父代理给的自检（逐字照跑） ----------------
a = json.load(io.open(IN, encoding="utf-8"))
b = json.load(io.open(OUT, encoding="utf-8"))
p("keys equal: %s %d %d" % (list(a) == list(b), len(a), len(b)))
for k in a:
    pa = re.findall(r"%\d+\$s|%s|%%", a[k]); pb = re.findall(r"%\d+\$s|%s|%%", b.get(k, ""))
    if pa != pb:
        p("PLACEHOLDER %s %s %s" % (k, pa, pb))
    if a[k].count("\\n") != b.get(k, "").count("\\n"):
        p("NEWLINE %s %s %s" % (k, a[k].count("\\n"), b.get(k, "").count("\\n")))
for tok in ["FE", "mB", "tick", "秒", "§"]:
    na = sum(a[k].count(tok) for k in a); nb = sum(b.get(k, "").count(tok) for k in b)
    if na != nb:
        p("TOKEN %s %d %d" % (tok, na, nb))
p("done")

# ---------------- 旁证 1：十个成就标题照表抄 ----------------
PINNED = {
    "advancements.potato_s_t.electrolyzer.title": u"析水為二氣",
    "advancements.potato_s_t.distillation.title": u"一油分五品",
    "advancements.potato_s_t.alloy_smelter.title": u"配成一爐",
    "advancements.potato_s_t.blast_furnace.title": u"築高爐",
    "advancements.potato_s_t.starfall.title": u"召星墜地",
    "advancements.potato_s_t.salt.title": u"向海取鹽",
    "advancements.potato_s_t.star_steel.title": u"煉得星璨鋼",
    "advancements.potato_s_t.oil_pump.title": u"海底取油",
    "advancements.potato_s_t.capacitor.title": u"攢得一電容",
    "advancements.potato_s_t.sulfur.title": u"瀝青中取硫",
}
bad = [(k, b.get(k)) for k, v in PINNED.items() if b.get(k) != v]
p("P10 titles verbatim: %s%s" % (not bad, (" " + repr(bad)) if bad else ""))

# ---------------- 旁证 2：术语表（新版）表项是否照抄 ----------------
TERMS = [u"電解器", u"分餾塔控制器", u"分餾塔操作器", u"合金爐主控", u"合金爐接線口", u"合金冶煉爐",
         u"電力高爐", u"微型粉碎機", u"液壓機", u"灌裝機", u"流體泵", u"容器換流器", u"採油機",
         u"柴油發電機控制器", u"鋰電池構造間", u"鹽分解器", u"空氣分離器", u"合成氨反應室",
         u"燃燒反應室", u"酸性反應室", u"加氫脫硫反應室", u"低級發電機", u"高壓氣罐", u"油桶",
         u"終界水晶", u"獄髓", u"獄髓碎片", u"木炭", u"砂礫", u"石英", u"原木",
         u"星璨鋼", u"鈦合金", u"高碳鋼", u"熱力金屬", u"輕質", u"硬質", u"振金", u"電容",
         u"空線軸", u"線纜軸", u"銅線", u"銀線", u"接線端子", u"接線塊", u"散熱裝置", u"加熱裝置",
         u"太陽能板", u"曬鹽機", u"鋰電池", u"星儀圖之章", u"星軌墜", u"海鹽", u"碳酸鋰", u"氯化鈉",
         u"液化石油氣", u"石腦油", u"瀝青", u"原油", u"鈦", u"鎢", u"鈾", u"鋁", u"鈷", u"鎳",
         u"錳", u"鋰", u"銀", u"硫", u"碳", u"磁石", u"柏油塊"]
joined = u"\n".join(b.values())
absent = [t for t in TERMS if t not in joined]
p("glossary terms present (informational, 只列本片用到的): %s" % (u"、".join(
    t for t in TERMS if t in joined)))

# ---------------- 旁证 3：没有简体字形漏网（只列**简繁不同形**的简体字） ----------------
SIMP = (u"电钢钛铁铜银铝钴镍锰锂矿锭气机层数为与产于过还这们来时后种样当经对应点线号处"
        u"车马鸟鱼龙买卖读说语门开关热温体结构壳无个块组变质压炉沥盐硅冲复归见观头护铠击弹减伤"
        u"坚稳属图纸荧灯国连选换远满尽单叠铺毕录态阵让认记计设试众从达运边烬装备约绘罗艺间团"
        u"发类干丰苏范苹资专业务写话铜钢铁铝锌钒钨铀铅锡镍镜钱锁锅针钉钩阵陈际陆险随难雠"
        u"凤鹤鸡鹰麦黄黑齐齿龄龟")
SIMP = u"".join(sorted(set(SIMP)))
hits = []
for k, v in b.items():
    h = [ch for ch in v if ch in SIMP]
    if h:
        hits.append((k, u"".join(h)))
p("simplified leftovers: %d %s" % (len(hits), hits[:8]))

# ---------------- 旁证 4：的 / 它 / 了 ----------------
for tok in (u"的", u"它", u"了", u"们", u"这"):
    hk = [k for k, v in b.items() if tok in v]
    p("modern particle %s: %d %s" % (tok, len(hk), hk[:6]))

# ---------------- 旁证 5：编码 / 换行 / 键序 ----------------
raw = io.open(OUT, "rb").read()
p("BOM: %s · CR: %s · bytes: %d · keys: %d" % (
    raw.startswith(b"\xef\xbb\xbf"), b"\r" in raw, len(raw), len(b)))
p("key order == zh_cn on-disk order: %s" % (list(a) == list(b)))
p("identical to zh_cn (%d): %s" % (len([k for k in a if a[k] == b[k]]),
                                   [k for k in a if a[k] == b[k]]))

# ---------------- 旁证 6：与姊妹稿的键不得重叠（merge 会拒绝） ----------------
import os
for name in (u"_rzh_lzh_out1.json", u"_rzh_lzh_out2.json"):
    fp = os.path.join(HERE, name)
    if not os.path.exists(fp):
        p("sibling %s: 尚未出现" % name)
        continue
    sib = json.load(io.open(fp, encoding="utf-8"))
    p("sibling %s: %d 键 · 与本片重叠 %d %s" % (
        name, len(sib), len(set(sib) & set(b)), sorted(set(sib) & set(b))[:6]))

io.open(LOG, "w", encoding="utf-8", newline="\n").write(u"\n".join(buf) + u"\n")
print("check log written")