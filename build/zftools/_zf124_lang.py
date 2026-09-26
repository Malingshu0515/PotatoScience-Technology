# -*- coding: utf-8 -*-
u"""_zf124_lang.py —— ZF124：成就页签「新的开始！」→「PotatoS&T」（四语言）

用户原话：「把成就的 新的开始！这一分类改成 PotatoS&T」。

**改的是什么**：根成就 `new_beginning` 的标题键 `advancements.potato_s_t.new_beginning.title`。
成就界面里**每个模组一个页签**，页签的悬浮名就是它、页签图标来自根成就的 `display.icon`
⇒ 改这一个值，页签就叫 PotatoS&T 了（JSON 里写的是 `translate` 键，数据包不用动）。

**四语言都写成 `PotatoS&T`**：这是**商标名**（创造页标题 `itemGroup.potato_s_t` 四语言也一直是
`PotatoS&T`，本来就是不翻译的），所以 ja/ru 也不该硬翻 —— 与那条口径保持一致。

⚠ 只改**值**，不动键、不动行序、不动其他键（照 `_zf121_lang.py` 那套"字面量替换"：
先用 `json.dumps(现值)` 生成它在盘上的逐字写法，确认全文只出现一次，再换成新值的字面量）。

跑法：
    python build\\zftools\\_zf124_lang.py            # 只校验
    python build\\zftools\\_zf124_lang.py --write    # 落盘
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
BK = r"C:\PotatoST救援\zf124_pre\src\main\resources\assets\potato_s_t\lang"
KEY = u"advancements.potato_s_t.new_beginning.title"
NEW = u"PotatoS&T"
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]
# 改前那四个值（写在这里是为了"改错了能一眼看出来"，不是判据）
OLD_VALUES = {u"zh_cn": u"新的开始！", u"en_us": u"A New Beginning!",
              u"ja_jp": u"新たな始まり！", u"ru_ru": u"Новое начало!"}


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)


def main(argv):
    do_write = "--write" in argv
    fails, done, out = [], 0, {}
    for name in LOCALES:
        p = os.path.join(LANG, name + u".json")
        text = read(p)
        cur = json.loads(text).get(KEY)
        if cur is None:
            fails.append(u"%s 里没有 %s" % (name, KEY))
            continue
        if cur == NEW:
            print(u"  [跳过] %-6s 已经是 PotatoS&T（幂等）" % name)
            done += 1
            out[p] = text
            continue
        if cur != OLD_VALUES[name]:
            fails.append(u"%s 的现值不是我记录的那个（实际 %r，记录的是 %r）—— 先看一眼再改"
                         % (name, cur, OLD_VALUES[name]))
            continue
        lit_old = json.dumps(cur, ensure_ascii=False)
        if text.count(lit_old) != 1:
            fails.append(u"%s 的现值字面量在文件里出现 %d 次" % (name, text.count(lit_old)))
            continue
        out[p] = text.replace(lit_old, json.dumps(NEW, ensure_ascii=False), 1)
        print(u"  [改]   %-6s %r → %r" % (name, cur, NEW))
        done += 1

    # ---- 自检：键集合没变、其他值没动 ----
    for name in LOCALES:
        p = os.path.join(LANG, name + u".json")
        before = json.loads(read(os.path.join(BK, name + u".json")))
        after = json.loads(out.get(p) or read(p))
        gone = [k for k in before if k not in after]
        if gone:
            fails.append(u"%s 少了键：%s" % (name, gone[:4]))
        changed = [k for k in before if k in after and before[k] != after[k]]
        if changed != [KEY]:
            fails.append(u"%s 值变动的不止 %s：%s" % (name, KEY, changed))
    counts = {}
    for name in LOCALES:
        p = os.path.join(LANG, name + u".json")
        counts[name] = len(json.loads(out.get(p) or read(p)))
    if len(set(counts.values())) != 1:
        fails.append(u"四语言键数不一致：%r" % counts)
    print(u"四语言键数：%s（本轮不加不减）" % u"、".join(u"%s=%d" % (k, v) for k, v in counts.items()))
    # 与创造页标题一致（用户要的就是"跟创造页一样叫 PotatoS&T"）
    zh = json.loads(out.get(os.path.join(LANG, u"zh_cn.json"))
                    or read(os.path.join(LANG, u"zh_cn.json")))
    if zh.get(u"itemGroup.potato_s_t") != NEW:
        fails.append(u"创造页标题不是 %s（实际 %r）—— 用户要的是两边一致"
                     % (NEW, zh.get(u"itemGroup.potato_s_t")))
    else:
        print(u"  [自检] 与创造页标题一致：%s" % NEW)

    if fails:
        print(u"")
        print(u"失败 = %d（**一个字节都没写**）" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    if do_write:
        for p, text in out.items():
            write(p, text)
        print(u"落盘：%d 份语言文件" % len(out))
    else:
        print(u"（只校验，没落盘；加 --write 才写）")
    print(u"通过 = %d   失败 = 0" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
