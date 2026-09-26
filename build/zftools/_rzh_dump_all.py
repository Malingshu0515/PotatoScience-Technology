# -*- coding: utf-8 -*-
r"""_rzh_dump_all.py —— 按类别把四语并排导出，供翻译线逐类过目。

`_rzh_dump_names.py` 只管 item/block；这个管全部类别（gui / message / tooltip /
fluid / fluid_type / death / biome / sky / mode / jukebox_song / itemGroup）。

⚠ 只读。输出走 `_rzh_dump_all_<tag>.txt`，**不用 shell 重定向**（PowerShell 的 `>`
   落盘是 UTF-16，read 工具会当二进制拒读 —— 这个坑本会话踩过一次了）。
"""
from __future__ import print_function
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]


def load(loc):
    with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
        return json.load(f)


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else u""
    if not tag:
        print(u"用法: python _rzh_dump_all.py <类别>  （gui / message / tooltip / ...）")
        print(u"      python _rzh_dump_all.py @<键前缀,逗号分隔> --json <输出路径>")
        return 1

    # @前缀模式：给文言文那批导一份「zh 原文 -> 待填」的 JSON 骨架，
    # 键序严格照 zh_cn 盘上顺序，方便最后合并时不错位。
    if tag.startswith(u"@"):
        prefixes = tuple(p for p in tag[1:].split(u",") if p)
        try:
            out_at = sys.argv.index(u"--json")
            out_path = sys.argv[out_at + 1]
        except (ValueError, IndexError):
            print(u"@前缀模式需要 --json <输出路径>")
            return 1
        zh = load(u"zh_cn")
        picked = dict((k, zh[k]) for k in zh if k.startswith(prefixes))
        with io.open(out_path, u"w", encoding=u"utf-8", newline=u"\n") as f:
            f.write(json.dumps(picked, ensure_ascii=False, indent=2) + u"\n")
        print(u"wrote %s  (%d keys)" % (out_path, len(picked)))
        return 0

    data = dict((loc, load(loc)) for loc in LOCALES)
    keys = sorted(k for k in data[u"zh_cn"] if k.startswith(tag + u"."))
    lines = [u"%s.* 共 %d 条" % (tag, len(keys)), u""]
    for k in keys:
        short = k.split(u".", 1)[1] if u"." in k else k
        lines.append(u"-------- %s" % short)
        for loc, label in zip(LOCALES, [u"zh", u"en", u"ja", u"ru"]):
            v = data[loc].get(k, u"<缺>")
            lines.append(u"  %-3s %s" % (label, v.replace(u"\n", u"\\n")))
        lines.append(u"")
    p = os.path.join(ROOT, u"build", u"zftools", u"_rzh_dump_all_%s.txt" % tag)
    with io.open(p, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(u"\n".join(lines) + u"\n")
    print(u"wrote %s  (%d keys, %d bytes)" % (p, len(keys), os.path.getsize(p)))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
