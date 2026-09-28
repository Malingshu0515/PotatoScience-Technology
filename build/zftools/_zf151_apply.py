# -*- coding: utf-8 -*-
u"""_zf151_apply.py —— ZF151 数据侧：给 `mineable/pickaxe` 补 3 个漏项（**只追加，不重排**）。

为什么只追加：`_zf125_verify.py` 的 D15 用的是 `only_inserted(...)` ——
那份标签文件与它的改前件**逐行对账**（只许新增）。所以本轮**不做格式化整理**
（文件里那几处缩进不齐的旧行一个字都不碰），只在末尾按同一缩进追加三行。

漏的三项（ZF151 侦察实测）：
  · `fluid_exchanger`              容器换流器 —— 有物品、有 getDrops，就是漏了标签（镐子不加速）
  · `electric_blast_furnace_part`  电力高炉外壳（无物品形态，拆解时给镐速加成）
  · `alloy_smelter_part`           合金炉外壳（同上）

跑法：python build\\zftools\\_zf151_apply.py [--write]
"""
import hashlib
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
TAG = os.path.join(ROOT, "src", "main", "resources", "data", "minecraft",
                   "tags", "block", "mineable", "pickaxe.json")
ADD = [u"potato_s_t:fluid_exchanger",
       u"potato_s_t:electric_blast_furnace_part",
       u"potato_s_t:alloy_smelter_part"]


def main(argv):
    write = u"--write" in argv
    raw = io.open(TAG, encoding=u"utf-8", newline=u"").read()
    table = json.loads(raw)
    have = set(table[u"values"])
    todo = [x for x in ADD if x not in have]
    print(u"标签现有 %d 项；要补 %d 项：%s" % (len(have), len(todo), todo))
    if not todo:
        print(u"  [跳过] 三项都已在（幂等）")
        return 0
    # ⚠ 这份文件**没有末尾换行**（`...\n  ]\n}` 结尾）—— 第一版按"有末尾换行"写，
    #   守卫当场拦下（这正是那条 `if not raw.endswith(tail)` 的用处）。追加时保持原样。
    tail = u'    "potato_s_t:diesel_generator_port"\n  ]\n}'
    if not raw.endswith(tail):
        print(u"!! 文件末尾与预期不符，停手先看清：%r" % raw[-120:])
        return 1
    lines = u",\n".join(u'    "%s"' % x for x in todo)
    new = raw[:-len(tail)] + u'    "potato_s_t:diesel_generator_port",\n' + lines + u"\n  ]\n}"
    after = json.loads(new)
    assert set(after[u"values"]) == have | set(todo), u"加完之后集合不对"
    assert len(after[u"values"]) == len(have) + len(todo), u"条数不对"
    print(u"  [改] %d → %d 项（只追加，旧行一字未动）" % (len(have), len(after[u"values"])))
    if not write:
        print(u"（没加 --write，只算不写）")
        return 0
    io.open(TAG, u"w", encoding=u"utf-8", newline=u"\n").write(new)
    chk = io.open(TAG, encoding=u"utf-8", newline=u"").read()
    assert chk == new
    print(u"已写盘；sha1 = %s" % hashlib.sha1(chk.encode(u"utf-8")).hexdigest()[:12])
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
