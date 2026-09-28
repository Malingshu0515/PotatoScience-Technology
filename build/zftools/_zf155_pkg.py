# -*- coding: utf-8 -*-
u"""_zf155_pkg.py —— ZF155 打包：重打 0.12 成品 + 把"活体哈希"三处联动跟平（§4.159）。

做的事：
  ① `gradlew build --offline` ⇒ `build\\libs\\potato_s_t-0.12.jar`
  ② 抄进 `release\\PotatoST-0.12.jar`，写 `.sha1`（**纯哈希一行**，§4.92）
  ③ 跟平写死旧哈希的三处：
       · `_zf149_verify.py` 的 WANT_SHA / WANT_SIZE（成品靶子）
       · `_zf149_jar.py` 的配方份数 89 → 91、五份语言键数 587/589 → 594/596
       · 英文公告里三处当前 jar 提法 + 交接 §1 的成品行
  ④ 公告里 ZF155 那一条补一段 Download（说明这一版装了通用升级模板）
  ⑤ 跑 `_zf149_jar.py` 与 `_zf149_verify.py` 自证

跑法：python build\\zftools\\_zf155_pkg.py [--write] [--skip-build]
"""
import hashlib
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
BUILT = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.12.jar")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.12.jar")
SHA = JAR + u".sha1"
LIB = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.12.jar")
Z149V = os.path.join(ZT, u"_zf149_verify.py")
Z149J = os.path.join(ZT, u"_zf149_jar.py")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")

OLD_SHA = u"b02fe30cd8aa7f9c135310439d227fed1dbbc87f"
OLD_SIZE = 5863907
OLD_SIZE_STR = u"5,863,907"
NEW_RECIPES, OLD_RECIPES = 91, 89
NEW_KEYS4, NEW_KEYS5 = 594, 596

fails, notes = [], []


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
    """把**所有**出现处一次跟平（哈希/体积这种"当前成品"的提法散在好几段里）。"""
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

    if not skip:
        print(u"① 构建")
        r = subprocess.run([os.path.join(ROOT, "gradlew.bat"), "build", "--offline", "-q"],
                           cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=1800)
        out = r.stdout.decode("utf-8", "replace")
        print(u"   gradlew build rc=%d" % r.returncode)
        if r.returncode != 0:
            print(out[-1500:])
            fails.append(u"构建失败")
    if not os.path.isfile(BUILT):
        fails.append(u"构建产物不在：%s" % BUILT)
        return report()
    new_sha = sha1(BUILT)
    new_size = os.path.getsize(BUILT)
    print(u"② 成品：%s" % BUILT)
    print(u"   %d 字节 / sha1 %s" % (new_size, new_sha))
    print(u"   旧：%d 字节 / sha1 %s" % (OLD_SIZE, OLD_SHA))
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
    notes.append(u"  [写] release/PotatoST-0.12.jar（%d B）+ .sha1" % new_size)

    print(u"④ 跟平写死旧哈希的三处")
    patch(Z149V, [(u'WANT_SHA = u"%s"' % OLD_SHA, u'WANT_SHA = u"%s"' % new_sha),
                  (u"WANT_SIZE = %d" % OLD_SIZE, u"WANT_SIZE = %d" % new_size),
                  (u'check(u"**358 classes, 43 advancements, 74 recipes**" in ann',
                   u'check(u"**%d classes, 43 advancements, %d recipes**" in ann' % (359, NEW_RECIPES)),
                  (u'u"C7 公告 Download 段那一句的三个数跟到 358 / 74（43 不变）")',
                   u'u"C7 公告 Download 段那一句的三个数跟到 359 / %d（43 不变）")' % NEW_RECIPES)],
          u"_zf149_verify.py 成品靶子")
    patch(Z149J, [(u"check(len(recipes) == %d," % OLD_RECIPES,
                   u"check(len(recipes) == %d," % NEW_RECIPES),
                  (u'u"① 配方份数（发布那一刻的实测值；ZF153 重打时 %d）"' % OLD_RECIPES,
                   u'u"① 配方份数（发布那一刻的实测值；ZF155 重打时 %d）"' % NEW_RECIPES)],
          u"_zf149_jar.py 审计靶子（配方份数；语言键数由 _zf155_retarget.py 统一跟平）")
    patch_all(ANN, [(OLD_SHA, new_sha),
                    (OLD_SIZE_STR, u"{:,}".format(new_size)),
                    (u"**358 classes, 43 advancements, 74 recipes**",
                     u"**359 classes, 43 advancements, %d recipes**" % NEW_RECIPES)],
              u"英文公告（所有「当前成品」提法 + 类/配方数）")
    patch(HAND, [(u"= `%s`（%s B，**最新一次重打**：含 ZF148 手册 / ZF149 打包 / "
                  u"**ZF151 挖掘口径修复** / ZF150 金属粒 / ZF153 振金剑）"
                  % (OLD_SHA, OLD_SIZE_STR),
                  u"= `%s`（%d B，**最新一次重打**：含 ZF148 手册 / ZF149 打包 / ZF151 挖掘口径修复 / "
                  u"ZF150 金属粒 / ZF153 振金剑 / **ZF155 通用升级模板**）" % (new_sha, new_size))],
          u"交接 §1 成品行")

    print(u"\n".join(notes))
    print(u"⑤ 自证")
    for script in (Z149J, Z149V):
        r = subprocess.run([sys.executable, script], cwd=ROOT, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=600)
        out = r.stdout.decode("utf-8", "replace")
        tail = [l for l in out.split(u"\n") if u"====" in l or u"通过" in l and u"失败" in l]
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
    print(u"================ ZF155 打包 ================")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
