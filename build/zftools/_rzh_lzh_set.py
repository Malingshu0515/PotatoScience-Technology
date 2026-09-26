# -*- coding: utf-8 -*-
r"""_rzh_lzh_set.py —— 改 `lzh.json` 里**指定键**的值（单一入口，带三重校验）。

为什么不让每个脚本各写各的：文言文那份是独立一套文字，改它最容易的错法是
**改错语言**（把 zh_cn 当 lzh 打开）或**键名拼错静默失效**。所以这里定死：

  1. 只认这一个文件 `src/main/resources/assets/potato_s_t/lang/lzh.json`；
  2. 键必须存在，且**当前值必须等于我给的旧值**（或已等于新值 ⇒ 幂等跳过）；
  3. 写后复读 + 键数不变 + 仍是合法 JSON + 纯 LF。

其它脚本 `from _rzh_lzh_set import apply` 即可。

用法（直接跑则只做自检）：`python build/zftools/_rzh_lzh_set.py`
"""
from __future__ import print_function
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LZH = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t",
                   u"lang", u"lzh.json")


def line_index(text):
    idx = {}
    for n, line in enumerate(text.split(u"\n")):
        s = line.lstrip()
        if s.startswith(u'"'):
            end = s.find(u'":')
            if end >= 0:
                idx[s[1:end]] = n
    return idx


def apply(pairs, label=u""):
    """pairs = [(键, 旧值, 新值)]；全量校验通过才落盘。返回改了几个键。"""
    with io.open(LZH, encoding=u"utf-8", newline=u"") as f:
        text = f.read()
    data = json.loads(text)
    n_before = len(data)

    lines = text.split(u"\n")
    idx = line_index(text)
    ops = []
    for key, old, new in pairs:
        if key not in data:
            raise SystemExit(u"[拒绝] lzh 里没有键 %s" % key)
        cur = data[key]
        if cur == new:
            continue                       # 幂等
        if cur != old:
            raise SystemExit(u"[拒绝] %s 与预期不符\n  盘上: %r\n  预期: %r"
                             % (key, cur, old))
        if key not in idx:
            raise SystemExit(u"[拒绝] %s 找不到行首骨架行" % key)
        ops.append((idx[key], key, new))

    if not ops:
        print(u"%s没有要改的（幂等）" % (label and (label + u"：") or u""))
        return 0

    for lineno, key, new in ops:
        lines[lineno] = u'  %s: %s,' % (json.dumps(key, ensure_ascii=False),
                                        json.dumps(new, ensure_ascii=False))
    out = u"\n".join(lines)
    if u"\r" in out:
        raise SystemExit(u"[拒绝] 出现 CR —— lzh.json 必须是纯 LF")
    json.loads(out)
    with io.open(LZH, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(out)

    # 写后复读
    data2 = json.load(io.open(LZH, encoding=u"utf-8"))
    if len(data2) != n_before:
        raise SystemExit(u"[拒绝] 键数变了：%d -> %d" % (n_before, len(data2)))
    for _, key, new in ops:
        if data2[key] != new:
            raise SystemExit(u"[拒绝] %s 没改成预期值" % key)
    print(u"%s改了 %d 个键（键数仍为 %d）" % (label and (label + u"：") or u"", len(ops), n_before))
    return len(ops)


if __name__ == u"__main__":
    print(u"本文件是库，不是脚本；请从改名脚本里 `from _rzh_lzh_set import apply` 调用。")
    print(u"目标文件：%s" % LZH)
    print(u"存在：%s" % os.path.exists(LZH))
