# -*- coding: utf-8 -*-
u"""_zf121_lang.py —— 合金冶炼炉那条 tooltip 的**脚注**改值（四语言，0.11 ZF121）

改的是 `tooltip.potato_s_t.alloy_smelter` 的**最后一行**（脚注）：
  「2 消耗槽 / 配方三条 / 只有三条配方的清单」→「4 消耗槽 / 配方四条 / 加上振金锭那条」。
**一个语言键都不加、不删、不挪**（键数仍是 454 —— 那个数并行那条线刚从 449 加上去 5 个），
所以没有任何"键数耦合"的往轮校验需要 retarget（§4.91 那条规矩本轮不触发）。

⚠ 为什么不 JSON 整份重写：这四份文件是 `2 空格缩进 + 冒号后 2 空格 + LF` 的手工排版。
整份 dump 一次会把**全部 454 行**都变成"脚本的口径"，diff 一片红、也没法证明
"只动了那一个值"。所以走**字面量替换**：先用 `json.dumps(现值)` 生成它在盘上的**逐字**写法，
确认全文只出现一次，再换成新值的字面量 —— 其余字节一个都不碰。

跑法：
    python build\\zftools\\_zf121_lang.py            # 只校验
    python build\\zftools\\_zf121_lang.py --write     # 落盘
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
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
BK = r"C:\PotatoST救援\zf121_pre"
BK_LANG = os.path.join(BK, r"src\main\resources\assets\potato_s_t\lang")

KEY = u"tooltip.potato_s_t.alloy_smelter"
LANGS = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]

NEW = {
    u"zh_cn": u'5 输入槽只收锭、3 输出槽、2 消耗槽（放配方点名要消耗的东西）；储能 32768 FE，'
              u'电只从接线口进。配方四条：轻质钛合金 / 硬质钛合金 / 星璨钢锭（下界合金+4 高碳钢+'
              u'钴+银+铜，另耗 1 深层钴矿石 + 1 末影水晶，12000 FE/t）/ 振金锭（硬质钛合金+'
              u'8 热力金属+2 高碳钢+3 银锭+12 金锭，另耗 1 粗振金+2 下界合金碎片，14500 FE/t）。',
    u"en_us": u'5 input slots that take ingots only, 3 output slots, 2 consumption slots '
              u'(they take whatever a recipe names as its consumable); 32768 FE of storage, and '
              u'power comes in through the port alone. Four recipes: Light Titanium Alloy / '
              u'Hard Titanium Alloy / Star Steel Ingot (netherite + 4 high carbon steel + cobalt + '
              u'silver + copper, plus 1 deepslate cobalt ore and 1 end crystal, 12000 FE/t) / '
              u'Vibranium Ingot (hard titanium alloy + 8 thermal metal + 2 high carbon steel + '
              u'3 silver ingots + 12 gold ingots, plus 1 raw vibranium + 2 netherite scraps, '
              u'14500 FE/t).',
    u"ja_jp": u'入力 5（インゴットのみ）/ 出力 3 / 消費 2（レシピが指定した消耗品を入れる）；'
              u'蓄電 32768 FE、電力は接続口からのみ。レシピ 4 種：軽質チタン合金 / 硬質チタン合金 / '
              u'星璨鋼インゴット（ネザライト+高炭素鋼×4+コバルト+銀+銅、さらに深層コバルト鉱石 1 + '
              u'エンドクリスタル 1、12000 FE/t）/ ヴィブラニウムインゴット（硬質チタン合金+'
              u'熱力金属×8+高炭素鋼×2+銀×3+金×12、さらに粗ヴィブラニウム 1 + ネザライトの欠片 2、'
              u'14500 FE/t）。',
    u"ru_ru": u'5 входных слотов только под слитки, 3 выходных, 2 расходных (туда кладётся то, '
              u'что рецепт называет расходником); буфер 32768 FE, энергия только через порт. '
              u'Четыре рецепта: лёгкий титановый сплав / твёрдый титановый сплав / слиток звёздной '
              u'стали (незерит + 4 высокоуглеродистая сталь + кобальт + серебро + медь, плюс '
              u'1 глубинная кобальтовая руда и 1 кристалл Края, 12000 FE/t) / слиток вибраниума '
              u'(твёрдый титановый сплав + 8 термальный металл + 2 высокоуглеродистая сталь + '
              u'3 серебряный слиток + 12 золотых слитков, плюс 1 необработанный вибраниум + '
              u'2 незеритовый скрап, 14500 FE/t).',
}


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)


def main(argv):
    do_write = "--write" in argv
    fails, done = [], 0
    out = {}
    for name in LANGS:
        p = os.path.join(LANG, name + u".json")
        text = read(p)
        data = json.loads(text)
        cur = data.get(KEY)
        if cur is None:
            fails.append(u"%s 里没有 %s" % (name, KEY))
            continue
        lines_old = cur.split(u"\n")
        lines_new = NEW[name].split(u"\n")
        if len(lines_new) != 1:
            fails.append(u"%s 新脚注里出现了换行" % name)
            continue
        if len(lines_old) != 2 and len(lines_old) < 2:
            fails.append(u"%s 现值不是「摆放图 + 脚注」两段以上（%d 行）" % (name, len(lines_old)))
            continue
        if lines_old[-1] == NEW[name]:
            print(u"  [跳过] %-6s 脚注已经是新的（幂等）" % name)
            done += 1
            out[p] = text
            continue
        lit_old = json.dumps(cur, ensure_ascii=False)
        if text.count(lit_old) != 1:
            fails.append(u"%s 的现值字面量在文件里出现 %d 次（应为 1）" % (name, text.count(lit_old)))
            continue
        new_value = u"\n".join(lines_old[:-1] + [NEW[name]])
        lit_new = json.dumps(new_value, ensure_ascii=False)
        for bad in (u'"',):
            if bad in NEW[name]:
                fails.append(u"%s 新脚注里有 ASCII 双引号（§4.x：中文串里不许出现）" % name)
        out[p] = text.replace(lit_old, lit_new, 1)
        print(u"  [改]   %-6s 脚注：配方三条 → 四条（末尾加振金锭那条）" % name)
        done += 1

    # ---- 反向自检（不管改没改都跑）----
    for name in LANGS:
        p = os.path.join(LANG, name + u".json")
        before = json.loads(read(os.path.join(BK_LANG, name + u".json")))
        after = json.loads(out.get(p) or read(p))
        gone = [k for k in before if k not in after]
        if gone:
            fails.append(u"%s 少了键：%s" % (name, gone[:4]))
        changed = [k for k in before if k in after and before[k] != after[k]]
        if changed != [KEY]:
            fails.append(u"%s 值变动的不止 %s：%s" % (name, KEY, changed))
        tip = after[KEY].split(u"\n")
        if len(tip) != len(before[KEY].split(u"\n")):
            fails.append(u"%s 脚注行数变了（%d → %d）"
                         % (name, len(before[KEY].split(u"\n")), len(tip)))
        if tip[:-1] != before[KEY].split(u"\n")[:-1]:
            fails.append(u"%s 的摆放图那几行被动过（_zf111/_zf55 会红）" % name)
        for must in (u"32768", u"12000", u"14500", u"58"):
            if must not in u"\n".join(tip):
                fails.append(u"%s 脚注里少了 %s" % (name, must))

    counts = {}
    for name in LANGS:
        p = os.path.join(LANG, name + u".json")
        counts[name] = len(json.loads(out.get(p) or read(p)))
    if len(set(counts.values())) != 1:
        fails.append(u"四语言键数不一致：%r" % counts)
    print(u"四语言键数：%s（本轮不加不减）" % u"、".join(u"%s=%d" % (k, v) for k, v in counts.items()))

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
