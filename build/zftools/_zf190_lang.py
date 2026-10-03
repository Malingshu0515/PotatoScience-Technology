# -*- coding: utf-8 -*-
u"""_zf190_lang.py —— ZF190 **唯一一个新增语言键**：第三个模式的显示名。

用户原话：「语言键都不需要改和加（**除了显示模式的**）」⇒ 只加
`message.potato_s_t.gravity.mode.collapse`（红色是代码里 withStyle 上的色，不是文案），
其余一个字不动。五语种必须键齐。

干跑：python build\\zftools\\_zf190_lang.py
落盘：python build\\zftools\\_zf190_lang.py --write
复验：python build\\zftools\\_zf190_lang.py --verify
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
FILES = [u"zh_cn.json", u"en_us.json", u"lzh.json", u"ja_jp.json", u"ru_ru.json"]

KEY = u"message.potato_s_t.gravity.mode.collapse"
VALUES = {
    u"zh_cn": u"坍缩模式-危险",
    u"en_us": u"Collapse mode - DANGER",
    u"lzh": u"坍縮之式-危",
    u"ja_jp": u"崩壊モード - 危険",
    u"ru_ru": u"Режим коллапса - ОПАСНО",
}
WANT_COUNT = {u"zh_cn.json": 690, u"en_us.json": 690, u"lzh.json": 692,
              u"ja_jp.json": 690, u"ru_ru.json": 690}


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
                fails.append(u"%s 与 zh_cn 键集合不一致：多 %s 缺 %s" % (f, sorted(extra)[:4], sorted(missing)[:4]))
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
