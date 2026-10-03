# -*- coding: utf-8 -*-
u"""_zf194_verify.py —— ZF194 常驻门（0.14：坍缩模式的方块改成**下落方块飞向奇点、到中心清除**）。

看四类东西：
  A 代码：坍缩分支走 `launchFalling`（不再码放）/ 天上飞的数量一次算好 / `consumeFalling` 会**拉向中心**
          并按 `CLEAR_RADIUS` 清除 / 不禁用重力（黑洞没了方块照常落地）/ 坍缩模式不设禁采区；
  B 回归：五语种键数没变（691 / lzh 693）、依赖清单一字未动；
  C 证据：探针 Zf194Check 5/0 + 回归 Zf192Check 6/0、Zf190Check 16/0、Zf186Check 20/0、Zf188Check 4/0；
          四道老门仍全绿；
  D 交付：成品 == build 产物 / 没有探针类 / `_zf149_verify.py` 靶子联动 / 文档与公告写了这一轮。

跑法：python build\\zftools\\_zf194_verify.py
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
PRE = os.path.join(ZT, "zf194_pre")
HOLE = os.path.join(SRC, "BlackHoleManager.java")
TOML = os.path.join(ROOT, "src", "main", "resources", "META-INF", "neoforge.mods.toml")
P194 = os.path.join(ZT, u"_zf194_probe_utf8.txt")
P192 = os.path.join(ZT, u"_zf192_probe_utf8.txt")
P190 = os.path.join(ZT, u"_zf190_probe_utf8.txt")
P186 = os.path.join(ZT, u"_zf186_probe_utf8.txt")
P188 = os.path.join(ZT, u"_zf188_probe_utf8.txt")
GATES = [os.path.join(ZT, n) for n in (u"_zf186_verify.py", u"_zf188_verify.py",
                                      u"_zf190_verify.py", u"_zf192_verify.py")]
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
    hole, hole_c = read(HOLE), strip_comments(read(HOLE))

    print(u"== A 代码 ==")
    check(u"if (launchFalling(hole, p, state)) {" in hole_c
          and u"flyingLeft--;" in hole_c
          and u"if (flyingLeft <= 0) {" in hole_c
          and u"level.getEntitiesOfClass(FallingBlockEntity.class, flyBox).size());" in hole_c,
          u"A1 坍缩分支走 `launchFalling`（不再码放），天上飞的数量**一次查好**再逐块减（不逐块查实体）")

    i_consume = hole_c.find(u"private static void consumeFalling(Hole hole) {")
    i_tick = hole_c.find(u"consumeFalling(hole);")
    check(i_consume > 0 and i_tick > 0 and u"hole.mode != GravityDeviceItem.MODE_COLLAPSE" in hole_c
          and u"fb.setDeltaMovement(dir.normalize().scale(flySpeed(dist)));" in hole_c
          and u"if (dist <= CLEAR_RADIUS) {" in hole_c and u"fb.discard();" in hole_c,
          u"A2 `consumeFalling`：每 tick 把下落方块**继续拉向中心**，到 CLEAR_RADIUS 以内**清除**")

    check(u"public static final double CLEAR_RADIUS = 2.5D;" in hole_c
          and u"Math.min(1.6D, 0.45D + dist * 0.02D)" in hole_c,
          u"A3 清除半径与飞行速度都是**明写的常量**（好调、好测）")

    check(u"setNoGravity" not in hole_c and u"falling.setStartPos(pos);" in hole_c
          and u"falling.hurtMarked = true;" in hole_c,
          u"A4 **没有禁用重力**：黑洞半路没了，在飞的方块会照常落地变回方块（不凭空丢东西）")

    check(u"if (!collapse && Math.abs(dx) <= PILE_GUARD" in hole_c,
          u"A5 坍缩模式**不设禁采区**（它没有「码放」这一步，而且连脚边那圈也吸才看得出它在吃周围）")

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
    v194, v192, v190, v186, v188 = (verdict(P194), verdict(P192), verdict(P190),
                                    verdict(P186), verdict(P188))
    check(v194 == (5, 0), u"C1 本轮探针 Zf194Check 5/0（变下落方块 / 朝中心 / 到中心清除 / 反面自证 / 断电不清）",
          u"读到 %s" % (v194,))
    check(v192 == (6, 0) and v190 == (16, 0) and v186 == (20, 0) and v188 == (4, 0),
          u"C2 回归：Zf192Check 6/0、Zf190Check 16/0、Zf186Check 20/0、Zf188Check 4/0",
          u"读到 %s / %s / %s / %s" % (v192, v190, v186, v188))
    lines, ok = [], True
    for g in GATES:
        rc, line = run_gate(g)
        lines.append(os.path.basename(g) + u"：" + line)
        ok = ok and rc == 0
    check(ok, u"C3 四道老门仍全绿（本轮没有改任何老判据）", u" ｜ ".join(lines))

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
        has_clear = b"CLEAR_RADIUS" in cls and b"consumeFalling" in cls
        keys_jar = len(json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))
        jar_ok = (not checks_) and has_clear and keys_jar == 691
        detail = u"探针类 %d ｜ 清除逻辑在 class %s ｜ jar 内 zh_cn 键 %d" % (len(checks_), has_clear, keys_jar)
        z.close()
    check(jar_ok, u"D2 成品里没有探针类、清除那套逻辑进包、语言键仍 691", detail)

    v149 = read(V149)
    m_sha = re.search(u'WANT_SHA = u?"([0-9a-f]{40})"', v149)
    m_size = re.search(u"WANT_SIZE = (\\d+)", v149)
    check(bool(m_sha) and bool(m_size) and m_sha.group(1) == h and int(m_size.group(1)) == size,
          u"D3 §4.159 三处联动：`_zf149_verify.py` 靶子指向这份成品",
          u"WANT_SHA=%s WANT_SIZE=%s" % (m_sha.group(1)[:12] if m_sha else u"-",
                                        m_size.group(1) if m_size else u"-"))
    doc, ann, hand = read(DOC), read(ANN), read(HAND)
    check(h in doc and h in ann and u"### 4.194 " in doc and u"## New in 0.14 ZF194" in ann
          and u"49. **ZF194 的账" in hand,
          u"D4 档案 §4.194 + 英文公告 + 交接第 49 条都写了这一轮，且哈希跟到新成品",
          u"档案命中 %s ｜ 公告命中 %s" % (h[:12] in doc, h[:12] in ann))

    print(u"\n通过 = %d   失败 = %d" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print(u"  !! " + f)
    return 1 if FAIL else 0


if __name__ == u"__main__":
    sys.exit(main())
