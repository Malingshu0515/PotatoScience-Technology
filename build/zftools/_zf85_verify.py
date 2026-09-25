# -*- coding: utf-8 -*-
u"""_zf85_verify.py —— ZF85 交付校验（常驻，跑在门里）

用户诉求（截图 25 条）：「这个警告和报错很烦人 … 你看看能不能优化掉」。
本轮不改变任何**行为**，只把代码搬到 NeoForge 21.1 的正路上、并删掉死代码：

  A 弃用项清零：`ModFluids` 里不再有 `initializeClient`；`PotatoSTClient` 不再用 `bus =`
  B 贴图注册搬家**一个都没搬丢**（8 种流体的 still/flow 路径与改前件**逐条对齐**）
  C 客户端隔离：注册只在 Dist.CLIENT 的类里；`ModFluids` 不引用任何客户端类
  D 删掉的死代码确实没人用
  E 其它 25 条（恒为 300 的形参 / 空行 / -ise 拼写）
  F 文档与成品
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
TOOLS = os.path.join(ROOT, "build", "zftools")
DOCS = os.path.join(ROOT, "docs")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
BK = r"C:\PotatoST救援\zf85_pre"
FLUIDS = [u"oxygen", u"hydrogen", u"chlorine", u"crude_oil",
          u"diesel", u"naphtha", u"gasoline", u"lpg"]

passed = 0
failed = 0
fails = []


def check(label, cond):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label)
        print(u"  [FAIL] " + label)


def eq(label, want, got):
    check(u"%s（期望 %r，实际 %r）" % (label, want, got), want == got)


def read(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else None


# ================= A 弃用项清零 =================

def section_a():
    print(u"\n== A 弃用项清零（IDE 报的 5 条红 + 2 条构建警告）==")
    mf = read(os.path.join(SRC, "ModFluids.java")) or u""
    pc = read(os.path.join(SRC, "PotatoSTClient.java")) or u""
    # ⚠ 断言要盯**代码形态**：类注释里会提到"原先那 5 个 initializeClient 覆盖"（历史说明），
    #   拿裸词去查会把注释也算进去（第一版就这么误报的）。
    check(u"ModFluids 里不再有 initializeClient 覆盖（5 条红消除）",
          u"public void initializeClient(" not in mf and u"initializeClient(Consumer" not in mf)
    check(u"ModFluids 不再 import 客户端类 / Consumer",
          u"IClientFluidTypeExtensions" not in mf and u"function.Consumer" not in mf)
    check(u"PotatoSTClient 不再用已弃用的 bus = 参数",
          u"EventBusSubscriber.Bus.MOD" not in pc and u"bus = EventBusSubscriber" not in pc)
    check(u"PotatoSTClient 仍只在客户端加载（value = Dist.CLIENT）",
          u"@EventBusSubscriber(modid = PotatoST.MODID, value = Dist.CLIENT)" in pc)
    # 构建日志：本轮编译**一条警告都不该有**（改前有 7 条弃用警告）
    log = read(os.path.join(TOOLS, u"_zf85_compile.utf8.txt"))
    if log is None:
        print(u"  [SKIP] 没找到 _zf85_compile.utf8.txt（跳过编译警告核对）")
    else:
        warns = [l.strip() for l in log.split(u"\n") if u"警告" in l]
        eq(u"编译期 0 条警告（改前 7 条：5×initializeClient + 2×EventBusSubscriber.bus）",
           0, len(warns))
        for w in warns[:5]:
            print(u"     —— " + w)


# ================= B 贴图注册搬家没搬丢 =================

def section_b():
    print(u"\n== B 8 种流体的贴图路径：与改前件逐条对齐 ==")
    pc = read(os.path.join(SRC, "PotatoSTClient.java")) or u""
    # 改前（备份）里的路径是从 initializeClient 里硬写的；改后是 "block/" + name + "_still"
    # ⇒ 逐种流体断言：注册调用 + 工厂会拼出同样的名字。
    for name in FLUIDS:
        check(u"%s 有客户端注册" % name, u'textures("%s")' % name in pc)
    check(u"工厂按 `block/ + 名字 + _still` 拼（与改前逐字相同）",
          u'"block/" + name + "_still"' in pc)
    check(u"工厂按 `block/ + 名字 + _flow` 拼",
          u'"block/" + name + "_flow"' in pc)
    # 拿改前件里那些硬写路径核对：每一个都应该等于工厂拼出来的字符串
    old = read(os.path.join(BK, r"src\main\java\com\potatost\mod\ModFluids.java"))
    if old is None:
        check(u"改前件在（zf85_pre）", False)
        return
    # 改前件里有两种写法：三种气体 + 原油是**硬写**路径，四种产物是 `"block/" + name + "_still"` 拼的。
    # ⇒ 断言分两半：硬写的那 8 条必须被工厂覆盖到；拼字符串那套必须原样保留。
    old_paths = set(re.findall(r'"block/([a-z_]+)"', old))
    want = set()
    for name in [u"oxygen", u"hydrogen", u"chlorine", u"crude_oil"]:
        want.add(name + u"_still")
        want.add(name + u"_flow")
    missing = sorted(want - old_paths)
    extra = sorted(old_paths - want)
    check(u"改前件里**硬写**的 8 条路径正好是三种气体 + 原油（缺 %s / 多 %s）"
          % (missing or u"无", extra or u"无"), not missing and not extra)
    check(u"改前件里四种产物用的是 `\"block/\" + name + \"_still\"` 拼法",
          u'"block/" + name + "_still"' in old and u'"block/" + name + "_flow"' in old)
    check(u"改后仍是同一种拼法（四种产物一个字母没改）",
          u'"block/" + name + "_still"' in pc and u'"block/" + name + "_flow"' in pc)
    # ModFluids 侧：8 个 FluidType 都还在（注册项没被搬丢）
    for name in [u"OXYGEN", u"HYDROGEN", u"CHLORINE", u"CRUDE_OIL", u"DIESEL",
                 u"NAPHTHA", u"GASOLINE", u"LPG"]:
        check(u"ModFluids.%s_TYPE 仍在" % name, (name + u"_TYPE") in (read(
            os.path.join(SRC, "ModFluids.java")) or u""))


# ================= C 客户端隔离 =================

def section_c():
    print(u"\n== C 客户端隔离（服务端绝不能碰客户端类）==")
    mf = read(os.path.join(SRC, "ModFluids.java")) or u""
    for bad in [u"net.minecraft.client", u"net.neoforged.neoforge.client",
                u"IClientFluidTypeExtensions"]:
        check(u"ModFluids 不引用 %s" % bad, bad not in mf)
    pc = read(os.path.join(SRC, "PotatoSTClient.java")) or u""
    check(u"客户端注册在 PotatoSTClient（自带 Dist.CLIENT 门）",
          u"Dist.CLIENT" in pc and u"registerFluidType" in pc)
    check(u"registerFluidType 的扩展实例由本类的工厂产出（不是从别处 import 的客户端对象）",
          u"private static IClientFluidTypeExtensions textures(String name)" in pc)


# ================= D 死代码确实没人用 =================

def section_d():
    print(u"\n== D 删掉的死代码确实没人调 ==")
    hits = []
    for dp, _, fs in os.walk(os.path.join(ROOT, "src", "main", "java")):
        for f in fs:
            if not f.endswith(u".java"):
                continue
            t = read(os.path.join(dp, f)) or u""
            for pat in [u"ModFluids.idOf", u"ModFluids.byId", u"ModFluids.GAS_COUNT"]:
                if pat in t:
                    hits.append(u"%s → %s" % (f, pat))
    check(u"全工程没有 ModFluids.idOf/byId/GAS_COUNT 的引用（%s）" % (hits or u"无"), not hits)
    mf = read(os.path.join(SRC, "ModFluids.java")) or u""
    check(u"三个成员确实已从 ModFluids 删除",
          u"GAS_COUNT" not in mf and u"public static int idOf(" not in mf
          and u"public static Fluid byId(" not in mf)
    check(u"类注释里交代了它们为什么被删（历史记录留档）", u"ZF85 删掉了这里的" in mf)


# ================= E 其余 25 条 =================

def section_e():
    print(u"\n== E 其余几条 ==")
    mf = read(os.path.join(SRC, "ModFluids.java")) or u""
    check(u"liquidType 不再有形参 temperature（IDE 说它恒为 300）",
          u"liquidType(String name, int density, int viscosity)" in mf)
    check(u"温度仍在工厂里显式设成 300", u".temperature(300)" in mf)
    check(u"8 个调用点都不再传第 4 个参数（4 种分馏产物 + 4 种酸）",
          mf.count(u"liquidType(\"") == 8
          and not re.search(r'liquidType\("[a-z]+", \d+, \d+,', mf))
    # ⚠ 缩进要按文件里的真实形态比（javadoc 是 5 个空格 + `* `）：第一版写成 `\n * ` 直接查不到。
    check(u"gases() 的 javadoc 里那处空行已重排（IDE 的「空行行将被忽略」）",
          u"chlorine).\n     * Deliberately a METHOD" in mf
          and u"chlorine).\n     *\n" not in mf)
    check(u"拼写改成美式 initializer（IDE 的 -iz- 提示）",
          u"initializer" in mf and u"initialiser" not in mf)


# ================= F 文档与成品 =================

def section_f():
    print(u"\n== F 文档与成品 ==")
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    check(u"档案里有 ZF85 那一行", u"| ZF85 |" in arch)
    check(u"档案里记了用户原话（警告很烦人）", u"警告和报错很烦人" in arch)
    check(u"档案里写明「行为一个字节没改」（只搬代码 / 删死代码）",
          u"行为一个字节没改" in arch or u"没有改动任何行为" in arch)
    if not os.path.exists(JAR):
        check(u"成品 jar 存在", False)
        return
    sha = hashlib.sha1(open(JAR, "rb").read()).hexdigest()
    rec = read(JAR + u".sha1")
    check(u".sha1 与 jar 一致（%s…）" % sha[:8], rec is not None and rec.strip().lower() == sha)
    with zipfile.ZipFile(JAR) as zf:
        names = zf.namelist()
        bad = [n for n in names if u"Check" in n.split(u"/")[-1] and n.endswith(u".class")]
        check(u"成品里没有探针 class（%s）" % (bad or u"0 个"), not bad)
        cls = [n for n in names if n.endswith(u"PotatoSTClient.class")]
        check(u"成品里有 PotatoSTClient（客户端注册那一份）", bool(cls))


def main():
    print(u"=========== ZF85 校验：清掉 ModFluids 的 25 条警告/报错 ===========")
    section_a()
    section_b()
    section_c()
    section_d()
    section_e()
    section_f()
    print(u"\n------------------------------")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
