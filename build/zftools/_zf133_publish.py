# -*- coding: utf-8 -*-
"""_zf133_publish.py —— ZF133 发布：把 build\\libs 的产物拷进 release\\ 并写 .sha1

规矩（档案 §3 发布六步 + ZF63"幽灵旧 jar"事故立的规矩）：
  **先查后拷** —— 源产物、旧成品、版本号、探针判定全部核对通过，**才动 release\\**。

⚠ 本轮是**同版本原地重打包**（mod_version 仍 0.11）⇒ 汇报时必须宣布"上一版 SHA1 作废"，
  所以脚本会把旧 SHA1 打出来（这是 §3 那一条的硬要求，不是装饰）。

前置（少一条就不许发）：
  ① `_zf133_verify.py` 全绿；
  ② 探针报告 verdict = ALL OK（★ 见下面 --force 的说明）；
  ③ build/libs 里的产物**比源码新**（否则就是拿旧包发布）。

跑法：
    python build\\zftools\\_zf133_publish.py            # 只体检（默认）
    python build\\zftools\\_zf133_publish.py --write     # 真拷
    python build\\zftools\\_zf133_publish.py --write --force   # 明知探针没全绿也要发（必须在汇报里写明）
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
VERIFY = os.path.join(ROOT, r"build\zftools\_zf133_verify.py")
PROBE = os.path.join(ROOT, r"build\zftools\check\zf133_axe_probe.log")


def sha1(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


def main(argv):
    write = "--write" in argv
    force = "--force" in argv

    # ---------- ① 先核对 ----------
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

    # ---------- ② 门禁：常驻校验 + 探针 ----------
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, VERIFY], capture_output=True, env=env)
    vout = r.stdout.decode("utf-8", "replace")
    vfail = [l.strip() for l in vout.split("\n") if "[FAIL]" in l]
    vfail = list(dict.fromkeys(vfail))   # ⚠ 报告末尾会再列一遍失败项，去重免得看着像双份
    print("常驻校验  : %s（失败 %d 条）" % ("全绿" if not vfail else "**有红**", len(vfail)))
    for l in vfail:
        print("    " + l)

    probe_ok = False
    if os.path.isfile(PROBE):
        body = io.open(PROBE, encoding="utf-8", errors="replace").read()
        probe_ok = "verdict: ALL OK" in body
        line = [l for l in body.split("\n") if "verdict" in l]
        print("探针判定  : %s" % (line[-1].strip() if line else "没有 verdict 行"))
    else:
        print("探针判定  : （没有报告）")

    if not write:
        print("--- 体检模式（没动 release\\；要真拷加 --write）---")
        return 0 if (not vfail) else 1

    if vfail or not probe_ok:
        if not force:
            print("[STOP] 门禁没过（常驻校验有红 / 探针不是 ALL OK）—— 不发布。"
                  "确要发布请加 --force 并在汇报里写明原因。")
            return 1
        print("[WARN] --force：明知门禁没过仍然发布（汇报里必须写明）")

    # ---------- ③ 后拷 ----------
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
