# -*- coding: utf-8 -*-
"""_zf71_javadoc_dump.py —— 把几台机器的类注释头抄出来（写公告要"这台机器到底干什么"）"""
import io
import os
import re
import sys

JAVA = r"E:\PotatoST\src\main\java\com\potatost\mod"

FILES = [
    "LowGeneratorBlockEntity.java", "GeneratorBlockEntity.java", "PowerCapturerBlockEntity.java",
    "MicroCrusherBlockEntity.java", "HydraulicPressBlockEntity.java", "FillingMachineBlockEntity.java",
    "SaltDryerBlockEntity.java", "SaltDecomposerBlockEntity.java", "SolarPanelBlockEntity.java",
    "ElectricBlastFurnaceBlockEntity.java", "TerminalBlockEntity.java", "LithiumBatteryBlockEntity.java",
    "ElectrolyzerBlockEntity.java", "MicroCrusherRecipes.java",
]


def main():
    for fn in FILES:
        p = os.path.join(JAVA, fn)
        if not os.path.isfile(p):
            print(u"!! 缺 %s" % fn)
            continue
        t = io.open(p, encoding="utf-8").read()
        m = re.search(r"/\*\*(.*?)\*/", t, re.S)
        print(u"==================== %s" % fn)
        if not m:
            print(u"  （没有类注释）")
            continue
        body = m.group(1)
        lines = [re.sub(r"^\s*\*ette?", "", l).strip() for l in body.split("\n")]
        lines = [re.sub(r"^\*\s?", "", l) for l in lines]
        for l in lines[:16]:
            if l:
                print(u"  " + l)
    return 0


if __name__ == "__main__":
    sys.exit(main())
