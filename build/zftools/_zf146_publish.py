# -*- coding: utf-8 -*-
u"""_zf146_publish.py —— ZF146 发布：把 build\\libs 的产物拷进 release\\ 并写 .sha1

规矩（档案 §3 发布六步 + ZF63「幽灵旧 jar」事故立的规矩）：
  **先查后拷** —— 源产物、版本号、常驻校验、两次开服对照、探针闸全部核对通过，**才动 release\\**。

本轮加的两条前置：
  · **陈旧闸**：jar 的 mtime 必须**晚于**本轮改过的源码 —— 防「拿上一轮的 jar 当成品」；
  · **两次开服对照闸**：`check\\zf146_before_run2.log` 必须是**红**的（复现了那个 bug）、
    `check\\zf146_after_run2.log` 必须是**绿**的。少了这一对，本轮的"修好了"就没有对照。

⚠ 本轮是**同版本原地重打包**（mod_version 仍 0.11）⇒ 汇报时必须宣布"上一版 SHA1 作废"。

跑法（先 `gradlew build --offline --no-build-cache`）：
    python build\\zftools\\_zf146_publish.py            # 只体检（默认）
    python build\\zftools\\_zf146_publish.py --write     # 真拷
"""
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
T = os.path.join(ROOT, r"build\zftools")
VERSION_FILE = os.path.join(ROOT, "gradle.properties")
SRC_DIR = os.path.join(ROOT, r"build\libs")
REL_DIR = os.path.join(ROOT, "release")
VERIFY = os.path.join(T, u"_zf146_verify.py")
POTATOST = os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java")
MGR = os.path.join(ROOT, r"src\main\java\com\potatost\mod\StarfallRitualManager.java")
PROBE_DST = os.path.join(ROOT, r"src\main\java\com\potatost\mod\Zf146Check.java")
BEFORE2 = os.path.join(T, "check", u"zf146_before_run2.log")
AFTER2 = os.path.join(T, "check", u"zf146_after_run2.log")


def sha1(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


def main(argv):
    write = u"--write" in argv

    props = io.open(VERSION_FILE, encoding="utf-8").read()
    m = re.search(r"^mod_version=(.+)$", props, re.M)
    if not m:
        print(u"[FAIL] gradle.properties 里找不到 mod_version")
        return 1
    version = m.group(1).strip()

    jar = os.path.join(SRC_DIR, u"potato_s_t-%s.jar" % version)
    rel = os.path.join(REL_DIR, u"PotatoST-%s.jar" % version)
    if not os.path.isfile(jar):
        print(u"[FAIL] 找不到产物：%s" % jar)
        return 1

    print(u"版本      : %s" % version)
    print(u"源产物    : %s（%d B，sha1 %s）" % (jar, os.path.getsize(jar), sha1(jar)))
    if os.path.isfile(rel):
        print(u"当前成品  : %s（sha1 %s）" % (rel, sha1(rel)))
        print(u"⚠ 同版本原地重打包 ⇒ 上面那个 SHA1 一旦发布即作废")
    else:
        print(u"当前成品  : （还没有）")

    fails = []

    # ---------- ① 陈旧闸 ----------
    stale = os.path.getmtime(jar) <= os.path.getmtime(MGR)
    print(u"陈旧闸    : jar mtime %s / 源码 mtime %s ⇒ %s"
          % (time_of(jar), time_of(MGR), u"**陈旧**" if stale else u"新"))
    if stale:
        fails.append(u"build\\libs 里的 jar 比本轮改过的源码还旧（先 gradlew build）")

    # ---------- ② 常驻校验 ----------
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, VERIFY], capture_output=True, env=env)
    vout = r.stdout.decode(u"utf-8", u"replace")
    vfail = list(dict.fromkeys(l.strip() for l in vout.split(u"\n") if u"[FAIL]" in l))
    print(u"常驻校验  : %s（失败 %d 条）" % (u"全绿" if not vfail else u"**有红**", len(vfail)))
    for l in vfail:
        print(u"    " + l)
    if vfail:
        fails.append(u"_zf146_verify.py 有 %d 条红" % len(vfail))

    # ---------- ③ 探针闸 ----------
    src = io.open(POTATOST, encoding="utf-8").read()
    probes = re.findall(r"(Zf\d\d\dCheck)\s*\.\s*register\s*\(", src)
    if probes or os.path.exists(PROBE_DST):
        tag = u"、".join(sorted(set(probes))) + (u" + 源码树里还留着 Zf146Check.java" if os.path.exists(PROBE_DST) else u"")
        print(u"[STOP] 源码树里挂着探针：%s ⇒ 现在 build 出来的 jar 会带上它、"
              u"构造器里还会真去 register()。" % tag)
        fails.append(u"源码树里挂着探针：%s" % tag)
    else:
        print(u"探针闸    : 干净（PotatoST.java 里没有任何 Zf*Check.register()）")

    # ---------- ④ 两次开服对照闸 ----------
    b = io.open(BEFORE2, encoding="utf-8", errors="replace").read() if os.path.exists(BEFORE2) else u""
    a = io.open(AFTER2, encoding="utf-8", errors="replace").read() if os.path.exists(AFTER2) else u""
    before_red = u"FAILED**" in b
    after_green = u"verdict: ALL OK" in a
    print(u"开服对照  : 改前那份 %s / 改后那份 %s"
          % (u"红（复现了 bug）" if before_red else u"**不红，没复现**",
             u"绿" if after_green else u"**不绿**"))
    if not before_red:
        fails.append(u"改前那趟没有复现 bug（第二趟不是红的）")
    if not after_green:
        fails.append(u"改后那趟不是全绿")

    if not write:
        print(u"--- 体检模式（没动 release\\；要真拷加 --write）---")
        return 0 if not fails else 1

    if fails:
        print(u"[STOP] 门禁没过 —— **一个字节都没拷**：")
        for f in fails:
            print(u"    " + f)
        return 1

    os.makedirs(REL_DIR, exist_ok=True)
    old = sha1(rel) if os.path.isfile(rel) else None
    shutil.copy2(jar, rel)
    if sha1(rel) != sha1(jar):
        print(u"[FAIL] 拷完哈希不一致")
        return 1
    io.open(rel + u".sha1", u"w", encoding=u"ascii", newline=u"\n").write(sha1(rel) + u"\n")
    print(u"已发布    : %s" % rel)
    print(u"新 SHA1   : %s" % sha1(rel))
    print(u"旧 SHA1   : %s（作废）" % (old if old else u"无"))
    return 0


def time_of(p):
    import time
    return time.strftime(u"%H:%M:%S", time.localtime(os.path.getmtime(p)))


sys.exit(main(sys.argv[1:]))
