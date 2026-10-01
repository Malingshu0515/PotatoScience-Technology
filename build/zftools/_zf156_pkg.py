# -*- coding: utf-8 -*-
u"""_zf156_pkg.py —— ZF156 打包：0.13 成品 + "活体哈希"三处联动跟平（§4.159）。

做的事：
  ① `gradlew build --offline` ⇒ `build\\libs\\potato_s_t-0.13.jar`
  ② 抄进 `release\\PotatoST-0.13.jar`，写 `.sha1`（**纯哈希一行**，§4.92）
  ③ 跟平写死旧哈希/旧体积/旧类数的门与文档：
        · `_zf149_verify.py` 的 WANT_SHA / WANT_SIZE / 公告那句类数
        · `_zf149_jar.py` 的默认 jar 路径；`_zf155_jarcheck.py` 的 jar 路径
        · 英文公告里**所有**「当前成品」提法（哈希 / 字节数 / 类数）
        · 交接 §1 的成品行
  ④ 自证：跑 `_zf149_jar.py` / `_zf149_verify.py` / `_zf156_verify.py`

跑法：python build\\zftools\\_zf156_pkg.py [--write] [--skip-build]
"""
import hashlib
import io
import os
import re
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
BUILT = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.13.jar")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")
SHA = JAR + u".sha1"
Z149V = os.path.join(ZT, u"_zf149_verify.py")
Z149J = os.path.join(ZT, u"_zf149_jar.py")
Z155J = os.path.join(ZT, u"_zf155_jarcheck.py")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")

OLD_SHA = u""      # 由 main() 从盘上现读（见 read_current()），可重跑
OLD_SIZES = []
OLD_CLASSES = u""
NEW_RECIPES = 91

fails, notes = [], []


def read_current():
    """从 `_zf149_verify.py` 现读"当前成品靶子" —— 这样脚本**可以重跑**（§10 的同族：
    别把上一次的值写死，第二次打包时它已经不是旧值了）。"""
    global OLD_SHA, OLD_SIZES, OLD_CLASSES
    t = io.open(Z149V, encoding="utf-8", newline=u"").read()
    m = re.search(u'WANT_SHA = u"([0-9a-f]{40})"', t)
    n = re.search(u"WANT_SIZE = (\\d+)", t)
    c = re.search(u"\\*\\*(\\d+) classes, 43 advancements, (\\d+) recipes\\*\\*", t)
    if not (m and n and c):
        return False
    OLD_SHA = m.group(1)
    OLD_SIZES = [u"{:,}".format(int(n.group(1)))]
    OLD_CLASSES = u"**%d classes, 43 advancements, %d recipes**" % (int(c.group(1)), int(c.group(2)))
    return True


def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def patch(path, pairs, label):
    text = io.open(path, encoding="utf-8", newline="").read()
    for old, new in pairs:
        if new in text and old not in text:
            notes.append(u"  [跳过] %s：%s（已经是新的）" % (label, old[:40]))
            continue
        if text.count(old) != 1:
            fails.append(u"%s：锚点命中 %d 次 → %s" % (label, text.count(old), old[:60]))
            continue
        text = text.replace(old, new, 1)
        notes.append(u"  [改] %s：%s" % (label, old[:56].replace(u"\n", u" ")))
    io.open(path, u"w", encoding="utf-8", newline="").write(text)


def patch_all(path, pairs, label):
    """把**所有**出现处一次跟平（"当前成品"的提法散在好几段里）。"""
    text = io.open(path, encoding="utf-8", newline="").read()
    for old, new in pairs:
        n = text.count(old)
        if n == 0:
            if new in text:
                notes.append(u"  [跳过] %s：%s（已经是新的）" % (label, old[:40]))
                continue
            fails.append(u"%s：锚点一处都没有 → %s" % (label, old[:60]))
            continue
        text = text.replace(old, new)
        notes.append(u"  [改] %s：%s（%d 处）" % (label, old[:48], n))
    io.open(path, u"w", encoding="utf-8", newline="").write(text)


def main(argv):
    write = u"--write" in argv
    skip = u"--skip-build" in argv
    if not read_current():
        print(u"!! 从 _zf149_verify.py 读不到当前的 WANT_SHA / WANT_SIZE / 类数 —— 停手")
        return 2

    if not skip:
        print(u"① 构建")
        with io.open(os.path.join(ZT, u"_zf156_build2.log"), "wb") as fh:
            r = subprocess.run([os.path.join(ROOT, "gradlew.bat"), "build", "--offline"],
                               cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, timeout=2400)
        print(u"   gradlew build rc=%d" % r.returncode)
        if r.returncode != 0:
            fails.append(u"构建失败（看 _zf156_build2.log）")
    if not os.path.isfile(BUILT):
        fails.append(u"构建产物不在：%s" % BUILT)
        return report()
    new_sha = sha1(BUILT)
    new_size = os.path.getsize(BUILT)
    new_size_str = u"{:,}".format(new_size)
    print(u"② 成品：%s" % BUILT)
    print(u"   %d 字节 / sha1 %s" % (new_size, new_sha))
    print(u"   旧：%s 字节 / sha1 %s" % (u",".join(OLD_SIZES), OLD_SHA))
    if new_sha == OLD_SHA:
        notes.append(u"  ⚠ 与旧成品哈希相同（源码没变？）")

    if not write:
        print(u"（没加 --write：只算不写）")
        return report()

    print(u"③ 抄进 release/ + 写 .sha1（纯哈希一行）")
    data = open(BUILT, "rb").read()
    open(JAR, "wb").write(data)
    if sha1(JAR) != new_sha or os.path.getsize(JAR) != new_size:
        fails.append(u"release 那份与构建产物不一致")
    io.open(SHA, "w", encoding="ascii", newline="\n").write(new_sha + u"\n")
    notes.append(u"  [写] release/PotatoST-0.13.jar（%d B）+ .sha1" % new_size)

    print(u"④ 跟平写死旧哈希/旧类数的门与文档")
    patch(Z149V, [(u'WANT_SHA = u"%s"' % OLD_SHA, u'WANT_SHA = u"%s"' % new_sha),
                  (u"WANT_SIZE = %s" % OLD_SIZES[0].replace(u",", u""),
                   u"WANT_SIZE = %d" % new_size),
                  (OLD_CLASSES, u"**%d classes, 43 advancements, %d recipes**" % (360, NEW_RECIPES)),
                  (u'u"C7 公告 Download 段那一句的三个数跟到 359 / 91（43 不变）")',
                   u'u"C7 公告 Download 段那一句的三个数跟到 360 / 91（43 不变，ZF156 多了 ModAttachments）")')],
          u"_zf149_verify.py 成品靶子")
    patch(Z149J, [(u'DEFAULT_JAR = os.path.join(ROOT, "release", "PotatoST-0.12.jar")',
                   u'DEFAULT_JAR = os.path.join(ROOT, "release", "PotatoST-0.13.jar")'),
                  (u"跑法：python build\\\\zftools\\\\_zf149_jar.py [jar 路径]（默认 release\\\\PotatoST-0.12.jar）",
                   u"跑法：python build\\\\zftools\\\\_zf149_jar.py [jar 路径]（默认 release\\\\PotatoST-0.13.jar）"),
                  (u'u"① 配方份数（发布那一刻的实测值；ZF155 重打时 91）"',
                   u'u"① 配方份数（发布那一刻的实测值；ZF156 重打时 91）"')],
          u"_zf149_jar.py 默认 jar 路径")
    patch(Z155J, [(u'JAR = os.path.join(ROOT, "release", u"PotatoST-0.12.jar")',
                   u'JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")'),
                  (u"拆开 `release\\\\PotatoST-0.12.jar`", u"拆开 `release\\\\PotatoST-0.13.jar`")],
          u"_zf155_jarcheck.py jar 路径")
    patch_all(ANN, [(OLD_SHA, new_sha),
                    (u"release/PotatoST-0.12.jar", u"release/PotatoST-0.13.jar"),
                    (OLD_CLASSES, u"**%d classes, 43 advancements, %d recipes**" % (360, NEW_RECIPES))]
                   + [(s, new_size_str) for s in OLD_SIZES],
              u"英文公告（当前成品：哈希/名字/体积/类数）")

    print(u"⑤ 交接 §1 成品行（正则跟平：任意 0.1x 版本名 + 任意 40 位哈希 + 任意字节数）")
    hand = io.open(HAND, encoding="utf-8", newline=u"").read()
    pat = re.compile(u"`release\\\\PotatoST-0\\.1\\d\\.jar` = `[0-9a-f]{40}`（[0-9,]+ B，\\*\\*最新一次重打\\*\\*：([^）]*)）")
    m = pat.search(hand)
    if not m:
        fails.append(u"交接 §1 成品行：正则没匹配上")
    else:
        tail = m.group(1).rstrip(u" /")
        new_line = (u"`release\\PotatoST-0.13.jar` = `%s`（%s B，**最新一次重打**：%s / "
                    u"**ZF156 端子连线 / 手册只发一次 / 金属板跨 mod**）" % (new_sha, new_size_str, tail))
        hand = hand[:m.start()] + new_line + hand[m.end():]
        io.open(HAND, u"w", encoding="utf-8", newline=u"").write(hand)
        notes.append(u"  [改] 交接 §1 成品行 → %s…（%s B）" % (new_sha[:12], new_size_str))

    print(u"\n".join(notes))
    print(u"⑥ 自证")
    for script in (Z149J, Z149V, os.path.join(ZT, u"_zf156_verify.py")):
        r = subprocess.run([sys.executable, script], cwd=ROOT, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=900)
        out = r.stdout.decode("utf-8", "replace")
        tail = [l for l in out.split(u"\n") if u"通过" in l and u"失败" in l]
        print(u"   %-22s rc=%d  %s" % (os.path.basename(script), r.returncode,
                                       (tail[-1].strip() if tail else u"")[:90]))
        if r.returncode != 0:
            fails.append(u"%s 没绿" % os.path.basename(script))
            for l in out.split(u"\n"):
                if u"[FAIL]" in l:
                    print(u"      " + l.strip()[:140])
    return report()


def report():
    print(u"")
    print(u"================ ZF156 打包 ================")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
