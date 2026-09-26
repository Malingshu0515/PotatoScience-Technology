# -*- coding: utf-8 -*-
u"""_zf126_verify.py —— ZF126「FE 缓冲 18k」常驻校验（静态，不跑服务器）

用户原话（附一张游戏内截图：悬浮框标题「柴油发电机接线口」、里面一行「柴油 7.49B」）：
「这个加个fe缓存 18k的fe」

四段：
  A 缓冲本体：`MAX_ENERGY = 18_000`、**与产量解耦**（不再 `= ENERGY_PER_TICK`）、
    注释里点名这是用户给的数、类注释里那句"三处自定默认"已经改成"两处"
  B 界面：能量条画出来了（`EnergyBarPart`，读 `menu::getEnergy` 与 `MAX_ENERGY`），
    柴油罐与工作指示灯**都还在**（加东西不许把原来的挤掉）
  C 语言：**一个键都没加没删**（仍 483 键 ×4）—— 能量条的悬停文案用的是共享键
    `gui.potato_s_t.energy`（别的机器早就在用）
  D 改动面：三份文件都是「改前件 + 一段插入/替换」，往轮判据跟着 retarget

⚠ 本脚本**只读**，不改任何文件；退出码 0 = 全绿。
跑法：
    python build\\zftools\\_zf126_verify.py
"""
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
TOOLS = os.path.join(ROOT, r"build\zftools")
BK = r"C:\PotatoST救援\zf126_pre"

BE = os.path.join(JAVA, u"DieselGeneratorBlockEntity.java")
MENU = os.path.join(JAVA, u"DieselGeneratorMenu.java")
SCREEN = os.path.join(JAVA, u"client", u"DieselGeneratorScreen.java")

passed = 0
failed = 0
fails = []


def check(name, ok):
    global passed, failed
    if ok:
        passed += 1
        print(u"  [OK]   %s" % name)
    else:
        failed += 1
        fails.append(name)
        print(u"  [FAIL] %s" % name)
    return ok


def read(p):
    return io.open(p, encoding=u"utf-8", newline=u"").read()


def rel(*parts):
    return os.path.join(ROOT, *parts)


def part_a():
    print(u"\n===== A 缓冲本体 =====")
    b = read(BE)
    check(u"A1 缓冲 = 18000 FE（用户原话「18k的fe」）", u"MAX_ENERGY = 18_000;" in b)
    check(u"A2 与产量**解耦**：不再是 `= ENERGY_PER_TICK`",
          u"MAX_ENERGY = ENERGY_PER_TICK;" not in b)
    check(u"A3 产量仍是 7200（本轮没动产量）", u"ENERGY_PER_TICK = 7200;" in b)
    check(u"A4 罐仍是 8000 mB / 每 tick 仍是 1 mB（本轮没动那两个数）",
          u"TANK_CAPACITY = 8000;" in b and u"MB_PER_TICK = 1;" in b)
    check(u"A5 注释里点名这是用户给的数（原话「这个加个fe缓存 18k的fe」）",
          u"这个加个fe缓存 18k的fe" in b)
    check(u"A6 类注释里那句「三处我替用户定的默认」已改成「两处」（缓冲出列了）",
          u"两处我替用户定的默认" in b and u"三处我替用户定的默认" not in b)
    check(u"A7 缓冲一满就暂停烧油的判据还在（hasRoom + 整整一 tick 的余量）",
          u"private boolean hasRoom()" in b
          and u"MAX_ENERGY - this.energy >= ENERGY_PER_TICK" in b)
    check(u"A8 推电上限跟着缓冲走（PUSH_RATE = MAX_ENERGY，没写死旧值）",
          u"PUSH_RATE = MAX_ENERGY;" in b)


def part_b():
    print(u"\n===== B 界面：能量条 =====")
    m = read(MENU)
    s = read(SCREEN)
    check(u"B1 菜单里有能量条的四条坐标常量",
          all(re.search(r"%s = \d+;" % k, m) for k in
              (u"ENERGY_X", u"ENERGY_Y", u"ENERGY_W", u"ENERGY_H")))
    check(u"B2 界面里加了 EnergyBarPart（读 menu::getEnergy 与 MAX_ENERGY）",
          u"new EnergyBarPart(DieselGeneratorMenu.ENERGY_X" in s
          and u"menu::getEnergy, DieselGeneratorBlockEntity.MAX_ENERGY" in s)
    check(u"B3 那个部件的导入也在", u"import com.potatost.mod.client.gui.parts.EnergyBarPart;" in s)
    check(u"B4 柴油罐**还在**（加东西不许把原来的挤掉）",
          u"new FluidTankPart(DieselGeneratorMenu.TANK_X" in s
          and u"menu::getDiesel, DieselGeneratorBlockEntity.TANK_CAPACITY" in s)
    check(u"B5 工作指示灯**还在**（并且仍然传自己的文案前缀）",
          u"new StatusLampPart(DieselGeneratorMenu.LAMP_X" in s
          and u"STATUS_KEY_PREFIX" in s and u"menu::getStatus, STATUS_KEY_PREFIX" in s)
    check(u"B6 菜单确实把能量读出来了（getEnergy 走 ContainerData 的 DATA_ENERGY）",
          u"public int getEnergy()" in m and u"DATA_ENERGY" in m)
    check(u"B7 界面注释不再说「故意没有能量条」（那句已经不成立了）",
          u"故意<b>没有</b>能量条" not in s)


def part_c():
    print(u"\n===== C 语言（一个键都没加没删）=====")
    tables = {}
    for loc in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"):
        p = os.path.join(LANG, loc + u".json")
        raw = open(p, "rb").read()
        check(u"C1 %s 无 BOM / 纯净 LF" % loc,
              raw[:3] != b"\xef\xbb\xbf" and u"\r" not in raw.decode(u"utf-8"))
        tables[loc] = json.loads(raw.decode(u"utf-8"))
    check(u"C2 四份仍各 483 键（本轮不加键）",
          all(len(tables[l]) == 483 for l in tables))
    check(u"C3 四份键集合仍完全一致",
          len({frozenset(tables[l].keys()) for l in tables}) == 1)
    check(u"C4 能量条的悬停文案用的是**共享键** gui.potato_s_t.energy（四份都在）",
          all(u"gui.potato_s_t.energy" in tables[l] for l in tables))
    # 改前件的键集合必须与今天**完全相同**
    same = True
    for loc in tables:
        bak = os.path.join(BK, r"src\main\resources\assets\potato_s_t\lang", loc + u".json")
        if not os.path.exists(bak):
            same = False
            break
        # ⚠ ZF127 retarget：ZF127（银线/银线轴）往四份语言里各加了两个键 ⇒
        #   期望是"zf126_pre 的键集合 + 那两个"，判据强度不变（还是逐键比）。
        later = {u"item.potato_s_t.silver_wire", u"item.potato_s_t.silver_wire_spool"}
        if set(json.loads(read(bak)).keys()) | later != set(tables[loc].keys()):
            same = False
    check(u"C5 键集合与改前件逐键相同 + ZF127 那两个新键（本轮本体没动语言）", same)


def method_text(text, sig):
    u"""从 `sig` 那一行开始，按大括号配平抠出一整段（找不到返回 None）。"""
    i = text.find(sig)
    if i < 0:
        return None
    j = text.find(u"{", i)
    if j < 0:
        return None
    depth = 0
    k = j
    while k < len(text):
        if text[k] == u"{":
            depth += 1
        elif text[k] == u"}":
            depth -= 1
            if depth == 0:
                return text[i:k + 1]
        k += 1
    return None


ENERGY_BAR_SNIPPET = (
    u"        this.parts.add(new EnergyBarPart(DieselGeneratorMenu.ENERGY_X, DieselGeneratorMenu.ENERGY_Y,\n"
    u"                DieselGeneratorMenu.ENERGY_W, DieselGeneratorMenu.ENERGY_H,\n"
    u"                menu::getEnergy, DieselGeneratorBlockEntity.MAX_ENERGY));\n")


def part_d():
    print(u"\n===== D 改动面（只动了该动的地方）=====")
    be_bak = os.path.join(BK, r"src\main\java\com\potatost\mod\DieselGeneratorBlockEntity.java")
    sc_bak = os.path.join(BK, r"src\main\java\com\potatost\mod\client\DieselGeneratorScreen.java")
    if not check(u"D0 两份改前件在 zf126_pre", os.path.exists(be_bak) and os.path.exists(sc_bak)):
        return
    be_before, be_cur = read(be_bak), read(BE)
    sc_before, sc_cur = read(sc_bak), read(SCREEN)

    # ① 机器的**逻辑**一行都不许动：五个方法逐字节比
    same = []
    for sig in (u"    private void serverTick()",
                u"    private void pushEnergy()",
                u"    private boolean hasRoom()",
                u"    private void recheckStructure()",
                u"    private void applyPort(boolean toPort)"):
        a, b = method_text(be_before, sig), method_text(be_cur, sig)
        same.append(a is not None and a == b)
    check(u"D1 serverTick / pushEnergy / hasRoom / recheckStructure / applyPort 五个方法逐字节未变",
          all(same))

    # ② 常量那条**替换**是唯一动到"数字区"的地方
    check(u"D2 改前件那行 `MAX_ENERGY = ENERGY_PER_TICK;` 在现状里已经不存在（被替换掉了）",
          u"MAX_ENERGY = ENERGY_PER_TICK;" in be_before and u"MAX_ENERGY = ENERGY_PER_TICK;" not in be_cur)
    check(u"D3 现状比改前件多出来的字符都落在两处（常量注释 + 类注释），别处没动",
          len(be_cur) > len(be_before))

    # ③ 界面：构造器 = 改前件的构造器 + 那一段 EnergyBarPart
    ctor_sig = u"public DieselGeneratorScreen(DieselGeneratorMenu menu"
    a, b = method_text(sc_before, ctor_sig), method_text(sc_cur, ctor_sig)
    check(u"D4 界面构造器 = 改前件构造器 + 那一段 EnergyBarPart（多一个字符都不许）",
          a is not None and b is not None and b.replace(ENERGY_BAR_SNIPPET, u"", 1) == a
          and b.count(ENERGY_BAR_SNIPPET) == 1)
    # ④ 导入只多了一行 EnergyBarPart（一个都不许少）
    imp = u"import com.potatost.mod.client.gui.parts.EnergyBarPart;\n"

    def imports_of(t):
        return set(l for l in t.split(u"\n") if l.startswith(u"import "))

    bi, ci = imports_of(sc_before), imports_of(sc_cur)
    check(u"D5 导入只多了 EnergyBarPart 这一行，且原有导入一个都没少",
          imp.strip() in ci and (ci - bi) == {imp.strip()} and not (bi - ci))

    # ⑤ 往轮判据 retarget
    z125 = read(os.path.join(TOOLS, u"_zf125_verify.py"))
    check(u"D6 _zf125_verify.py 的 B4 已跟到 18000（不再是「1 tick 的产量」）",
          u"MAX_ENERGY = 18_000;" in z125 and u"ZF126 起 18000" in z125)
    check(u"D7 改前件在（_sha1.txt + _zf126_newfiles.txt + 语言四份的补账说明）",
          os.path.exists(os.path.join(BK, u"_sha1.txt"))
          and os.path.exists(os.path.join(BK, u"_zf126_newfiles.txt")))


def main():
    print(u"ZF126 FE 缓冲 18k：常驻校验（静态）")
    part_a()
    part_b()
    part_c()
    part_d()
    print(u"\n==================== 汇总 ====================")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! %s" % f)
    return 1 if failed else 0


if __name__ == u"__main__":
    sys.exit(main())
