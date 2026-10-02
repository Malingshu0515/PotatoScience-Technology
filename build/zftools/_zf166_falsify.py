# -*- coding: utf-8 -*-
u"""_zf166_falsify.py —— ZF166 的**反证刀**：砍一刀，`_zf166_verify.py` 必须当场变红。

其中 K1 砍的是**本轮那个差点白干的致命 bug**（`output.fill(drained)`），
K5 砍的是**另一条线指出的"能力没登记"缺口** —— 这两刀证明了门不是摆设。

跑法：python build\\zftools\\_zf166_falsify.py
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
GATE = os.path.join(ZT, u"_zf166_verify.py")
TMP = os.path.join(ZT, u"_zf166_falsify_bak")
BE = os.path.join(JAVA, u"FluidConverterBlockEntity.java")
BLK = os.path.join(JAVA, u"FluidConverterBlock.java")
POT = os.path.join(JAVA, u"PotatoST.java")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang\zh_cn.json")

KNIVES = [
    dict(id=u"K1", why=u"把「转化」写回 output.fill(drained)（本轮那个致命 bug；B4b 要抓到）", path=BE,
         old=u"        FluidStack produced = new FluidStack(out, drained.getAmount());",
         new=u"        FluidStack produced = drained;",
         want=u"B4b"),
    dict(id=u"K2", why=u"去掉 c: 命名空间过滤（B3 要抓到）", path=BE,
         old=u'            if ("c".equals(tag.location().getNamespace())) {',
         new=u"            if (true) {",
         want=u"B3"),
    dict(id=u"K3", why=u"改一个锁定数字 RATE（B1 要抓到）", path=BE,
         old=u"public static final int RATE = 50;",
         new=u"public static final int RATE = 60;",
         want=u"B1"),
    dict(id=u"K4", why=u"把 Audit B 那行字从 onRemove 里删掉（B7 要抓到）", path=BLK,
         old=u"            MachineDrops.dropInventory(level, pos, be.getInventory());",
         new=u"            // 刀：这里本该有 MachineDrops.dropInventory",
         want=u"B7"),
    dict(id=u"K5", why=u"删掉流体能力登记（另一条线指出的缺口；B9 要抓到）", path=POT,
         old=u"        // ⑬c 流体转化器：两个罐对外是一个句柄 —— **进的一律进输入罐、抽的一律从输出罐出**\n"
             u"        //     （管道不用管接的是哪一面；语义见 FluidConverterBlockEntity.getFluidHandler 的注释）\n"
             u"        event.registerBlockEntity(\n"
             u"                Capabilities.FluidHandler.BLOCK,\n"
             u"                ModBlocks.FLUID_CONVERTER_BE.get(),\n"
             u"                (machine, side) -> machine.getFluidHandler());\n",
         new=u"",
         want=u"B9"),
    dict(id=u"K6", why=u"从 zh_cn 里删一个转化器的键（C6 要抓到）", path=LANG,
         old=u'  "gui.potato_s_t.fluid_converter.status.idle": "待机",\n',
         new=u"",
         want=u"C6"),
]


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


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
            io.open(path, "w", encoding="utf-8", newline=u"").write(text.replace(k[u"old"], k[u"new"], 1))
            rc, out = run_gate()
            caught = [l.strip() for l in out.split(u"\n")
                      if l.strip().startswith(u"[FAIL]") and k[u"want"] in l]
            if rc != 0 and caught:
                ok += 1
                print(u"  [OK]   %s 门红了，抓到：%s" % (k[u"id"], caught[0][:74]))
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
