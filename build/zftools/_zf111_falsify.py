# -*- coding: utf-8 -*-
u"""_zf111_falsify.py —— ZF111 的反证刀（K123~K132）

口径同前几轮（§4.17 / §4.77）：先确认基线绿 → 每把刀改一处语义 ⇒ 校验器必须 FAIL、
**而且要咬住指定的那条检查** ⇒ 逐字节还原 ⇒ 收尾回到全绿；一把刀 180 秒超时。
"""
import hashlib
import io
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
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
VERIFY = os.path.join(ZT, u"_zf111_verify.py")

RECIPES = os.path.join(JAVA, "AlloySmelterRecipes.java")
BE = os.path.join(JAVA, "AlloySmelterBlockEntity.java")
MR = os.path.join(JAVA, "MachineRecipes.java")
ZH = os.path.join(LANG, "zh_cn.json")
EN = os.path.join(LANG, "en_us.json")
REPORT = os.path.join(ZT, u"_zf111_probe_utf8.txt")

KNIVES = [
    ("K123", u"高碳钢从 4 个改成 1 个", RECIPES,
     u'new Need(ingot("steel"), 4)', u'new Need(ingot("steel"), 1)', u"高碳钢 ×4"),
    ("K124", u"产物从 3 个改成 1 个", RECIPES,
     u"new ItemStack(ModArmorItems.STAR_STEEL_INGOT.get(), 3)",
     u"new ItemStack(ModArmorItems.STAR_STEEL_INGOT.get(), 1)", u"产物：3 个星璨钢锭"),
    ("K125", u"耗电从 12000 改回 800", RECIPES,
     u"public static final int MAX_ENERGY_PER_TICK = 12_000;",
     u"public static final int MAX_ENERGY_PER_TICK = 800;", u"MAX_ENERGY_PER_TICK = 12000"),
    ("K126", u"消耗品少掉末影水晶", RECIPES,
     u"                List.of(new Consume(PotatoSTOres.DEEPSLATE_COBALT_ORE.get().asItem(), 1),\n"
     u"                        new Consume(Items.END_CRYSTAL, 1)),",
     u"                List.of(new Consume(PotatoSTOres.DEEPSLATE_COBALT_ORE.get().asItem(), 1)),",
     u"消耗品：1 个末影水晶"),
    ("K127", u"craftTick 退回全局常量（星璨钢会被按 800 扣电）", BE,
     u"        int cost = smelt.energyPerTick();",
     u"        int cost = ENERGY_PER_TICK;", u"craftTick 读这条配方自己的每 tick 耗电"),
    ("K128", u"消耗槽重新锁死", BE,
     u"                return isConsumable(stack);     // 0.11 ZF111：只收\"某条配方真的会消耗\"的东西",
     u"                return false;", u"消耗槽 isItemValid 走 isConsumable"),
    ("K129", u"zh 的消耗槽标签退回「暂未开放」", ZH,
     u"\"gui.potato_s_t.alloy_smelter.consume_slot\":  \"消耗槽（放配方点名要消耗的东西）\",",
     u"\"gui.potato_s_t.alloy_smelter.consume_slot\":  \"消耗槽（暂未开放）\",",
     u"消耗槽不再是「未开放」"),
    ("K130", u"en 的介绍脚注把 12000 抹掉", EN,
     u"12000 FE/t", u"800 FE/t", u"脚注写了 12000"),
    ("K131", u"JEI 里不再画消耗品", MR,
     u"            for (AlloySmelterRecipes.Consume consume : smelt.consumes()) {\n"
     u"                inputs.add(new ItemStack(consume.item(), consume.count()));\n"
     u"            }\n", u"",
     u"MachineRecipes 把消耗品也画进输入"),
    ("K132", u"探针报告改成不绿（伪造证据）", REPORT,
     u"verdict: ALL OK", u"verdict: **1 FAILED**", u"报告是全绿"),
]

fails = []


def sha1b(b):
    return hashlib.sha1(b).hexdigest()


def run_verify():
    try:
        r = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=180)
        return r.returncode, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 99, u"**超时 180 秒**"


def main():
    print(u"== 基线 ==")
    rc, out = run_verify()
    if rc != 0:
        print(u"  [STOP] 基线不是绿的（退出码 %d）—— 先修再动刀" % rc)
        for line in out.split(u"\n"):
            if line.strip().startswith(u"!!"):
                print(u"    " + line.strip())
        return 1
    line = [l for l in out.split(u"\n") if u"通过" in l and u"失败" in l]
    print(u"  基线绿：%s" % (line[-1].strip() if line else u"?"))

    n_ok = 0
    for kid, why, path, old, new, expect in KNIVES:
        if not os.path.exists(path):
            fails.append(u"%s：目标文件不在 %s" % (kid, path))
            continue
        orig = open(path, "rb").read()
        before = sha1b(orig)
        text = orig.decode("utf-8")
        if text.count(old) != 1:
            fails.append(u"%s：原文命中 %d 次（要求 1 次）—— 锚点过时了" % (kid, text.count(old)))
            continue
        open(path, "wb").write(text.replace(old, new, 1).encode("utf-8"))

        rc, out = run_verify()
        back = sha1b(open(path, "rb").read())
        open(path, "wb").write(orig)
        restored = sha1b(open(path, "rb").read()) == before
        if not restored:
            fails.append(u"%s：**还原失败**（哈希对不上）" % kid)
            break
        if rc != 0 and expect in out:
            n_ok += 1
            print(u"  [OK]   %s %s ⇒ 校验器 FAIL 且咬住「%s」" % (kid, why, expect))
        else:
            if rc == 0:
                fails.append(u"%s %s ⇒ **校验器还是绿的（这把刀没咬住）**" % (kid, why))
            else:
                fails.append(u"%s %s ⇒ 红了但咬错的检查（没出现「%s」）" % (kid, why, expect))
            print(u"  [BAD]  %s %s（退出码 %d）" % (kid, why, rc))
            for l in out.split(u"\n"):
                if l.strip().startswith(u"!!"):
                    print(u"         %s" % l.strip()[:110])

    print(u"\n== 收尾：还原后必须回到全绿 ==")
    rc, out = run_verify()
    line = [l for l in out.split(u"\n") if u"通过" in l and u"失败" in l]
    print(u"  %s（退出码 %d）" % (line[-1].strip() if line else u"?", rc))
    if rc != 0:
        fails.append(u"收尾不是全绿")
        for l in out.split(u"\n"):
            if l.strip().startswith(u"!!"):
                print(u"    " + l.strip())

    print(u"\n刀 = %d 把，咬住 = %d，失败项 = %d" % (len(KNIVES), n_ok, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
