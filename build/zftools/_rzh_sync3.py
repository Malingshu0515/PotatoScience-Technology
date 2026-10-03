# -*- coding: utf-8 -*-
r"""_rzh_sync3.py —— 同步用户本轮改动（cola 两条 + 引力装置两条 + 配置三条）。

用户原话：「语言更新了一下仅同步 "tooltip.potato_s_t.cola.1": "肥宅快乐水"、
"tooltip.potato_s_t.cola.2": "饮用后给予正面效果"，以及新的配置文件语言键」。

⚠ 事实核对（翻之前查过代码，免得把错的翻进四语）：
  `ColaItem`：`HASTE_TICKS = 20*120`（急迫 120 秒）、`REGENERATION_TICKS = 20*3`（生命恢复 I 3 秒）、
  食物值 3 饥饿 / 9 饱和度、`usingConvertsTo(空铝罐)`（吃完返还空罐，走原版那条路）。
  ⇒ 用户把 `.1` 改成玩梗名、把 `.2` 改成「饮用后给予正面效果」。
  **两条旧描述本身仍然成立**（效果与返还都还在代码里），这一点已回报给用户；
  这里按用户写的中文翻，不下判断。

配置那三条（`black_hole.one_shot / pull_entities / void_damage` 的 tooltip）已由
`_rzh_cfg_polish.py` 一并收口，故本表只列剩下 6 键。

用法：`python build/zftools/_rzh_sync3.py`
"""
from __future__ import print_function
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")

T = {}

T[u"tooltip.potato_s_t.cola.1"] = {
    u"en_us": u"Gamer Fuel",
    u"ja_jp": u"肥満児の炭酸水",
    u"ru_ru": u"Газировка для домоседа",
    u"lzh": u"肥宅之樂水",
}

T[u"tooltip.potato_s_t.cola.2"] = {
    u"en_us": u"Grants positive effects when drunk",
    u"ja_jp": u"飲用すると良い効果を得る",
    u"ru_ru": u"Даёт положительные эффекты при употреблении",
    u"lzh": u"飲之則得正面之效",
}

T[u"tooltip.potato_s_t.gravity_device.one_shot.on"] = {
    u"en_us": u"Single-use item (can be disabled in the config)",
    u"ja_jp": u"使い切りの品（設定で無効にできる）",
    u"ru_ru": u"Одноразовый предмет (отключается в настройках)",
    u"lzh": u"一次性之物（可於設置關之）",
}

T[u"tooltip.potato_s_t.gravity_device.one_shot.off"] = {
    u"en_us": u"Reusable: consumes power only",
    u"ja_jp": u"再利用可：消費するのは電力だけ",
    u"ru_ru": u"Многоразовый: расходуется только энергия",
    u"lzh": u"可重複使用：僅耗電力",
}

T[u"potato_s_t.configuration.gravity_device.charge_seconds.tooltip"] = {
    u"en_us": u"How long right-click is held before the black hole is released (5-60, default 30 seconds).",
    u"ja_jp": u"右クリックを長押ししてからブラックホールが出るまでの秒数（5~60、既定 30 秒）。",
    u"ru_ru": u"Сколько держать ПКМ до появления чёрной дыры (5-60, по умолчанию 30 секунд).",
    u"lzh": u"長按右鍵幾息放出黑洞（5~60，默 30 息）。",
}

T[u"potato_s_t.configuration.gravity_device.capacity_fe.tooltip"] = {
    u"en_us": u"How much energy the gravity device holds (1,000,000-64,000,000, default 8,000,000).",
    u"ja_jp": u"重力装置が蓄えられる電力（1,000,000~64,000,000、既定 8,000,000）。",
    u"ru_ru": u"Сколько энергии вмещает гравитационное устройство (1 000 000-64 000 000, по умолчанию 8 000 000).",
    u"lzh": u"引力裝置能存幾電（1,000,000~64,000,000，默 8,000,000）。",
}


def read_val(loc, key):
    with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
        return json.load(f)[key]


def main():
    if u"zh_cn" in set(l for per in T.values() for l in per):
        raise SystemExit(u"[拒绝] 表里出现了 zh_cn")
    edits, lzh_pairs = [], []
    for key, per in sorted(T.items()):
        for loc, new in sorted(per.items()):
            old = read_val(loc, key)
            if old == new:
                continue
            if loc == u"lzh":
                lzh_pairs.append((key, old, new))
            else:
                edits.append((loc, key, old, new))

    import _rzh_fix_batch as fb
    fb.SUBSTITUTIONS = []
    fb.REGEX_SUBST = []
    fb.EDITS = edits
    print(u"待改 %d 条（lzh 另 %d 条）" % (len(edits), len(lzh_pairs)))
    rc = fb.main()
    if lzh_pairs:
        import _rzh_lzh_set as ls
        ls.apply(lzh_pairs, u"第三批同步")
    return rc


if __name__ == u"__main__":
    sys.exit(main())
