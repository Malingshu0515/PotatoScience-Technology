# -*- coding: utf-8 -*-
r"""_rzh_guide_lint.py —— 按用户给的口径给手册正文做风格体检（五语）。

用户口径：「不要用感叹号、破折号、括号解释和口语化备注。不要用"可以""能够"这类废话词。
句子要短，主谓宾清晰。不要输出"这是……的证明""那副躯体从不索取"这类抒情句。」

每条判据都**按语言**给字符串，不做机器翻译式猜测。

用法：`python build/zftools/_rzh_guide_lint.py [loc ...]`（默认五语全查）
"""
from __future__ import print_function
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(HERE, u"_rzh_guide_lint.txt")

# 每种语言一组"禁用的味道标记"
RULES = {
    u"zh_cn": [
        (u"感叹号", [u"！", u"!"]),
        (u"破折号", [u"——", u"—", u"–", u"──"]),
        (u"省略号", [u"……", u"..."]),
        (u"废话词", [u"可以", u"能够", u"就能", u"即可", u"就能把", u"好得多", u"毕竟"]),
        (u"口语备注", [u"别嫌", u"手滑", u"没事", u"不要紧", u"就行", u"吧", u"呢", u"啊", u"啦",
                       u"算了", u"想想", u"指望", u"省事"]),
        (u"抒情", [u"浪漫", u"地基因", u"才算", u"无所遁形"]),
    ],
    u"en_us": [
        (u"感叹号", [u"!"]),
        (u"破折号", [u" - ", u"—", u"–"]),
        (u"省略号", [u"..."]),
        (u"废话词", [u" you can ", u" can be ", u" able to ", u" just ", u" merely "]),
        (u"口语备注", [u"don't ", u"doesn't ", u"won't ", u"y'know", u"okay", u"fine.",
                       u"feel free", u"by the way", u"honestly"]),
        (u"抒情", [u"romance", u"truly", u"genuinely", u"the proof"]),
    ],
    u"ja_jp": [
        (u"感叹号", [u"！", u"!"]),
        (u"破折号", [u"——", u"—", u"–"]),
        (u"省略号", [u"……", u"..."]),
        (u"废话词", [u"できます", u"ことができ", u"ましょう", u"すれば"]),
        (u"口语备注", [u"してください", u"ですね", u"でしょう", u"ましょう", u"ください"]),
        (u"抒情", [u"ロマン", u"こそ"]),
    ],
    u"ru_ru": [
        (u"感叹号", [u"!"]),
        (u"破折号", [u"—", u"–", u" - "]),
        (u"省略号", [u"...", u"…"]),
        (u"废话词", [u" можно ", u" можете ", u" способн"]),
        (u"口语备注", [u"просто ", u"например", u"кстати", u"ведь "]),
        # ⚠ `именно` **不禁**：它在俄文里是规范的强调词（「正是那一个」），
        #   对应中文的「它不要什么」「那正是那个配置项的作用」。归到"抒情"是口径错；
        #   本轮实测三处全是正当用法（指代前文名词），故从禁词表移除。
        (u"抒情", [u"романтик"]),
    ],
    u"lzh": [
        (u"感叹号", [u"！", u"!"]),
        (u"破折号", [u"——", u"—", u"–"]),
        (u"省略号", [u"……", u"..."]),
        # ⚠ 只禁**填充式**的「可/能」组合（即可 / 亦能 / 則可 / 可以 / 能夠），
        #   不禁「可」与「能」本身：它们在文言里是正当助动词
        #   （惟流體泵可抽 / 亦可入原版爐 / 一格不可闕 / 此皆能燒），
        #   禁掉会误报。第一版把单字也列进去，实测报了 19 处全是假阳性。
        (u"废话词", [u"即可", u"亦能", u"則可", u"可以", u"能夠", u"就能"]),
        (u"口语备注", [u"吧", u"呢", u"啊", u"啦", u"耳"]),
        (u"抒情", [u"浪漫", u"而已"]),
    ],
}


def main():
    locs = sys.argv[1:] or [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]
    L = []
    total = 0
    for loc in locs:
        d = json.load(io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8"))
        ks = sorted(k for k in d if k.startswith(u"potato_s_t.guide"))
        L.append(u"===== %s（%d 条 guide 键）=====" % (loc, len(ks)))
        hits_by_rule = {}
        for k in ks:
            v = d[k]
            for rule, needles in RULES.get(loc, []):
                hit = [n for n in needles if n in v]
                if hit:
                    hits_by_rule.setdefault(rule, []).append((k, hit, v[:90]))
        for rule, _ in RULES.get(loc, []):
            items = hits_by_rule.get(rule, [])
            if not items:
                L.append(u"  OK   %s：0 处" % rule)
                continue
            L.append(u"  [注意] %s：%d 处" % (rule, len(items)))
            total += len(items)
            for k, hit, snippet in items[:12]:
                L.append(u"        %-56s %s | %s" % (k, u",".join(hit), snippet))
        L.append(u"")

    L.append(u"合计待看 %d 处（有些是误报：例如 lzh 的「可」是正常文言助动词）" % total)
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
    print(u"flagged=%d -> %s" % (total, OUT))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
