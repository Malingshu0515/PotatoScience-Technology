# -*- coding: utf-8 -*-
u"""_zf137_lang.py —— 把"头盔给夜视 I（4 s）"写进四语言的星璨钢套说明

用户原话：「星璨钢头盔穿戴加个夜视效果 1级 4s」。

**只改值、不加键** ⇒ 不触发"语言键数是活体数字"那条链（那要改十几份校验器，§4.64）。
做法：把新句子接在 `tooltip.potato_s_t.star_steel_set` 的**第一行末尾**
（第一行正是"每件在夜晚获得抗性提升 I / 夜晚装备耐久不消耗"，夜视是同一档"只头盔"的东西）。

每条都核：
  ① 键在、值非空、**键数一个没变**；
  ② 改完 JSON 解析得开、四语言键集合仍完全一致；
  ③ 新句子里确实有该语言的"夜视"词（少一种语言就是玩家切语言后看不到这条）。

跑法：
    python build/zftools/_zf137_lang.py            # 只体检
    python build/zftools/_zf137_lang.py --write
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
LANG = os.path.join(PROJ, r"src\main\resources\assets\potato_s_t\lang")
KEY = u"tooltip.potato_s_t.star_steel_set"

# (语言文件, 追加到第一行末尾的句子, 这一句里必须出现的"夜视"词)
SUFFIX = [
    (u"zh_cn.json", u"头盔还额外给夜视 I：每次 4 秒，戴着就一直续。", u"夜视"),
    (u"en_us.json", u" The helmet also grants Night Vision I (4 s at a time, topped up while worn).",
     u"Night Vision"),
    (u"ja_jp.json", u" ヘルメットは追加で暗視 I を付与します（1 回 4 秒、装着中は途切れず更新）。", u"暗視"),
    (u"ru_ru.json", u" Шлем вдобавок даёт Ночное зрение I (по 4 секунды, продлевается, пока он надет).",
     u"Ночное зрение"),
]

fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def main(argv):
    write = u"--write" in argv
    before = {}
    after = {}
    for name, suffix, word in SUFFIX:
        p = os.path.join(LANG, name)
        raw = read(p)
        before[name] = json.loads(raw)
        text = before[name].get(KEY, u"")
        if not text:
            fails.append(u"%s：没有 %s" % (name, KEY))
            continue
        if word in text:
            print(u"  [SKIP] %s：说明里已经有「%s」了（重复跑，不写第二遍）" % (name, word))
            after[name] = before[name]
            continue
        first, sep, rest = text.partition(u"\n")
        new_text = first + suffix + (sep + rest if sep else u"")
        if not write:
            print(u"  [将改] %s：第一行末尾 + 「%s」" % (name, suffix.strip()[:56]))
            after[name] = dict(before[name], **{KEY: new_text})
            continue
        # ⚠ 只重写**那一行**，不要 `json.dumps(整个文件)` ——
        #   那会把缩进从 2 空格改成 4 空格、把 `":  "` 的双空格改成单空格，
        #   整份文件全变（LangCheck/JsonCheck 之外还会把 diff 撑爆）。
        #   口径与 `_zf120_lang.py` 一致：一行一条 `  "键":  值,`。
        lines = raw.split(u"\n")
        idx = [i for i, l in enumerate(lines) if l.startswith(u'  "%s":' % KEY)]
        if len(idx) != 1:
            fails.append(u"%s：`%s` 那一行命中 %d 次（应为 1）" % (name, KEY, len(idx)))
            continue
        lines[idx[0]] = u'  "%s":  %s,' % (KEY, json.dumps(new_text, ensure_ascii=False))
        out = u"\n".join(lines)
        # ⚠ 先算好整份文本、**再**以 "w" 打开（§4.99：open(w) 与 read() 写在同一行会先截断）
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(out)
        after[name] = json.loads(read(p))
        print(u"  [写出] %s" % name)

    print(u"")
    for name, suffix, word in SUFFIX:
        if name not in after:
            continue
        t = after[name]
        check = (t.get(KEY, u"").find(word) >= 0)
        ok = check and len(t) == len(before[name])
        if not ok:
            fails.append(u"%s：新句子/键数不对（有夜视词=%s，键数 %d → %d）"
                         % (name, check, len(before[name]), len(t)))
        print(u"  [%s] %-12s 键数 %d（未变）  说明里有「%s」%s"
              % (u"OK" if ok else u"FAIL", name, len(t), word, u"" if ok else u"  ← 有问题"))

    sets = {n: set(t) for n, t in after.items()}
    if sets:
        base = sets[sorted(sets)[0]]
        for n, s in sets.items():
            if s != base:
                fails.append(u"%s 的键集合与 %s 不一致" % (n, sorted(sets)[0]))
        print(u"  [%s] 四语言键集合仍完全一致（%d 键）"
              % (u"OK" if all(s == base for s in sets.values()) else u"FAIL", len(base)))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
