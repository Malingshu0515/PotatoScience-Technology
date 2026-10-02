# -*- coding: utf-8 -*-
u"""_zf162_falsify.py —— ZF162 的**反证刀**：把本轮每一条判据各砍一刀，门必须当场变红。

口径（§4 的老规矩）：刀要**真搬移/真替换**代码，不许只注释掉；砍完必须还原，
并且**还原后逐字节等于砍之前**；每一刀都要记录"门里哪一条抓到了它"。

跑法：python build\\zftools\\_zf162_falsify.py
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
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
DATA = os.path.join(ROOT, r"src\main\resources\data\potato_s_t")
GATE = os.path.join(ZT, u"_zf162_verify.py")
TMP = os.path.join(ZT, u"_zf162_falsify_bak")

KNIVES = [
    dict(id=u"K1", why=u"把扳手又注册回 ModItems（A1/A2 要抓到）",
         path=os.path.join(JAVA, u"ModItems.java"),
         old=u"    // ========== 星轨坠 + 粗振金（0.11 ZF114）==========",
         new=(u"    public static final DeferredItem<Item> WRENCH =\n"
              u"            ITEMS.register(\"wrench\", () -> new Item(new Item.Properties().stacksTo(1)));\n\n"
              u"    // ========== 星轨坠 + 粗振金（0.11 ZF114）=========="),
         want=u"A1"),
    dict(id=u"K2", why=u"把扳手那条 lang 键塞回 zh_cn（A7 + D1 键数要抓到）",
         path=os.path.join(LANG, u"zh_cn.json"),
         old=u'  "block.potato_s_t.filling_machine":',
         new=u'  "item.potato_s_t.wrench": "扳手（暂时没用）",\n  "block.potato_s_t.filling_machine":',
         want=u"A7"),
    dict(id=u"K3", why=u"把电力高炉那条配方 JSON 放回盘上（B7/B8/D3 要抓到）",
         path=os.path.join(DATA, r"recipe\electric_blast_furnace.json"),
         old=None, new=u'{ "type": "minecraft:crafting_shaped" }\n',
         want=u"B7"),
    dict(id=u"K4", why=u"进度改回老判据（B13/B15 要抓到）",
         path=os.path.join(DATA, r"advancement\blast_furnace.json"),
         old=u'"trigger": "potato_s_t:ebf_formed"',
         new=u'"trigger": "minecraft:inventory_changed", "items": "potato_s_t:electric_blast_furnace"',
         want=u"B13"),
    dict(id=u"K5", why=u"方块实体 isItemValid 改回只认自家接口（C1 要抓到）",
         path=os.path.join(JAVA, u"FillingMachineBlockEntity.java"),
         old=u"            return true;\n        }\n    };",
         new=u"            return stack.getItem() instanceof FluidContainerItem;\n        }\n    };",
         want=u"C1"),
    dict(id=u"K6", why=u"菜单手放那道门改回只认自家接口（C2/C4 要抓到）",
         path=os.path.join(JAVA, u"FillingMachineMenu.java"),
         old=u"                    return true;\n                }",
         new=u"                    return stack.getItem() instanceof FluidContainerItem;\n                }",
         want=u"C2"),
    dict(id=u"K7", why=u"把跨 mod 那条能力查询删掉（C5 要抓到）",
         path=os.path.join(JAVA, u"FillingMachineBlockEntity.java"),
         old=u"        return stack.copyWithCount(1).getCapability(Capabilities.FluidHandler.ITEM);",
         new=u"        return null;",
         want=u"C5"),
    dict(id=u"K8", why=u"拆掉「结果与灌前相同即放弃」那道闸门（C7 要抓到）",
         path=os.path.join(JAVA, u"FillingMachineBlockEntity.java"),
         old=u"        if (result.isEmpty() || ItemStack.isSameItemSameComponents(result, inSlot)) {",
         new=u"        if (result.isEmpty()) {",
         want=u"C7"),
    dict(id=u"K9", why=u"动一下用户点名「不要动」的文件（C13 要抓到）",
         path=os.path.join(JAVA, u"HighPressureTankItem.java"),
         old=u"package com.potatost.mod;",
         new=u"package com.potatost.mod;   ",
         want=u"C13"),
    dict(id=u"K10", why=u"改一个锁定数字 FILL_RATE（C12 要抓到）",
         path=os.path.join(JAVA, u"FillingMachineBlockEntity.java"),
         old=u"public static final int FILL_RATE = 5;",
         new=u"public static final int FILL_RATE = 6;",
         want=u"C12"),
]


def raw(p):
    with open(p, "rb") as fh:
        return fh.read()


def sha1(p):
    return hashlib.sha1(raw(p)).hexdigest()


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
        existed = os.path.isfile(path)
        bak = os.path.join(TMP, k[u"id"] + u"__" + os.path.basename(path))
        if existed:
            shutil.copy2(path, bak)
            before = sha1(path)
        else:
            before = None
        try:
            if k[u"old"] is None:
                with io.open(path, "w", encoding="utf-8", newline=u"\n") as fh:
                    fh.write(k[u"new"])
            else:
                text = io.open(path, encoding="utf-8", newline=u"").read()
                if k[u"old"] not in text:
                    raise AssertionError(u"刀砍不下去：找不到锚点")
                with io.open(path, "w", encoding="utf-8", newline=u"") as fh:
                    fh.write(text.replace(k[u"old"], k[u"new"], 1))
            rc, out = run_gate()
            hit = k[u"want"] in out and u"[FAIL]" in out
            if rc != 0 and hit:
                ok += 1
                caught = [l.strip() for l in out.split(u"\n") if l.strip().startswith(u"[FAIL]") and k[u"want"] in l]
                print(u"  [OK]   %s 门红了，抓到：%s" % (k[u"id"], caught[0][:78] if caught else k[u"want"]))
            else:
                bad.append(k[u"id"])
                print(u"  [FAIL] %s 门没抓到（rc=%d, 想看到 %s）—— %s" % (k[u"id"], rc, k[u"want"], k[u"why"]))
        finally:
            if existed:
                shutil.copy2(bak, path)
                if sha1(path) != before:
                    bad.append(k[u"id"] + u"(还原不一致)")
                    print(u"  !! %s 还原后与砍之前不一致" % k[u"id"])
            else:
                if os.path.isfile(path):
                    os.remove(path)
    print(u"\n反证刀：%d/%d 抓到（漏网 %s）" % (ok, len(KNIVES), u" / ".join(bad) if bad else u"无"))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
