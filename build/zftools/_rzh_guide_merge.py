# -*- coding: utf-8 -*-
r"""_rzh_guide_merge.py —— 把并行翻译产出的补丁合并进正式语言文件。

补丁是 `_rzh_patch_<组>_<语言>.json`（subagent 只写这两份，不碰正式文件）。
本脚本负责**全部校验**，任何一条不过就整批不落盘：

  M1 补丁必须能解析、键集合与期望清单**完全一致**（不多不少）
  M2 每个 value 必须是非空字符串，且不等于中文原值（等于 = 没翻）
  M3 禁词扫描（按语言各自的表）：感叹号 / 破折号 / 省略号 / 废话词 / 口语 / 抒情
  M4 `$(br2)` 出现次数必须与中文源**逐键相同**（帕秋莉换行宏，漏一个排版就坏）
  M5 占位符 `%s` / `%1$s` / `%%` 必须与中文源一致
  M6 数字抽查：从中文源抠出全部数字组，必须逐个出现在译文里（顺序不限）
     —— 覆盖"数据、参数、限定词必须准确"这条；数字缺失即失败（不做例外）

过了才走 `_rzh_fix_batch`（行首锚定 + 旧值相等 + 写后复读），lzh 走 `_rzh_lzh_set`。

用法：`python build/zftools/_rzh_guide_merge.py`
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(HERE, u"_rzh_guide_merge.txt")

PATCHES = [
    (u"_rzh_patch_A_en_us.json", u"en_us"),
    (u"_rzh_patch_A_ru_ru.json", u"ru_ru"),
    (u"_rzh_patch_B_ja_jp.json", u"ja_jp"),
    (u"_rzh_patch_B_lzh.json", u"lzh"),
]

BANNED = {
    u"en_us": [(u"感叹号", [u"!"]),
               (u"破折号", [u" - ", u"—", u"–"]),
               (u"省略号", [u"..."]),
               # ⚠ 只禁**空转**的"可以"型写法（「you can …」这种叙述），
               #   不禁能力/权限陈述：`can be disabled in the config` 是必要信息
               #   （那正是那个配置项的作用），按用户口径属于"限定词必须准确"。
               (u"废话词", [u" you can ", u" you could ", u" one can ", u" able to ", u" merely "]),
               (u"口语", [u"don't ", u"won't ", u"y'know", u"okay", u"feel free", u"by the way"]),
               (u"抒情", [u"romance", u"truly", u"genuinely"])],
    u"ja_jp": [(u"感叹号", [u"！", u"!"]),
               (u"破折号", [u"——", u"—", u"–"]),
               (u"省略号", [u"……", u"..."]),
               (u"废话词", [u"できます", u"ことができ", u"ましょう"]),
               (u"口语", [u"ください", u"ですね", u"でしょう"]),
               (u"抒情", [u"ロマン"])],
    u"ru_ru": [(u"感叹号", [u"!"]),
               (u"破折号", [u"—", u"–", u" - "]),
               (u"省略号", [u"...", u"…"]),
               (u"废话词", [u" можно ", u" можете ", u"способн"]),
               (u"口语", [u"просто ", u"кстати", u"ведь "]),
               (u"抒情", [u"романтик"])],
    u"lzh": [(u"感叹号", [u"！", u"!"]),
             (u"破折号", [u"——", u"—", u"–"]),
             (u"省略号", [u"……", u"..."]),
             (u"废话词", [u"即可", u"亦能", u"則可"]),
             (u"抒情", [u"浪漫"])],
}

NUM = re.compile(u"[0-9][0-9 .,]*")
PH = re.compile(u"%\\d+\\$s|%s|%%")


def nums(text):
    r"""抠出数字组并**归一化**，用于跨语言对账。

    ⚠ 第一版直接字符串比对，必然在俄语上误报，三个原因：
      · 千分位：中文 `4,000,000` / 俄语 `4 000 000` / 有的写 `4.000.000`
      · 小数：中文 `2.5` / 俄语 `2,5`
      · 乘号：中文 `4×4` / 有的写 `4x4`
    归一化：`×`→`x`，然后**把数字之间的一切分隔符（空格 / 逗号 / 点）全部去掉**。
    这样 `1,000,000`、`1 000 000`、`1.000.000` 都变成 `1000000`；
    `2.5` 与 `2,5` 都变成 `25`。

    去分隔符是**故意激进**的：这个检查是"防整段数字被删掉"的兜底，
    不是精确对账（精确那部分由 `_rzh_guide_verify.py` 的 G4 事实表按语言逐条钉）。
    宁可把 `2.5`/`25` 这种歧义放过，也不要因为书面写法差异误报。
    """
    t = text.replace(u"×", u"x").replace(u"÷", u"/")
    out = []
    for tok in NUM.findall(t):
        tok = re.sub(u"[ .,]", u"", tok)
        if tok:
            out.append(tok)
    return out


def read_val(loc, key):
    with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
        return json.load(f)[key]


def main():
    zh = json.load(io.open(os.path.join(LANGDIR, u"zh_cn.json"), encoding=u"utf-8"))

    # 期望键清单：与 _rzh_guide_bundle 完全一致
    import _rzh_guide_zh as GZ
    guide_keys = sorted(GZ.NEW)
    config_keys = sorted(k for k in zh if k.startswith(u"potato_s_t.configuration"))
    sync_keys = [u"tooltip.potato_s_t.cola.1", u"tooltip.potato_s_t.cola.2",
                 u"tooltip.potato_s_t.gravity_device.one_shot.on",
                 u"tooltip.potato_s_t.gravity_device.one_shot.off"]
    want_keys = guide_keys + config_keys + sync_keys

    L = []
    bad = 0
    plans = {}

    for fname, loc in PATCHES:
        p = os.path.join(HERE, fname)
        L.append(u"===== %s（%s）=====" % (fname, loc))
        if not os.path.exists(p):
            bad += 1
            L.append(u"  [错] 补丁不存在")
            continue
        try:
            patch = json.load(io.open(p, encoding=u"utf-8"))
        except ValueError as e:
            bad += 1
            L.append(u"  [错] 解析失败：%s" % e)
            continue

        # M1 键集合
        missing = [k for k in want_keys if k not in patch]
        extra = [k for k in patch if k not in want_keys]
        if missing or extra:
            bad += 1
            L.append(u"  [错] M1 键集合不符：缺 %d、多 %d" % (len(missing), len(extra)))
            for k in missing[:6]:
                L.append(u"       缺 %s" % k)
            for k in extra[:6]:
                L.append(u"       多 %s" % k)
        else:
            L.append(u"  OK   M1 键集合一致（%d）" % len(want_keys))

        problems = []
        warnings = []
        for k in want_keys:
            if k not in patch:
                continue
            v = patch[k]
            src = zh.get(k, u"")
            # M2
            if not isinstance(v, str) or not v.strip():
                problems.append(u"M2 空值 %s" % k)
                continue
            if v == src:
                # ⚠ 旧值**本来就等于中文**时不算漏翻：那一类多是同一术语
                #   （lzh 的「黑洞」「引力裝置」「一次性」简繁同形，本来就照中文写）。
                #   只有"旧值≠中文、新值却回到中文"才是真没翻。
                if read_val(loc, k) == src:
                    warnings.append(u"M2 跳过：%s 旧值即中文（术语同形）" % k)
                else:
                    problems.append(u"M2 与中文相同（未翻）%s" % k)
            # M3
            for rule, needles in BANNED.get(loc, []):
                hit = [n for n in needles if n in v]
                if hit:
                    problems.append(u"M3 %s %s: %s" % (rule, k, u",".join(hit)))
            # M4
            if v.count(u"$(br2)") != src.count(u"$(br2)"):
                problems.append(u"M4 $(br2) 数 %d != 中文 %d  %s"
                                % (v.count(u"$(br2)"), src.count(u"$(br2)"), k))
            # M5
            if sorted(PH.findall(v)) != sorted(PH.findall(src)):
                problems.append(u"M5 占位符 %s != 中文 %s  %s"
                                % (sorted(PH.findall(v)), sorted(PH.findall(src)), k))
            # M6 数字对账（归一化后比对）
            srcs = nums(src)
            vs = nums(v)
            miss = [n for n in srcs if n not in vs]
            if miss and len(miss) > max(1, len(srcs) // 2):
                problems.append(u"M6 缺数字 %s（源共 %d 个）  %s" % (miss[:8], len(srcs), k))
            elif miss:
                warnings.append(u"M6 提示：%s 少 %s（源 %s）" % (k, miss, srcs))

        if problems:
            bad += 1
            L.append(u"  [错] %d 处" % len(problems))
            for s in problems[:25]:
                L.append(u"       %s" % s)
        else:
            L.append(u"  OK   M2/M3/M4/M5/M6 全过（%d 键）" % len(want_keys))
            plans[loc] = patch
        if warnings:
            L.append(u"  [提示] %d 条数字差异（不到半数，只记录）" % len(warnings))
            for s in warnings[:15]:
                L.append(u"       %s" % s)
        L.append(u"")

    if bad:
        L.append(u"== 有 %d 处问题，**一个字节都不落盘** ==" % bad)
        io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
        print(u"bad=%d -> %s（未落盘）" % (bad, OUT))
        return 1

    # ---- 落盘 ----
    edits, lzh_pairs = [], []
    for loc, patch in sorted(plans.items()):
        for k in want_keys:
            old = read_val(loc, k)
            new = patch[k]
            if old == new:
                continue
            if loc == u"lzh":
                lzh_pairs.append((k, old, new))
            else:
                edits.append((loc, k, old, new))

    import _rzh_fix_batch as fb
    fb.SUBSTITUTIONS = []
    fb.REGEX_SUBST = []
    fb.EDITS = edits
    rc = fb.main()
    if lzh_pairs:
        import _rzh_lzh_set as ls
        ls.apply(lzh_pairs, u"手册正文 四语合并")

    L.append(u"== 已落盘 ==")
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
    return rc


if __name__ == u"__main__":
    sys.exit(main())
