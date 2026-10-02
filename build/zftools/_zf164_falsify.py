# -*- coding: utf-8 -*-
u"""_zf164_falsify.py —— ZF164 的**反证刀**：把本轮每条判据各砍一刀，`_zf164_verify.py` 必须当场变红。

口径同 `_zf162_falsify.py`：真替换（不许只注释掉）、砍完还原、还原后逐字节等于砍之前。

跑法：python build\\zftools\\_zf164_falsify.py
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
GATE = os.path.join(ZT, u"_zf164_verify.py")
TMP = os.path.join(ZT, u"_zf164_falsify_bak")
BRIDGE = os.path.join(JAVA, u"MekChemicalBridge.java")
BE = os.path.join(JAVA, u"FillingMachineBlockEntity.java")

KNIVES = [
    dict(id=u"K1", why=u"把 spaceFor 里的 present() 守卫拆掉（B2 要抓到）", path=BE,
         old=u"        if (MekChemicalBridge.present()) {\n            return MekChemicalBridge.spaceFor(stack, fluid);",
         new=u"        if (true) {\n            return MekChemicalBridge.spaceFor(stack, fluid);",
         want=u"B2"),
    dict(id=u"K2", why=u"把 getKey 反查换成「永远为真」（A5 要抓到）", path=BRIDGE,
         old=u"if (candidate != null && wanted.equals(MekanismAPI.CHEMICAL_REGISTRY.getKey(candidate))) {",
         new=u"if (candidate != null) {",
         want=u"A5"),
    dict(id=u"K3", why=u"把软依赖判据改成恒真（A4 要抓到）", path=BRIDGE,
         old=u"return ModList.get().isLoaded(MekanismAPI.MEKANISM_MODID);",
         new=u"return true;",
         want=u"A4"),
    dict(id=u"K4", why=u"把第三条路的调用删掉（B1 要抓到）", path=BE,
         old=u"        return tryFillMekChemical(index, tank, inSlot);",
         new=u"        return false;",
         want=u"B1"),
    dict(id=u"K5", why=u"给灌装机也塞一个 mekanism import（A6 要抓到）", path=BE,
         old=u"import net.neoforged.neoforge.items.ItemStackHandler;",
         new=u"import net.neoforged.neoforge.items.ItemStackHandler;\nimport mekanism.api.MekanismAPI;",
         want=u"A6"),
    dict(id=u"K6", why=u"改一个锁定数字 FILL_RATE（B4 要抓到）", path=BE,
         old=u"public static final int FILL_RATE = 5;",
         new=u"public static final int FILL_RATE = 6;",
         want=u"B4"),
]


def raw(p):
    with open(p, "rb") as fh:
        return fh.read()


def sha1(p):
    return hashlib.sha1(raw(p)).hexdigest()


def run_gate():
    r = subprocess.run([sys.executable, GATE], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def main():
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)
    ok, bad = 0, []
    for k in KNIVES:
        path = k[u"path"]
        bak = os.path.join(TMP, k[u"id"] + u"__" + os.path.basename(path))
        shutil.copy2(path, bak)
        before = sha1(path)
        try:
            text = io.open(path, encoding="utf-8", newline=u"").read()
            if k[u"old"] not in text:
                raise AssertionError(u"刀砍不下去：找不到锚点")
            io.open(path, "w", encoding="utf-8", newline=u"").write(
                text.replace(k[u"old"], k[u"new"], 1))
            rc, out = run_gate()
            caught = [l.strip() for l in out.split(u"\n")
                      if l.strip().startswith(u"[FAIL]") and k[u"want"] in l]
            if rc != 0 and caught:
                ok += 1
                print(u"  [OK]   %s 门红了，抓到：%s" % (k[u"id"], caught[0][:76]))
            else:
                bad.append(k[u"id"])
                print(u"  [FAIL] %s 门没抓到（rc=%d，想看到 %s）—— %s" % (k[u"id"], rc, k[u"want"], k[u"why"]))
        finally:
            shutil.copy2(bak, path)
            if sha1(path) != before:
                bad.append(k[u"id"] + u"(还原不一致)")
                print(u"  !! %s 还原后与砍之前不一致" % k[u"id"])
    print(u"\n反证刀：%d/%d 抓到（漏网 %s）" % (ok, len(KNIVES), u" / ".join(bad) if bad else u"无"))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
