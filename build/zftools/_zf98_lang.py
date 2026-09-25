# -*- coding: utf-8 -*-
u"""_zf98_lang.py —— ZF98：把流体泵的 tooltip 改写成新行为（**改值、不增减键**）

泵从"内部罐中转"改成"只做传输、优先送目标收得下的流体" ⇒ 这句话要跟着改口：
补上「泵本身不存液体」与「只送目标收得下的流体（收不下的不抽）」。

做法（照 ZF96/ZF97 那两条规矩：**先探测格式、先解析、过了才落盘**）：
  ① 只在**那一行**上动手：把以 `    "tooltip.potato_s_t.fluid_pump":` 开头的整行换成新行
  ② 其余每一行**逐字节不动**（改完逐行比对自证）
  ③ 先在内存里 `json.loads`，过了才写盘；写完读回来核键数与四份一致性
  ④ 幂等：已经是新值就跳过

⚠ 本轮**键数不变**（303 → 303）⇒ 所有往轮"键数 = 303"的断言都不用改。
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
KEY = u"tooltip.potato_s_t.fluid_pump"
EXPECT_KEYS = 303

NEW = {
    "zh_cn": (u"正面为输入、背面为输出；只有前/后能接管道。\n"
              u"泵本身不存液体：抽出来的那一笔当场送进目标容器。\n"
              u"只送目标收得下的流体（目标收不下的，一滴都不抽）。\n"
              u"右键打开界面调节速率（0% - 800%）。"),
    "en_us": (u"Front face is the input, back face is the output; pipes only attach to the front/back.\n"
              u"The pump stores no fluid itself: whatever it pulls out goes straight into the "
              u"destination.\n"
              u"It only moves fluids the destination accepts (anything it refuses is left in the "
              u"source).\n"
              u"Right-click to configure the rate (0% - 800%)."),
    "ja_jp": (u"正面が入力、背面が出力です。パイプは前後面にのみ接続できます。\n"
              u"ポンプ自体は液体を溜めません：吸い出した分はその場で送り先へ入ります。\n"
              u"送り先が受け取れる液体だけを送ります（受け取れないものは吸い出しません）。\n"
              u"右クリックで画面を開き速度を調整します（0% - 800%）。"),
    "ru_ru": (u"Передняя грань — вход, задняя — выход; трубы подключаются только спереди и сзади.\n"
              u"Насос сам не хранит жидкость: всё, что он откачал, сразу уходит в приёмник.\n"
              u"Он перекачивает только те жидкости, которые приёмник принимает (остальные "
              u"остаются в источнике).\n"
              u"ПКМ открывает интерфейс для настройки скорости (0% - 800%)."),
}

fails = []
examined = 0


def check(ok, msg):
    global examined
    examined += 1
    print((u"  [OK]   " if ok else u"  [FAIL] ") + msg)
    if not ok:
        fails.append(msg)


def main():
    new_line = {n: u'    "%s":  %s,' % (KEY, json.dumps(v, ensure_ascii=False)) for n, v in NEW.items()}
    for name in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"):
        fails_before = len(fails)
        path = os.path.join(LANG_DIR, name + u".json")
        raw = io.open(path, encoding="utf-8", newline=u"").read()
        data = json.loads(raw)
        check(len(data) == EXPECT_KEYS, u"%s：键数 %d（期望 %d，本轮不增减键）"
              % (name, len(data), EXPECT_KEYS))
        if data.get(KEY) == NEW[name]:
            print(u"  [SKIP] %s：已经是新文案" % name)
            continue
        check(KEY in data, u"%s：旧键在" % name)

        had_nl = raw.endswith(u"\n")
        body = raw[:-1] if had_nl else raw
        lines = body.split(u"\n")
        hits = [i for i, ln in enumerate(lines) if ln.startswith(u'    "%s"' % KEY)]
        check(len(hits) == 1, u"%s：这个键在文件里正好一行（命中 %d 行）" % (name, len(hits)))
        if len(hits) != 1 or len(fails) != fails_before:
            continue
        idx = hits[0]
        old_line = lines[idx]
        lines[idx] = new_line[name]
        text = u"\n".join(lines) + (u"\n" if had_nl else u"")

        after = json.loads(text)                     # ⚠ 先解析、过了才落盘
        check(after.get(KEY) == NEW[name], u"%s：新文本里这句已是新文案" % name)
        check(len(after) == EXPECT_KEYS and set(after) == set(data),
              u"%s：键集合与键数都没变（%d）" % (name, len(after)))
        changed = [k for k in data if after.get(k) != data[k]]
        check(changed == [KEY], u"%s：**只有这一句**的值变了（实际 %s）" % (name, changed))
        if len(fails) != fails_before:
            check(False, u"%s：新文本有问题 ⇒ **不落盘**" % name)
            continue

        io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
        back = json.loads(io.open(path, encoding="utf-8").read())
        check(back == after, u"%s：落盘后重新读回与写前一致" % name)
        new_body = (back and io.open(path, encoding="utf-8", newline=u"").read())
        new_lines = (new_body[:-1] if new_body.endswith(u"\n") else new_body).split(u"\n")
        check(len(new_lines) == len(lines), u"%s：行数不变（%d）" % (name, len(lines)))
        others = [(i, a, b) for (i, (a, b)) in enumerate(zip(lines, new_lines))
                  if i != idx and a != b]
        check(not others, u"%s：除那一行外逐字节未动（变了 %d 行）" % (name, len(others)))

    print()
    print(u"检查项 = %d" % examined)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"   - " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
