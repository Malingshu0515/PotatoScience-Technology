# -*- coding: utf-8 -*-
u"""_zf188_repack.py —— ZF188 重新打包 release\\PotatoST-0.14.jar（先体检、后拷贝）。

规矩（ZF63 那一课）：**先判后拷** —— 体检不过就一个字节都不动 release/。
跑法：python build\\zftools\\_zf188_repack.py
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
LIB = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.14.jar")
REL = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")
PRE_JAR = os.path.join(ROOT, "build", "zftools", "zf188_pre", "release", u"PotatoST-0.14.jar")


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def main():
    print(u"== ① 编译打包（gradlew build --offline） ==")
    r = subprocess.run([os.path.join(ROOT, "gradlew.bat"), "build", "--offline"],
                       cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=1800, shell=True)
    out = r.stdout.decode("utf-8", "replace")
    for line in out.split(u"\n")[-5:]:
        print(u"   " + line.rstrip())
    if r.returncode != 0 or not os.path.isfile(LIB):
        print(u"打包失败（rc=%d）⇒ 不动 release/" % r.returncode)
        return 1

    print(u"== ② 体检 build/libs 产物 ==")
    z = zipfile.ZipFile(LIB)
    n = z.namelist()
    toml = z.read(u"META-INF/neoforge.mods.toml").decode("utf-8")
    cfg_cls = z.read(u"com/potatost/mod/PotatoSTConfig.class")
    scr_cls = z.read(u"com/potatost/mod/client/PotatoSTConfigScreen.class")
    checks = {
        u"新策略方法进了 class（shouldRegisterOwnConfigScreen）":
            b"shouldRegisterOwnConfigScreen" in cfg_cls,
        u"「configured」这个可选 modid 在客户端 class 里（让位判据真的打进去了）":
            b"configured" in scr_cls,
        u"没有探针类（Zf*Check）": not [x for x in n if u"Check.class" in x],
        u"五份 lang 键数 = 689/689/691/689/689":
            all(len(json.loads(z.read(u"assets/potato_s_t/lang/%s.json" % f).decode("utf-8"))) == want
                for f, want in ((u"zh_cn", 689), (u"en_us", 689), (u"lzh", 691),
                                (u"ja_jp", 689), (u"ru_ru", 689))),
        u"mods.toml 版本仍是 0.14": u'version="0.14"' in toml,
        u"依赖清单与改前一字不差（Configured 不是依赖）":
            os.path.isfile(PRE_JAR)
            and zipfile.ZipFile(PRE_JAR).read(u"META-INF/neoforge.mods.toml") == toml.encode("utf-8"),
        u"上一轮的东西都还在（配置类 + 猛砸伤害类型 + 装备标签）":
            u"com/potatost/mod/PotatoSTConfig.class" in n
            and u"data/potato_s_t/damage_type/vibranium_slam.json" in n
            and all(u"data/minecraft/tags/item/%s.json" % t in n for t in
                    (u"head_armor", u"chest_armor", u"leg_armor", u"foot_armor", u"swords",
                     u"pickaxes", u"axes", u"shovels", u"hoes")),
        u"压缩包本身没坏（testzip）": (z.testzip() is None),
    }
    bad = 0
    for k, v in checks.items():
        print((u"  [OK]   " if v else u"  [FAIL] ") + k)
        bad += 0 if v else 1
    print(u"  class %d ｜ 配方 %d ｜ 进度 %d"
          % (len([x for x in n if x.endswith(u".class")]),
             len([x for x in n if x.startswith(u"data/potato_s_t/recipe/") and x.endswith(u".json")]),
             len([x for x in n if x.startswith(u"data/potato_s_t/advancement/") and x.endswith(u".json")])))
    z.close()
    if bad:
        print(u"体检 %d 项不过 ⇒ **不动 release/**（先判后拷）" % bad)
        return 1

    print(u"== ③ 拷贝进 release/ ==")
    old = sha(REL) if os.path.isfile(REL) else u"-"
    shutil.copy2(LIB, REL)
    h = sha(REL)
    io.open(REL + u".sha1", "w", encoding="ascii", newline=u"\n").write(h + u"\n")
    same = (h == sha(LIB) and sha(REL) == h
            and io.open(REL + u".sha1", encoding="ascii").read().strip() == h)
    print(u"  旧品 %s → 新品 %s" % (old[:12], h[:12]))
    print(u"  %d 字节 ｜ 回读与 .sha1 一致：%s" % (os.path.getsize(REL), same))
    if not same:
        print(u"  !! 回读不一致")
        return 1
    print(u"\n判词：打包完成；成品 = release/PotatoST-0.14.jar（%d 字节 / sha1 %s）"
          % (os.path.getsize(REL), h))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
