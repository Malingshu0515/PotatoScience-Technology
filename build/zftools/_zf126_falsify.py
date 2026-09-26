# -*- coding: utf-8 -*-
u"""_zf126_falsify.py —— ZF126 的反证刀（K199~K204，6 把）

口径同前：基线绿 → 改一处语义 ⇒ 门必须 FAIL 且**咬住指定的那一条** ⇒ 逐字节还原 ⇒ 收尾回到全绿。

刀面：
  K199 缓冲 18000 → 7200（改回旧值）          K202 工作指示灯那行删掉
  K200 缓冲写回 ENERGY_PER_TICK（又耦合上）  K203 往轮判据的 B4 改回旧文案
  K201 能量条那行删掉                        K204 只给 zh_cn 加一个键（四份就不一致了）
"""
import hashlib
import io
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, r"build\zftools")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
BE = os.path.join(JAVA, u"DieselGeneratorBlockEntity.java")
SCREEN = os.path.join(JAVA, u"client", u"DieselGeneratorScreen.java")
LANG_ZH = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang\zh_cn.json")
Z125 = os.path.join(ZT, u"_zf125_verify.py")
VERIFY = os.path.join(ZT, u"_zf126_verify.py")

KNIVES = [
    dict(id="K199", why=u"缓冲 18000 → 7200（改回 ZF125 那个自定值）", path=BE,
         old=u"MAX_ENERGY = 18_000;", new=u"MAX_ENERGY = 7200;",
         expect=u"A1 缓冲 = 18000 FE"),
    dict(id="K200", why=u"缓冲写回 ENERGY_PER_TICK（又和产量耦上）", path=BE,
         old=u"MAX_ENERGY = 18_000;", new=u"MAX_ENERGY = ENERGY_PER_TICK;",
         expect=u"A2 与产量**解耦**"),
    dict(id="K201", why=u"能量条那一段删掉（用户要的缓存看不见了）", path=SCREEN,
         old=(u"        this.parts.add(new EnergyBarPart(DieselGeneratorMenu.ENERGY_X, "
              u"DieselGeneratorMenu.ENERGY_Y,\n"
              u"                DieselGeneratorMenu.ENERGY_W, DieselGeneratorMenu.ENERGY_H,\n"
              u"                menu::getEnergy, DieselGeneratorBlockEntity.MAX_ENERGY));\n"),
         new=u"",
         expect=u"B2 界面里加了 EnergyBarPart"),
    dict(id="K202", why=u"工作指示灯那三行删掉（加东西把原来的挤掉了）", path=SCREEN,
         old=(u"        this.parts.add(new StatusLampPart(DieselGeneratorMenu.LAMP_X, "
              u"DieselGeneratorMenu.LAMP_Y,\n"
              u"                DieselGeneratorMenu.LAMP_SIZE, menu::getStatus, STATUS_KEY_PREFIX));\n"),
         new=u"",
         expect=u"B5 工作指示灯**还在**"),
    dict(id="K203", why=u"往轮判据 _zf125_verify 的 B4 改回旧文案（那道门又会过期）", path=Z125,
         old=u"B4 缓冲（ZF126 起 18000 —— 用户点名给的；与产量解耦）",
         new=u"B4 缓冲 = 1 tick 的产量（用户没给，自定的默认已在注释里点名）",
         expect=u"D6 _zf125_verify.py 的 B4 已跟到 18000"),
    dict(id="K204", why=u"只给 zh_cn 加一个键（四份键集合/键数就不一致了）", path=LANG_ZH,
         mode="resub",
         old_re=u"(\\n)\\}\\n\\Z",
         new_re=u",\\n    \"zz.probe.only.zh\":  \"只有中文有\"\\n}\\n",
         expect=u"C2 四份仍各 476 键"),
]

fails = []


def run():
    try:
        r = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=300)
        return r.returncode, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 99, u"**超时**"


def summary(out):
    line = [l for l in out.split(u"\n") if u"通过" in l and u"失败" in l]
    return line[-1].strip() if line else u"?"


def bitten(out, expect):
    return any(l.strip().startswith(u"!!") and expect in l for l in out.split(u"\n"))


def main():
    rc, out = run()
    print(u"基线：%s（退出码 %d）" % (summary(out), rc))
    if rc != 0:
        print(u"  [STOP] 基线不绿，先修")
        for l in out.split(u"\n"):
            if l.strip().startswith(u"!!"):
                print(u"    " + l.strip())
        return 1
    n_ok = 0
    for k in KNIVES:
        path = k["path"]
        orig = open(path, "rb").read()
        before = hashlib.sha1(orig).hexdigest()
        try:
            text = orig.decode("utf-8")
            if k.get("mode") == "resub":
                new_text, n = re.subn(k["old_re"], k["new_re"], text, count=1)
                if n != 1:
                    fails.append(u"%s：正则命中 %d 次" % (k["id"], n))
                    print(u"  [BAD]  %s 锚点没命中" % k["id"])
                    continue
                open(path, "wb").write(new_text.encode("utf-8"))
            else:
                if text.count(k["old"]) != 1:
                    fails.append(u"%s：锚点命中 %d 次" % (k["id"], text.count(k["old"])))
                    print(u"  [BAD]  %s 锚点命中 %d 次" % (k["id"], text.count(k["old"])))
                    continue
                open(path, "wb").write(text.replace(k["old"], k["new"], 1).encode("utf-8"))
            rc, out = run()
        finally:
            open(path, "wb").write(orig)
        after = hashlib.sha1(open(path, "rb").read()).hexdigest()
        if after != before:
            fails.append(u"%s：还原失败" % k["id"])
            break
        if rc != 0 and bitten(out, k["expect"]):
            n_ok += 1
            print(u"  [OK]   %s %s ⇒ 咬住「%s」" % (k["id"], k["why"], k["expect"]))
        else:
            print(u"  [BAD]  %s %s（退出码 %d）" % (k["id"], k["why"], rc))
            fails.append(u"%s %s ⇒ %s" % (k["id"], k["why"],
                                          u"门还是绿的" if rc == 0 else u"咬错了检查"))
    rc, out = run()
    print(u"收尾：%s（退出码 %d）" % (summary(out), rc))
    if rc != 0:
        fails.append(u"收尾不是全绿")
    print(u"刀 = %d，咬住 = %d，失败项 = %d" % (len(KNIVES), n_ok, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
