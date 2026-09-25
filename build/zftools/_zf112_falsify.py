# -*- coding: utf-8 -*-
u"""_zf112_falsify.py —— ZF112 的反证刀（K133~K137，5 把）

口径同前：先确认基线绿 → 改一处语义 ⇒ 校验器必须 FAIL 且**咬住指定的那条检查** ⇒
逐字节还原 ⇒ 收尾回到全绿。一把刀 180 秒超时（§4.77）。
"""
import hashlib
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, r"build\zftools")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
DATA = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
VERIFY = os.path.join(ZT, u"_zf112_verify.py")

BE = os.path.join(JAVA, "LithiumBatteryPlantBlockEntity.java")
REC = os.path.join(DATA, "lithium_battery.json")
REPORT = os.path.join(ZT, u"_zf112_probe_utf8.txt")

KNIVES = [
    ("K133", u"硫酸从 10 mB/t 改成 1 mB/t", BE, u"ACID_PER_TICK = 10;", u"ACID_PER_TICK = 1;",
     u"每 tick 10 mB"),
    ("K134", u"罐从 8000 改回 2000（装不下一炉）", BE, u"TANK_CAPACITY = 8000;",
     u"TANK_CAPACITY = 2000;", u"罐 8000"),
    ("K135", u"三元锂配方那格改回碳酸锂", REC, u"\"item\": \"potato_s_t:lithium_battery_component\"",
     u"\"item\": \"potato_s_t:lithium_carbonate\"", u"锂电池原件"),
    ("K136", u"产物改回 insertItem（会走 isItemValid ⇒ 扣料不出货）", BE,
     u"        out.grow(OUTPUT_COUNT);\n        this.items.setStackInSlot(OUTPUT_SLOT, out);",
     u"        this.items.insertItem(OUTPUT_SLOT, new ItemStack(\n"
     u"                ModItems.LITHIUM_BATTERY_COMPONENT.get(), OUTPUT_COUNT), false);",
     u"输出用 setStackInSlot"),
    ("K137", u"探针报告改成不绿（伪造证据）", REPORT, u"verdict: ALL OK",
     u"verdict: **1 FAILED**", u"报告全绿"),
]

fails = []


def run_verify():
    try:
        r = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=180)
        return r.returncode, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 99, u"**超时**"


def main():
    rc, out = run_verify()
    line = [l for l in out.split(u"\n") if u"通过" in l and u"失败" in l]
    print(u"基线：%s（退出码 %d）" % (line[-1].strip() if line else u"?", rc))
    if rc != 0:
        print(u"  [STOP] 基线不绿，先修")
        return 1
    n_ok = 0
    for kid, why, path, old, new, expect in KNIVES:
        orig = open(path, "rb").read()
        before = hashlib.sha1(orig).hexdigest()
        text = orig.decode("utf-8")
        if text.count(old) != 1:
            fails.append(u"%s：锚点命中 %d 次" % (kid, text.count(old)))
            continue
        open(path, "wb").write(text.replace(old, new, 1).encode("utf-8"))
        rc, out = run_verify()
        open(path, "wb").write(orig)
        if hashlib.sha1(open(path, "rb").read()).hexdigest() != before:
            fails.append(u"%s：还原失败" % kid)
            break
        if rc != 0 and expect in out:
            n_ok += 1
            print(u"  [OK]   %s %s ⇒ 咬住「%s」" % (kid, why, expect))
        else:
            fails.append(u"%s %s ⇒ %s" % (kid, why, u"校验器还是绿的" if rc == 0 else u"咬错了检查"))
            print(u"  [BAD]  %s %s（退出码 %d）" % (kid, why, rc))
    rc, out = run_verify()
    line = [l for l in out.split(u"\n") if u"通过" in l and u"失败" in l]
    print(u"收尾：%s（退出码 %d）" % (line[-1].strip() if line else u"?", rc))
    if rc != 0:
        fails.append(u"收尾不是全绿")
    print(u"刀 = %d，咬住 = %d，失败项 = %d" % (len(KNIVES), n_ok, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
