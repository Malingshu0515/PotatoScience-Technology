# -*- coding: utf-8 -*-
u"""_zf192_verify.py —— ZF192 常驻门（0.14：坍缩模式**空手也能放**）。

看四类东西：
  A 代码：`use()` / `onUseTick()` / `fire()` 三处按模式放行；种子方块用 AIR 哨兵；
          `loadFrom` 只对**非坍缩**模式把 AIR 当「方块没了」；
  B 文案：五语种各 +1 键（691 / lzh 693），且**只有这一个**新键；
  C 证据：本轮探针 Zf192Check 6/0 + 回归 Zf186Check 20/0、Zf188Check 4/0、Zf190Check 16/0
          （后者是本轮**重写判据后重跑**的：同一个洞量两次 + 洞开在出生点区块里）；
          四道老门仍全绿（本轮跟平了 `_zf190_verify.py` 的键数/证据数、`_zf188_verify.py` 的键数）；
  D 交付：成品 == build 产物 / 没有探针类 / `_zf149_verify.py` 靶子联动 / 文档与公告写了这一轮。

跑法：python build\\zftools\\_zf192_verify.py
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
PRE = os.path.join(ZT, "zf192_pre")
GRAV = os.path.join(SRC, "GravityDeviceItem.java")
HOLE = os.path.join(SRC, "BlackHoleManager.java")
TOML = os.path.join(ROOT, "src", "main", "resources", "META-INF", "neoforge.mods.toml")
P192 = os.path.join(ZT, u"_zf192_probe_utf8.txt")
P190 = os.path.join(ZT, u"_zf190_probe_utf8.txt")
P186 = os.path.join(ZT, u"_zf186_probe_utf8.txt")
P188 = os.path.join(ZT, u"_zf188_probe_utf8.txt")
G186 = os.path.join(ZT, u"_zf186_verify.py")
G188 = os.path.join(ZT, u"_zf188_verify.py")
G190 = os.path.join(ZT, u"_zf190_verify.py")
V149 = os.path.join(ZT, u"_zf149_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")
LIB = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.14.jar")
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
    grav, hole = read(GRAV), read(HOLE)
    grav_c, hole_c = strip_comments(grav), strip_comments(hole)

    print(u"== A 代码 ==")
    use = grav_c[grav_c.index(u"public InteractionResultHolder<ItemStack> use("):]
    use = use[:use.index(u"\n    }\n")]
    tick = grav_c[grav_c.index(u"public void onUseTick("):]
    tick = tick[:tick.index(u"\n    }\n")]
    fire = grav_c[grav_c.index(u"private void fire("):]
    fire = fire[:fire.index(u"\n    }\n")]
    check(u"offhandBlock(player) == null && mode != MODE_COLLAPSE" in use
          and u"offhandBlock(player) == null && getMode(stack) != MODE_COLLAPSE" in tick
          and u"block == null && mode != MODE_COLLAPSE" in fire,
          u"A1 三处（use / onUseTick / fire）都按模式放行：只有**坍缩模式**不要求副手方块")

    check(u"seeded ? block : Blocks.AIR" in fire
          and u"message.potato_s_t.gravity.fired.everything" in fire,
          u"A2 空手放时种子方块用 `Blocks.AIR` 当哨兵，并换成「它开始吸取周围的一切了」那句")

    # ⚠ 判据要钉**那一整条条件**：`mode != MODE_COLLAPSE` 在别的分支里也有
    #   （比如 tick 里的"普通模式才看配置寿命"）⇒ 只搜这个片段会在反证刀 K6 下漏网（本轮真踩过）。
    ok_a3 = (u"int mode = tag.getInt(\"mode\");" in hole_c
             and re.search(u"Blocks\\.AIR\\s*\\n\\s*&& mode != GravityDeviceItem\\.MODE_COLLAPSE\\)", hole) is not None)
    check(ok_a3, u"A3 `loadFrom`：只有**非坍缩**模式才把 AIR 当「方块没了」丢掉（空手洞读得回来）")

    check(sha1(TOML) == sha1(os.path.join(PRE, r"src\main\resources\META-INF\neoforge.mods.toml")),
          u"A4 依赖清单仍然一字未动")

    print(u"== B 文案 ==")
    keys = {f: json.loads(read(os.path.join(LANG, f)))
            for f in (u"zh_cn.json", u"en_us.json", u"lzh.json", u"ja_jp.json", u"ru_ru.json")}
    want = {u"zh_cn.json": 691, u"en_us.json": 691, u"lzh.json": 693, u"ja_jp.json": 691, u"ru_ru.json": 691}
    bad = [f for f, n in want.items()
           if len(keys[f]) != n
           or not keys[f].get(u"message.potato_s_t.gravity.fired.everything")]
    check(not bad, u"B1 五语种各 +1 键（691 / lzh 693）：空手放那一句在五份里都有", u"不符：%s" % bad)
    parity = True
    base = set(keys[u"zh_cn.json"])
    for f, ks in keys.items():
        if base - set(ks) or (set(ks) - base - {u"language.name", u"language.region"}):
            parity = False
    check(parity, u"B2 五份键集合依旧一致（除 lzh 那两个 language.*）")

    print(u"== C 证据 ==")
    v192, v190, v186, v188 = verdict(P192), verdict(P190), verdict(P186), verdict(P188)
    check(v192 == (6, 0), u"C1 本轮探针 Zf192Check 6/0（空手三处放行 + 两条反面自证 + 存档哨兵）",
          u"读到 %s" % (v192,))
    check(v190 == (16, 0) and v186 == (20, 0) and v188 == (4, 0),
          u"C2 回归：Zf190Check **16/0**（判据重写后重跑）、Zf186Check 20/0、Zf188Check 4/0",
          u"读到 %s / %s / %s" % (v190, v186, v188))
    ok186, l186 = run_gate(G186)
    ok188, l188 = run_gate(G188)
    ok190, l190 = run_gate(G190)
    check(ok186 == 0 and ok188 == 0 and ok190 == 0,
          u"C3 三道老门仍全绿（本轮跟平了它们的键数/证据数判据）",
          u"%s ｜ %s ｜ %s" % (l186, l188, l190))

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
        has_new = b"fired.everything" in z.read(u"com/potatost/mod/GravityDeviceItem.class")
        jar_ok = (not checks_) and keys_jar == 691 and has_new
        detail = u"探针类 %d ｜ jar 内 zh_cn 键 %d（要 691）｜ 新句子进了 class %s" % (
            len(checks_), keys_jar, has_new)
        z.close()
    check(jar_ok, u"D2 成品里没有探针类、语言键跟得上（691）", detail)

    v149 = read(V149)
    m_sha = re.search(u'WANT_SHA = u?"([0-9a-f]{40})"', v149)
    m_size = re.search(u"WANT_SIZE = (\\d+)", v149)
    check(bool(m_sha) and bool(m_size) and m_sha.group(1) == h and int(m_size.group(1)) == size,
          u"D3 §4.159 三处联动：`_zf149_verify.py` 靶子指向这份成品",
          u"WANT_SHA=%s WANT_SIZE=%s" % (m_sha.group(1)[:12] if m_sha else u"-",
                                        m_size.group(1) if m_size else u"-"))
    doc, ann, hand = read(DOC), read(ANN), read(HAND)
    check(h in doc and h in ann and u"### 4.192 " in doc and u"## New in 0.14 ZF192" in ann
          and u"48. **ZF192 的账" in hand,
          u"D4 档案 §4.192 + 英文公告 + 交接第 48 条都写了这一轮，且哈希跟到新成品",
          u"档案命中 %s ｜ 公告命中 %s" % (h[:12] in doc, h[:12] in ann))

    print(u"\n通过 = %d   失败 = %d" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print(u"  !! " + f)
    return 1 if FAIL else 0


if __name__ == u"__main__":
    sys.exit(main())
