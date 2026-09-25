# -*- coding: utf-8 -*-
u"""_zf96_lang.py —— ZF96 给四份语言各加 **12 个键**（272 → 284）

做法（与往轮一致）：**只在文件末尾加行**，一个既有的键都不动（逐行比对自证）：
  ① 读原文 → 解析成有序字典（记下加之前的键集合与值）
  ② 断言 12 个新键一个都不存在
  ③ 最后一行（`}` 之前那行）补一个逗号，再把 12 行插进去
  ④ 写回（LF；4 空格缩进；`":` 后面**两个空格**，与既有行逐字对齐）
  ⑤ 复核：JSON 能解析、键数 = 284、**旧键的值逐个不变**

新增的 12 个键：
  block.potato_s_t.hydrodesulfurization_chamber
  item.potato_s_t.sulfur
  tooltip.potato_s_t.hydrodesulfurization_chamber
  gui.potato_s_t.hydrodesulfurization_chamber.status.{running,disabled,empty,material,output_full,no_hydrogen}
  gui.potato_s_t.hydrodesulfurization_chamber.pour.{empty,rejected}
  gui.potato_s_t.jei.no_energy

⚠ 本文件里**不许出现 ASCII 双引号**（脚本是 PowerShell 之外的纯 Python，问题不大），
但真正要守的是那条老规矩：中文串里要引号就用「」。
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
LANG_DIR = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
EXPECT_BEFORE = 272
EXPECT_AFTER = 284

KEYS = [
    "block.potato_s_t.hydrodesulfurization_chamber",
    "item.potato_s_t.sulfur",
    "tooltip.potato_s_t.hydrodesulfurization_chamber",
    "gui.potato_s_t.hydrodesulfurization_chamber.status.running",
    "gui.potato_s_t.hydrodesulfurization_chamber.status.disabled",
    "gui.potato_s_t.hydrodesulfurization_chamber.status.empty",
    "gui.potato_s_t.hydrodesulfurization_chamber.status.material",
    "gui.potato_s_t.hydrodesulfurization_chamber.status.output_full",
    "gui.potato_s_t.hydrodesulfurization_chamber.status.no_hydrogen",
    "gui.potato_s_t.hydrodesulfurization_chamber.pour.empty",
    "gui.potato_s_t.hydrodesulfurization_chamber.pour.rejected",
    "gui.potato_s_t.jei.no_energy",
]

# 四份文案：键 → 值（顺序与 KEYS 一致）。`\n` 在**文件里**要写成两个字符（反斜杠 + n），
# 所以 Python 串里用 \\n —— 与既有 tooltip 的写法逐字一致。
TEXT = {
    "zh_cn": [
        u"加氢脱硫反应仓",
        u"硫",
        (u"每批：16 个沥青 + 1000 mB 氢气 → 10 秒 → 1 个硫\n"
         u"氢气罐 4000 mB：可接管道/泵灌入，也可拿着装氢的高压气罐右键机器倒进去\n"
         u"左侧沥青槽只收沥青 · 有红石信号即停机（进度保留）\n"
         u"⚠ 这台机器不耗电"),
        u"正在加氢脱硫",
        u"已停机（红石信号）",
        u"沥青槽为空",
        u"沥青不够：每批要 16 个",
        u"输出槽已满，等待腾出位置",
        u"氢气不足：每批要 1000 mB（拿装氢的气罐右键机器可倒进去）",
        u"手里的容器是空的",
        u"倒不进去：%s（只收氢气；罐满 / 流体不对）",
        u"不需要电",
    ],
    "en_us": [
        u"Hydrodesulfurization Chamber",
        u"Sulfur",
        (u"Per batch: 16 Bitumen + 1000 mB hydrogen -> 10 s -> 1 Sulfur\n"
         u"Hydrogen tank holds 4000 mB: feed it with pipes/pumps, or right-click the machine with a "
         u"gas tank full of hydrogen to pour\n"
         u"The left slot takes bitumen only; a redstone signal stops it (progress is kept)\n"
         u"This machine uses no energy"),
        u"Reacting",
        u"Stopped (redstone signal)",
        u"Bitumen slot is empty",
        u"Not enough bitumen: 16 per batch",
        u"Output slot is full, waiting for room",
        u"Not enough hydrogen: 1000 mB per batch (right-click the machine with a tank of hydrogen to pour)",
        u"That container is empty",
        u"Cannot pour %s in (hydrogen only; tank full / wrong fluid)",
        u"No energy needed",
    ],
    "ja_jp": [
        u"加氢脱硫反応チャンバー",
        u"硫黄",
        (u"1 バッチ：瀝青 16 個 + 水素 1000 mB → 10 秒 → 硫黄 1 個\n"
         u"水素タンクは 4000 mB：配管／ポンプで注入、または水素入りガスタンクを持って右クリックで注げます\n"
         u"左のスロットは瀝青のみ · レッドストーン信号で停止（進捗は保持）\n"
         u"⚠ このマシンは電力を消費しません"),
        u"加氢脱硫中",
        u"停止中（レッドストーン信号）",
        u"瀝青スロットが空です",
        u"瀝青不足：1 バッチに 16 個",
        u"出力スロットが満杯です",
        u"水素不足：1 バッチに 1000 mB（水素入りタンクで右クリックすると注げます）",
        u"その容器は空です",
        u"%s を注げません（水素のみ／満杯・種類違い）",
        u"電力不要",
    ],
    "ru_ru": [
        u"Камера гидроочистки",
        u"Сера",
        (u"За партию: 16 битума + 1000 mB водорода → 10 с → 1 сера\n"
         u"Бак водорода — 4000 mB: подача трубами/насосом либо ПКМ баллоном с водородом по машине\n"
         u"Левый слот принимает только битум · сигнал редстоуна останавливает (прогресс сохраняется)\n"
         u"⚠ Машина не потребляет энергию"),
        u"Реакция",
        u"Остановлено (сигнал редстоуна)",
        u"Слот битума пуст",
        u"Недостаточно битума: 16 на партию",
        u"Выходной слот заполнен",
        u"Недостаточно водорода: 1000 mB на партию (ПКМ баллоном с водородом)",
        u"Этот контейнер пуст",
        u"Не удалось залить %s (только водород; бак полон / другая жидкость)",
        u"Энергия не нужна",
    ],
}

fails = []
examined = 0


def check(ok, msg):
    global examined
    examined += 1
    print((u"  [OK]   " if ok else u"  [FAIL] ") + msg)
    if not ok:
        fails.append(msg)


def line_for(key, value):
    # 与既有行逐字对齐：4 空格缩进 + `":` 后**两个空格**
    return u'    "%s":  %s,' % (key, json.dumps(value, ensure_ascii=False))


def main():
    for name in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"):
        fails_before = len(fails)
        path = os.path.join(LANG_DIR, name + u".json")
        raw = io.open(path, encoding="utf-8", newline=u"").read()
        before = json.loads(raw)
        # 幂等：已经加过就跳过（脚本可以被反复跑，不会加两遍）
        if len(before) == EXPECT_AFTER and all(k in before for k in KEYS):
            print(u"  [SKIP] %s：已经是 %d 键（本轮加过了）" % (name, EXPECT_AFTER))
            continue
        check(len(before) == EXPECT_BEFORE,
              u"%s：改前 %d 键（期望 %d）" % (name, len(before), EXPECT_BEFORE))
        dup = [k for k in KEYS if k in before]
        check(not dup, u"%s：12 个新键一个都还没存在（重复的 %d 个）" % (name, len(dup)))
        if len(before) != EXPECT_BEFORE or dup:
            continue

        # ⚠ 四份文件的"结尾换行"**不一致**（实测：zh_cn/en_us 没有、ja_jp/ru_ru 有）——
        #   第一版写死了"没有结尾换行"，ja_jp 当场被 json 解析器轰下来。
        #   所以这里先摘掉可能的结尾换行、处理完再按原样接回去（解析不过就不落盘）。
        had_trailing_nl = raw.endswith(u"\n")
        body = raw[:-1] if had_trailing_nl else raw
        lines = body.split(u"\n")
        check(lines[-1] == u"}", u"%s：末行是右花括号" % name)
        check(True, u"%s：原文%s结尾换行（按原样写回）" % (name, u"有" if had_trailing_nl else u"没有"))
        last_key_line = lines[-2]
        check(not last_key_line.rstrip().endswith(u","),
              u"%s：最后一个键那一行原本没有逗号（要补一个）" % name)
        lines[-2] = last_key_line.rstrip() + u","

        new_lines = [line_for(k, v) for (k, v) in zip(KEYS, TEXT[name])]
        # ⚠ 最后一行不能带逗号（第一版就是这样被 json 解析器当场轰下来的）
        new_lines[-1] = new_lines[-1][:-1]
        out = lines[:-1] + new_lines + lines[-1:]
        text = u"\n".join(out) + (u"\n" if had_trailing_nl else u"")

        # ⚠ 先解析、**过了才落盘**：解析不过就当场停，绝不把半成品写进资源目录
        after = json.loads(text)
        check(len(after) == EXPECT_AFTER, u"%s：新文本 %d 键（期望 %d）" % (name, len(after), EXPECT_AFTER))
        check(set(after) == set(before) | set(KEYS), u"%s：键集合 = 旧 + 12 个新键" % name)
        unchanged = [k for k in before if after.get(k) != before[k]]
        check(not unchanged, u"%s：旧键的值逐个不变（变了 %d 个）" % (name, len(unchanged)))
        if len(fails) != fails_before:
            check(False, u"%s：新文本有问题 ⇒ **不落盘**" % name)
            continue

        io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)

        # 落盘后重新读回来再核一遍（§10：备份/写盘都要核"副本自己"）
        back = json.loads(io.open(path, encoding="utf-8").read())
        check(back == after, u"%s：落盘后重新读回与写前一致（%d 键）" % (name, len(back)))
        check(io.open(path, encoding="utf-8", newline=u"").read().endswith(u"\n") == had_trailing_nl,
              u"%s：落盘后结尾换行与原文一致（原文%s）"
              % (name, u"有" if had_trailing_nl else u"没有"))
        # tooltip 的换行：文件里必须是**反斜杠 + n 两个字符**（JSON 转义），解析回来才是真换行
        check(u"\n" in TEXT[name][2] and u"\\n" in text,
              u"%s：tooltip 的换行在文件里是反斜杠 + n（解析后 %d 个真换行）"
              % (name, TEXT[name][2].count(u"\n")))
        # 逐行自证：去掉新加的行之后，剩下的每一行与原文逐字节相同（除了补的那一个逗号）
        old_lines = body.split(u"\n")
        kept = out[:len(out) - 1 - len(new_lines)] + out[len(out) - 1:]
        diff = [(i, a, b) for (i, (a, b)) in enumerate(zip(old_lines, kept)) if a != b]
        check(len(old_lines) == len(kept) and len(diff) == 1 and diff[0][0] == len(old_lines) - 2,
              u"%s：原文 %d 行里只有「最后一个键那行补逗号」一处变化（实际 %d 处）"
              % (name, len(old_lines), len(diff)))

    print()
    print(u"检查项 = %d" % examined)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"   - " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
