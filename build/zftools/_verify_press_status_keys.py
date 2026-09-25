# -*- coding: utf-8 -*-
"""核对：四种语言的液压机状态键都齐、且**不再借用**微型粉碎机的键。

这是"复用部件漏参数化"那类 bug 的机械化查法：
部件默认前缀是粉碎机的，所以**键本身都存在**，LangCheck 的键集一致性也照样通过 ——
只有"液压机这台机器的键"必须自己存在，才能在运行时显示对。
"""
import io
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
SUFFIXES = ["disabled", "empty", "invalid", "no_power", "output_full", "running"]
PREFIX = "gui.potato_s_t.hydraulic_press.status."

ok = True
for lang in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
    d = json.load(io.open("%s\\%s.json" % (LANG, lang), encoding="utf-8"))
    missing = [s for s in SUFFIXES if PREFIX + s not in d]
    print("%-8s 键数=%3d  液压机状态键 %s" % (lang, len(d), "齐" if not missing else "缺 " + str(missing)))
    ok &= not missing
    if lang == "zh_cn":
        for s in SUFFIXES:
            print("        %-12s %s" % (s, d[PREFIX + s]))
    # 顺手确认粉碎机那 6 个键还在（老调用点没被破坏）
    mc = [s for s in SUFFIXES if "gui.potato_s_t.micro_crusher.status." + s not in d]
    if mc:
        ok = False
        print("        [FAIL] 粉碎机状态键丢了：%s" % mc)

print("\n结论：", "四语言齐全，两条前缀互不干扰" if ok else "**有问题**")
sys.exit(0 if ok else 1)
