# -*- coding: utf-8 -*-
u"""_zf186_verify.py —— ZF186 常驻门（0.14：配置系统 + 配置界面，配置项真的驱动行为）。

看四类东西：
  A 基建：配置类 / 兜底取值 / 主类注册 / **依赖一个字没加** / 客户端隔离 / 无反射；
  B 接线：三个点名项 + 我加的那些，逐个对着源码核（常量删干净、取值器用上、两个开关互相独立）；
  C 文案：五份 lang 键齐 + Java 里每个 translation 键都在 lang 里 + 中文串无 ASCII 转义引号；
  D 交付：真服务端探针报告 16+/0、成品 == build 产物、jar 里没有探针类、mods.toml 依赖段没变、
           `_zf149_verify.py` 的哈希靶子已联动。

跑法：python build\\zftools\\_zf186_verify.py
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
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
PRE = os.path.join(ZT, "zf186_pre")
CFG = os.path.join(SRC, "PotatoSTConfig.java")
GRAV = os.path.join(SRC, "GravityDeviceItem.java")
HOLE = os.path.join(SRC, "BlackHoleManager.java")
BATT = os.path.join(SRC, "LithiumBatteryBlockEntity.java")
BATTBLK = os.path.join(SRC, "LithiumBatteryBlock.java")
MAIN = os.path.join(SRC, "PotatoST.java")
SCREEN = os.path.join(SRC, "client", "PotatoSTConfigScreen.java")
PROBE = os.path.join(ZT, u"_zf186_probe_utf8.txt")
V149 = os.path.join(ZT, u"_zf149_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")
LIB = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.14.jar")
TOML_SRC = os.path.join(ROOT, "src", "main", "resources", "META-INF", "neoforge.mods.toml")

PASS, FAIL = [], []


def check(ok, label, detail=u""):
    (PASS if ok else FAIL).append(label)
    print(u"  %s %s%s" % (u"[OK]  " if ok else u"[FAIL]", label,
                          (u" ｜ " + detail) if detail else u""))
    return ok


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def strip_comments(t):
    u"""去掉块注释与行注释 —— 判据只该看**代码**，不能被我自己的类注释里那些
    「{@code ConfigurationScreen}」「老的 PER_BLOCK = 4_000_000L」误伤（本轮真踩过：
    第一版门就是这么红的，红的是判据不是代码）。"""
    t = re.sub(u"/\\*.*?\\*/", u"", t, flags=re.S)
    t = re.sub(u"(?m)//.*$", u"", t)
    return t


def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def main():
    cfg = read(CFG)
    grav = read(GRAV)
    hole = read(HOLE)
    batt = read(BATT)
    battblk = read(BATTBLK)
    main_t = read(MAIN)
    screen = read(SCREEN)
    # 代码体（去注释）：所有「某某字面量不该再出现」的判据都只对这个版本生效
    cfg_c, grav_c, hole_c, batt_c, battblk_c = map(strip_comments, (cfg, grav, hole, batt, battblk))

    print(u"== A 基建 ==")
    want = [
        (u"one_shot", u"true"), (u"lifetime_seconds", u"20"), (u"max_blocks", u"1500"),
        (u"scan_radius_blocks", u"40"), (u"pull_entities", u"true"), (u"void_damage", u"true"),
        (u"charge_seconds", u"30"), (u"capacity_fe", u"8_000_000"),
    ]
    miss = [k for k, v in want if (u'define("%s", %s)' % (k, v)) not in cfg
            and (u'defineInRange("%s", %s,' % (k, v)) not in cfg]
    # 带范围的三项也把范围一起核（用户点名要的区间）
    ranges = [u'defineInRange("charge_seconds", 30, 5, 60)',
              u'defineInRange("per_block_fe", 4_000_000, 1_000_000, 20_000_000)',
              u'defineInRange("lifetime_seconds", 20, 5, 120)']
    miss_r = [r for r in ranges if r not in cfg]
    check(not miss and not miss_r and u"ModConfigSpec SPEC" in cfg,
          u"A1 配置类：SPEC + 点名三项的默认值/区间对得上表",
          u"缺 %s / 区间缺 %s" % (miss, miss_r))

    n_get = cfg_c.count(u".get()")
    guard = (u"private static boolean specReady()" in cfg_c and u"SPEC.isLoaded()" in cfg_c
             and u"v.getDefault()" in cfg_c)
    check(n_get == 2 and guard,
          u"A2 取值器全走 specReady() 兜底（没加载时返回出厂值，绝不裸 .get()）",
          u"代码里 .get() 出现 %d 次（应当恰好 2 次，都在 b()/i() 里）" % n_get)

    check(u"registerConfig(net.neoforged.fml.config.ModConfig.Type.COMMON" in main_t
          and u"PotatoSTConfig.SPEC" in main_t,
          u"A3 主类把 SPEC 注册成 COMMON 配置（客户端/服务端各读自己那份）")

    same_toml = (sha1(TOML_SRC) == sha1(os.path.join(PRE, r"src\main\resources\META-INF\neoforge.mods.toml")))
    check(same_toml, u"A4 依赖一个字没加（neoforge.mods.toml 与改前备份逐字节相同）",
          u"sha1 %s" % sha1(TOML_SRC)[:12])

    bad_ref = []
    for dirpath, _dirs, files in os.walk(SRC):
        if os.path.basename(dirpath) == u"client":
            continue
        for fn in files:
            if fn.endswith(u".java") and fn != u"PotatoSTConfigScreen.java":
                t = strip_comments(read(os.path.join(dirpath, fn)))
                if u"IConfigScreenFactory" in t or u"ConfigurationScreen" in t:
                    bad_ref.append(fn)
    ok_screen = (u"value = Dist.CLIENT" in strip_comments(screen)
                 and u"IConfigScreenFactory.class" in strip_comments(screen)
                 and u"FMLClientSetupEvent" in strip_comments(screen) and not bad_ref)
    check(ok_screen,
          u"A5 配置界面只在客户端（非 client 代码里没有 IConfigScreenFactory/ConfigurationScreen）",
          u"越界的文件 = %s" % bad_ref)

    refl = [fn for fn in (u"PotatoSTConfig.java", u"PotatoSTConfigScreen.java")
            if re.search(u"Class\\.forName|getDeclaredField|getDeclaredMethod|setAccessible",
                         read(os.path.join(SRC, u"client", fn)) if fn.endswith(u"Screen.java") else read(os.path.join(SRC, fn)))]
    check(not refl, u"A6 新增代码里没有反射（本工程硬规矩）", u"命中 %s" % refl)

    print(u"== B 接线 ==")
    b1 = (u"int CAPACITY = 8_000_000" not in grav_c and u"CHARGE_TICKS = 20 * 25" not in grav_c
          and grav_c.count(u"PotatoSTConfig.gravityCapacity()") >= 6
          and grav_c.count(u"PotatoSTConfig.gravityChargeTicks()") >= 3
          and u"return PotatoSTConfig.gravityChargeTicks();" in grav_c)
    check(b1, u"B1 引力装置：CAPACITY/CHARGE_TICKS 两个常量删干净，容量/蓄力全走配置",
          u"代码里 gravityCapacity() %d 处、gravityChargeTicks() %d 处"
          % (grav_c.count(u"PotatoSTConfig.gravityCapacity()"),
             grav_c.count(u"PotatoSTConfig.gravityChargeTicks()")))

    fire = grav_c[grav_c.index(u"private void fire("):]
    fire = fire[:fire.index(u"\n    }\n")]
    # 0.14 ZF190 跟平：扣电从「抽干整条」改成「扣这一次的召唤费」，一次性那一刀照旧受
    # oneShotBlackHole() 管（坍缩模式的豁免由 `_zf190_verify.py` 单独钉）。判据强度没降。
    b2 = (u"setEnergy(stack, getEnergy(stack) - cost);" in fire
          and u"if (PotatoSTConfig.oneShotBlackHole()" in fire
          and fire.index(u"if (PotatoSTConfig.oneShotBlackHole()") < fire.index(u"hurtAndBreak"))
    check(b2, u"B2 点名①：扣电永远发生，损坏那一刀受 oneShotBlackHole() 管（false 就不坏）")

    b3 = (u"LIFETIME = 20 * 20" not in hole_c and u"MAX_BLOCKS = 1500" not in hole_c
          and u"HALF = 40" not in hole_c and u"SCAN_SIDE = HALF" not in hole_c
          and u"SCAN_VOLUME = SCAN_SIDE" not in hole_c
          and hole_c.count(u"lifetime()") >= 4 and hole_c.count(u"maxBlocks()") >= 3
          and hole_c.count(u"half()") >= 3 and hole_c.count(u"scanVolume()") >= 2)
    check(b3, u"B3 黑洞：寿命/搬运上限/扫描半径三个常量删干净，6 处改走配置",
          u"lifetime() %d、maxBlocks() %d、half() %d、scanVolume() %d"
          % (hole_c.count(u"lifetime()"), hole_c.count(u"maxBlocks()"), hole_c.count(u"half()"),
             hole_c.count(u"scanVolume()")))

    b4 = (u"PER_BLOCK = 4_000_000L" not in batt_c and u"TRANSFER_RATE = 65_536" not in batt_c
          and u"MAX_BLOCKS = 800" not in batt_c
          and all(u"public static %s %s()" % (t, n) in batt_c
                  for t, n in ((u"long", u"perBlock"), (u"int", u"transferRate"), (u"int", u"maxBlocks")))
          and u"perBlock()" in battblk_c and u"maxBlocks()" in battblk_c
          and u".PER_BLOCK" not in battblk_c and u".MAX_BLOCKS" not in battblk_c)
    check(b4, u"B4 点名③：锂电池 三个常量删干净，单块容量真的被总容量/成型/解散三处用上",
          u"perBlock() %d 处（实体）+ %d 处（方块）"
          % (batt_c.count(u"perBlock()"), battblk_c.count(u"perBlock()")))

    b5 = (u"if (!pull && !hurt) {" in hole_c and u"if (hurt && dist <= VOID_RADIUS" in hole_c)
    check(b5, u"B5 两个开关互相独立（关掉「吸引生物」不该顺手把虚空伤害也关掉）")

    print(u"== C 文案 ==")
    keys = {}
    for f in (u"zh_cn.json", u"en_us.json", u"lzh.json", u"ja_jp.json", u"ru_ru.json"):
        keys[f] = set(json.loads(read(os.path.join(LANG, f))))
    base = keys[u"zh_cn.json"]
    parity = all(not (base - keys[f]) and not (keys[f] - base - {u"language.name", u"language.region"})
                 for f in keys)
    check(parity and len(base) >= 689,
          u"C1 五份 lang 键齐（配置界面的 34 个新键一次补齐五语种）",
          u"、".join(u"%s=%d" % (f, len(v)) for f, v in sorted(keys.items())))

    tr_keys = set(re.findall(u'translation\\("([^"]+)"\\)', cfg_c))
    # 只有**条目级**的键才有 .tooltip（section.xxx 是分组标题，没有 tooltip）
    entry_keys = {k for k in tr_keys if u".section." not in k}
    item_keys = set(re.findall(u'"(tooltip\\.potato_s_t\\.gravity_device[^"]*)"', grav_c))
    missing = {}
    for f, ks in keys.items():
        need = set(tr_keys)
        for k in entry_keys:
            need.add(k + u".tooltip")
        need |= item_keys
        lack = sorted(need - ks)
        if lack:
            missing[f] = lack[:4]
    check(not missing and len(tr_keys) >= 9 and len(item_keys) >= 3,
          u"C2 配置界面每个键（条目级还要 .tooltip）+ 引力装置三行动态 tooltip 都在五语种里",
          u"Java 侧 %d 个界面键（其中条目级 %d）/ %d 个物品键；缺 %s"
          % (len(tr_keys), len(entry_keys), len(item_keys), missing))

    cjk = re.compile(u"[\u4e00-\u9fff]")
    esc = []
    for p in (CFG, SCREEN, os.path.join(ZT, "check", u"Zf186Check.java")):
        if not os.path.isfile(p):
            continue
        for i, line in enumerate(read(p).split(u"\n"), 1):
            if cjk.search(line) and u'\\"' in line:
                esc.append(u"%s:%d" % (os.path.basename(p), i))
    check(not esc, u"C3 新增中文串里没有 ASCII 转义引号（§4.53 的硬规矩）", u"命中 %s" % esc)

    print(u"== D 交付 ==")
    probe_ok, probe_line = False, u"（报告不在盘上）"
    if os.path.isfile(PROBE):
        pt = read(PROBE)
        m = re.search(u"通过 = (\\d+)\\s+失败 = (\\d+)", pt)
        if m:
            ok_n, bad_n = int(m.group(1)), int(m.group(2))
            must = [u"D1 默认一次性", u"D2 改成「非一次性」", u"C2 配置改成 5 秒 / 60 秒",
                    u"B2 配置改成 12M", u"E1 寿命改成 5 秒", u"F1 半径改成 8", u"G2b 打开"]
            absent = [x for x in must if x not in pt]
            probe_ok = (bad_n == 0 and ok_n >= 18 and not absent)
            probe_line = u"通过 = %d 失败 = %d%s" % (ok_n, bad_n,
                                                 (u"，缺判据 %s" % absent) if absent else u"")
    check(probe_ok, u"D0 真服务端探针：配置项真的驱动行为（点名三项 + 黑洞六项）", probe_line)

    same_jar = os.path.isfile(JAR) and os.path.isfile(LIB) and sha1(JAR) == sha1(LIB)
    check(same_jar, u"D1 成品 release/PotatoST-0.14.jar == build 产物（逐字节）",
          u"%d 字节 / sha1 %s" % (os.path.getsize(JAR) if os.path.isfile(JAR) else -1,
                                sha1(JAR)[:12] if os.path.isfile(JAR) else u"-"))

    jar_ok, jar_detail = False, u"成品不在盘上"
    if os.path.isfile(JAR):
        z = zipfile.ZipFile(JAR)
        names = z.namelist()
        checks_ = [n for n in names if u"Check" in n and n.endswith(u".class")]
        has_cfg = u"com/potatost/mod/PotatoSTConfig.class" in names
        has_screen = u"com/potatost/mod/client/PotatoSTConfigScreen.class" in names
        keys_jar = {}
        for f, short in ((u"zh_cn", u"zh_cn"), (u"lzh", u"lzh")):
            keys_jar[short] = len(json.loads(z.read(u"assets/potato_s_t/lang/%s.json" % f).decode(u"utf-8")))
        jar_ok = (not checks_) and has_cfg and has_screen and keys_jar[u"zh_cn"] >= 689
        jar_detail = u"探针类 %d 个；新类 cfg/screen = %s/%s；jar 内键 %s" % (
            len(checks_), has_cfg, has_screen, keys_jar)
        z.close()
    check(jar_ok, u"D2 成品里有新类、没有探针类、语言文件跟得上", jar_detail)

    dep_ok, dep_detail = False, u"缺备份成品"
    pre_jar = os.path.join(PRE, r"release\PotatoST-0.14.jar")
    if os.path.isfile(JAR) and os.path.isfile(pre_jar):
        a = zipfile.ZipFile(JAR).read(u"META-INF/neoforge.mods.toml").decode(u"utf-8")
        b = zipfile.ZipFile(pre_jar).read(u"META-INF/neoforge.mods.toml").decode(u"utf-8")
        dep_ok = (a == b)
        dep_detail = u"依赖段%s（mods.toml 逐字节相同）" % (u"没动" if dep_ok else u"被改过")
    check(dep_ok, u"D3 成品里的依赖清单与改前一字不差（「不是必须依赖项」的物证）", dep_detail)

    v149 = read(V149)
    m_sha = re.search(u'WANT_SHA = u?"([0-9a-f]{40})"', v149)
    m_size = re.search(u"WANT_SIZE = (\\d+)", v149)
    linked = (os.path.isfile(JAR) and m_sha and m_size
              and m_sha.group(1) == sha1(JAR) and int(m_size.group(1)) == os.path.getsize(JAR))
    check(linked, u"D4 §4.159 三处联动：`_zf149_verify.py` 的靶子已指向这份成品",
          u"WANT_SHA=%s WANT_SIZE=%s" % (m_sha.group(1)[:12] if m_sha else u"-",
                                        m_size.group(1) if m_size else u"-"))

    print(u"\n通过 = %d   失败 = %d" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print(u"  !! " + f)
    return 1 if FAIL else 0


if __name__ == u"__main__":
    sys.exit(main())
