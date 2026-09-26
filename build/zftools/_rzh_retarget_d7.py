# -*- coding: utf-8 -*-
r"""_rzh_retarget_d7.py —— 按 §4.36「**改锚点、不放宽断言**」重写 `_zf117_verify.py` 的
`TOUCHED_BY_RZH` 表。

做法（关键在"算"而不是"写"）：
  1. 读 zf117_pre 快照 vs 工作树，机械算出**每个语言被改过值的键**；
  2. 从中**减掉**门上已有的两张名单：`TOUCHED_BY_MAIN_LINE`（本项目线自己改的，
     ZF121/ZF124）与 `ACID_FIX_KEY`（门单独列的那一条）；
  3. 剩下的就是"翻译线碰过的"，逐条断言**每一个都能在我的台账里找到归属**
     —— 找不到就直接报错，不许把来路不明的键塞进期望值；
  4. 只替换 `TOUCHED_BY_RZH = { ... }` 那一段，其余一个字节不动。

判据本身没动：仍是"被改动的键**正好等于**这张名单"，多一个都不行。

用法：`python build/zftools/_rzh_retarget_d7.py`
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SNAP = r"C:\PotatoST救援\zf117_pre"
REL = u"src/main/resources/assets/potato_s_t/lang/%s.json"
TARGET = os.path.join(HERE, u"_zf117_verify.py")
LANGS = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]

sys.path.insert(0, HERE)
import _rzh_touched  # noqa: E402


def main():
    src = io.open(TARGET, encoding=u"utf-8").read()

    # 门上已有的两张名单（从源码里读出来，不重抄）
    main_line = set(re.findall(r'u"([a-z]+\.[a-z0-9_.]+)"',
                               re.search(u"TOUCHED_BY_MAIN_LINE = \\[(.*?)\\]", src,
                                         re.S).group(1)))
    acid = re.search(u'ACID_FIX_KEY\\s*=\\s*(\\w+)', src).group(1)
    acid_key = re.search(u'%s\\s*=\\s*u"([^"]+)"' % acid, src)
    acid_key = acid_key.group(1) if acid_key else acid
    print(u"门上已有：MAIN_LINE %d 条，ACID_FIX_KEY = %s" % (len(main_line), acid_key))

    table = {}
    for loc in LANGS:
        sp = os.path.join(SNAP, REL.replace(u"/", os.sep) % loc)
        if not os.path.exists(sp):
            raise SystemExit(u"[拒绝] 快照缺 %s" % sp)
        old = json.load(io.open(sp, encoding=u"utf-8"))
        cur = json.load(io.open(os.path.join(ROOT, REL % loc), encoding=u"utf-8"))
        changed = set(k for k in old if k in cur and old[k] != cur[k])
        rest = changed - main_line - {acid_key}
        # 归属校验：每一个都得在我的台账里有说法
        mine = _rzh_touched.touched(loc) or set()
        unknown = sorted(k for k in rest if k not in mine)
        if unknown:
            raise SystemExit(
                u"[拒绝] %s 有 %d 个被改的键在台账里没有归属，不敢写进期望值：\n   %s"
                % (loc, len(unknown), u"\n   ".join(unknown)))
        table[loc] = sorted(rest)
        print(u"%-6s 被改 %2d = 本项目线 %d + 翻译线 %d"
              % (loc, len(changed), len(changed & (main_line | {acid_key})), len(rest)))

    # 生成新表
    out = [u"    TOUCHED_BY_RZH = {"]
    for loc in LANGS:
        out.append(u'        u"%s": [' % loc)
        for k in table[loc]:
            out.append(u'                   u"%s",' % k)
        # 去掉最后一行的逗号，保持 Python 风格一致
        out[-1] = out[-1].rstrip(u",")
        out.append(u"                   ],")
    out.append(u"    }")
    new_block = u"\n".join(out)

    pat = re.compile(u"    TOUCHED_BY_RZH = \\{.*?\\n    \\}", re.S)
    if not pat.search(src):
        raise SystemExit(u"[拒绝] 在 %s 里找不到 TOUCHED_BY_RZH 块" % TARGET)
    new_src = pat.sub(lambda m: new_block, src, count=1)

    # 自检：语法能编过、且新表真的进了文件
    compile(new_src, TARGET, u"exec")
    if new_block not in new_src:
        raise SystemExit(u"[拒绝] 替换没生效")
    io.open(TARGET, u"w", encoding=u"utf-8", newline=u"\n").write(new_src)
    print(u"\n已改写 %s（键序照快照差集排序）" % TARGET)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
