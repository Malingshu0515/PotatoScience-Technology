# -*- coding: utf-8 -*-
"""_zf140_publish.py —— ZF140 发布：把 build\\libs 的产物拷进 release\\ 并写 .sha1

规矩（档案 §3 发布六步 + ZF63「幽灵旧 jar」事故立的规矩）：
  **先查后拷** —— 源产物、旧成品、版本号、常驻校验、开机自检日志全部核对通过，**才动 release\\**。

⚠ 本轮是**同版本原地重打包**（mod_version 仍 0.11）⇒ 汇报时必须宣布"上一版 SHA1 作废"。

⚠⚠ ZF140 加的一条前置（并发环境专用）：**源码树里不许挂着别人的探针**。
  别的线把 `Zf1xxCheck.java` 挂进 `PotatoST.java` 时，`gradlew build` 出来的 jar 里
  **会带上那个探针类、而且构造器里真会去 register()** —— 那就等于替别人发了包。
  判据：`PotatoST.java` 里出现 `Zf1\\d\\dCheck.register()` 就**拒绝发布**。

跑法：
    python build\\zftools\\_zf140_publish.py            # 只体检（默认）
    python build\\zftools\\_zf140_publish.py --write     # 真拷
"""
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
VERSION_FILE = os.path.join(ROOT, "gradle.properties")
SRC_DIR = os.path.join(ROOT, r"build\libs")
REL_DIR = os.path.join(ROOT, "release")
VERIFY = os.path.join(ROOT, r"build\zftools\_zf140_verify.py")
POTATOST = os.path.join(ROOT, r"src\main\java\com\potatost\mod\PotatoST.java")
CLIENT_LOG = os.path.join(ROOT, r"build\zftools\_zf140_client.log")


def sha1(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


def main(argv):
    write = "--write" in argv

    props = io.open(VERSION_FILE, encoding="utf-8").read()
    m = re.search(r"^mod_version=(.+)$", props, re.M)
    if not m:
        print("[FAIL] gradle.properties 里找不到 mod_version")
        return 1
    version = m.group(1).strip()

    jar = os.path.join(SRC_DIR, "potato_s_t-%s.jar" % version)
    rel = os.path.join(REL_DIR, "PotatoST-%s.jar" % version)
    if not os.path.isfile(jar):
        print("[FAIL] 找不到产物：%s" % jar)
        return 1

    print("版本      : %s" % version)
    print("源产物    : %s（%d B，sha1 %s）" % (jar, os.path.getsize(jar), sha1(jar)))
    if os.path.isfile(rel):
        print("当前成品  : %s（sha1 %s）" % (rel, sha1(rel)))
        print("⚠ 同版本原地重打包 ⇒ 上面那个 SHA1 一旦发布即作废")
    else:
        print("当前成品  : （还没有）")

    # ---------- ② 常驻校验 ----------
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, VERIFY], capture_output=True, env=env)
    vout = r.stdout.decode("utf-8", "replace")
    vfail = list(dict.fromkeys(l.strip() for l in vout.split("\n") if "[FAIL]" in l))
    print("常驻校验  : %s（失败 %d 条）" % ("全绿" if not vfail else "**有红**", len(vfail)))
    for l in vfail:
        print("    " + l)

    # ---------- ③ 并发闸：源码树里不许挂别人的探针 ----------
    src = io.open(POTATOST, "r", encoding="utf-8").read()
    probes = re.findall(r"(Zf\d\d\dCheck)\s*\.\s*register\s*\(", src)
    if probes:
        print("[STOP] 源码树里挂着别人的探针：%s ⇒ 现在 build 出来的 jar 会带上它、"
              "构造器里还会真去 register()。**等对方 _zf1xx_unprobe.py 摘掉再发。**"
              % u"、".join(sorted(set(probes))))
    else:
        print("探针闸    : 干净（PotatoST.java 里没有任何 Zf*Check.register()）")

    # ---------- ④ 开机自检（真的跑过客户端才有的正面证据）----------
    self_check = None
    for p in (CLIENT_LOG, os.path.join(ROOT, r"build\zftools\_zf140_client2.log")):
        if os.path.isfile(p):
            body = io.open(p, encoding="utf-8", errors="replace").read()
            hit = [l for l in body.split("\n") if "black-hole caps OK" in l]
            if hit:
                self_check = hit[-1].strip()
                break
    print("开机自检  : %s" % (self_check if self_check else "（日志里没找到 black-hole caps OK）"))

    # 汇成一张失败清单 —— ToolLint 那条「阶段脚本必须先查后拷」的规矩认的就是 `if fails`
    fails = list(vfail)
    if probes:
        fails.append(u"源码树里挂着别人的探针：%s" % u"、".join(sorted(set(probes))))
    if not self_check:
        fails.append(u"客户端日志里没有开机自检那一行")

    if not write:
        print("--- 体检模式（没动 release\\；要真拷加 --write）---")
        return 0 if not fails else 1

    if fails:
        print("[STOP] 门禁没过 —— **一个字节都没拷**：")
        for f in fails:
            print("    " + f)
        return 1

    os.makedirs(REL_DIR, exist_ok=True)
    old = sha1(rel) if os.path.isfile(rel) else None
    shutil.copy2(jar, rel)
    if sha1(rel) != sha1(jar):
        print("[FAIL] 拷完哈希不一致")
        return 1
    io.open(rel + ".sha1", "w", encoding="ascii", newline="\n").write(sha1(rel) + "\n")
    print("已发布    : %s" % rel)
    print("新 SHA1   : %s" % sha1(rel))
    print("旧 SHA1   : %s（作废）" % (old if old else "无"))
    return 0


sys.exit(main(sys.argv[1:]))
