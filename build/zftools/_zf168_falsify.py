# -*- coding: utf-8 -*-
u"""_zf168_falsify.py —— ZF168 的**反证刀**：砍一刀，`_zf168_verify.py` 必须当场变红。

K1/K2 砍的是"用户报的那件事"的两半（反方向那条路、以及那句提示），
K3/K4 砍的是本轮挖出来的**桶包装器只认整桶**那条 API 雷，K5 砍守恒，K6 砍语言键。

跑法：python build\\zftools\\_zf168_falsify.py
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
GATE = os.path.join(ZT, u"_zf168_verify.py")
TMP = os.path.join(ZT, u"_zf168_falsify_bak")
BE = os.path.join(JAVA, u"FluidConverterBlockEntity.java")
BLK = os.path.join(JAVA, u"FluidConverterBlock.java")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang\zh_cn.json")

KNIVES = [
    dict(id=u"K1", why=u"删掉「倒不进就反过来装走」那一句（A2 要抓到）", path=BLK,
         old=u"            pour = be.fillContainerFrom(stack, toOutput, FluidConverterBlockEntity.POUR_PER_CLICK);",
         new=u"            // 刀：这里本该反过来试 fillContainerFrom",
         want=u"A2"),
    dict(id=u"K2", why=u"删掉那句提示（A3 要抓到）", path=BLK,
         old=u"            if (player instanceof ServerPlayer sp && be.targetBlocked(stack, toOutput)) {",
         new=u"            if (false) {",
         want=u"A3"),
    dict(id=u"K3", why=u"探桶里内容改回 drain(1)（那条 API 雷；D1 要抓到）", path=BE,
         old=u"        FluidStack sim = handler.drain(Integer.MAX_VALUE, IFluidHandler.FluidAction.SIMULATE);",
         new=u"        FluidStack sim = handler.drain(1, IFluidHandler.FluidAction.SIMULATE);",
         want=u"D1"),
    dict(id=u"K4", why=u"把「整桶取」改回「按余量取」（D2 要抓到）", path=BE,
         old=u"        FluidStack drained = handler.drain(sim.getAmount(), IFluidHandler.FluidAction.EXECUTE);",
         new=u"        FluidStack drained = handler.drain(limit, IFluidHandler.FluidAction.EXECUTE);",
         want=u"D2"),
    dict(id=u"K5", why=u"删掉「装多了退回去」（C1 要抓到）", path=BE,
         old=u"                container.drain(stack, put - taken.getAmount());",
         new=u"                // 刀：这里本该把多装的退回去",
         want=u"C1"),
    dict(id=u"K6", why=u"从 zh_cn 删掉新键（E3 要抓到）", path=LANG,
         old=u'  "gui.potato_s_t.fluid_converter.pour.occupied":',
         new=u'  "gui.potato_s_t.fluid_converter.pour.occupied_DELETED":',
         want=u"E3"),
]


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_gate():
    r = subprocess.run([sys.executable, GATE], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=300)
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
            io.open(path, "w", encoding="utf-8", newline=u"").write(text.replace(k[u"old"], k[u"new"], 1))
            rc, out = run_gate()
            caught = [l.strip() for l in out.split(u"\n")
                      if l.strip().startswith(u"[FAIL]") and k[u"want"] in l]
            if rc != 0 and caught:
                ok += 1
                print(u"  [OK]   %s 门红了，抓到：%s" % (k[u"id"], caught[0][:72]))
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
