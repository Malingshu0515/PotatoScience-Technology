# -*- coding: utf-8 -*-
u"""ZF145：算出"四语言各 16 个新成就键的值"的 sha1 指纹（供 `_zf145_verify.py` 的 E8 用）。
   指纹口径：按**键名排序**后，把 `键\0值` 用 \n 连起来取 sha1。只读。
"""
import hashlib, io, json, os, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = r'E:\PotatoST'
ADIR = os.path.join(ROOT, r'src\main\resources\data\potato_s_t\advancement')
LANG = os.path.join(ROOT, r'src\main\resources\assets\potato_s_t\lang')
NEW = ["diesel_generator", "silver_wire", "star_chart_tome", "star_steel_slash",
       "star_steel_tools", "titanium_armor", "vibranium", "vibranium_armor"]
# ⚠ 键名必须**排序**后再算（与 verify 里 sorted(keys) 一致）
keys = []
for n in NEW:
    keys.append(u'advancements.potato_s_t.%s.title' % n)
    keys.append(u'advancements.potato_s_t.%s.description' % n)
keys = sorted(keys)
assert len(keys) == 16, len(keys)

out = []
for loc in ('zh_cn', 'en_us', 'ja_jp', 'ru_ru'):
    t = json.load(io.open(os.path.join(LANG, loc + '.json'), encoding='utf-8'))
    blob = u'\n'.join(u'%s\u0000%s' % (k, t[k]) for k in keys)
    h = hashlib.sha1(blob.encode('utf-8')).hexdigest()
    out.append(u'    u"%s": u"%s",' % (loc, h))
print(u'NEW_VALUE_SHA = {')
print(u'\n'.join(out))
print(u'}')
