# -*- coding: utf-8 -*-
u"""_zf75_gatefix2.py —— 修 `_zf71_verify.py` 里"矿石数"的坏代理

它原来数的是 `data/potato_s_t/worldgen/configured_feature/` **目录里的文件数**（9），
ZF75 加了一个非矿物特征 `mini_oilfield.json` 之后变成 10 ⇒ 校验报「矿石 10 种」，
而实际上矿石还是 9 种。改成只数 `ore_*` 前缀文件。
"""
import io
import sys

PATH = r"E:\PotatoST\build\zftools\_zf71_verify.py"
OLD = u'    ore_n = len(os.listdir(os.path.join(RES, r"data\\potato_s_t\\worldgen\\configured_feature")))'
NEW = (u'    # \u26a0 ZF75 \u4fee\u6b63\uff1a\u539f\u6765\u6570\u7684\u662f**\u6574\u4e2a configured_feature \u76ee\u5f55**\u7684\u6587\u4ef6\u6570\uff089\uff09\uff0c\n'
       u'    #    \u52a0\u4e00\u4e2a\u975e\u77ff\u7269\u7279\u5f81\uff08mini_oilfield\uff09\u5c31\u53d8 10\u3001\u8bef\u62a5\u300c\u77ff\u77f3 10 \u79cd\u300d\u3002\n'
       u'    #    \u6539\u6210\u53ea\u6570 ore_* \u524d\u7f00\uff0c\u8bed\u4e49\u624d\u5bf9\u5f97\u4e0a\u6807\u7b7e\u3002\n'
       u'    ore_n = len([f for f in os.listdir(os.path.join(RES, r"data\\potato_s_t\\worldgen\\configured_feature"))\n'
       u'                  if f.startswith(u"ore_")])')


def main():
    t = io.open(PATH, "r", encoding="utf-8").read()
    n = t.count(OLD)
    print(u"锚点命中 %d 次" % n)
    if n != 1:
        return 1
    io.open(PATH, "w", encoding="utf-8", newline=u"\n").write(t.replace(OLD, NEW, 1))
    print(u"  [OK] ore_n 改成只数 ore_*")
    return 0


if __name__ == "__main__":
    sys.exit(main())
