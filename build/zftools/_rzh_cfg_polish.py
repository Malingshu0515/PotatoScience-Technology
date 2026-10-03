# -*- coding: utf-8 -*-
r"""_rzh_cfg_polish.py —— 配置说明按用户口径收口（去破折号、去口语备注、去废话词）。

用户口径：「不要用感叹号、破折号、括号解释和口语化备注。不要用"可以""能够"这类废话词。
句子要短，主谓宾清晰。……数据、参数、限定词必须准确。」

实测（`_rzh_cfg_probe.py`）31 条里只有 5 处违规，全在两条上：
  · `black_hole.scan_radius_blocks.tooltip`：zh 有「——」与「先想想 TPS」；
    en/ru/lzh 各有一个破折号。
  · `black_hole.one_shot.tooltip`：en 有「you can」，lzh 有「——」。
  · `black_hole.lifetime_seconds.tooltip` / `pull_entities.tooltip` /
    `void_damage.tooltip`：ru 用「—」当破折号。
数字与括号里的取值范围一律不动（那是数据，不是解释性括号）。

用法：`python build/zftools/_rzh_cfg_polish.py`
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

SCAN = u"potato_s_t.configuration.black_hole.scan_radius_blocks.tooltip"
LIFE = u"potato_s_t.configuration.black_hole.lifetime_seconds.tooltip"
PULL = u"potato_s_t.configuration.black_hole.pull_entities.tooltip"
VOID = u"potato_s_t.configuration.black_hole.void_damage.tooltip"
ONESHOT = u"potato_s_t.configuration.black_hole.one_shot.tooltip"

NEW = {
    SCAN: {
        u"zh_cn": u"以黑洞为中心、各轴 ±N 格（8~80，默认 40 = 5×5×5 区块）。每加一格，扫描体积按三次方增长。调大之前须先评估 TPS。",
        u"en_us": u"Each axis spans +/- N blocks around the hole (8-80, default 40 = 5x5x5 chunks). Each added block grows the scanned volume cubically. Raise it only after checking your TPS.",
        u"ja_jp": u"ブラックホールを中心に各軸 ±N ブロック（8~80、既定 40 = 5×5×5 チャンク）。1 増やすごとに走査体積は三乗で増える。大きくする前に TPS を確認すること。",
        u"ru_ru": u"По +/- N блоков на каждую ось вокруг дыры (8-80, по умолчанию 40 = 5x5x5 чанков). Каждый добавленный блок увеличивает объём сканирования в кубе. Повышайте только после проверки TPS.",
        u"lzh": u"以黑洞為心、各軸 ±N 格（8~80，默 40 = 5×5×5 區塊）。每加一格，所掃體積以三方增。調大之前須先量 TPS。",
    },
    LIFE: {
        u"ru_ru": u"Сколько секунд живёт чёрная дыра (5-120, по умолчанию 20). Чем дольше, тем больше блоков и тем выше нагрузка.",
    },
    PULL: {
        u"ru_ru": u"Притягивать ли существ (включая игроков) к сингулярности. Выкл: только блоки.",
    },
    VOID: {
        u"ru_ru": u"Получают ли сущности внутри горизонта событий (6 блоков) урон пустоты. Выкл: только притягивание.",
    },
    ONESHOT: {
        u"en_us": u"On: the device breaks after firing (the original behaviour). Off: only the energy bar is drained, and the device can be recharged and fired again.",
        u"lzh": u"開：放畢黑洞裝置當場損壞（舊行為）。關：只抽乾電力條，裝置留之，充上電可再放。",
    },
}


def read_val(loc, key):
    with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
        return json.load(f)[key]


def main():
    edits = []
    for key, per in sorted(NEW.items()):
        for loc, new in sorted(per.items()):
            old = read_val(loc, key)
            if old == new:
                continue
            edits.append((loc, key, old, new))

    import _rzh_fix_batch as fb
    fb.SUBSTITUTIONS = []
    fb.REGEX_SUBST = []
    fb.EDITS = edits
    print(u"待改 %d 条" % len(edits))
    return fb.main()


if __name__ == u"__main__":
    sys.exit(main())
