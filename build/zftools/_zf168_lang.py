# -*- coding: utf-8 -*-
u"""_zf168_lang.py —— ZF168 新增 1 个语言键 × 5 份 lang（只加键）。

键：`gui.potato_s_t.fluid_converter.pour.occupied`
    = 「目标罐里已经是**另一种**流体 ⇒ 告诉玩家先拿空容器把它装走再换样板」。
    用户实测「输出罐改不了」时缺的就是这句话（FluidTank 对异种流体一律拒收，必须先腾空）。

键数：620 → 621（lzh 622 → 623）。

跑法：python build\\zftools\\_zf168_lang.py [--write]
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
LANGDIR = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]
ANCHOR = u"block.potato_s_t.fluid_converter"
KEY = u"gui.potato_s_t.fluid_converter.pour.occupied"

V = {
    u"zh_cn": u"输出罐里已经是别的流体（%s）—— 手拿空容器右键机器就能把样板装走，然后再倒新的",
    u"en_us": u"the output tank already holds a different fluid (%s) - right-click the machine with an "
              u"empty container to take the sample out first, then pour the new one",
    u"ja_jp": u"出力タンクには既に別の流体（%s）が入っています——空の容器を持って右クリックすると"
              u"見本を汲み出せます。その後で新しい流体を入れてください",
    u"ru_ru": u"в выходном баке уже другая жидкость (%s) — щёлкните по машине с пустым контейнером, "
              u"чтобы слить образец, затем налейте новый",
    u"lzh": u"輸出罐中已有他流（%s）——手持空器右擊可先取樣本，而後注新者",
}


def main(argv):
    write = u"--write" in argv
    fails, notes = [], []
    for loc in LOCALES:
        p = os.path.join(LANGDIR, loc + u".json")
        text = io.open(p, encoding="utf-8", newline=u"").read()
        before = json.loads(text)
        if KEY in before:
            notes.append(u"%s：（已加过）%d 键" % (loc, len(before)))
            continue
        eol = u"\r\n" if u"\r\n" in text else u"\n"
        lines = text.split(eol)
        idx, ind = -1, u"  "
        for i, ln in enumerate(lines):
            if ln.strip().startswith(u'"%s":' % ANCHOR):
                idx, ind = i, ln[:len(ln) - len(ln.lstrip())]
                break
        if idx < 0:
            fails.append(u"%s：找不到锚点 %s" % (loc, ANCHOR))
            continue
        lines.insert(idx + 1, ind + u'"%s": %s,' % (KEY, json.dumps(V[loc], ensure_ascii=False)))
        new_text = eol.join(lines)
        if not new_text.endswith(eol):
            new_text += eol
        parsed = json.loads(new_text)
        if len(parsed) != len(before) + 1 or parsed[KEY] != V[loc]:
            fails.append(u"%s：写回后不一致" % loc)
            continue
        notes.append(u"%s：%d → %d 键" % (loc, len(before), len(parsed)))
        if write:
            io.open(p, "w", encoding="utf-8", newline=u"").write(new_text)
    print(u"模式：%s" % (u"落盘" if write else u"干跑（不写）"))
    for n in notes:
        print(u"  " + n)
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
