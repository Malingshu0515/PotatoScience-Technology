# -*- coding: utf-8 -*-
u"""_zf125_falsify.py —— ZF125 的反证刀（K187~K198，12 把）

口径同前：基线绿 → 改一处语义 ⇒ 门必须 FAIL 且**咬住指定的那一条**（串必须出现在以 `!!`
开头的 FAIL 行里）⇒ 逐字节还原 ⇒ 收尾回到全绿。

刀面（每把只动一个语义，专挑"改了也不会编译报错、也不会崩"的那种）：
  K187 罐容量 8000 → 8001                K193 配方中排 CBC → CCC
  K188 发电 7200 → 7201                  K194 zh_cn 的 invalid 少一个 %s
  K189 铜块集合里删掉「氧化+涂蜡」那一项   K195 方块状态只留三个朝向
  K190 接线块那一格不再认接线口           K196 创造页那一行删掉（§4.82 的老坑）
  K191 给控制器本体也登记能量能力         K197 往轮判据 _zf103 又写回 464
  K192 接线口不再看"成型没成型"           K198 判定改回 holes.isEmpty()（§4.56 的老坑）
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
STRUCT = os.path.join(JAVA, u"DieselGeneratorStructure.java")
BE = os.path.join(JAVA, u"DieselGeneratorBlockEntity.java")
PORTBE = os.path.join(JAVA, u"DieselGeneratorPortBlockEntity.java")
MAIN = os.path.join(JAVA, u"PotatoST.java")
ITEMS = os.path.join(JAVA, u"ModItems.java")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
RECIPE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe\diesel_generator_controller.json")
BS = os.path.join(ASSETS, u"blockstates", u"diesel_generator_controller.json")
Z103 = os.path.join(ZT, u"_zf103_verify.py")
VERIFY = os.path.join(ZT, u"_zf125_verify.py")

KNIVES = [
    dict(id="K187", why=u"罐容量 8000 → 8001", path=BE,
         old=u"TANK_CAPACITY = 8000;", new=u"TANK_CAPACITY = 8001;",
         expect=u"B1 罐 8000 mB"),
    dict(id="K188", why=u"每 tick 发电 7200 → 7201", path=BE,
         old=u"ENERGY_PER_TICK = 7200;", new=u"ENERGY_PER_TICK = 7201;",
         expect=u"B3 每 tick 发 7200 FE"),
    dict(id="K189", why=u"铜块集合里删掉「氧化+涂蜡」那一项", path=STRUCT,
         old=(u"            Blocks.WAXED_WEATHERED_COPPER,\n"
              u"            Blocks.WAXED_OXIDIZED_COPPER);\n"),
         new=u"            Blocks.WAXED_WEATHERED_COPPER);\n",
         expect=u"A6 铜块 8 个变体全在"),
    dict(id="K190", why=u"接线块那一格不再认接线口", path=STRUCT,
         old=u"return state.is(ModBlocks.WIRING_BLOCK.get()) || isPort(state);",
         new=u"return state.is(ModBlocks.WIRING_BLOCK.get());",
         expect=u"A8 接线块那一格认"),
    dict(id="K191", why=u"给控制器本体也登记能量能力（电就不只从接线口出了）", path=MAIN,
         old=u"        // 51 大型柴油发电机：8000 mB 柴油罐",
         new=(u"        event.registerBlockEntity(\n"
              u"                Capabilities.EnergyStorage.BLOCK,\n"
              u"                ModBlocks.DIESEL_GENERATOR_BE.get(),\n"
              u"                (machine, side) -> machine.getEnergyStorage());\n\n"
              u"        // 51 大型柴油发电机：8000 mB 柴油罐"),
         expect=u"D5 控制器本体"),
    dict(id="K192", why=u"接线口不再看「成型没成型」，一律给电", path=PORTBE,
         old=u"master != null && master.isFormed() ? master.getEnergyStorage() : null;",
         new=u"master != null ? master.getEnergyStorage() : null;",
         expect=u"C5 未成型 / 没主控"),
    dict(id="K193", why=u"配方中排 铜块·熔炉·铜块 → 铜块·铜块·铜块", path=RECIPE,
         old=u"\"CBC\"", new=u"\"CCC\"",
         expect=u"E7 控制器配方逐字照用户原话"),
    dict(id="K194", why=u"zh_cn 的 invalid 键少一个 %s（四语言签名就不一致了）", path=os.path.join(LANG, u"zh_cn.json"),
         mode="resub",
         old_re=u"(\"gui\\.potato_s_t\\.diesel_generator\\.invalid\":\\s*\")[^\"]*(\")",
         new_re=u"\\g<1>结构缺口：第 %s 层 第 %s 排 第 %s 列 应该是 %s，现在那里是 %s（坐标 %s %s）\\g<2>",
         expect=u"E15 十二个新键的占位符签名四份一致"),
    dict(id="K195", why=u"方块状态里删掉 facing=west（那个朝向就没有模型了）", path=BS,
         old=(u"    \"facing=south\": {\n"
              u"      \"model\": \"potato_s_t:block/diesel_generator_controller\"\n"
              u"    },\n"
              u"    \"facing=west\": {\n"
              u"      \"model\": \"potato_s_t:block/diesel_generator_controller\"\n"
              u"    }\n"),
         new=(u"    \"facing=south\": {\n"
              u"      \"model\": \"potato_s_t:block/diesel_generator_controller\"\n"
              u"    }\n"),
         expect=u"E2 方块状态覆盖四个朝向"),
    dict(id="K196", why=u"创造页那一行删掉（§4.82 坑过的那个）", path=ITEMS,
         old=u"                        output.accept(ModBlocks.DIESEL_GENERATOR_ITEM.get());// ← 新增（0.11 ZF125 大型柴油发电机控制器）\n",
         new=u"",
         expect=u"D2 进创造页了"),
    dict(id="K197", why=u"往轮判据 _zf103 又写回 464", path=Z103,
         old=u"len(table) == 476", new=u"len(table) == 464",
         expect=u"F2 _zf103_verify.py 的键数"),
    dict(id="K198", why=u"判定改回 holes.isEmpty()（§4.56 坑过的那个）", path=STRUCT,
         old=u"return this.holeCount == 0;", new=u"return this.holes.isEmpty();",
         expect=u"A10 判定用的是 holeCount"),
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


if __name__ == "__main__":
    sys.exit(main())
