# -*- coding: utf-8 -*-
r"""_zf103_publish.py —— ZF103 出成品（用户自己润色了中文翻译）+ 把 §9 的占位填实

口径照 ZF84/ZF93 那两次「用户自己动手改东西」的先例：
  · **改动是用户的**，我只负责取证 + 构进去 + 记录（不替用户"改进"他的文字）；
  · 改前那份成品 jar 就是等级 ① 的权威来源（§4.17）—— 用它比对；
  · 同版本重打包 ⇒ 必须声明作废上一版 SHA1。

⚠ 本轮**额外**加了一条防线：`resources` 目录**逐份**与改前那份 jar 比对，
  把"除了预期的那几份，别的一个字节都没变"打成表 ——
  工程里最近出现过"文件被别的东西还原回去"的事（见 §5 ZF102 那一行的 slip 3），
  这条能把那种事当场摆在台面上。
"""
import hashlib
import io
import json
import os
import re
import shutil
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "build", "libs", "potato_s_t-0.11.jar")
DST = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
SHA = DST + ".sha1"
PUB = os.path.join(ROOT, "build", "zftools", "_zf103_publish.py")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
RES = os.path.join(ROOT, r"src\main\resources")
LANGDIR = os.path.join(RES, r"assets\potato_s_t\lang")
VOID = "90510e1890af79242cb41e0cda0a2f6472b12cdf"
PREV_ROUND_SHA = "48bc3358b1a68da81827b952ab4eb8b645415cc2"
EXPECT_KEYS = 335
# 预期**只有**这份跟改前成品不同（用户润色的就是它）
EXPECT_DIFF = {u"assets/potato_s_t/lang/zh_cn.json"}
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def read(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else u""


def patch(path, old, new, label, expect=1, optional=False):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != expect:
        if optional and hits == 0:
            print(u"  [SKIP] %s（已经填过了）" % label)
            return
        fails.append(u"%s：锚点命中 %d 次（必须 %d）" % (label, hits, expect))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def resource_diff(old_jar):
    u"""盘上的 resources 与改前那份 jar 逐份比 —— 返回 (变了的名, 多出来的名, 少掉的名)"""
    changed, extra = [], []
    with zipfile.ZipFile(old_jar) as zf:
        inside = {n: zf.read(n) for n in zf.namelist()
                  if (n.startswith(u"assets/") or n.startswith(u"data/")) and not n.endswith(u"/")}
    for name, blob in sorted(inside.items()):
        p = os.path.join(RES, name.replace(u"/", os.sep))
        if not os.path.exists(p):
            changed.append(name + u"（盘上没了）")
        elif open(p, "rb").read() != blob:
            changed.append(name)
    for dp, _, fs in os.walk(RES):
        for f in fs:
            full = os.path.join(dp, f)
            rel = os.path.relpath(full, RES).replace(os.sep, u"/")
            if rel not in inside:
                extra.append(rel)
    return changed, extra


def main():
    old = sha1(DST) if os.path.exists(DST) else u"(缺)"
    if old != VOID:
        fails.append(u"当前成品 %s ≠ 预期要作废的 %s" % (old, VOID))

    print(u"\n== 一、盘上 resources 与改前成品逐份比 ==")
    changed, extra = resource_diff(DST)
    only_expected = set(changed) == EXPECT_DIFF
    print(u"  变了 %d 份：%s" % (len(changed), u"、".join(changed) or u"无"))
    print(u"  新增 %d 份：%s" % (len(extra), u"、".join(extra) or u"无"))
    if not only_expected:
        fails.append(u"变的不止预期那几份：%s" % changed)
    else:
        print(u"  [OK]   只有用户润色的那份 lang 变了（其余 resources 逐字节未动）")

    print(u"\n== 二、四份语言的键数（只改文字、不许动键） ==")
    for f in (u"zh_cn.json", u"en_us.json", u"ja_jp.json", u"ru_ru.json"):
        d = json.loads(read(os.path.join(LANGDIR, f)))
        if len(d) != EXPECT_KEYS:
            fails.append(u"%s 键数 %d ≠ %d" % (f, len(d), EXPECT_KEYS))
        else:
            print(u"  [OK]   %s 仍是 %d 键" % (f, EXPECT_KEYS))

    if not os.path.exists(SRC):
        print(u"  [FAIL] 缺构建产物 ⇒ 一个字节都不动")
        return 1
    new = sha1(SRC)
    size = os.path.getsize(SRC)
    with zipfile.ZipFile(SRC) as zf:
        names = zf.namelist()
        entries = len(names)
        if [n for n in names if "Check" in n.split("/")[-1] and n.endswith(".class")]:
            fails.append(u"成品里带探针")
        inside = json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
        disk = json.loads(read(os.path.join(LANGDIR, u"zh_cn.json")))
        if inside != disk:
            fails.append(u"成品里的 zh_cn 与盘上那份**不一致**（构建没带上？）")
        else:
            print(u"  [OK]   成品里的 zh_cn 就是盘上那份（%d 键）" % len(inside))
    if new == old:
        fails.append(u"新旧哈希相同 ⇒ 没重新构建？")

    if fails:
        print(u"\n  [FAIL] 以上 %d 条没过 ⇒ 一个字节都不动" % len(fails))
        for f in fails:
            print(u"    !! " + f)
        return 1

    shutil.copy2(SRC, DST)
    io.open(SHA, "w", encoding="ascii", newline=u"\n").write(new + u"\n")
    print(u"\n① 已发布 release\\PotatoST-0.11.jar = %s（%d B / %d 条目）" % (new, size, entries))
    print(u"   作废 %s（ZF102）" % VOID[:8])
    patch(DOC, u"__ZF103_SHA1__", new, u"§9 ZF103 条目：哈希填实", optional=True)
    patch(DOC, u"__ZF103_BYTES__", str(size), u"§9 ZF103 条目：字节数填实", optional=True)
    patch(DOC, u"__ZF103_ENTRIES__", str(entries), u"§9 ZF103 条目：条目数填实", optional=True)
    patch(DOC, u"**成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"**当时的成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"§9 ZF102 条目：成品 → 当时的成品", optional=True)
    patch(PUB, u'VOID = "%s"' % VOID, u'VOID = "%s"' % new, u"发布脚本 VOID 跟到最新")
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
