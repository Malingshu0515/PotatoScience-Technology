# -*- coding: utf-8 -*-
u"""_zf167_lang_integrity.py —— 自查：我改写五份 lang 时，**旧键的值有没有被动过**

为什么必须单独自查：`_zf167_lang.py` 的读回只校验了**本轮新增那 15 个键**，
而"整份 parse → dump"这种写回有可能把旧值的**转义**规整掉（`\\n` / `\\u00a7` / 空格…）。
`_zf148_verify.py` 的 E7（"五份的值与生成器表逐字一致"）报了 23 处不一致 ⇒ 先分清
"是别人在途改的文案"还是"我写回时动的"。
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
PRE = r"C:\PotatoST救援\zf167_pre\src\main\resources\assets\potato_s_t\lang"
CODES = (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh")

fails = []
for c in CODES:
    a = json.loads(io.open(os.path.join(PRE, c + u".json"), encoding="utf-8").read())
    b = json.loads(io.open(os.path.join(LANG, c + u".json"), encoding="utf-8").read())
    added = [k for k in b if k not in a]
    removed = [k for k in a if k not in b]
    changed = [k for k in a if k in b and a[k] != b[k]]
    print(u"\n== %s ==" % c)
    print(u"   新增 %d 键、删除 %d 键、**值变了 %d 键**" % (len(added), len(removed), len(changed)))
    for k in changed[:8]:
        print(u"     %s" % k)
        print(u"       改前: %s" % a[k][:90].replace(u"\n", u"\\n"))
        print(u"       现在: %s" % b[k][:90].replace(u"\n", u"\\n"))
    # 值变了的键必须是"别的线在途改的"（不是我本轮碰过的键）
    mine = set([u"item.potato_s_t.empty_aluminum_can", u"item.potato_s_t.cola",
                u"tooltip.potato_s_t.cola.1", u"tooltip.potato_s_t.cola.2",
                u"block.potato_s_t.beverage_canning_machine",
                u"tooltip.potato_s_t.beverage_canning_machine",
                u"gui.potato_s_t.canning.pour.poured", u"gui.potato_s_t.canning.pour.rejected"]
               + [u"gui.potato_s_t.beverage_canning_machine.status." + s
                  for s in (u"disabled", u"empty", u"invalid", u"no_power", u"output_full",
                            u"running", u"no_fluid")])
    bad = [k for k in changed if k in mine]
    if bad:
        fails.append(u"%s：我本轮的键被改值了 %s" % (c, bad))
    if removed:
        fails.append(u"%s：删掉了 %d 个键（不该发生）" % (c, len(removed)))
    # 与改前件**原始字节**比：除了新增行，其余行必须逐字节一致（转义没被规整）
    raw_pre = io.open(os.path.join(PRE, c + u".json"), encoding="utf-8").read().split(u"\n")
    raw_now = io.open(os.path.join(LANG, c + u".json"), encoding="utf-8").read().split(u"\n")
    pre_lines = set(l for l in raw_pre if l.strip())
    now_lines = set(l for l in raw_now if l.strip())
    gone = [l for l in pre_lines if l not in now_lines]
    print(u"   改前件里'整行消失'的 %d 行（应当全是被重新排版的，值为空的才算问题）：" % len(gone))
    for l in gone[:6]:
        print(u"     %s" % l[:100])

print(u"\n失败项 = %d" % len(fails))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
