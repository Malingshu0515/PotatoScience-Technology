# -*- coding: utf-8 -*-
u"""_zf73_verifypatch.py —— 把 `_zf71_verify.py` 里 4 个**硬编码的活体数字**改成 0.11 的实测值

为什么这 4 个数要改：`_zf71_verify.py` 是"公告 vs 当前工程"的活体核对，
这 4 处把期望值**写死在脚本里**（3 流体 / 28 合成 / 210 键 / 8 张借贴图），
ZF73 加原油后实测是 4 / 29 / 218 / 9 ⇒ 它按设计跳闸（这就是它的用途）。
公告已同步升到 0.11，这里把期望值对齐。
"""
import io
import sys

PATH = r"E:\PotatoST\build\zftools\_zf71_verify.py"

PAIRS = [
    (u'check(fl == 3 and u"oxygen, hydrogen, chlorine" in doc',
     u'check(fl == 4 and u"oxygen, hydrogen, chlorine" in doc', u"流体 3 → 4"),
    (u'check(craft == 28, u"合成配方 %d 条" % craft)',
     u'check(craft == 29, u"合成配方 %d 条" % craft)', u"合成配方 28 → 29"),
    (u'check(len(keys) == 4 and set(keys.values()) == {210} and u"210 keys each" in doc',
     u'check(len(keys) == 4 and set(keys.values()) == {218} and u"218 keys each" in doc',
     u"语言键 210 → 218"),
    (u'check(n_draw == 8 and u"8 models still do this" in doc,',
     u'check(n_draw == 9 and u"9 models still do this" in doc,', u"借贴图 8 → 9"),
    (u'u"还在借原版贴图的模型 = %d 个（公告写 8）" % n_draw)',
     u'u"还在借原版贴图的模型 = %d 个（公告写 9）" % n_draw)', u"标签里的 8 → 9"),
]


def main():
    text = io.open(PATH, "r", encoding="utf-8").read()
    for old, new, label in PAIRS:
        n = text.count(old)
        if n != 1:
            print(u"  !! %s：命中 %d 次（必须 1 次）⇒ 不写" % (label, n))
            return 1
        text = text.replace(old, new, 1)
        print(u"  [OK] %s" % label)
    io.open(PATH, "w", encoding="utf-8", newline=u"\n").write(text)
    print(u"_zf71_verify.py 已更新（0.11 的活体期望值）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
