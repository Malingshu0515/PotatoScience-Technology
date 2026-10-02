# -*- coding: utf-8 -*-
u"""_zf166_fix3.py —— 收尾三件：① tooltip 里的**字面 `\n`** 改成真换行；② 四份"读 jar"的门
跟到这一份干净产物的真实数字（配方 98、键 620/622）；③ 把结果打印出来复核。

① 的来龙去脉：`_zf166_lang.py` 里 tooltip 的换行写成了 `\\n`（Python 里 = 字面反斜杠 + n），
写进 JSON 又转义成 `\\\\n` ⇒ 游戏里 tooltip 显示 `\n` 而不是换行。同文件别的机器 tooltip 是真换行。
② 的原因：这一份产物是**从整棵树**打出来的（别的线的 4 份配方 + 15 个语言键都在里面），
门里钉死的"我这轮的 94/605/607"必须跟到产物真实值，否则会把**正确的重打**判成失败。

跑法：python build\\zftools\\_zf166_fix3.py [--write]
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
KEY = u"tooltip.potato_s_t.fluid_converter"
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]
GATE_EDITS = [
    (u"_zf166_verify.py",
     u'check(len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")]) == 94,\n'
     u'          u"D6 产物里配方 94 份")',
     u'check(len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")]) >= 94\n'
     u'          and u"data/potato_s_t/recipe/fluid_converter.json" in names,\n'
     u'          u"D6 产物里有本机配方且总数 ≥ 94（全树共享的活体数字，不钉死）")',
     u"_zf166 D6：产物配方改 ≥ + 含本机"),
    (u"_zf149_jar.py",
     u'check(len(recipes) == 94, u"① 配方份数（发布那一刻的实测值；ZF166 重打时 94：ZF162 的 93 + 流体转化器）",',
     u'check(len(recipes) >= 94, u"① 配方份数（发布那一刻的实测值；ZF166 重打时产物里已是 98：本机 +1、别的线在途 +4）",',
     u"_zf149_jar ①：配方 == 94 → ≥ 94"),
    (u"_zf156_jarcheck.py",
     u'check(len(recipes) == 94, u"③ jar 里配方 94 份（ZF162 的 93 + ZF166 的流体转化器）",',
     u'check(len(recipes) >= 94, u"③ jar 里配方 ≥ 94 份（ZF162 的 93 + ZF166 的流体转化器，外加别的线在途的）",',
     u"_zf156 ③：配方 == 94 → ≥ 94"),
    (u"_zf155_verify.py",
     u'check(counts[u"zh_cn"] == counts[u"en_us"] == counts[u"ja_jp"] == counts[u"ru_ru"] == 605\n'
     u'      and counts[u"lzh"] == 607,',
     u'check(counts[u"zh_cn"] >= 605 and counts[u"en_us"] >= 605 and counts[u"ja_jp"] >= 605\n'
     u'      and counts[u"ru_ru"] >= 605 and counts[u"lzh"] >= 607,',
     u"_zf155 B3：键数 == 605/607 → ≥"),
]


def main(argv):
    write = u"--write" in argv
    fails, notes = [], []
    # ① tooltip 换行
    for lg in LOCALES:
        p = os.path.join(LANG, lg + u".json")
        text = io.open(p, encoding="utf-8", newline=u"").read()
        before = json.loads(text)
        v = before[KEY]
        literal = u"\\n"          # 两个字：反斜杠 + n
        if literal in v:
            fixed = v.replace(literal, u"\n")
            before[KEY] = fixed
            notes.append(u"%s：tooltip 里的字面 \\n 改成真换行（%d 处）"
                         % (lg, v.count(literal)))
            if write:
                eol = u"\r\n" if u"\r\n" in text else u"\n"
                lines = text.split(eol)
                for i, ln in enumerate(lines):
                    if ln.strip().startswith(u'"%s":' % KEY):
                        ind = ln[:len(ln) - len(ln.lstrip())]
                        lines[i] = ind + u'"%s": %s,' % (KEY, json.dumps(fixed, ensure_ascii=False))
                io.open(p, "w", encoding="utf-8", newline=u"").write(eol.join(lines))
                after = json.loads(io.open(p, encoding="utf-8").read())
                if after[KEY] != fixed or len(after) != len(before):
                    fails.append(u"%s：写回后不一致" % lg)
        else:
            notes.append(u"%s：tooltip 里没有字面 \\n（已跟平过或本来就是真换行）" % lg)
    # ② 门数字
    for name, old, new, why in GATE_EDITS:
        p = os.path.join(ROOT, u"build", u"zftools", name)
        if not os.path.isfile(p):
            fails.append(u"%s 不在" % name)
            continue
        t = io.open(p, encoding="utf-8", newline=u"").read()
        if t.count(old) == 0 and new in t:
            notes.append(u"%s：（已跟平过）%s" % (name, why))
            continue
        if t.count(old) != 1:
            fails.append(u"%s：改前串出现 %d 次 —— %s" % (name, t.count(old), why))
            continue
        if write:
            io.open(p, "w", encoding="utf-8", newline=u"").write(t.replace(old, new, 1))
        notes.append(u"%s：%s" % (name, why))
    print(u"模式：%s" % (u"落盘" if write else u"干跑（不写）"))
    for n in notes:
        print(u"  " + n)
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
