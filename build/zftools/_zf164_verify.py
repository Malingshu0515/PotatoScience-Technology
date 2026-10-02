# -*- coding: utf-8 -*-
u"""_zf164_verify.py —— ZF164（0.13 第七笔）**常驻校验**：灌装机 × Mekanism 化学品/气体兼容。

用户原话：「mek喷气背包还是不可以灌本mod的氢 你看看能不能做一下兼容 或者搞一个流体转化装置
可以把本mod的流体转成同标签的别的mod流体」

  A 软依赖与桥：libs 里那份 Mek jar（sha1 钉住）/ build.gradle 的 compileOnly /
    `MekChemicalBridge` 存在且**公开签名里没有 mekanism 类型**（没装 Mek 不会 NoClassDefFound）/
    映射走 `c:` 同名标签 + **getKey 反查**（DefaultedRegistry 查不到会回默认值，直接 get 会误判"有"）
  B 灌装机第三条路：tryFillSlot → tryFillMekChemical；spaceFor / acceptsFluid / stateOf 三处都有
    `MekChemicalBridge.present()` 守卫；锁定数字没动
  C 探针与文档：`_zf164_probe_utf8.txt` 19/0（含喷气背包真的装进 mekanism:hydrogen ×100）；
    §4.171 / §5 ZF164 行 / 交接第 36 条 / 英文公告；语言键数仍 593×4 + 595（本轮不加键）
  D 成品：jar 里不许有 mekanism 的 class（软依赖不进产物）+ 哈希三处联动

跑法：python build\\zftools\\_zf164_verify.py
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
LIBS = os.path.join(ROOT, "libs")
MEK_JAR = os.path.join(LIBS, u"Mekanism-1.21.1-10.7.19.85.jar")
MEK_SHA1 = u"b78945c40cfe"          # 只钉前 12 位（防手滑换错包；要换包就一起改这里）
BRIDGE = os.path.join(JAVA, u"MekChemicalBridge.java")
BE = os.path.join(JAVA, u"FillingMachineBlockEntity.java")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")
PROBE = os.path.join(ZT, u"_zf164_probe_utf8.txt")
LANGDIR = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")

passed, failed, fails = 0, 0, []


def check(cond, label, detail=u""):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label if not detail else u"%s（%s）" % (label, detail))
        print(u"  [FAIL] " + label + (u" —— " + detail if detail else u""))


def read(p):
    return io.open(p, encoding="utf-8", errors="replace").read() if os.path.isfile(p) else u""


def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


print(u"=== A 段：软依赖与桥 ===")
check(os.path.isfile(MEK_JAR), u"A1 libs 里有 Mek jar", MEK_JAR)
if os.path.isfile(MEK_JAR):
    check(sha1(MEK_JAR).startswith(MEK_SHA1), u"A1b 那份 jar 的 sha1 前 12 位 = %s" % MEK_SHA1,
          sha1(MEK_JAR)[:12])
gradle = read(os.path.join(ROOT, "build.gradle"))
check(u"compileOnly files('libs/Mekanism-1.21.1-10.7.19.85.jar')" in gradle,
      u"A2 build.gradle 里是 compileOnly（不进产物）")
bridge = read(BRIDGE)
check(bool(bridge), u"A3 MekChemicalBridge.java 存在")
check(bridge.count(u"ModList.get().isLoaded(MekanismAPI.MEKANISM_MODID)") == 1,
      u"A4 软依赖判据走 ModList.get().isLoaded")
check(u"MekanismAPI.CHEMICAL_REGISTRY.getKey(" in bridge and u"wanted.equals(" in bridge,
      u"A5 映射做了 getKey 反查（DefaultedRegistry 的默认值不会误判成「有」）")
meks = []
for root, _d, files in os.walk(JAVA):
    for f in files:
        if f.endswith(u".java"):
            p = os.path.join(root, f)
            if u"import mekanism." in read(p):
                meks.append(os.path.relpath(p, JAVA))
check(meks == [u"MekChemicalBridge.java"], u"A6 全工程只有桥这一个文件 import mekanism", u" / ".join(meks))
pub = [l for l in bridge.split(u"\n") if l.strip().startswith(u"public static")]
check(all(u"mekanism." not in l for l in pub),
      u"A7 桥的公开方法签名里没有 mekanism 类型（没装 Mek 也不会 NoClassDefFound）",
      u" / ".join([l.strip()[:60] for l in pub if u"mekanism." in l][:2]))

print(u"\n=== B 段：灌装机第三条路 ===")
be = read(BE)
check(u"return tryFillMekChemical(index, tank, inSlot);" in be
      and u"MekChemicalBridge.fill(inSlot, tank.getFluid(), FILL_RATE)" in be,
      u"B1 tryFillSlot 末尾真的调了 tryFillMekChemical（不是只留了个方法定义）")
check(be.count(u"MekChemicalBridge.present()") == 4,
      u"B2 spaceFor / acceptsFluid / tryFillMekChemical / stateOf 四处都有 present() 守卫",
      u"实际 %d 处" % be.count(u"MekChemicalBridge.present()"))
check(u"boolean mek = foreign == null && MekChemicalBridge.present()" in be,
      u"B3 stateOf 里给 Mek 那一路留了名字（不会再显示成「没放东西」）")
check(u"FILL_RATE = 5" in be and u"ENERGY_PER_TANK = 60" in be,
      u"B4 锁定数字没动（5 mB/t、60 FE/罐/t）")

print(u"\n=== C 段：探针、文档与键数 ===")
report = read(PROBE)
check(u"通过 = 19   失败 = 0" in report, u"C1 探针报告 19/0", report.strip().split(u"\n")[-1] if report else u"（没有报告）")
check(u"mekanism:hydrogen × 100" in report, u"C1b 报告里有「喷气背包真的装进 mekanism:hydrogen × 100」")
check(u"### 4.171 " in read(DOC) and u"| ZF164 |" in read(DOC), u"C2 档案 §4.171 + §5 ZF164 行")
check(u"36. **ZF164 的账" in read(HAND), u"C3 交接 §6 第 36 条")
check(u"## New in 0.13 ZF164" in read(ANN), u"C4 英文公告有 ZF164 那一段")
counts = {}
for lg in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"):
    p = os.path.join(LANGDIR, lg + u".json")
    if os.path.isfile(p):
        counts[lg] = len(json.loads(io.open(p, encoding="utf-8").read()))
check(counts.get(u"zh_cn") == 593 and counts.get(u"lzh") == 595,
      u"C5 语言键数仍是 593×4 + 595（本轮不加键）", repr(counts))

print(u"\n=== D 段：成品（软依赖不进产物）===")
if os.path.isfile(JAR):
    names = zipfile.ZipFile(JAR).namelist()
    mek_cls = [n for n in names if n.startswith(u"mekanism/")]
    check(not mek_cls, u"D1 产物 jar 里没有 Mek 的 class（compileOnly 生效）", u"／".join(mek_cls[:3]))
    check(u"com/potatost/mod/MekChemicalBridge.class" in names, u"D2 但桥自己的 class 在产物里")
else:
    check(False, u"D0 成品 jar 不在：%s" % JAR)

print(u"\n通过 = %d   失败 = %d" % (passed, failed))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if failed else 0)
