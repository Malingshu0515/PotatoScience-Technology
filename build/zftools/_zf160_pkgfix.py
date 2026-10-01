# -*- coding: utf-8 -*-
u"""_zf160_pkgfix.py —— ZF160 重打后跟平三处"活体数字"（幂等，默认 dry-run）。

重打出来的 jar 里 **class 365 / 配方 94 / 进度 43**（上一版 360 / 91 / 43）——
多出来的那份是**另一条线在途**的活（3 份 `generator_fuel/*` 配方 + `DieselGeneratorBlockEntity$FuelClass`
+ 3 张 `c:dusts/*` 标签），jar 是从工作树打的，所以照样进去了（账记在档案 §4.168 与轮报里）。

要跟平的三处：
  ① `_zf149_jar.py` 的配方份数断言 91 → 94（+ 标签注明为什么）
  ② `_zf149_verify.py` 里钉公告那句 `**360 classes, 43 advancements, 91 recipes**` → 365 / 94
  ③ 英文公告里同一句（4 处提法里那一处）

跑法：python build\\zftools\\_zf160_pkgfix.py [--write]
"""
import io
import os
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
Z149J = os.path.join(ZT, u"_zf149_jar.py")
Z149V = os.path.join(ZT, u"_zf149_verify.py")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")

notes, fails = [], []


def main(argv):
    write = u"--write" in argv
    z = zipfile.ZipFile(JAR)
    names = z.namelist()
    cls = len([n for n in names if n.endswith(".class")])
    rec = len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(".json")])
    adv = len([n for n in names if n.startswith(u"data/potato_s_t/advancement/") and n.endswith(".json")])
    print(u"jar 实测：class %d / 配方 %d / 进度 %d" % (cls, rec, adv))

    OLD_STR = u"**360 classes, 43 advancements, 91 recipes**"
    NEW_STR = u"**%d classes, 43 advancements, %d recipes**" % (cls, rec)

    # ① _zf149_jar.py
    t = io.open(Z149J, encoding="utf-8", newline=u"").read()
    if u"check(len(recipes) == %d," % rec in t:
        notes.append(u"  [跳过] _zf149_jar.py 配方份数（已经是 %d）" % rec)
    elif t.count(u"check(len(recipes) == 91,") == 1:
        t = t.replace(u"check(len(recipes) == 91,", u"check(len(recipes) == %d," % rec, 1)
        t = t.replace(u'u"① 配方份数（发布那一刻的实测值；ZF156 重打时 91）"',
                      u'u"① 配方份数（发布那一刻的实测值；ZF160 重打时 %d，其中 3 份是另一条线在途的 generator_fuel）"' % rec, 1)
        notes.append(u"  [改] _zf149_jar.py 配方份数 91 → %d" % rec)
        if write:
            io.open(Z149J, u"w", encoding="utf-8", newline=u"").write(t)
    else:
        fails.append(u"_zf149_jar.py 的配方份数锚点找不到")

    # ② _zf149_verify.py
    v = io.open(Z149V, encoding="utf-8", newline=u"").read()
    if NEW_STR in v:
        notes.append(u"  [跳过] _zf149_verify.py 的公告类数/配方数（已经是 %d/%d）" % (cls, rec))
    elif v.count(OLD_STR) == 1:
        v = v.replace(OLD_STR, NEW_STR, 1)
        v = v.replace(u'u"C7 公告 Download 段那一句的三个数跟到 360 / 91（43 不变，ZF156 多了 ModAttachments）"',
                      u'u"C7 公告 Download 段那一句的三个数跟到 %d / %d（43 不变；ZF160 重打时的实测值）"' % (cls, rec), 1)
        notes.append(u"  [改] _zf149_verify.py 的 C7 靶子 → %d / %d" % (cls, rec))
        if write:
            io.open(Z149V, u"w", encoding="utf-8", newline=u"").write(v)
    else:
        fails.append(u"_zf149_verify.py 的 %s 命中 %d 次" % (OLD_STR, v.count(OLD_STR)))

    # ③ 公告
    a = io.open(ANN, encoding="utf-8", newline=u"").read()
    n = a.count(OLD_STR)
    if n == 0 and NEW_STR in a:
        notes.append(u"  [跳过] 公告里那句（已经是 %d/%d）" % (cls, rec))
    elif n:
        a = a.replace(OLD_STR, NEW_STR)
        notes.append(u"  [改] 公告里那句（%d 处）→ %d / %d" % (n, cls, rec))
        if write:
            io.open(ANN, u"w", encoding="utf-8", newline=u"").write(a)
    else:
        fails.append(u"公告里找不到 %s" % OLD_STR)

    print(u"\n".join(notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    if not write:
        print(u"（没加 --write，只算不写）")
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
