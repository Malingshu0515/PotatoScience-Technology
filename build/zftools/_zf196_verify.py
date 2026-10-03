# -*- coding: utf-8 -*-
u"""_zf196_verify.py —— ZF196 常驻门（0.14：坍缩模式"看得见地拆"——近处优先 + 像爆炸那样的碎裂）。

看四类东西：
  A 代码：坍缩模式**不走线性游标**、改走"球内取样"（近处优先）/ 暴露的飞、埋着的就地拆 /
         拆除走原版 2001 事件 / 半径随年龄涨且受配置扫描半径约束 / 拆除与搬运都算进 `pulled` 上限；
  B 回归：语言键没动（691 / lzh 693）、依赖清单一字未动；
  C 证据：探针 Zf196Check 5/0 + 回归 Zf194Check 5/0、Zf192Check 6/0、Zf190Check 16/0、
          Zf186Check 20/0、Zf188Check 4/0；四道老门仍全绿（本轮跟平了 `_zf190` 的 B5、`_zf194` 的 A1/A5）；
  D 交付：成品 == build 产物 / 没有探针类 / `_zf149_verify.py` 靶子联动 / 文档与公告写了这一轮。

跑法：python build\\zftools\\_zf196_verify.py
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
PRE = os.path.join(ZT, "zf196_pre")
HOLE = os.path.join(SRC, "BlackHoleManager.java")
TOML = os.path.join(ROOT, "src", "main", "resources", "META-INF", "neoforge.mods.toml")
REPORTS = {n: os.path.join(ZT, u"_zf%s_probe_utf8.txt" % n)
           for n in (u"196", u"194", u"192", u"190", u"186", u"188")}
GATES = [os.path.join(ZT, n) for n in (u"_zf186_verify.py", u"_zf188_verify.py",
                                      u"_zf190_verify.py", u"_zf192_verify.py", u"_zf194_verify.py")]
V149 = os.path.join(ZT, u"_zf149_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.15.jar")
LIB = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.15.jar")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")

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


def run_gate(p):
    r = subprocess.run([sys.executable, p], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
    out = r.stdout.decode("utf-8", "replace")
    line = [l.strip() for l in out.split(u"\n") if l.strip().startswith(u"通过 =")]
    return r.returncode, (line[-1] if line else u"rc=%d" % r.returncode)


def main():
    hole, hole_c = read(HOLE), strip_comments(read(HOLE))

    print(u"== A 代码 ==")
    check(u"if (hole.mode == GravityDeviceItem.MODE_COLLAPSE) {" in hole_c
          and u"collapseEat(hole);" in hole_c
          and u"return;" in hole_c,
          u"A1 坍缩模式**不再走线性游标**，一进门就分派给 `collapseEat`（近处优先的球内取样）")

    check(u"private static void collapseEat(Hole hole) {" in hole_c
          and u"double rr = radius * u;" in hole_c
          and u"public static double demolishRadiusAt(int age) {" in hole_c
          and u"DEMOLISH_START_RADIUS + age * DEMOLISH_GROWTH_PER_TICK" in hole_c
          and u"public static final double DEMOLISH_START_RADIUS = 3.0D;" in hole_c,
          u"A2 取样半径用 `U(0,R)`（体密度 ∝ 1/r² ⇒ **先拆身边那一圈**），R 随年龄涨（纯函数可验）")

    check(u"if (!exposed(level, p)) {" in hole_c and u"demolish(level, hole, p, state);" in hole_c
          and u"launchFalling(hole, p, state)" in hole_c,
          u"A3 两种吃法：**埋着的**就地拆、**露着的**飞进奇点（露着=至少一面贴空气）")

    check(u"LevelEvent.PARTICLES_DESTROY_BLOCK" in hole_c and u"level.removeBlock(p, false);" in hole_c,
          u"A4 拆除走原版的「方块破坏」事件 2001（碎裂粒子 + 音效 = 「像爆炸那样」），且不掉落")

    check(u"Math.min(demolishRadiusAt(hole.age), (double) PotatoSTConfig.blackHoleScanRadius())" in hole_c,
          u"A5 拆除半径**不超过**配置的扫描半径（配置说只吃 8 格就只吃 8 格）")

    check(u"hole.pulled < maxBlocks()" in hole_c and u"MAX_FLYING" in hole_c
          and u"int flyingLeft = Math.max(0, MAX_FLYING" in hole_c,
          u"A6 拆除与搬运都算进 `pulled` 上限；天上飞的数量仍然一次查好、逐块减")

    print(u"== B 回归 ==")
    keys = {f: len(json.loads(read(os.path.join(LANG, f))))
            for f in (u"zh_cn.json", u"en_us.json", u"lzh.json", u"ja_jp.json", u"ru_ru.json")}
    check(keys == {u"zh_cn.json": 691, u"en_us.json": 691, u"lzh.json": 693,
                   u"ja_jp.json": 691, u"ru_ru.json": 691},
          u"B1 本轮**没有动语言键**（五语种仍然 691 / lzh 693）",
          u"、".join(u"%s=%d" % kv for kv in sorted(keys.items())))
    check(sha1(TOML) == sha1(os.path.join(PRE, r"src\main\resources\META-INF\neoforge.mods.toml")),
          u"B2 依赖清单仍然一字未动")

    print(u"== C 证据 ==")
    v = {n: verdict(p) for n, p in REPORTS.items()}
    check(v[u"196"] == (5, 0),
          u"C1 本轮探针 Zf196Check 5/0（身边被拆 / 半径随年龄涨 / 埋着的就地拆 / 露着的仍飞 / 上限生效）",
          u"读到 %s" % (v[u"196"],))
    check(v[u"194"] == (5, 0) and v[u"192"] == (6, 0) and v[u"190"] == (16, 0)
          and v[u"186"] == (20, 0) and v[u"188"] == (4, 0),
          u"C2 回归：Zf194Check 5/0、Zf192Check 6/0、Zf190Check 16/0、Zf186Check 20/0、Zf188Check 4/0",
          u"读到 %s / %s / %s / %s / %s" % (v[u"194"], v[u"192"], v[u"190"], v[u"186"], v[u"188"]))
    lines, ok = [], True
    for g in GATES:
        rc, line = run_gate(g)
        lines.append(os.path.basename(g) + u"：" + line)
        ok = ok and rc == 0
    check(ok, u"C3 五道老门仍全绿（本轮跟平了 `_zf190` 的 B5、`_zf194` 的 A1/A5）", u" ｜ ".join(lines))

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
        cls = z.read(u"com/potatost/mod/BlackHoleManager.class")
        has = b"collapseEat" in cls and b"DEMOLISH_START_RADIUS" in cls
        keys_jar = len(json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))
        jar_ok = (not checks_) and has and keys_jar == 691
        detail = u"探针类 %d ｜ 近处拆除逻辑在 class %s ｜ jar 内 zh_cn 键 %d" % (len(checks_), has, keys_jar)
        z.close()
    check(jar_ok, u"D2 成品里没有探针类、近处拆除逻辑进包、语言键仍 691", detail)

    v149 = read(V149)
    m_sha = re.search(u'WANT_SHA = u?"([0-9a-f]{40})"', v149)
    m_size = re.search(u"WANT_SIZE = (\\d+)", v149)
    check(bool(m_sha) and bool(m_size) and m_sha.group(1) == h and int(m_size.group(1)) == size,
          u"D3 §4.159 三处联动：`_zf149_verify.py` 靶子指向这份成品",
          u"WANT_SHA=%s WANT_SIZE=%s" % (m_sha.group(1)[:12] if m_sha else u"-",
                                        m_size.group(1) if m_size else u"-"))
    doc, ann, hand = read(DOC), read(ANN), read(HAND)
    check(h in doc and h in ann and u"### 4.196 " in doc and u"## New in 0.14 ZF196" in ann
          and u"50. **ZF196 的账" in hand,
          u"D4 档案 §4.196 + 英文公告 + 交接第 50 条都写了这一轮，且哈希跟到新成品",
          u"档案命中 %s ｜ 公告命中 %s" % (h[:12] in doc, h[:12] in ann))

    print(u"\n通过 = %d   失败 = %d" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print(u"  !! " + f)
    return 1 if FAIL else 0


if __name__ == u"__main__":
    sys.exit(main())
