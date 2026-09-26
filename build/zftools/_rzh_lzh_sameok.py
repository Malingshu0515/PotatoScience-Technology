# -*- coding: utf-8 -*-
r"""_rzh_lzh_sameok.py —— 白名单辅助：把"与中文逐字相同"的条目按**逐字同形**分类。

白名单的规矩是"条目里每一个字，在繁体里都写作同一个字形"。这句话可以机械判定：
维护一张**简繁异形字**对照表，凡是条目里出现表内字的，就说明它**有字可改**
⇒ 是真漏译，不许进白名单；一个字都不沾的，才是"无字可改"。

⚠ 表里**只收字形确实不同的字**。第一版把「面 / 器 / 只 / 言 / 能 / 量 / 速 / 率 /
   流 / 粉 / 碎 / 分 / 解 / 原 / 油 / 柴 / 汽 / 硝 / 硫 / 碳 / 酸 / 空 / 桶 / 罐 /
   正 / 在 / 每 / 水 / 化 / 信 / 号」这类**简繁同形**的字也收进去了，于是把纯粹的
   简繁同形条目判成"有字可改"。这次逐个字形对过，删掉全部同形字。

用法：`python build/zftools/_rzh_lzh_sameok.py <译稿序号>`
结论写 `_rzh_lzh_sameok.txt`。
"""
from __future__ import print_function
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, u"_rzh_lzh_sameok.txt")

# 简体 -> 繁体；**只列字形不同的**。
S2T = {
    u"钛": u"鈦", u"钨": u"鎢", u"铀": u"鈾", u"铝": u"鋁", u"钴": u"鈷",
    u"镍": u"鎳", u"锰": u"錳", u"锂": u"鋰", u"硅": u"矽", u"矿": u"礦",
    u"锭": u"錠", u"铁": u"鐵", u"铜": u"銅", u"银": u"銀", u"钢": u"鋼",
    u"电": u"電", u"气": u"氣", u"机": u"機", u"门": u"門", u"开": u"開",
    u"关": u"關", u"热": u"熱", u"温": u"溫", u"层": u"層", u"数": u"數",
    u"这": u"這", u"们": u"們", u"来": u"來", u"时": u"時", u"与": u"與",
    u"并": u"並", u"产": u"產", u"于": u"於", u"过": u"過", u"进": u"進",
    u"还": u"還", u"种": u"種", u"样": u"樣", u"当": u"當", u"经": u"經",
    u"应": u"應", u"对": u"對", u"点": u"點", u"线": u"線", u"号": u"號",
    u"处": u"處", u"车": u"車", u"马": u"馬", u"鸟": u"鳥", u"鱼": u"魚",
    u"龙": u"龍", u"凤": u"鳳", u"买": u"買", u"卖": u"賣", u"读": u"讀",
    u"写": u"寫", u"说": u"說", u"话": u"話", u"语": u"語", u"体": u"體",
    u"图": u"圖", u"岛": u"島", u"长": u"長", u"单": u"單", u"发": u"發",
    u"现": u"現", u"实": u"實", u"为": u"為", u"头": u"頭", u"风": u"風",
    u"华": u"華", u"转": u"轉", u"换": u"換", u"设": u"設", u"计": u"計",
    u"认": u"認", u"让": u"讓", u"运": u"運", u"连": u"連", u"远": u"遠",
    u"边": u"邊", u"运": u"運", u"带": u"帶", u"积": u"積", u"极": u"極",
    u"构": u"構", u"树": u"樹", u"样": u"樣", u"标": u"標", u"准": u"準",
    u"确": u"確", u"认": u"認", u"记": u"記", u"试": u"試", u"验": u"驗",
    u"检": u"檢", u"测": u"測", u"际": u"際", u"陆": u"陸", u"药": u"藥",
    u"处": u"處", u"备": u"備", u"够": u"夠", u"冲": u"衝", u"决": u"決",
}


def main():
    n = sys.argv[1] if len(sys.argv) > 1 else u"2"
    a = json.load(io.open(os.path.join(HERE, u"_rzh_lzh_in%s.json" % n), encoding=u"utf-8"))
    b = json.load(io.open(os.path.join(HERE, u"_rzh_lzh_out%s.json" % n), encoding=u"utf-8"))

    clean, dirty = [], []
    for k in a:
        if k not in b or a[k] != b[k]:
            continue
        hits = sorted(set(ch for ch in b[k] if ch in S2T))
        if hits:
            dirty.append((k, u"".join(hits), u"".join(S2T[c] for c in hits)))
        else:
            clean.append((k, b[k]))

    L = [u"== 第 %s 份：与中文逐字相同且**逐字简繁同形**（可入白名单）：%d 条 ==" % (n, len(clean))]
    for k, v in clean:
        L.append(u'    u"%s",' % k)
    L.append(u"")
    L.append(u"== 含**简繁异形字**的（有字可改 ⇒ 疑似漏译，**不许**入白名单）：%d 条 ==" % len(dirty))
    for k, s, t in dirty:
        L.append(u"   %-46s 异形字 %s -> 应作 %s   | %s" % (k, s, t, b[k][:50]))
    text = u"\n".join(L)
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(text + u"\n")
    print(u"wrote %s" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
