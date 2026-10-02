# -*- coding: utf-8 -*-
u"""_zf176_lang.py —— ZF176：把 tooltip 改成"按面分工"那套说明（**只改值**，键不动）。

用户反馈「还是不可以 要不然试试样本只能通过泵输入呢」⇒ 本轮让**上/下面 = 样板罐**、
**侧面 = 原料罐**，并把这条写进 tooltip（不然玩家猜不到）。

跑法：python build\\zftools\\_zf176_lang.py [--write]
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
KEY = u"tooltip.potato_s_t.fluid_converter"
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]

V = {
    u"zh_cn": u"把输入罐里的流体按同名 c: 标签 1:1 转成输出罐里那一种。两罐各 5000 mB，50 mB/t、"
              u"30 FE/t，储能 2000 FE。\\n**管道：接上/下面 = 灌样板（输出罐）；接四个侧面 = 灌原料"
              u"（输入罐）；抽出来的永远是产物。**\\n手倒：普通右键 = 原料，潜行右键 = 样板；"
              u"空容器右键 = 把罐里的装走。空手潜行右键 = 逐条诊断。",
    u"en_us": u"Converts the input tank's fluid 1:1 into the fluid in the output tank when the two "
              u"share a c: tag. 5,000 mB per tank, 50 mB/t, 30 FE/t, 2,000 FE buffer.\\n**Pipes: the top "
              u"and bottom faces fill the SAMPLE (output tank); the four sides fill the INPUT tank; "
              u"draining always yields the output (product).**\\nBy hand: right-click = input, "
              u"sneak-right-click = sample, empty container right-click = take fluid out. "
              u"Sneak-right-click empty-handed = diagnosis.",
    u"ja_jp": u"入力タンクの流体を、同じ c: タグを持つ出力タンクの流体へ 1:1 で変換します。各タンク "
              u"5,000 mB、50 mB/t、30 FE/t、蓄電 2,000 FE。\\n**配管：上/下面＝見本（出力タンク）へ、"
              u"側面＝入力タンクへ。抜き出せるのは常に出力（製品）。**\\n素手：右クリック＝入力、"
              u"スニーク右クリック＝見本、空の容器で右クリック＝汲み出し。素手スニーク右クリック＝診断。",
    u"ru_ru": u"Преобразует жидкость входного бака 1:1 в жидкость выходного бака при общем теге c:. "
              u"По 5 000 mB на бак, 50 mB/т, 30 FE/т, буфер 2 000 FE.\\n**Трубы: верх/низ — образец "
              u"(выходной бак), боковые стороны — входной бак; слив всегда из выходного.**\\nРукой: "
              u"правый клик — вход, с приседом — образец, пустой контейнер — слить. Присев пустой рукой "
              u"— диагностика.",
    u"lzh": u"以輸入罐之流體，依同名 c: 標籤，一比一化為輸出罐中者。兩罐各五千毫，每秒五十毫、"
             u"每刻三十 FE，儲能二千 FE。\\n**管：上下二面注樣本（輸出罐），四側注輸入罐；所抽者恆為產物。**"
             u"\\n手注：右擊＝原料，潛行右擊＝樣本，持空器右擊＝取走。空手潛行右擊＝逐條診斷。",
}


def main(argv):
    write = u"--write" in argv
    fails, notes = [], []
    for loc in LOCALES:
        p = os.path.join(LANG, loc + u".json")
        text = io.open(p, encoding="utf-8", newline=u"").read()
        before = json.loads(text)
        if before.get(KEY) == V[loc]:
            notes.append(u"%s：（已是最新）" % loc)
            continue
        eol = u"\r\n" if u"\r\n" in text else u"\n"
        lines = text.split(eol)
        hit = 0
        for i, ln in enumerate(lines):
            if ln.strip().startswith(u'"%s":' % KEY):
                ind = ln[:len(ln) - len(ln.lstrip())]
                lines[i] = ind + u'"%s": %s,' % (KEY, json.dumps(V[loc], ensure_ascii=False))
                hit += 1
        if hit != 1:
            fails.append(u"%s：命中 %d 次" % (loc, hit))
            continue
        new_text = eol.join(lines)
        parsed = json.loads(new_text)
        if len(parsed) != len(before) or parsed[KEY] != V[loc]:
            fails.append(u"%s：写回后不一致" % loc)
            continue
        notes.append(u"%s：tooltip 改成按面说明（键数仍 %d）" % (loc, len(parsed)))
        if write:
            io.open(p, "w", encoding="utf-8", newline=u"").write(new_text)
    print(u"模式：%s" % (u"落盘" if write else u"干跑（不写）"))
    for n in notes:
        print(u"  " + n)
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
