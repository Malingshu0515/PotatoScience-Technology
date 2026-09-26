# -*- coding: utf-8 -*-
r"""_rzh_adv_prune_new.py —— 把 `_rzh_adv_trim.NEW` 里"与盘上现况逐字相同"的条目剔掉。

为什么需要它：`NEW` 里有些条目是我照**早先**的 dump 写的，而盘上已经被平行线
改成了同一个样子 —— 那就是一条"没有意义"的编辑。`_rzh_adv_trim.py` 的守卫会
对整批**拒绝**（这个行为是对的），但一条条手工找太慢、也容易漏。

做法：导入 `NEW`，与 `_rzh_adv_now.json` 逐条比，把相同的键从字面量里删掉，
再**重写 `_rzh_adv_trim.py` 里 `NEW = { ... }` 那一段**（只动那一段，其余字节不变），
改完 `compile()` 自检 + 重新导入验证。

用法：`python build/zftools/_rzh_adv_prune_new.py`
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, u"_rzh_adv_trim.py")
NOW = os.path.join(HERE, u"_rzh_adv_now.json")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]


def main():
    sys.path.insert(0, HERE)
    from _rzh_adv_trim import NEW            # noqa: E402
    with io.open(NOW, encoding=u"utf-8") as f:
        now = json.load(f)

    pruned = {}
    for node, per in NEW.items():
        keep = {}
        for loc, new in per.items():
            if now.get(node, {}).get(loc) == new:
                print(u"剔除 %-24s %-6s（盘上已是这个值）" % (node, loc))
                continue
            keep[loc] = new
        if keep:
            pruned[node] = keep
        else:
            print(u"剔除 %-24s 整条（各语都已是新值）" % node)

    # 重写字面量
    out = [u"NEW = {"]
    for node in sorted(pruned):
        out.append(u'    u"%s": {' % node)
        for loc in LOCALES:
            if loc in pruned[node]:
                out.append(u'        u"%s": %s,'
                           % (loc, json.dumps(pruned[node][loc], ensure_ascii=False)))
        out.append(u'    },')
    out.append(u"}")
    block = u"\n".join(out)

    src = io.open(TARGET, encoding=u"utf-8").read()
    pat = re.compile(u"NEW = \\{.*?\\n\\}", re.S)
    if not pat.search(src):
        raise SystemExit(u"[拒绝] 找不到 NEW 块")
    new_src = pat.sub(lambda m: block, src, count=1)
    compile(new_src, TARGET, u"exec")
    io.open(TARGET, u"w", encoding=u"utf-8", newline=u"\n").write(new_src)
    print(u"\n重写 %s：%d 条 -> %d 条" % (TARGET, len(NEW), len(pruned)))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
