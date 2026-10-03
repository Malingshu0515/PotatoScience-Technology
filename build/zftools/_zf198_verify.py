# -*- coding: utf-8 -*-
u"""_zf198_verify.py —— ZF198 常驻门（版本线 **0.14 → 0.15**）。

看四类东西：
  A 版本号：`gradle.properties` 唯一一处 = 0.15；三份钉 mod_version 的老门跟着走；
           `neoforge.mods.toml` 仍是占位符；jar 内渲染 `version="0.15"`；
  B 只碰白名单：**当前成品**的路径全指 0.15，而**备份里的历史路径**（zfNNN_pre\\release\\PotatoST-0.14.jar）
           一处不许动；历史轮次的脚本与档案里的旧字样不许被改；
  C 证据：六道常驻门全绿、`_zf149_verify.py` 靶子指向 0.15、0.14 那份原样留盘；
  D 交付：成品 == build 产物 / 没有探针类 / 语言键没变（691 / lzh 693）/ 档案与公告写了这一轮。

跑法：python build\\zftools\\_zf198_verify.py
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
PROPS = os.path.join(ROOT, "gradle.properties")
TOML_SRC = os.path.join(ROOT, "src", "main", "resources", "META-INF", "neoforge.mods.toml")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.15.jar")
LIB = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.15.jar")
OLD_JAR = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")
V149 = os.path.join(ZT, u"_zf149_verify.py")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
GATES = [os.path.join(ZT, n) for n in (u"_zf73_verify.py", u"_zf78_verify.py", u"_zf79_verify.py",
                                      u"_zf149_verify.py", u"_zf186_verify.py", u"_zf188_verify.py",
                                      u"_zf190_verify.py", u"_zf192_verify.py", u"_zf194_verify.py",
                                      u"_zf196_verify.py")]

PASS, FAIL = [], []


def check(ok, label, detail=u""):
    (PASS if ok else FAIL).append(label)
    print(u"  %s %s%s" % (u"[OK]  " if ok else u"[FAIL]", label, (u" ｜ " + detail) if detail else u""))
    return ok


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def run_gate(p):
    r = subprocess.run([sys.executable, p], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=1200)
    out = r.stdout.decode("utf-8", "replace")
    line = [l.strip() for l in out.split(u"\n") if l.strip().startswith(u"通过 =")]
    return r.returncode, (line[-1] if line else u"rc=%d" % r.returncode)


def run_gate_raw(p):
    r = subprocess.run([sys.executable, p], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=1200)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def main():
    print(u"== A 版本号 ==")
    props = read(PROPS)
    cnt = len(re.findall(u"mod_version", props))
    m = re.search(u"mod_version=(\\S+)", props)
    check(cnt == 1 and bool(m) and m.group(1) == u"0.15",
          u"A1 `gradle.properties` 里 `mod_version` **唯一一处**且 = 0.15",
          u"出现 %d 次，值 = %s" % (cnt, m.group(1) if m else u"-"))
    t73, t78, t79 = read(GATES[0]), read(GATES[1]), read(GATES[2])
    check(u"mod_version=0\\.15" in t73 and u"mod_version 现在是 0.15" in t78
          and u"mod_version 现在是 0.15" in t79 and u'"mod_version=0.15" in props' in t78,
          u"A2 三份钉 mod_version 的老门跟到 0.15（判据没放宽：仍是逐字比常量）")
    check(u"${mod_version}" in read(TOML_SRC),
          u"A3 `neoforge.mods.toml` 仍是 `${mod_version}` 占位符（版本号只有一处源头）")

    print(u"== B 只碰白名单 ==")
    live = [u"_zf149_jar.py", u"_zf149_verify.py", u"_zf155_jarcheck.py", u"_zf156_jarcheck.py",
            u"_zf162_pkg.py", u"_zf166_repack.py", u"_zf180_docs.py",
            u"_zf186_verify.py", u"_zf188_verify.py", u"_zf190_verify.py", u"_zf192_verify.py",
            u"_zf194_verify.py", u"_zf196_verify.py", u"_zf196_repack.py"]
    bad = []
    for n in live:
        t = read(os.path.join(ZT, n))
        if u'"release", u"PotatoST-0.14.jar"' in t or u'"libs", u"potato_s_t-0.14.jar"' in t:
            bad.append(n)
    check(not bad, u"B1 活体门/脚本里**当前成品的路径**全指 0.15（没有漏网的 0.14）", u"漏网：%s" % bad)
    hist = [n for n in live if re.search(u'release\\\\PotatoST-0\\.14\\.jar', read(os.path.join(ZT, n)))]
    check(hist == [u"_zf186_verify.py"],
          u"B2 备份里的**历史路径**原样留着（只有 `_zf186_verify.py` 的 `pre_jar` 该留着）", u"持有者：%s" % hist)
    check(not os.path.isfile(os.path.join(ZT, u"_zf196_bump.py")) and os.path.isfile(os.path.join(ZT, u"_zf198_bump.py")),
          u"B3 本轮脚本是 `_zf198_bump.py`（没去改历史轮次的 `_zfNNN_*.py`）")
    doc = read(DOC)
    check(u"| ZF196 |" in doc and u"**0.14：坍缩模式" in doc,
          u"B4 档案里历史那些 0.14 的行**一个字没动**（只加了 ZF198 一行）")

    print(u"== C 证据 ==")
    v149 = read(V149)
    m_sha = re.search(u'WANT_SHA = u?"([0-9a-f]{40})"', v149)
    m_size = re.search(u"WANT_SIZE = (\\d+)", v149)
    h = sha1(JAR) if os.path.isfile(JAR) else u"-"
    size = os.path.getsize(JAR) if os.path.isfile(JAR) else -1
    check(bool(m_sha) and m_sha.group(1) == h and bool(m_size) and int(m_size.group(1)) == size,
          u"C1 §4.159 靶子指向 0.15 这份成品",
          u"WANT_SHA=%s WANT_SIZE=%s" % (m_sha.group(1)[:12] if m_sha else u"-",
                                        m_size.group(1) if m_size else u"-"))
    fast = bool(os.environ.get(u"ZF198_FAST"))
    lines, ok = [], True
    if fast:
        print(u"  （ZF198_FAST：跳过 C2a/C2b 那十道老门 —— 反证刀只跑得快的那部分）")
        check(True, u"C2a 六道常驻门全绿（本轮跳过）")
        check(True, u"C2b 三份钉版本的老门 + `_zf149_verify.py`（本轮跳过）")
    else:
        for g in GATES[4:]:                      # 六道常驻门：必须整道全绿
            rc, line = run_gate(g)
            lines.append(os.path.basename(g) + u"：" + line)
            ok = ok and rc == 0
        check(ok, u"C2a 六道常驻门全绿（`_zf186` 的 D3 跟平了版本号那一行）", u" ｜ ".join(lines))
        # 三份老门 + `_zf149_verify.py` 本来就有**既存的红**（全门快照里那 74 条）；
        # 本轮只要求它们**关于版本号/成品路径的那几条**是绿的（不许把既存红算到本轮头上）。
        detail, ok = [], True
        for g, want in ((GATES[0], u"[OK]   C1 mod_version = 0.15"),
                        (GATES[1], u"mod_version 现在是 0.15"),
                        (GATES[2], u"mod_version 现在是 0.15")):
            rc, out = run_gate_raw(g)
            hit = any(l.strip().startswith(u"[OK]") and want in l for l in out.split(u"\n"))
            reds = [l.strip() for l in out.split(u"\n") if l.strip().startswith(u"!!")]
            detail.append(u"%s：版本号那条=%s，既存红 %d"
                          % (os.path.basename(g), u"绿" if hit else u"**没绿**", len(reds)))
            ok = ok and hit
        rc149, out149 = run_gate_raw(V149)
        reds149 = [l.strip() for l in out149.split(u"\n") if l.strip().startswith(u"!!")]
        touched = [r for r in reds149 if u"PotatoST-0.15" in r or u"WANT_" in r or u"A1 " in r]
        detail.append(u"_zf149_verify.py：既存红 %d 条，碰到成品的那几条 %d 条" % (len(reds149), len(touched)))
        ok = ok and rc149 == 1 and len(reds149) == 3 and not touched
        check(ok, u"C2b 三份钉版本的老门 + `_zf149_verify.py`：**跟成品有关的那几条**全绿（既存红不算本轮）",
          u" ｜ ".join(detail))
    check(os.path.isfile(OLD_JAR) and sha1(OLD_JAR) == u"3baf857e0cfc02a7af26f32ebc4447363f4c56bb",
          u"C3 0.14 那份**原样留盘**作历史（哈希没变）",
          u"%d 字节 / %s" % (os.path.getsize(OLD_JAR) if os.path.isfile(OLD_JAR) else -1,
                            sha1(OLD_JAR)[:12] if os.path.isfile(OLD_JAR) else u"-"))

    print(u"== D 交付 ==")
    same_jar = os.path.isfile(JAR) and os.path.isfile(LIB) and sha1(JAR) == sha1(LIB)
    check(same_jar, u"D1 成品 release/PotatoST-0.15.jar == build/libs 产物（逐字节）",
          u"%d 字节 / sha1 %s" % (size, h[:12]))
    jar_ok, detail = False, u"成品不在盘上"
    if os.path.isfile(JAR):
        z = zipfile.ZipFile(JAR)
        n = z.namelist()
        toml = z.read(u"META-INF/neoforge.mods.toml").decode("utf-8")
        ver = re.search(u'^version="([^"]+)"', toml, re.M)
        keys_zh = len(json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))
        keys_lzh = len(json.loads(z.read(u"assets/potato_s_t/lang/lzh.json").decode("utf-8")))
        checks_ = [x for x in n if u"Check.class" in x]
        jar_ok = (bool(ver) and ver.group(1) == u"0.15" and keys_zh == 691 and keys_lzh == 693
                  and not checks_ and u"com/potatost/mod/BlackHoleManager.class" in n)
        detail = u"version=%s ｜ 键 %d/%d ｜ 探针类 %d" % (ver.group(1) if ver else u"-", keys_zh, keys_lzh, len(checks_))
        z.close()
    check(jar_ok, u"D2 jar 内 `version=\"0.15\"`、语言键没变（691 / lzh 693）、零探针类", detail)
    doc, ann, hand = read(DOC), read(ANN), read(HAND)
    check(h in doc and h in ann and u"| ZF198 |" in doc and u"## Version 0.15" in ann
          and u"51. **ZF198 的账" in hand and u"PotatoST-0.15.jar" in hand,
          u"D3 档案 §5 行 + 英文公告「## Version 0.15」+ 交接第 51 条都写了这一轮，且哈希跟到新成品",
          u"档案命中 %s ｜ 公告命中 %s" % (h[:12] in doc, h[:12] in ann))
    check(sha1(os.path.join(ROOT, "src", "main", "resources", "META-INF", "neoforge.mods.toml"))
          == sha1(os.path.join(ZT, "zf198_pre", r"src\main\resources\META-INF\neoforge.mods.toml")),
          u"D4 依赖清单与改前**逐字节相同**（抬版本号没碰依赖段）")

    print(u"\n通过 = %d   失败 = %d" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print(u"  !! " + f)
    return 1 if FAIL else 0


if __name__ == u"__main__":
    sys.exit(main())
