# -*- coding: utf-8 -*-
u"""_zf73_publish.py —— ZF73 发布：把 build/libs/potato_s_t-0.11.jar 变成 release\\PotatoST-0.11.jar

两条硬规矩：
  ① **先核对、后拷贝**（ToolLint ② 的规矩：拷贝动作必须排在失败判定之后）；
  ② 拷贝后**核哈希**，并写 `.sha1`。

顺带做一件本轮特有的事：把新 jar 与 **v0.10 成品**逐条目对账，把"这一版到底动了哪些文件"
列成清单 —— 这一版是**新版本**（0.10 → 0.11），不是同版本重打包，
所以 `PotatoST-0.10.jar` **原样保留、不作废**，两个 jar 并存。
"""
import hashlib
import io
import os
import shutil
import sys
import zipfile

PROJ = r"E:\PotatoST"
BUILT = os.path.join(PROJ, u"build", u"libs", u"potato_s_t-0.11.jar")
OLD = os.path.join(PROJ, u"release", u"PotatoST-0.10.jar")
OUT = os.path.join(PROJ, u"release", u"PotatoST-0.11.jar")
OUT_SHA = OUT + u".sha1"

# 预期"只在旧 jar 里"的条目：用户 2026-09-22 删掉的孤儿贴图（0.10 打完之后才删）
EXPECT_ONLY_OLD = {u"assets/potato_s_t/textures/block/lv_001.png"}

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def entries(path):
    out = {}
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            out[info.filename] = (info.CRC, info.file_size)
    return out


def main():
    if not os.path.isfile(BUILT):
        print(u"!! 没有构建产物：%s" % BUILT)
        return 1
    built_sha = sha1(BUILT)
    print(u"构建产物 %s" % BUILT)
    print(u"  SHA1 = %s   %d B" % (built_sha, os.path.getsize(BUILT)))

    # 探针残留（jar 里不许有任何 *Check* class）
    with zipfile.ZipFile(BUILT) as zf:
        probes = [n for n in zf.namelist() if u"Check" in n]
    print(u"  jar 内 *Check* 条目 = %d" % len(probes))
    if probes:
        fails.append(u"jar 里还有探针类：%s" % u", ".join(probes[:5]))

    # 与 v0.10 逐条目对账
    if os.path.isfile(OLD):
        a, b = entries(OLD), entries(BUILT)
        only_old = sorted(set(a) - set(b))
        only_new = sorted(set(b) - set(a))
        changed = sorted(k for k in (set(a) & set(b)) if a[k] != b[k])
        print(u"\n与 v0.10 成品对账（旧 %d 条目 / 新 %d 条目）" % (len(a), len(b)))
        print(u"  只在 0.10 里（%d）：" % len(only_old))
        for k in only_old:
            print(u"    - %s" % k)
        print(u"  只在 0.11 里（%d）：" % len(only_new))
        for k in only_new:
            print(u"    + %s" % k)
        print(u"  同名但内容变了（%d）：" % len(changed))
        for k in changed:
            print(u"    ~ %s" % k)
        unexpected = [k for k in only_old if k not in EXPECT_ONLY_OLD]
        if unexpected:
            fails.append(u"0.10 有而 0.11 没有、且不在预期清单里：%s" % u", ".join(unexpected[:5]))
        if any(k for k in changed if k.endswith(u".class") and u"Check" in k):
            fails.append(u"有探针 class 混进 jar")
    else:
        print(u"（找不到 v0.10 成品，跳过对账）")

    if fails:
        print(u"\n**核对没过，不拷贝**：")
        for f in fails:
            print(u"  !! " + f)
        return 1

    shutil.copy2(BUILT, OUT)
    got = sha1(OUT)
    ok = got == built_sha
    print(u"\n已发布 %s" % OUT)
    print(u"  SHA1 = %s（与构建产物一致 = %s）" % (got, ok))
    io.open(OUT_SHA, "w", encoding="ascii", newline=u"\n").write(got + u"\n")
    print(u"  已写 %s" % OUT_SHA)
    print(u"\n★ v0.10 成品 %s 原样保留（%s）—— 这是**版本升级**，不是同版本重打包，"
          u"所以不作废任何 SHA1。" % (os.path.basename(OLD), sha1(OLD)[:12] if os.path.isfile(OLD) else u"缺"))
    if not ok:
        fails.append(u"发布副本哈希与构建产物不一致")
    print(u"\n失败项 = %d" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
