# -*- coding: utf-8 -*-
"""从**已打包的 release jar** 里读出 lang，核对两条 tooltip 就是新文案。

为什么要从 jar 里读：源码改了不等于产物改了（§4.21 的教训）。
"""
import io
import json
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
JAR = r"E:\PotatoST\release\PotatoST-0.10.jar"
KEYS = ["tooltip.potato_s_t.hydraulic_press", "tooltip.potato_s_t.solar_panel"]
NEEDLES = {
    "tooltip.potato_s_t.hydraulic_press": ["耗电 400 FE/t，3 秒产出一块板。", "配方一览见 JEI。"],
    "tooltip.potato_s_t.solar_panel": ["雨天出力降至 60%，雷暴降至 20%。", "正上方须为空气或无色玻璃。"],
}
# 旧文案里不该再出现的口语痕迹
STALE = ["不会吞产物", "别的 mod 的锭也能用", "储能上限 = 块数", "都不行", "查看并联数量"]

z = zipfile.ZipFile(JAR)
data = json.loads(z.read("assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
ok = True
for key in KEYS:
    tip = data[key]
    print("== %s ==" % key)
    print(tip)
    for needle in NEEDLES[key]:
        hit = needle in tip
        ok &= hit
        print("   [%s] 含 %r" % ("OK" if hit else "FAIL", needle))
    for bad in STALE:
        if bad in tip:
            ok = False
            print("   [FAIL] 还留着旧口语：%r" % bad)
    print()
print("键数 =", len(data))
print("结论：", "jar 里的改前文案都换掉了" if ok else "**还有问题**")
sys.exit(0 if ok else 1)
