# -*- coding: utf-8 -*-
u"""_zf192_lang.py —— ZF192 **唯一一个新增语言键**：空手放坍缩模式时那句"它开始吸取周围的一切了"。

为什么要它：原来那句话是 `message.potato_s_t.gravity.fired`（「它开始吸取 %s 了」），
%s 填的是副手方块的名字；**空手放**时没有方块可填 ⇒ 要么加这一个键，要么那句话没法说
（我不想拿"石头/空气"去糊弄 —— 那会当场说错"它在吸什么"）。

干跑：python build\\zftools\\_zf192_lang.py
落盘：python build\\zftools\\_zf192_lang.py --write
复验：python build\\zftools\\_zf192_lang.py --verify
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
FILES = [u"zh_cn.json", u"en_us.json", u"lzh.json", u"ja_jp.json", u"ru_ru.json"]

KEY = u"message.potato_s_t.gravity.fired.everything"
VALUES = {
    u"zh_cn": u"黑洞成形：它开始吸取周围的一切了",
    u"en_us": u"The black hole forms: it starts devouring everything around it",
    u"lzh": u"黑洞既成：始吸取周遭一切矣",
    u"ja_jp": u"ブラックホールが形成：周囲のすべてを吸い始めた",
    u"ru_ru": u"Чёрная дыра сформировалась: она начинает пожирать всё вокруг",
}
WANT_COUNT = {u"zh_cn.json": 691, u"en_us.json": 691, u"lzh.json": 693,
              u"ja_jp.json": 691, u"ru_ru.json": 691}


def dump(d, tail_nl):
    return json.dumps(d, ensure_ascii=False, indent=2) + (u"\n" if tail_nl else u"")


def main(argv):
    write = u"--write" in argv
    verify = u"--verify" in argv
    fails, loaded = [], {}
    for f in FILES:
        p = os.path.join(LANG, f)
        raw = io.open(p, encoding="utf-8", newline=u"").read()
        d = json.loads(raw)
        tail_nl = raw.endswith(u"\n")
        style_ok = (dump(d, tail_nl) == raw)
        print(u"%-12s 键 %d  回环自证 %s" % (f, len(d), u"OK" if style_ok else u"**不符**"))
        if not style_ok:
            fails.append(u"%s：原样回环自证不符（格式口径不对，拒绝写盘）" % f)
        loaded[f] = (d, tail_nl)

    if verify:
        sets = {}
        for f in FILES:
            d = loaded[f][0]
            sets[f] = set(d)
            if d.get(KEY) != VALUES[f[:-5]]:
                fails.append(u"%s：%s 的值不对（现在是 %r）" % (f, KEY, d.get(KEY)))
            if len(d) != WANT_COUNT[f]:
                fails.append(u"%s：键数 %d ≠ %d" % (f, len(d), WANT_COUNT[f]))
        base = sets[u"zh_cn.json"]
        for f in FILES:
            extra = sets[f] - base - {u"language.name", u"language.region"}
            missing = base - sets[f]
            if extra or missing:
                fails.append(u"%s 与 zh_cn 键集合不一致：多 %s 缺 %s"
                             % (f, sorted(extra)[:4], sorted(missing)[:4]))
        print(u"复验：%s" % (u"全绿" if not fails else u"红 %d" % len(fails)))
        for x in fails:
            print(u"  !! " + x)
        return 1 if fails else 0

    if fails:
        print(u"干跑红 ⇒ 不写盘")
        for x in fails:
            print(u"  !! " + x)
        return 1

    for f in FILES:
        d, tail_nl = loaded[f]
        if KEY in d:
            print(u"%-12s 已经有这个键（值 %r），跳过" % (f, d[KEY]))
            continue
        d[KEY] = VALUES[f[:-5]]
        print(u"%-12s +1 键 ⇒ %d 键：%s" % (f, len(d), d[KEY]))
        if write:
            io.open(os.path.join(LANG, f), "w", encoding="utf-8", newline=u"").write(dump(d, tail_nl))
    print(u"模式：%s ｜ 失败 = 0" % (u"落盘" if write else u"干跑"))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
