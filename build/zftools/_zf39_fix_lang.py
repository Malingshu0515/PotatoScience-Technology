# -*- coding: utf-8 -*-
"""ZF39 收尾修补：
① 把 4 个 lang 里的 `gui.potato_s_t.ebf.invalid` 改成 4 个占位符（层/排/格/期望方块），
   因为结构校验改成回传结构化数据了（Audit E 项禁止 Java 里硬编码中文）。
② 让 ModelCheck.py 认识 **`.mtl` 里的 map_Kd 引用** —— OBJ 模型的贴图不走模型 JSON，
   否则 `electric_blast_furnace.png` 会被误报成孤儿贴图。
"""
import io
import json
import os
import re

ROOT = r"E:\PotatoST"
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")

NEW = {
    "zh_cn": u"结构不成立：第 %s 层 第 %s 排 第 %s 格应为 %s",
    "en_us": u"Structure invalid: layer %s, row %s, column %s should be %s",
    "ja_jp": u"構造が不正です：%s 層目 %s 列目 %s 番目は %s である必要があります",
    "ru_ru": u"Конструкция неверна: слой %s, ряд %s, столбец %s — ожидается %s",
}

fail = []


def check(ok, msg):
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fail.append(msg)


print("== ① lang：invalid 改成 4 占位符 ==")
for code in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
    path = os.path.join(LANG, code + ".json")
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    data = json.loads(text)
    key = "gui.potato_s_t.ebf.invalid"
    old = data.get(key, "")
    if old == NEW[code]:
        check(True, "%s 已经是 4 占位符" % code)
        continue
    # 按行替换，保住 "key":  "value" 的双空格格式
    lines = text.split("\n")
    hit = 0
    for i, l in enumerate(lines):
        if ('"' + key + '"') in l:
            lines[i] = u'    "%s":  "%s"%s' % (key, NEW[code], "," if l.rstrip().endswith(",") else "")
            hit += 1
    check(hit == 1, "%s 找到并替换 %d 处" % (code, hit))
    out = "\n".join(lines)
    after = json.loads(out)          # 先校验再写
    check(after[key] == NEW[code], "%s 替换后值正确" % code)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)

print()
print(u"== ② ModelCheck.py：把 .mtl 里的 map_Kd 也算成'被引用' ==")
mc = os.path.join(ROOT, r"build\zftools\ModelCheck.py")
with io.open(mc, "r", encoding="utf-8") as f:
    src = f.read()

if "map_Kd" in src:
    check(True, "ModelCheck 已经认识 map_Kd，跳过")
else:
    # 找"扫 Java 收集引用"的那段，在它后面补一段扫 .mtl
    anchor = "referenced"
    print("    现有代码里出现 referenced 的行：")
    for i, l in enumerate(src.split("\n")):
        if anchor in l:
            print("      %4d: %s" % (i + 1, l.rstrip()))
    check(False, "需要人工指定插入点（见上面的行号）—— 这一步没做，请手工补")

print()
if fail:
    print("有 %d 项失败" % len(fail))
    raise SystemExit(1)
print("语言文件改完。")
