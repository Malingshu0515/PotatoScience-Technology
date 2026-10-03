# -*- coding: utf-8 -*-
u"""_zf190_verify.py —— ZF190 常驻门（0.14：召唤费 bug 修复 + 引力装置第三模式「坍缩模式-危险」）。

看四类东西：
  A 召唤费：固定 8M / 按容量封顶 / `fire()` 不再抽干整条 / `use()` 的闸门跟着换；
  B 坍缩模式：第三档与红色显示 / 4M + 50k per tick / 一次性豁免 / 电费与找回 / 2 分钟硬上限 + 30 威力爆炸 /
             无差别（含基岩边界）/ 掉落物销毁 / 强度伤害随年龄涨 / **先摘后播报**的顺序修复 / 语言键只加一个；
  C 证据：本轮探针 15/0 + 上一轮两个探针回归（20/0、4/0）+ 上一轮两道门仍全绿；
  D 交付：成品 == build 产物 / 没有探针类 / `_zf149_verify.py` 靶子联动 / 文档与公告写了这一轮。

跑法：python build\\zftools\\_zf190_verify.py
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
PRE = os.path.join(ZT, "zf190_pre")
GRAV = os.path.join(SRC, "GravityDeviceItem.java")
HOLE = os.path.join(SRC, "BlackHoleManager.java")
TOML = os.path.join(ROOT, "src", "main", "resources", "META-INF", "neoforge.mods.toml")
P190 = os.path.join(ZT, u"_zf190_probe_utf8.txt")
P186 = os.path.join(ZT, u"_zf186_probe_utf8.txt")
P188 = os.path.join(ZT, u"_zf188_probe_utf8.txt")
G186 = os.path.join(ZT, u"_zf186_verify.py")
G188 = os.path.join(ZT, u"_zf188_verify.py")
V149 = os.path.join(ZT, u"_zf149_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")
LIB = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.14.jar")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

PASS, FAIL = [], []


def check(ok, label, detail=u""):
    (PASS if ok else FAIL).append(label)
    print(u"  %s %s%s" % (u"[OK]  " if ok else u"[FAIL]", label, (u" ｜ " + detail) if detail else u""))
    return ok


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def strip_comments(t):
    t = re.sub(u"/\\*.*?\\*/", u"", t, flags=re.S)
    return re.sub(u"(?m)//.*$", u"", t)


def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def verdict(p):
    if not os.path.isfile(p):
        return None
    m = re.search(u"通过 = (\\d+)\\s+失败 = (\\d+)", read(p))
    return (int(m.group(1)), int(m.group(2))) if m else None


def main():
    grav, hole = read(GRAV), read(HOLE)
    grav_c, hole_c = strip_comments(grav), strip_comments(hole)

    print(u"== A 召唤费（用户报的 bug） ==")
    check(u"public static final int SUMMON_COST = 8_000_000;" in grav_c
          and u"public static int summonCost(int mode) {" in grav_c
          and u"Math.min(want, PotatoSTConfig.gravityCapacity())" in grav_c,
          u"A1 召唤费是**固定 8M**，并按当前容量封顶（小容量也能放得出来）")

    fire = grav_c[grav_c.index(u"private void fire("):]
    fire = fire[:fire.index(u"\n    }\n")]
    check(u"setEnergy(stack, getEnergy(stack) - cost);" in fire
          and u"setEnergy(stack, 0);" not in fire,
          u"A2 `fire()` 扣的是**这一次的费用**，不再是 `setEnergy(stack, 0)`（抽干整条 = 用户报的 bug）")

    use = grav_c[grav_c.index(u"public InteractionResultHolder<ItemStack> use("):]
    use = use[:use.index(u"\n    }\n")]
    check(u"int cost = summonCost(getMode(stack));" in use and u"getEnergy(stack) < cost" in use
          and u"gravityCapacity()" not in use,
          u"A3 `use()` 的闸门也换成「至少够这一次的费用」（容量调大不必先充满）")

    check(u"if (PotatoSTConfig.oneShotBlackHole() && mode != MODE_COLLAPSE) {" in fire,
          u"A4 一次性那一刀对**坍缩模式豁免**（它靠装置每 tick 供电，装置坏了黑洞立刻消失）")

    print(u"== B 坍缩模式 ==")
    check(u"public static final int MODE_COLLAPSE = 2;" in grav_c
          and u"case MODE_TOW -> MODE_COLLAPSE;" in grav_c
          and u"default -> MODE_SWALLOW;" in grav_c
          and u"message.potato_s_t.gravity.mode.collapse" in grav_c
          and u"net.minecraft.ChatFormatting.RED" in grav_c,
          u"B1 第三档「坍缩模式-危险」：循环三档 + 红色显示 + 只用**一个**新语言键")

    check(u"public static final int COLLAPSE_SUMMON_COST = 4_000_000;" in grav_c
          and u"public static final int COLLAPSE_COST_PER_TICK = 50_000;" in grav_c,
          u"B2 坍缩模式的价格：召唤 4M + 每 tick 50k（用户原话）")

    check(u"private static boolean payCollapsePower(Hole hole) {" in hole_c
          and u"private static ItemStack resolvePowerStack(Hole hole) {" in hole_c
          and u"!payCollapsePower(hole)" in hole_c
          and hole_c.index(u"!payCollapsePower(hole)") < hole_c.index(u"pullBlocks(hole);"),
          u"B3 电费在 tick 最前面交：交不出来 ⇒ 黑洞当场消失（装置换手/离线会现场找回）")

    check(u"public static final int HARD_CAP_TICKS = 2 * 60 * 20;" in hole_c
          and u"public static final float HARD_CAP_EXPLOSION_POWER = 30.0F;" in hole_c
          and u"level.explode(null, c.x, c.y, c.z, HARD_CAP_EXPLOSION_POWER," in hole_c
          and u"ExplosionInteraction.TNT" in hole_c,
          u"B4 2 分钟硬上限 ⇒ 销毁 + **真爆炸 30 威力**（原版 TNT 是 4；不是特效）")

    check(u"private static boolean eatable(BlockState state) {" in hole_c
          and u"defaultDestroyTime() >= 0.0F" in hole_c
          and u"Block moved = collapse ? state.getBlock() : hole.block;" in hole_c
          and u"placeAt(hole, p, moved)" in hole_c,
          u"B5 「无差别」吸方块（搬的是**原位那一种**），边界 = 空气/流体/不可破坏（基岩那类）")

    check(u"getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class, box)" in hole_c
          and u"item.discard();" in hole_c,
          u"B6 吸引到的**掉落物销毁**（discard，不掉落）")

    check(u"public static final double RAMP_PER_TICK = 1.0D / 400.0D;" in hole_c
          and u"return hole.mode == GravityDeviceItem.MODE_COLLAPSE ? 1.0D + hole.age * RAMP_PER_TICK : 1.0D;" in hole_c
          and u"1.6D / (dist / CORE + 1.0D) * ramp" in hole_c
          and u"e.hurt(level.damageSources().fellOutOfWorld(), (float) (4.0D * ramp));" in hole_c,
          u"B7 强度与伤害**随年龄递增**（每 400 tick 翻倍；普通模式倍率恒 1 ⇒ 行为不变）")

    ok_order = (re.search(u"it\\.remove\\(\\);[^\\n]*\\n\\s*collapse\\(hole\\);", hole) is not None
                and re.search(u"it\\.remove\\(\\);[^\\n]*\\n\\s*boom\\(hole\\);", hole) is not None
                and re.search(u"collapse\\(hole\\);[^\\n]*\\n\\s*it\\.remove\\(\\);", hole) is None
                and re.search(u"boom\\(hole\\);[^\\n]*\\n\\s*it\\.remove\\(\\);", hole) is None)
    check(ok_order,
          u"B8 顺手修的存档顺序 bug：一律**先 it.remove() 再 collapse()/boom()**"
          u"（旧顺序会把刚结束的黑洞写回存档 ⇒ 每次重启复活一次）")

    keys = {f: json.loads(read(os.path.join(LANG, f)))
            for f in (u"zh_cn.json", u"en_us.json", u"lzh.json", u"ja_jp.json", u"ru_ru.json")}
    want = {u"zh_cn.json": (690, u"坍缩模式-危险"), u"en_us.json": (690, u"Collapse mode - DANGER"),
            u"lzh.json": (692, u"坍縮之式-危"), u"ja_jp.json": (690, u"崩壊モード - 危険"),
            u"ru_ru.json": (690, u"Режим коллапса - ОПАСНО")}
    bad = [f for f, (n, v) in want.items()
           if len(keys[f]) != n or keys[f].get(u"message.potato_s_t.gravity.mode.collapse") != v]
    check(not bad, u"B9 五语种各 +1 键（690 / lzh 692），只有「模式显示」这一个新键，其余一个字没动",
          u"不符：%s" % bad)
    check(sha1(TOML) == sha1(os.path.join(PRE, r"src\main\resources\META-INF\neoforge.mods.toml")),
          u"B10 依赖清单仍然一字未动")

    print(u"== C 证据 ==")
    v190, v186, v188 = verdict(P190), verdict(P186), verdict(P188)
    check(v190 == (16, 0), u"C1 真服务端探针 Zf190Check 16/0（召唤费 + 坍缩模式全项）", u"读到 %s" % (v190,))
    check(v186 == (20, 0) and v188 == (4, 0),
          u"C2 回归再跑：Zf186Check 20/0、Zf188Check 4/0（老功能没被碰坏）",
          u"读到 %s / %s" % (v186, v188))
    r186 = subprocess.run([sys.executable, G186], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
    r188 = subprocess.run([sys.executable, G188], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
    check(r186.returncode == 0, u"C3 上一轮的门 `_zf186_verify.py` 仍然全绿（本轮跟平了它的 B2 判据）",
          u" ｜ ".join([l.strip() for l in r186.stdout.decode("utf-8", "replace").split(u"\n")
                        if l.strip().startswith(u"通过 =")][-1:]) or (u"rc=%d" % r186.returncode))
    check(r188.returncode == 0, u"C4 上一轮的门 `_zf188_verify.py` 仍然全绿（本轮跟平了它的键数判据）",
          u" ｜ ".join([l.strip() for l in r188.stdout.decode("utf-8", "replace").split(u"\n")
                        if l.strip().startswith(u"通过 =")][-1:]) or (u"rc=%d" % r188.returncode))

    print(u"== D 交付 ==")
    same_jar = os.path.isfile(JAR) and os.path.isfile(LIB) and sha1(JAR) == sha1(LIB)
    h = sha1(JAR) if os.path.isfile(JAR) else u"-"
    size = os.path.getsize(JAR) if os.path.isfile(JAR) else -1
    check(same_jar, u"D1 成品 == build 产物（逐字节）", u"%d 字节 / sha1 %s" % (size, h[:12]))
    jar_ok, detail = False, u"成品不在盘上"
    if os.path.isfile(JAR):
        z = zipfile.ZipFile(JAR)
        n = z.namelist()
        checks_ = [x for x in n if u"Check.class" in x]
        keys_jar = len(json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))
        jar_ok = (not checks_ and keys_jar == 690)
        detail = u"探针类 %d ｜ jar 内 zh_cn 键 %d（要 690）" % (len(checks_), keys_jar)
        z.close()
    check(jar_ok, u"D2 成品里没有探针类、语言键跟得上（690）", detail)

    v149 = read(V149)
    m_sha = re.search(u'WANT_SHA = u?"([0-9a-f]{40})"', v149)
    m_size = re.search(u"WANT_SIZE = (\\d+)", v149)
    check(bool(m_sha) and bool(m_size) and m_sha.group(1) == h and int(m_size.group(1)) == size,
          u"D3 §4.159 三处联动：`_zf149_verify.py` 靶子指向这份成品",
          u"WANT_SHA=%s WANT_SIZE=%s" % (m_sha.group(1)[:12] if m_sha else u"-",
                                        m_size.group(1) if m_size else u"-"))
    doc, ann = read(DOC), read(ANN)
    check(h in doc and h in ann and u"### 4.190 " in doc and u"## New in 0.14 ZF190" in ann,
          u"D4 档案 §4.190 + 英文公告都写了这一轮，且哈希跟到新成品",
          u"档案命中 %s ｜ 公告命中 %s" % (h[:12] in doc, h[:12] in ann))

    print(u"\n通过 = %d   失败 = %d" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print(u"  !! " + f)
    return 1 if FAIL else 0


if __name__ == u"__main__":
    sys.exit(main())
