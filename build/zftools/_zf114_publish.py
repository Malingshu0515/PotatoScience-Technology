# -*- coding: utf-8 -*-
u"""_zf114_publish.py —— ZF114 发布：把 build\\libs 的产物拷进 release\\ 并写 .sha1

规矩（档案 §3 的发布六步 + ZF63 那次"幽灵旧 jar"事故立的规矩）：
  **先查后拷** —— 先把源产物、旧成品、版本号全部核对一遍，**全部通过才动 release\\ 目录**。
（ToolLint 会按命名约定检查本文件里"先核对、后 copy"的顺序，别把两段调过来。）

本轮是**同版本原地重打包**（mod_version 仍 0.11）⇒ 汇报时必须宣布"上一版 SHA1 作废"，
所以脚本会把旧 SHA1 打出来。

跑法：
    python build\\zftools\\_zf114_publish.py            # 只体检（默认）
    python build\\zftools\\_zf114_publish.py --write     # 真拷
"""
import hashlib
import io
import os
import re
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
VERSION_FILE = os.path.join(ROOT, "gradle.properties")
SRC_DIR = os.path.join(ROOT, r"build\libs")
REL_DIR = os.path.join(ROOT, "release")


def sha1(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


def main(argv):
    write = "--write" in argv

    # ---------- ① 先核对 ----------
    props = io.open(VERSION_FILE, encoding="utf-8").read()
    m = re.search(r"^mod_version=(.+)$", props, re.M)
    if not m:
        print(u"[FAIL] gradle.properties 里找不到 mod_version")
        return 1
    version = m.group(1).strip()
    src = os.path.join(SRC_DIR, u"potato_s_t-%s.jar" % version)
    dst = os.path.join(REL_DIR, u"PotatoST-%s.jar" % version)
    dst_sha = dst + u".sha1"

    if not os.path.exists(src):
        print(u"[FAIL] 找不到构建产物：%s（先跑 build）" % src)
        return 1
    if not os.path.isdir(REL_DIR):
        print(u"[FAIL] 找不到 release 目录")
        return 1

    new_sha1 = sha1(src)
    old_sha1 = sha1(dst) if os.path.exists(dst) else u"(本来就没有)"
    print(u"   版本号（唯一来源 gradle.properties）= %s" % version)
    print(u"   源产物 : %s  %d B  sha1=%s" % (src, os.path.getsize(src), new_sha1))
    print(u"   旧成品 : %s  %d B  sha1=%s"
          % (dst, os.path.getsize(dst) if os.path.exists(dst) else 0, old_sha1))
    if os.path.exists(dst) and old_sha1 == new_sha1:
        print(u"   ⚠ 新旧 sha1 完全相同 ⇒ 什么都没变，不需要重发")
        return 0

    # 版本号与成品文件名必须一致（Audit H 项也核这条）
    if not os.path.basename(dst).endswith(u"%s.jar" % version):
        print(u"[FAIL] 成品名与 mod_version 对不上")
        return 1

    if not write:
        print(u"（体检模式：核对全过，未动 release\\）")
        return 0

    # ---------- ② 后拷 ----------
    shutil.copy2(src, dst)
    copied = sha1(dst)
    if copied != new_sha1:
        print(u"[FAIL] 拷贝后 sha1 不一致：%s != %s" % (copied, new_sha1))
        return 1
    io.open(dst_sha, "w", encoding="utf-8", newline=u"").write(u"%s  %s\n"
                                                               % (new_sha1, os.path.basename(dst)))
    print(u"   已发布：%s（%d B）" % (dst, os.path.getsize(dst)))
    print(u"   已写 SHA1：%s" % io.open(dst_sha, encoding="utf-8").read().strip())
    print(u"")
    print(u"   ★ 汇报里必须写：上一版 SHA1 %s **作废**；新 SHA1 = %s" % (old_sha1, new_sha1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
