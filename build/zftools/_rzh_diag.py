# -*- coding: utf-8 -*-
r"""_rzh_diag.py —— 对账：盘上的成就标题 vs 期望值（四语言），逐条打印。"""
import io
import json
import importlib.util

LANG = u"src/main/resources/assets/potato_s_t/lang/%s.json"
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]

spec = importlib.util.spec_from_file_location(u"kv", u"build/zftools/_rzh_setkv.py")
kv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kv)

for loc in LOCALES:
    d = json.load(io.open(LANG % loc, encoding=u"utf-8"))
    print(u"== %s" % loc)
    for nid in sorted(kv.TITLES):
        key = u"advancements.potato_s_t.%s.title" % nid
        want = kv.TITLES[nid].get(loc)
        got = d.get(key)
        mark = u"OK " if got == want else u"DIFF"
        print(u"   %s %-22s now=%-24r want=%r" % (mark, nid, got, want))
