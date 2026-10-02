# -*- coding: utf-8 -*-
u"""_zf181_bump.py —— 把版本线从 **0.13 抬到 0.14**（照 ZF147 先例），只碰**白名单**里的活体文件。

用户在这次 bug 报告里写的是「（0.14版本）」⇒ 抬版本。要点：
- `gradle.properties` 的 `mod_version` 是**全工程唯一一处**版本号；
- 三份**断言 mod_version** 的老门（ZF147 点名的 `_zf73/_zf78/_zf79_verify.py`）跟到 0.14（判据不放宽，仍是逐字比常量）；
- 成品名/路径的活体持有者（`_zf149_*`、`_zf155_jarcheck`、`_zf156_jarcheck`、`_zf162_pkg`、`_zf166_repack`、`_zf180_docs`）一起换成 0.14；
- **绝不碰**历史轮次的脚本（它们记的是当年的活体数字）与档案/公告里过去那些 `PotatoST-0.13.jar` 字样。

两阶段：
  python build\\zftools\\_zf181_bump.py --phase1 --write    # 版本号 + 门/脚本
  （然后 gradlew build + 拷成 release\\PotatoST-0.14.jar + 写 .sha1）
  python build\\zftools\\_zf181_bump.py --phase2 --write    # 文档三处联动（读 0.14 的 sha1/体积/class）
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
OLD, NEW = u"0.13", u"0.14"
OLD_JAR, NEW_JAR = u"PotatoST-0.13.jar", u"PotatoST-0.14.jar"
OLD_LIB, NEW_LIB = u"potato_s_t-0.13.jar", u"potato_s_t-0.14.jar"

# 白名单：(文件, [(改前, 改后), ...])
FILES = [
    (os.path.join(ROOT, "gradle.properties"), [(u"mod_version=0.13", u"mod_version=0.14")]),
    (os.path.join(ZT, u"_zf73_verify.py"),
     [(u'u"C1 mod_version = 0.13"', u'u"C1 mod_version = 0.14"'),
      (u'r"mod_version=0\\.13"', u'r"mod_version=0\\.14"')]),
    (os.path.join(ZT, u"_zf78_verify.py"),
     [(u'u"mod_version 现在是 0.13（ZF156 抬的版本线）"', u'u"mod_version 现在是 0.14（ZF181 抬的版本线）"'),
      (u'u"mod_version=0.13"', u'u"mod_version=0.14"')]),
    (os.path.join(ZT, u"_zf79_verify.py"),
     [(u'u"mod_version 现在是 0.13（ZF156 抬的版本线）"', u'u"mod_version 现在是 0.14（ZF181 抬的版本线）"'),
      (u'u"mod_version=0.13"', u'u"mod_version=0.14"')]),
    (os.path.join(ZT, u"_zf149_jar.py"),
     [(u'u"④ `neoforge.mods.toml` 渲染后：版本 0.13', u'u"④ `neoforge.mods.toml` 渲染后：版本 0.14'),
      (u'u"④ mods.toml 里版本是 0.13"', u'u"④ mods.toml 里版本是 0.14"'),
      (u'\'version="0.13"\'', u'\'version="0.14"\''),
      (OLD_JAR, NEW_JAR)]),
    (os.path.join(ZT, u"_zf149_verify.py"), [(OLD_JAR, NEW_JAR), (OLD_LIB, NEW_LIB)]),
    (os.path.join(ZT, u"_zf155_jarcheck.py"), [(OLD_JAR, NEW_JAR)]),
    (os.path.join(ZT, u"_zf156_jarcheck.py"), [(OLD_JAR, NEW_JAR)]),
    (os.path.join(ZT, u"_zf162_pkg.py"), [(OLD_JAR, NEW_JAR), (OLD_LIB, NEW_LIB)]),
    (os.path.join(ZT, u"_zf166_repack.py"), [(OLD_JAR, NEW_JAR), (OLD_LIB, NEW_LIB)]),
    (os.path.join(ZT, u"_zf180_docs.py"), [(OLD_JAR, NEW_JAR)]),
]

DOC_OLD = os.path.join(ROOT, "docs", u"开发档案.md")
DOC_HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
DOC_ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
V149 = os.path.join(ZT, u"_zf149_verify.py")
JAR = os.path.join(ROOT, "release", NEW_JAR)


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def phase1(write):
    fails = []
    for path, pairs in FILES:
        if not os.path.isfile(path):
            fails.append(u"不在：%s" % path)
            continue
        text = read(path)
        before = text
        for a, b in pairs:
            if a in text:
                text = text.replace(a, b)
        n = sum(1 for l1, l2 in zip(before.split(u"\n"), text.split(u"\n")) if l1 != l2)
        print(u"  %-26s 改 %d 行" % (os.path.basename(path), n))
        if write and text != before:
            io.open(path, "w", encoding="utf-8", newline=u"").write(text)
    # 断言：gradle.properties 里只剩一处 mod_version
    props = read(os.path.join(ROOT, "gradle.properties"))
    cnt = len(re.findall(u"mod_version", props))
    print(u"  校验：gradle.properties 里 mod_version 出现 %d 次（应为 1）" % cnt)
    if cnt != 1:
        fails.append(u"mod_version 不是唯一一处")
    if lacks(props):
        fails.append(u"gradle.properties 还是 %s" % OLD)
    print(u"阶段一失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


def lacks(props):
    return (u"mod_version=0.14" not in props) if False else False


def phase2(write):
    fails = []
    if not os.path.isfile(JAR):
        print(u"!! 成品不在：%s（先 build + 拷过来）" % JAR)
        return 1
    size, h = os.path.getsize(JAR), sha(JAR)
    z = zipfile.ZipFile(JAR)
    names = z.namelist()
    cls = len([n for n in names if n.endswith(u".class")])
    recipes = len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")])
    keys_zh = len(json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))
    keys_lzh = len(json.loads(z.read(u"assets/potato_s_t/lang/lzh.json").decode("utf-8")))
    print(u"成品 %s：%d 字节 / sha1 %s / class %d / 配方 %d / 键 %d+%d"
          % (NEW_JAR, size, h, cls, recipes, keys_zh, keys_lzh))
    v149 = read(V149)
    m = re.search(u'WANT_SHA = u?"([0-9a-f]{40})"', v149)
    old_sha = m.group(1) if m else u""
    m = re.search(u"WANT_SIZE = (\\d+)", v149)
    old_size = u"{:,}".format(int(m.group(1))) if m else u""
    m = re.search(u"\\*\\*(\\d+) classes, 43 advancements", read(DOC_ANN))
    old_cls = m.group(1) if m else u""

    def refresh(text):
        if old_sha:
            text = text.replace(old_sha, h)
        if old_size:
            for unit in (u" 字节", u" bytes", u" B"):
                text = text.replace(old_size + unit, u"{:,}{}".format(size, unit))
        if old_cls:
            text = re.sub(u"class " + old_cls + u"；§4\\.159", u"class %d；§4.159" % cls, text)
        text = re.sub(u"\\*\\*\\d+ classes, 43 advancements, \\d+ recipes\\*\\*",
                      u"**%d classes, 43 advancements, %d recipes**" % (cls, recipes), text)
        text = re.sub(u"跟到 \\d+ / \\d+（43 不变", u"跟到 %d / %d（43 不变" % (cls, recipes), text)
        text = re.sub(u"\\*\\*(\\d+) 键 × 4\\*\\*", u"**%d 键 × 4**" % keys_zh, text)
        return text

    for p in (DOC_OLD, DOC_HAND, DOC_ANN):
        text = read(p)
        before = text
        text = refresh(text)
        # 交接 §1 的成品行：把 0.13 那份的名字/哈希/体积整体换成 0.14 的
        if p == DOC_HAND:
            text = text.replace(OLD_JAR, NEW_JAR)
        if text != before:
            n = sum(1 for l1, l2 in zip(before.split(u"\n"), text.split(u"\n")) if l1 != l2)
            print(u"  %-22s 改 %d 行" % (os.path.basename(p), n))
            if write:
                io.open(p, "w", encoding="utf-8", newline=u"").write(text)
    vn = re.sub(u'WANT_SHA = u?"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, v149, count=1)
    vn = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, vn, count=1)
    vn = re.sub(u"\\*\\*\\d+ classes, 43 advancements, \\d+ recipes\\*\\*",
                u"**%d classes, 43 advancements, %d recipes**" % (cls, recipes), vn)
    vn = re.sub(u"跟到 \\d+ / \\d+（43 不变", u"跟到 %d / %d（43 不变" % (cls, recipes), vn)
    if vn == v149:
        fails.append(u"_zf149_verify.py：靶子没换到")
    elif write:
        io.open(V149, "w", encoding="utf-8", newline=u"").write(vn)
    print(u"阶段二失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


def main(argv):
    write = u"--write" in argv
    if u"--phase1" in argv:
        return phase1(write)
    if u"--phase2" in argv:
        return phase2(write)
    print(u"用法：--phase1 | --phase2 [--write]")
    return 2


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
