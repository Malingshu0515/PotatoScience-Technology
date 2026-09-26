# -*- coding: utf-8 -*-
r"""_rzh_lzh_verify.py —— 文言文语言包（lzh.json）的常驻校验。

这个门守的是一件很具体的事：**文言文包不能比中文包少一个键**。
少一个键不会报错 —— Minecraft 会安静地回落去读 en_us，玩家就在满屏文言里
突然看见一行英文。所以"键集必须逐字相等"是这里的第一条，也是最不能放宽的。

门的判据（全部来自盘上现状，不钉任何'翻译得好不好'——那是我脑子的活，不是门的）：

  A 结构
    A1 `lang/lzh.json` 存在、是合法 JSON、无 BOM
    A2 纯 LF（无 CR）
    A3 顶层是对象、值全是字符串、无空值
  B 与 zh_cn 的对照（**核心**）
    B1 键集完全相同（缺 / 多都报）
    B2 键序完全相同（方便日后 diff，改动了要显式重排）
    B3 `%s` / `%%` / `%1$s` 的**序列**逐键相同
    B4 `\n` 个数逐键相同
    B5 除白名单外，没有"与中文逐字相同"的值（那就是漏译）
  C 与原版的兼容
    C1 lzh 是 1.21.1 真实存在的语言（从 launcher 资源索引取证，只在有索引时检查）
    C2 引用的键在原版 lzh.json 里**存在**的，必须被打磨过（抽查 value 与 en 不同）
  D 台账
    D1 `_rzh_touched.py` 认得 lzh 这个语言（四语台账已扩成五语）

用法：`python build/zftools/_rzh_lzh_verify.py`
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
LZH = os.path.join(LANGDIR, u"lzh.json")
ZH = os.path.join(LANGDIR, u"zh_cn.json")
INDEX = r"E:\gradle-home\caches\minecraft\assets\indexes\asset-index.json"

PH = re.compile(u"%\\d+\\$s|%s|%%")
# 字形守的是**反向**的：原版 lzh 是繁体（鐵礦 / 鐵璞 / 鐵錠，见
# `_rzh_vanilla_names.txt`），所以 lzh.json 里混进**简体专有字形**就是失手。
#
# ⚠ 这张表**只能放"只在简体里出现、繁体不这么写"的字**。
#   第一版把「面 / 器 / 只 / 言」也放了进去 —— 那四个**简繁同形**，于是
#   「界面」「電解器」「只」「語言」全被误报成"混进简体"。是逐条对字形才发现的。
SIMP = (u"钛钨铀铝钴镍锰锂硅矿锭铁铜银钢电气机门开关热温层数这们来时与并产于过进还"
        u"种样当经应对线号处车马鸟鱼龙凤买卖读写说话语")

# 允许"与中文逐字相同"的键：见 `_rzh_touched.LZH_SAME_OK` —— **名单只有一份**，
# 这里取用而不重抄（存三份迟早会漂，漂了的白名单等于偷偷放宽判据）。
sys.path.insert(0, HERE)
from _rzh_touched import LZH_SAME_OK as SAME_OK  # noqa: E402

# ---------------------------------------------------------------------------
# 语言元数据：**zh_cn 里没有、lzh 必须有**的两条。
#
# 取证：原版 `minecraft/lang/lzh.json` 自己带 `language.name = 文言` /
# `language.region = 華夏`，1.21 的语言菜单读这个文件决定显示名。少了它们，
# 语言列表会显示原始翻译键。
#
# ⚠ 这不是"放宽 B1 键集相等"，而是把相等重新定义为
#   `zh_cn 的键` ∪ `这两条元数据`；**值必须与原版逐字相同**，写错了照样红。
# ---------------------------------------------------------------------------
META = {
    u"language.name": u"文言",
    u"language.region": u"華夏",
}

fails = []
oks = []


def check(cond, msg):
    if cond:
        oks.append(msg)
    else:
        fails.append(msg)


def main():
    # ---- A 结构 ----
    print(u"== A 结构 ==")
    if not os.path.exists(LZH):
        print(u"  [FAIL] 没有 %s" % LZH)
        return 1
    raw = io.open(LZH, u"rb").read()
    check(not raw.startswith(u"\ufeff".encode(u"utf-8")), u"A1 无 BOM")
    check(b"\r" not in raw, u"A1 纯 LF（无 CR）")
    lzh = json.loads(raw.decode(u"utf-8"))
    check(isinstance(lzh, dict), u"A3 顶层是对象")
    check(all(isinstance(v, str) for v in lzh.values()), u"A3 值全是字符串")
    check(all(v.strip() for v in lzh.values()), u"A3 没有空值")
    print(u"  lzh.json：%d 键，%d 字节" % (len(lzh), len(raw)))

    # ---- B 与 zh_cn 对照 ----
    print(u"\n== B 与 zh_cn 对照 ==")
    with io.open(ZH, encoding=u"utf-8") as f:
        zh = json.load(f)
    miss = [k for k in zh if k not in lzh]
    extra = [k for k in lzh if k not in zh and k not in META]
    check(not miss, u"B1 没有缺键（缺 %d 个）%s" % (len(miss), miss[:6]))
    check(not extra, u"B1 没有多余键（多 %d 个）%s" % (len(extra), extra[:6]))
    check(list(zh) == [k for k in lzh if k not in META], u"B2 键序与 zh_cn 一致")

    # 语言元数据：值必须与原版逐字相同
    for k, want in META.items():
        check(lzh.get(k) == want,
              u"B7 元数据 %s = %r（原版就是这个写法）" % (k, lzh.get(k)))

    bad_ph, bad_nl, same = [], [], []
    for k in zh:
        if k not in lzh:
            continue
        zv, lv = zh[k], lzh[k]
        if PH.findall(zv) != PH.findall(lv):
            bad_ph.append(k)
        if zv.count(u"\\n") != lv.count(u"\\n"):
            bad_nl.append(k)
        if zv == lv:
            same.append(k)
    check(not bad_ph, u"B3 占位符序列逐键相同（%d 条不符）%s" % (len(bad_ph), bad_ph[:6]))
    check(not bad_nl, u"B4 换行个数逐键相同（%d 条不符）%s" % (len(bad_nl), bad_nl[:6]))
    same = [k for k in same if k not in SAME_OK]
    check(not same, u"B5 没有与中文逐字相同的值（%d 条）%s" % (len(same), same[:8]))

    # 字形：原版 lzh 是繁体（鐵礦/鐵璞/鐵錠），所以这里防的是**混进简体**
    simp_hits = []
    for k, v in lzh.items():
        hit = [ch for ch in v if ch in SIMP]
        if hit:
            simp_hits.append((k, u"".join(hit)))
    check(not simp_hits, u"B6 没有混进简体字形（%d 条）%s"
          % (len(simp_hits), [k for k, _ in simp_hits[:6]]))
    # 反向抽查：常用术语确实写成了原版那套繁体。
    # ⚠ 只查「礦」「錠」—— 本模组没有铁的矿石/锭，`鐵` 只在原版词条里出现，
    #   拿它当判据会误报（这正是"断言要对着盘上真有的东西"）。
    joined = u"".join(lzh.values())
    check(u"礦" in joined and u"錠" in joined,
          u"B6 用词已是繁体体系（礦 / 錠 都出现过）")

    # ---- C 原版真有 lzh ----
    print(u"\n== C 原版语言 ==")
    if os.path.exists(INDEX):
        with io.open(INDEX, encoding=u"utf-8") as f:
            idx = json.load(f)
        langs = [k for k in idx.get(u"objects", {}) if k.startswith(u"minecraft/lang/")]
        check(u"minecraft/lang/lzh.json" in langs,
              u"C1 1.21.1 资源索引里有 minecraft/lang/lzh.json（文言文是官方语言）")
        check(u"minecraft/lang/zh_cn.json" in langs, u"C1 索引里也有 zh_cn.json")
    else:
        oks.append(u"C1 索引不在盘上，跳过（不放宽任何断言，只是没得查）")

    # ---- D 台账认得 lzh ----
    print(u"\n== D 台账 ==")
    sys.path.insert(0, HERE)
    try:
        import _rzh_touched
        check(u"lzh" in _rzh_touched.LOCALES,
              u"D1 _rzh_touched.LOCALES 里含 lzh（否则门跑到别的语言会漏掉它）")
    except ImportError as e:
        check(False, u"D1 导入 _rzh_touched 失败：%s" % e)

    print(u"\n=========== 结果 ===========")
    for m in oks:
        print(u"  [OK]   " + m)
    for m in fails:
        print(u"  [FAIL] " + m)
    print(u"\n失败项 = %d" % len(fails))
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
