# -*- coding: utf-8 -*-
r"""_rzh_t2_terms.py —— 术语表合规体检（更新后的繁体表）。

对每一对（zh 原词 → 表中规定写法）：凡原文出现该词的键，译文必须含有规定写法；
且译文里不得残留该词的简体形。原料名（原油/柴油/碳酸…）两形同字，自动跳过。
"""
from __future__ import print_function
import io
import json

IN = r"E:\PotatoST\build\zftools\_rzh_lzh_in2.json"
OUT = r"E:\PotatoST\build\zftools\_rzh_lzh_out2.json"

PAIRS = [
    (u"钛", u"鈦"), (u"钨", u"鎢"), (u"铀", u"鈾"), (u"铝", u"鋁"), (u"钴", u"鈷"),
    (u"镍", u"鎳"), (u"锰", u"錳"), (u"银", u"銀"), (u"锂", u"鋰"),
    (u"振金", u"振金"), (u"星璨钢", u"星璨鋼"), (u"钛合金", u"鈦合金"),
    (u"高碳钢", u"高碳鋼"), (u"热力金属", u"熱力金屬"), (u"轻质", u"輕質"),
    (u"硬质", u"硬質"), (u"铁矿", u"鐵"), (u"铜", u"銅"), (u"铁", u"鐵"),
    (u"钢", u"鋼"), (u"锭", u"錠"), (u"深层钴矿石", u"深鈷礦"), (u"磁铁", u"磁石"),
    (u"柏油块", u"柏油塊"), (u"沥青", u"瀝青"), (u"石脑油", u"石腦油"),
    (u"液化石油气", u"液化石油氣"), (u"接线端子", u"接線端子"), (u"接线块", u"接線塊"),
    (u"散热装置", u"散熱裝置"), (u"加热装置", u"加熱裝置"), (u"一般金属块", u"一般金屬塊"),
    (u"耐热金属块", u"耐熱金屬塊"), (u"太阳能板", u"太陽能板"), (u"晒盐机", u"曬鹽機"),
    (u"海盐", u"海鹽"), (u"锂电池", u"鋰電池"), (u"星轨坠", u"星軌墜"),
    (u"电解器", u"電解器"), (u"分馏塔控制器", u"分餾塔控制器"),
    (u"分馏塔操作器", u"分餾塔操作器"), (u"合金炉主控", u"合金爐主控"),
    (u"合金冶炼炉", u"合金冶煉爐"), (u"电力高炉", u"電力高爐"), (u"微型粉碎机", u"微型粉碎機"),
    (u"液压机", u"液壓機"), (u"灌装机", u"灌裝機"), (u"流体泵", u"流體泵"),
    (u"容器换流器", u"容器換流器"), (u"采油机", u"採油機"),
    (u"柴油发电机控制器", u"柴油發電機控制器"), (u"低级发电机", u"低級發電機"),
    (u"动力能源捕获器", u"動力能源捕獲器"), (u"高压气罐", u"高壓氣罐"),
    (u"末影水晶", u"終界水晶"), (u"下界合金", u"獄髓"), (u"砂砾", u"砂礫"),
    (u"氧气", u"氧氣"), (u"氢气", u"氫氣"), (u"氮气", u"氮氣"), (u"氯气", u"氯氣"),
    (u"氨气", u"氨氣"), (u"盐酸", u"鹽酸"), (u"氯化钠", u"氯化鈉"), (u"碳酸锂", u"碳酸鋰"),
    (u"电解", u"電解"), (u"耗电", u"耗電"), (u"电力", u"電力"), (u"储能", u"儲能"),
    (u"储罐", u"儲罐"), (u"红石信号", u"紅石信號"), (u"停机", u"停機"),
    (u"输出槽", u"輸出槽"), (u"输入槽", u"輸入槽"), (u"层", u"層"),
    (u"坐标", u"坐標"), (u"群系", u"群系"), (u"多方块", u"多方塊"),
    (u"流体", u"流體"), (u"机器", u"機"), (u"结构", u"結構"), (u"燃料", u"燃料"),
    (u"进度", u"進度"), (u"管道", u"管道"), (u"温度", u"溫度"), (u"铜线", u"銅線"),
    (u"端子", u"端子"), (u"方块", u"方塊"), (u"物品", u"物品"),
]


def main():
    a = json.load(io.open(IN, encoding=u"utf-8"))
    b = json.load(io.open(OUT, encoding=u"utf-8"))
    bad_missing, bad_residue = [], []
    for zh, lzh in PAIRS:
        if zh == lzh:
            continue
        for k, z in a.items():
            if zh in z and lzh not in b[k]:
                bad_missing.append((k, zh, lzh, b[k][:60]))
            if zh in b[k]:
                bad_residue.append((k, zh, b[k][:60]))
    print(u"术语缺失（原文有、译文未用表中写法）：%d" % len(bad_missing))
    for it in bad_missing[:30]:
        print(u"   %s  缺「%s」(应作「%s」)  %s" % it)
    print(u"简体残留：%d" % len(bad_residue))
    for it in bad_residue[:30]:
        print(u"   %s  含「%s」  %s" % it)
    # 现代用字残留
    for ch in u"它的了":
        hits = [k for k, v in b.items() if ch in v]
        print(u"残留「%s」：%d %s" % (ch, len(hits), hits[:5]))
    return 0 if not (bad_missing or bad_residue) else 1


if __name__ == u"__main__":
    raise SystemExit(main())
