# -*- coding: utf-8 -*-
r"""_rzh_zrepair.py —— 修 `_rzh_fix_batch` 上一版写坏的末尾逗号。

坏在哪：老写法重写一行时**无条件补逗号**（`u'  %s: %s,'`）。被改的键恰好是
JSON 对象里的**最后一个键**时，写出来就是「值, \n }」⇒ 非法 JSON。
上一批 19 条里 `advancements.potato_s_t.gravity_device.description`
正好是每份文件的最后一个键，于是 en_us / ja_jp / ru_ru 三份同时中招。

坏文件 parse 不了 ⇒ 走不了 `_rzh_fix_batch` 的三段校验，所以这里做**精确文本修复**，
但每一步都验：
  1. 末行必须是 `}`（前面允许有空行），否则拒绝动手；
  2. `}` 之上最近的非空行**必须**以 `",` 结尾，且去掉逗号后能解析出新值；
  3. 改完 `json.loads` 必须过，且**键数等于 zh_cn**（口径：五份键集合一致，lzh 多 2）；
  4. 不许有 CR；
  5. 写后复读：字面量等于预期值、键数不变、文件仍是纯 LF。

用法：`python build/zftools/_rzh_zrepair.py`
"""
from __future__ import print_function
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
LOCS = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]


def load_raw(loc):
    with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8", newline=u"") as f:
        return f.read()


def main():
    zh = json.loads(load_raw(u"zh_cn"))
    n_base = len(zh)
    fixed, skipped, bad = [], [], 0

    for loc in LOCS:
        text = load_raw(loc)
        try:
            json.loads(text)
            skipped.append(loc)
            continue
        except ValueError:
            pass                                    # 就是它坏了 -> 往下修

        lines = text.split(u"\n")
        # 找最后一个非空行
        last = None
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip():
                last = i
                break
        if last is None or lines[last].strip() != u"}":
            print(u"[拒绝] %s 的最后一个非空行不是 } —— 不是「末尾逗号」这一种坏法" % loc)
            bad += 1
            continue

        k = last - 1
        while k >= 0 and not lines[k].strip():
            k -= 1
        if k < 0 or not lines[k].rstrip().endswith(u","):
            print(u"[拒绝] %s 的 } 之上那行不是以逗号结尾，修不了" % loc)
            bad += 1
            continue

        before = lines[k]
        lines[k] = lines[k].rstrip()[: -1]          # 只去掉那个逗号
        newtext = u"\n".join(lines)
        try:
            data = json.loads(newtext)
        except ValueError as e:
            print(u"[拒绝] %s 去掉逗号后仍解析失败：%s" % (loc, e))
            bad += 1
            continue

        want = n_base + (2 if loc == u"lzh" else 0)
        if len(data) != want:
            print(u"[拒绝] %s 键数 %d != 期望 %d" % (loc, len(data), want))
            bad += 1
            continue
        if u"\r" in newtext:
            print(u"[拒绝] %s 里出现了 CR" % loc)
            bad += 1
            continue

        with io.open(os.path.join(LANGDIR, loc + u".json"), u"w",
                     encoding=u"utf-8", newline=u"\n") as f:
            f.write(newtext)

        # 写后复读
        back = load_raw(loc)
        d2 = json.loads(back)
        ok = (len(d2) == want
              and d2[u"advancements.potato_s_t.gravity_device.description"]
              == data[u"advancements.potato_s_t.gravity_device.description"]
              and u"\r" not in back)
        if not ok:
            print(u"[拒绝] %s 写后复读不一致" % loc)
            bad += 1
            continue

        fixed.append(loc)
        print(u"%-6s 修好：去掉末尾逗号，键数 %d，解析通过" % (loc, len(d2)))
        print(u"       修前: ...%s" % before[-70:])
        print(u"       修后: ...%s" % lines[k][-70:])
        print(u"       末键: %s" % d2[u"advancements.potato_s_t.gravity_device.description"][:70])

    print(u"")
    print(u"修了 %d 份：%s" % (len(fixed), u", ".join(fixed) or u"（无）"))
    print(u"本来就好的：%s" % u", ".join(skipped))
    print(u"失败 %d" % bad)
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
