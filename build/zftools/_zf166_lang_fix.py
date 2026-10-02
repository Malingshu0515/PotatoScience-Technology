# -*- coding: utf-8 -*-
u"""_zf166_lang_fix.py —— ZF166 第二轮：把转化器的状态文案**改短**（只改值，键一个不动）。

为什么：那 8 条状态是画在 176×166 的小面板上的（居中一行），原来按"聊天栏诊断"的长度写
（带 `[流体转化器]` 前缀、最长 40 汉字）会两边溢出、还压住"物品栏"标签。
现在：**GUI 用短句**；聊天栏那侧由 `FluidConverterBlock.diagnose` 自己在前面拼上机器名
（复用 `block.potato_s_t.fluid_converter`，不新增键）。顺带把 `target_empty` 与 tooltip
改成"手倒"那套手势（样板只能由玩家亲手给）。

跑法：python build\\zftools\\_zf166_lang_fix.py [--write]
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
LANGDIR = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]

T = u"gui.potato_s_t.fluid_converter.tank."
S = u"gui.potato_s_t.fluid_converter.status."
BLOCK = u"block.potato_s_t.fluid_converter"
TIP = u"tooltip.potato_s_t.fluid_converter"

NEW = {
    u"zh_cn": {
        TIP: u"把输入罐里的流体按同名 c: 标签 1:1 转成输出罐里那一种。两罐各 5000 mB，50 mB/t、"
             u"30 FE/t，储能 2000 FE。\\n手拿装着目标流体的容器右键机器 = 倒进输出罐（设样板）；"
             u"潜行右键 = 倒进输入罐；空手潜行右键 = 逐条诊断。",
        T + u"input": u"输入",
        T + u"output": u"输出（样板）",
        S + u"input_empty": u"输入罐空 —— 没有东西可转",
        S + u"target_empty": u"输出罐空 —— 手拿目标流体右键机器设样板",
        S + u"same_fluid": u"两边同种流体 —— 不用转",
        S + u"no_shared_tag": u"没有共同的 c: 标签（%s / %s）",
        S + u"output_full": u"输出罐满了",
        S + u"no_power": u"缺电（每 tick %s FE，现有 %s FE）",
        S + u"running": u"正在转：%s → %s（%s mB/t）",
        S + u"idle": u"待机",
    },
    u"en_us": {
        TIP: u"Converts the input tank's fluid 1:1 into the fluid in the output tank, if they share "
             u"a c: tag. 5,000 mB per tank, 50 mB/t, 30 FE/t, 2,000 FE buffer.\\nRight-click the "
             u"machine holding a container of the target fluid = pour into the output tank (the "
             u"sample); sneak-right-click = pour into the input tank; sneak-right-click empty-handed "
             u"= diagnosis.",
        T + u"input": u"Input",
        T + u"output": u"Output (sample)",
        S + u"input_empty": u"input tank empty - nothing to convert",
        S + u"target_empty": u"output tank empty - right-click with the target fluid to set a sample",
        S + u"same_fluid": u"same fluid on both sides - nothing to convert",
        S + u"no_shared_tag": u"no shared c: tag (%s / %s)",
        S + u"output_full": u"output tank full",
        S + u"no_power": u"no power (%s FE/t, %s FE left)",
        S + u"running": u"converting: %s -> %s (%s mB/t)",
        S + u"idle": u"idle",
    },
    u"ja_jp": {
        TIP: u"入力タンクの流体を、同じ c: タグを持つ出力タンクの流体へ 1:1 で変換します。各タンク "
             u"5,000 mB、50 mB/t、30 FE/t、蓄電 2,000 FE。\\n目標の流体を入れた容器を持って右クリック "
             u"= 出力タンクへ注入（見本を設定）。スニーク右クリック = 入力タンクへ注入。"
             u"素手でスニーク右クリック = 診断。",
        T + u"input": u"入力",
        T + u"output": u"出力（見本）",
        S + u"input_empty": u"入力タンクが空——変換するものがありません",
        S + u"target_empty": u"出力タンクが空——目標の流体を持って右クリックで見本を設定",
        S + u"same_fluid": u"両側とも同じ流体——変換不要",
        S + u"no_shared_tag": u"共通の c: タグがありません（%s / %s）",
        S + u"output_full": u"出力タンクが満杯",
        S + u"no_power": u"電力不足（毎 tick %s FE、残り %s FE）",
        S + u"running": u"変換中：%s → %s（%s mB/t）",
        S + u"idle": u"待機中",
    },
    u"ru_ru": {
        TIP: u"Преобразует жидкость входного бака 1:1 в жидкость выходного бака, если у них общий "
             u"тег c:. По 5 000 mB на бак, 50 mB/т, 30 FE/т, буфер 2 000 FE.\\nПравый клик по машине "
             u"с контейнером нужной жидкости = налить в выходной бак (образец); присев и щёлкнув — "
             u"во входной бак; присев с пустой рукой — диагностика.",
        T + u"input": u"Вход",
        T + u"output": u"Выход (образец)",
        S + u"input_empty": u"входной бак пуст — преобразовывать нечего",
        S + u"target_empty": u"выходной бак пуст — щёлкните с нужной жидкостью, чтобы задать образец",
        S + u"same_fluid": u"с обеих сторон одна жидкость — преобразование не нужно",
        S + u"no_shared_tag": u"нет общего тега c: (%s / %s)",
        S + u"output_full": u"выходной бак полон",
        S + u"no_power": u"нет энергии (%s FE/т, осталось %s FE)",
        S + u"running": u"преобразование: %s → %s (%s mB/т)",
        S + u"idle": u"ожидание",
    },
    u"lzh": {
        TIP: u"以輸入罐之流體，依同名 c: 標籤，一比一化為輸出罐中者。兩罐各五千毫，每秒五十毫、"
             u"每刻三十 FE，儲能二千 FE。\\n手持盛目標流體之器右擊＝注入輸出罐（立樣本）；"
             u"潛行右擊＝注入輸入罐；空手潛行右擊＝逐條診斷。",
        T + u"input": u"輸入",
        T + u"output": u"輸出（樣本）",
        S + u"input_empty": u"輸入罐空——無可轉者",
        S + u"target_empty": u"輸出罐空——手持目標流體右擊以立樣本",
        S + u"same_fluid": u"兩罐同流——無須轉",
        S + u"no_shared_tag": u"無共通之 c: 標籤（%s ／ %s）",
        S + u"output_full": u"輸出罐已滿",
        S + u"no_power": u"乏電（每刻 %s FE，餘 %s FE）",
        S + u"running": u"方轉：%s → %s（每秒 %s 毫）",
        S + u"idle": u"待機",
    },
}


def main(argv):
    write = u"--write" in argv
    fails, notes = [], []
    for loc in LOCALES:
        p = os.path.join(LANGDIR, loc + u".json")
        text = io.open(p, encoding="utf-8", newline=u"").read()
        eol = u"\r\n" if u"\r\n" in text else u"\n"
        before = json.loads(text)
        lines = text.split(eol)
        changed = 0
        for i, ln in enumerate(lines):
            s = ln.strip()
            for key, val in NEW[loc].items():
                if s.startswith(u'"%s":' % key):
                    ind = ln[:len(ln) - len(ln.lstrip())]
                    lines[i] = ind + u'"%s": %s,' % (key, json.dumps(val, ensure_ascii=False))
                    changed += 1
        new_text = eol.join(lines)
        parsed = json.loads(new_text)
        if len(parsed) != len(before):
            fails.append(u"%s：键数变了 %d -> %d" % (loc, len(before), len(parsed)))
            continue
        if changed != len(NEW[loc]):
            fails.append(u"%s：只改到 %d 条（应 %d）" % (loc, changed, len(NEW[loc])))
            continue
        for k, v in NEW[loc].items():
            if parsed[k] != v:
                fails.append(u"%s：%s 没写对" % (loc, k))
        notes.append(u"%s：改了 %d 条值（键数仍 %d）" % (loc, changed, len(parsed)))
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
