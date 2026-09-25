# -*- coding: utf-8 -*-
u"""_zf114_lang.py —— ZF114 四语言补键：星轨坠 + 粗振金 + 倒计时文案

用户原话里跟文案有关的只有两句：「快捷栏上方显示30s红色倒计时」「最后1s聊天栏显示 星轨坠使用者 坐标」，
其余（起手/取消/锁定/通报/下落）都是把机制讲清楚必需的，我照项目既有的语气写。

**为什么是"行插入"而不是 json.load + json.dump**：
本工程的 lang 文件是**排好序、4 空格缩进、冒号后两个空格**的手工排版，
`json.dump` 会把整份重新格式化 ⇒ 一次补键变成全文件 diff（档案 §4.7「汇合点文件只准加行」）。
所以这里逐行插：找到第一个比新键大的条目行，插在它前面；都没找到就追加到末尾，
并且**该补逗号才补**（§4.6：锚点自带逗号时别再补一个）。

三条会失败的断言（写完 `--verify` 再只读复核一遍，§4.28 的规矩）：
  ① 写盘**前**先 `json.loads` 一遍，解析不过就 raise，**一个字节都不落盘**；
  ② 四份语言新增的键集合必须完全一致、键数必须相等；
  ③ 同一个键在四语言里的 `%s` 占位符个数必须一致（LangCheck 也查这条，这里先自查）。

跑法：
    python build\\zftools\\_zf114_lang.py            # 只体检，不写盘
    python build\\zftools\\_zf114_lang.py --write     # 真写
    python build\\zftools\\_zf114_lang.py --verify    # 只读复核（独立于写盘逻辑，逐条打印）
"""
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
LANGS = ("zh_cn", "en_us", "ja_jp", "ru_ru")
BASE_KEYS = 417          # 动手前四份各自的键数（活体数字；写完要把往轮校验里的 417 一起改）

ENTRY = re.compile(u'^    "([^"]+)":  "')

# (键, zh, en, ja, ru)
DATA = [
    (u"gui.potato_s_t.starfall.countdown",
     u"★ 星轨坠 %s 秒 ★",
     u"★ Starfall Pendant %s s ★",
     u"★ スターフォール・ペンダント %s 秒 ★",
     u"★ Звёздный подвесок: %s с ★"),
    (u"gui.potato_s_t.starfall.falling",
     u"⚠ 陨石下落中 ⚠",
     u"⚠ Meteor falling ⚠",
     u"⚠ 隕石落下中 ⚠",
     u"⚠ Метеорит падает ⚠"),
    (u"item.potato_s_t.raw_vibranium",
     u"粗振金",
     u"Raw Vibranium",
     u"粗ヴィブラニウム",
     u"Необработанный вибраниум"),
    (u"item.potato_s_t.starfall_pendant",
     u"星轨坠",
     u"Starfall Pendant",
     u"スターフォール・ペンダント",
     u"Звёздный подвесок"),
    (u"message.potato_s_t.starfall.cancelled",
     u"星轨坠的召唤已取消",
     u"The starfall has been called off",
     u"スターフォールの召喚を取り消しました",
     u"Вызов звездопада отменён"),
    (u"message.potato_s_t.starfall.countdown",
     u"★ %s 的星轨坠：还剩 %s 秒",
     u"★ %s's starfall lands in %s s",
     u"★ %s のスターフォール：残り %s 秒",
     u"★ Звездопад (%s): осталось %s с"),
    (u"message.potato_s_t.starfall.incoming",
     u"⚠ 陨石正砸向 %s %s —— 抬头看",
     u"⚠ A meteor is falling toward %s %s - look up",
     u"⚠ 隕石が %s %s に向かって落下中 ― 見上げてください",
     u"⚠ Метеорит летит в %s %s — поднимите голову"),
    (u"message.potato_s_t.starfall.locked",
     u"已经锁定，取消不了了",
     u"Locked in - it can no longer be cancelled",
     u"すでにロックされています。取り消せません",
     u"Уже зафиксировано — отменить нельзя"),
    (u"message.potato_s_t.starfall.started",
     u"星轨坠开始牵引：30 秒后落地，10 秒内再右键一次可以取消",
     u"The starfall is gathering: impact in 30 s; right-click again within 10 s to cancel",
     u"スターフォールが降り始めます：30 秒後に着弾、10 秒以内ならもう一度右クリックで取り消せます",
     u"Звездопад начал вызов: удар через 30 с; отмена — правый клик в первые 10 с"),
    (u"message.potato_s_t.starfall.warning",
     u"⚠ %s 的星轨坠已锁定 %s %s %s —— 快离开那里！",
     u"⚠ %s's starfall is locked on %s %s %s - get away from there!",
     u"⚠ %s のスターフォールが %s %s %s にロックされました ― そこから離れてください！",
     u"⚠ Звездопад (%s) нацелен на %s %s %s — уходите оттуда!"),
    (u"tooltip.potato_s_t.starfall_pendant.1",
     u"右键：把陨石叫到你脚下。30 秒后它从 y=200 砸下来",
     u"Right-click: call a meteor down on your position. It falls from y=200 after 30 s",
     u"右クリック：自分の足元に隕石を呼びます。30 秒後に y=200 から落下します",
     u"Правый клик: вызвать метеорит на свою позицию. Он упадёт с y=200 через 30 с"),
    (u"tooltip.potato_s_t.starfall_pendant.2",
     u"前 10 秒可以再右键一次取消；之后锁定，全服都会看到倒计时与坐标",
     u"Right-click again within the first 10 s to cancel; after that it is locked and everyone sees the countdown and your coordinates",
     u"最初の 10 秒以内ならもう一度右クリックで取り消せます。以降はロックされ、全員にカウントダウンと座標が出ます",
     u"Отмена — повторный правый клик в первые 10 с; затем вызов фиксируется, и все видят отсчёт и ваши координаты"),
    (u"tooltip.potato_s_t.starfall_pendant.3",
     u"落地：7~20 威力爆炸（带火），并喷出一批粗矿 —— 威力越高，矿越好也越多",
     u"Impact: an explosion of power 7-20 (with fire) plus a spray of raw ores - the higher the power, the better and the more",
     u"着弾：威力 7〜20 の爆発（炎上あり）と粗鉱の飛散。威力が高いほど良質で多くなります",
     u"Удар: взрыв силой 7–20 (с огнём) и разлёт руды — чем выше сила, тем лучше и больше"),
    (u"tooltip.potato_s_t.starfall_pendant.4",
     u"· 7~12：粗铁 / 粗铜 · 13 以上：全部粗矿 · 15 以上：额外 3 个粗振金",
     u"· 7-12: raw iron / raw copper · 13+: any raw ore · 15+: 3 extra raw vibranium",
     u"· 7〜12：粗鉄 / 粗銅 · 13 以上：すべての粗鉱 · 15 以上：粗ヴィブラニウム ×3 追加",
     u"· 7–12: рудное железо / рудная медь · 13+: любая руда · 15+: ещё 3 рудного вибраниума"),
    (u"tooltip.potato_s_t.starfall_pendant.5",
     u"一共 4 点耐久，用一次少一点；不可附魔",
     u"4 uses in total; cannot be enchanted",
     u"耐久は 4 回分。エンチャント不可",
     u"Всего 4 применения; зачарование невозможно"),
]


def read(path):
    return io.open(path, encoding="utf-8").read()


def insert_entry(lines, key, value):
    u"""把一条键插到排序位置上（返回插入的行号）"""
    target = None
    last_entry = None
    for i, line in enumerate(lines):
        m = ENTRY.match(line)
        if not m:
            continue
        last_entry = i
        if target is None and m.group(1) > key:
            target = i
    new_line = u'    "%s":  "%s"' % (key, value)
    if target is not None:
        lines.insert(target, new_line + u",")
        return target
    if last_entry is None:
        raise ValueError(u"文件里找不到任何条目行：%s" % key)
    tail = lines[last_entry].rstrip()
    if not tail.endswith(u","):
        lines[last_entry] = tail + u","
    lines.insert(last_entry + 1, new_line)
    return last_entry + 1


def check_placeholders(values):
    counts = set(v.count(u"%s") for v in values)
    if len(counts) != 1:
        raise ValueError(u"占位符个数四语言不一致：%s" % values)
    for v in values:
        if u'"' in v:
            raise ValueError(u"文案里出现 ASCII 双引号（本项目一律用「」）：%s" % v)
    return counts.pop()


def main(argv):
    write = "--write" in argv
    verify = "--verify" in argv
    n_fail = 0

    if verify:
        print(u"=== 只读复核（独立于写盘逻辑）===")
        texts = dict((l, json.loads(read(os.path.join(LANG, l + u".json")))) for l in LANGS)
        for l in LANGS:
            print(u"   %-6s 键数 = %d" % (l, len(texts[l])))
        base = set(texts["zh_cn"].keys())
        for l in LANGS[1:]:
            if set(texts[l].keys()) != base:
                print(u"   [FAIL] %s 的键集合与 zh_cn 不一致" % l)
                n_fail += 1
        for key, zh, en, ja, ru in DATA:
            values = (zh, en, ja, ru)
            want = dict(zip(LANGS, values))
            for l in LANGS:
                got = texts[l].get(key)
                if got != want[l]:
                    print(u"   [FAIL] %s / %s\n          期望 %r\n          实际 %r" % (l, key, want[l], got))
                    n_fail += 1
            try:
                check_placeholders(values)
            except ValueError as exc:
                print(u"   [FAIL] %s" % exc)
                n_fail += 1
        print(u"   复核完成：失败 = %d（期望键 %d 个 × 四语言）" % (n_fail, len(DATA)))
        return 1 if n_fail else 0

    for key, zh, en, ja, ru in DATA:
        check_placeholders((zh, en, ja, ru))

    for l in LANGS:
        path = os.path.join(LANG, l + u".json")
        text = read(path)
        before = json.loads(text)                      # 解析不过就抛，绝不继续
        if len(before) != BASE_KEYS:
            print(u"   [警告] %s 现在是 %d 键，脚本头写的基线是 %d —— 说明有别的会话刚改过，"
                  u"请先把 BASE_KEYS 改成实测值" % (l, len(before), BASE_KEYS))
        lines = text.split(u"\n")
        added = []
        for key, zh, en, ja, ru in DATA:
            if key in before:
                continue                               # 幂等：已经有的不重复插
            insert_entry(lines, key, {u"zh_cn": zh, u"en_us": en, u"ja_jp": ja, u"ru_ru": ru}[l])
            added.append(key)
        new_text = u"\n".join(lines)
        after = json.loads(new_text)                   # ① 写盘前再解析一遍

        expect = set(before.keys()) | set(k for k, _, _, _, _ in DATA)
        if set(after.keys()) != expect:
            raise SystemExit(u"%s: 键集合对不上" % l)
        if len(after) != len(before) + len(added):
            raise SystemExit(u"%s: 键数对不上（%d -> %d，新增 %d）" % (l, len(before), len(after), len(added)))
        for key, zh, en, ja, ru in DATA:               # 值也要核，别只核键
            want = {u"zh_cn": zh, u"en_us": en, u"ja_jp": ja, u"ru_ru": ru}[l]
            if after[key] != want:
                raise SystemExit(u"%s: %s 的值不对：%r" % (l, key, after[key]))

        print(u"   %-6s %d -> %d 键（新增 %d）%s" % (l, len(before), len(after), len(added),
                                                 u"  [已写盘]" if write else u"  [仅体检]"))
        if write:
            io.open(path, "w", encoding="utf-8", newline=u"").write(new_text)

    print(u"完成。新增键集合（%d 个）：%s" % (len(DATA), u", ".join(k for k, _, _, _, _ in DATA)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
