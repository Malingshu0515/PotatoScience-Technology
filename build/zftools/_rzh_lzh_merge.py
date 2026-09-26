# -*- coding: utf-8 -*-
r"""_rzh_lzh_merge.py —— 把三份文言文译稿合成 assets/potato_s_t/lang/lzh.json。

为什么要有这一道：三份译稿是并行产出的，各自只管自己的键。合并时必须证明它们
**合起来正好等于 zh_cn 的键集**，否则游戏里会出现"一半中文一半英文"（缺的键
会回落到 en_us）。所以这里是一道门，不是一次复制粘贴：

  1. 三份译稿的键**两两不相交**，合起来 == zh_cn 的键集（一个不多一个不少）；
  2. 键序照 zh_cn 盘上顺序（方便日后 diff）；
  3. 逐键核对 `%s` / `%%` / `%1$s` 的**序列完全相同**；
  4. 逐键核对 `\n` 的**个数完全相同**；
  5. 空值 / 与中文原文逐字相同的值全部报出来（除白名单外都算未翻译）。

任一不过 ⇒ 抛异常，不落盘。

用法：`python build/zftools/_rzh_lzh_merge.py`
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
ZH = os.path.join(LANGDIR, u"zh_cn.json")
OUT = os.path.join(LANGDIR, u"lzh.json")
PARTS = [u"_rzh_lzh_out1.json", u"_rzh_lzh_out2.json", u"_rzh_lzh_out3.json"]

# 允许"与中文原文逐字相同"的键：简繁同形的纯名词 / 纯格式串，**无字可改**。
#
# ⚠ 这是白名单，不是"大概没事"。每一条都必须是**简繁同形**、且不含任何可替换的
#   实词 —— 例如「原油」「柴油」「FE」这类；一旦某条里出现「盐 / 铁 / 层 / 为」
#   之类有繁体写法的字，它就不该在这张表里。
#   先由合并脚本全量打印，人工过一遍，再抄进来（见 _rzh_lzh_merge 的输出）。
SAME_OK = set()

# ---------------------------------------------------------------------------
# 语言元数据：**zh_cn 里没有、但 lzh 必须有**
#
# 取证（`_rzh_probe_lzh_meta.txt`）：原版 `minecraft/lang/lzh.json` 自己带
#     language.name   = 文言
#     language.region = 華夏
# 1.21 的语言菜单就是读**这个文件**来决定显示名。我们的 lzh.json 若不带这两条，
# 语言列表会显示原始翻译键（`language.name`）而不是「文言」。
#
# ⚠ 所以合并时它们是"必须多出来的两条"，而校验器里也要给它们开一个
#   **显式例外**（且值必须与原版逐字相同）—— 不是放宽"键集必须相等"，
#   而是把"相等"重新定义为"zh_cn 的键 + 这两条元数据"。
# ---------------------------------------------------------------------------
META = {
    u"language.name": u"文言",
    u"language.region": u"華夏",
}

PH = re.compile(u"%\\d+\\$s|%s|%%")


def main():
    with io.open(ZH, encoding=u"utf-8") as f:
        zh = json.load(f)

    merged = {}
    for name in PARTS:
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            raise SystemExit(u"[拒绝] 缺译稿 %s" % p)
        with io.open(p, encoding=u"utf-8") as f:
            part = json.load(f)
        dup = set(part) & set(merged)
        if dup:
            raise SystemExit(u"[拒绝] %s 与前面的译稿键重叠 %d 个：%s"
                             % (name, len(dup), sorted(dup)[:5]))
        merged.update(part)
        print(u"%-24s %4d 键" % (name, len(part)))

    print(u"\n三份合计 %d 键；zh_cn %d 键" % (len(merged), len(zh)))
    missing = [k for k in zh if k not in merged]
    extra = [k for k in merged if k not in zh]
    if missing or extra:
        print(u"  [缺] %d 个：%s" % (len(missing), missing[:10]))
        print(u"  [多] %d 个：%s" % (len(extra), extra[:10]))
        raise SystemExit(u"[拒绝] 键集不齐 —— 缺键的会在游戏里回落成英文")

    # 语言元数据：照原版两条，值逐字相同
    for k, v in META.items():
        merged[k] = v
    print(u"另加语言元数据 %d 条：%s" % (len(META), u", ".join(u"%s=%s" % kv for kv in META.items())))

    # 逐键体检
    bad_ph, bad_nl, same, empty = [], [], [], []
    for k, zv in zh.items():
        v = merged[k]
        if not isinstance(v, str) or not v.strip():
            empty.append(k)
            continue
        if PH.findall(zv) != PH.findall(v):
            bad_ph.append((k, PH.findall(zv), PH.findall(v)))
        if zv.count(u"\\n") != v.count(u"\\n"):
            bad_nl.append((k, zv.count(u"\\n"), v.count(u"\\n")))
        if zv == v and k not in SAME_OK:
            same.append(k)

    def dump(title, items, limit=10):
        if items:
            print(u"\n== %s：%d 条 ==" % (title, len(items)))
            for it in items[:limit]:
                print(u"   %s" % (it,))

    dump(u"占位符序列不一致", bad_ph)
    dump(u"换行个数不一致", bad_nl)
    # 「与中文逐字相同」**全量打印**：这张表要人工过一遍再抄进 SAME_OK，
    # 只打前 10 条等于逼着人猜剩下的。同时也是可以留档的证据。
    print(u"\n== 与中文逐字相同（简繁同形，逐条过目）：%d 条 ==" % len(same))
    for k in same:
        print(u"   %-52s %s" % (k, zh[k]))
    dump(u"空值", empty)
    if bad_ph or bad_nl or empty:
        raise SystemExit(u"[拒绝] 上列问题必须先修掉")

    # 落盘：键序照 zh_cn，元数据放最后
    ordered = dict((k, merged[k]) for k in zh)
    for k, v in META.items():
        ordered[k] = v
    text = json.dumps(ordered, ensure_ascii=False, indent=2)
    if u"\r" in text:
        text = text.replace(u"\r\n", u"\n")
    with io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(text + u"\n")
    print(u"\nwrote %s（%d 键，%d 字节）" % (OUT, len(ordered), os.path.getsize(OUT)))
    if same:
        print(u"⚠ 有 %d 条与中文逐字相同（已在上方列出）—— 请人工确认是不是专有名词"
              % len(same))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
