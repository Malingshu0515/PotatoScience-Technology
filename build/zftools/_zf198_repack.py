# -*- coding: utf-8 -*-
u"""_zf198_repack.py —— ZF198 打包 `release\\PotatoST-0.15.jar`（先体检、后拷贝）。

与 ZF196 的 repack 的唯一区别：**渲染后的 mods.toml 要比"除版本号那一行外逐字节相同"**
（抬版本号本来就会改那一行，拿旧 jar 逐字节比必然变红 —— 但依赖段一个字都不许动）。

跑法：python build\\zftools\\_zf198_repack.py
"""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
LIB = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.15.jar")
REL = os.path.join(ROOT, "release", u"PotatoST-0.15.jar")
OLD_JAR = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")
TOML_SRC = os.path.join(ROOT, "src", "main", "resources", "META-INF", "neoforge.mods.toml")


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def norm(t):
    return re.sub(u'(?m)^version="[^"]*"$', u'version="X"', t)


def main():
    print(u"== ① 编译打包（gradlew build --offline） ==")
    r = subprocess.run([os.path.join(ROOT, "gradlew.bat"), "build", "--offline"],
                       cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=1800, shell=True)
    out = r.stdout.decode("utf-8", "replace")
    for line in out.split(u"\n")[-4:]:
        print(u"   " + line.rstrip())
    if r.returncode != 0 or not os.path.isfile(LIB):
        print(u"打包失败（rc=%d，产物 %s）⇒ 不动 release/" % (r.returncode, os.path.isfile(LIB)))
        return 1

    print(u"== ② 体检 build/libs 产物 ==")
    z = zipfile.ZipFile(LIB)
    n = z.namelist()
    toml = z.read(u"META-INF/neoforge.mods.toml").decode("utf-8")
    hole = z.read(u"com/potatost/mod/BlackHoleManager.class")
    grav = z.read(u"com/potatost/mod/GravityDeviceItem.class")
    ver = re.search(u'^version="([^"]+)"', toml, re.M)
    old = zipfile.ZipFile(OLD_JAR) if os.path.isfile(OLD_JAR) else None
    dep_ok, dep_detail = False, u"0.14 那份不在盘上"
    if old is not None:
        a, b = norm(toml), norm(old.read(u"META-INF/neoforge.mods.toml").decode("utf-8"))
        dep_ok = (a == b)
        dep_detail = u"依赖段%s（与 0.14 那份除版本号一行外逐字节相同）" % (u"没动" if dep_ok else u"**被改过**")
    checks = {
        u"jar 内 mods.toml 渲染版本 = 0.15": bool(ver) and ver.group(1) == u"0.15",
        u"依赖段没动（除版本号那一行）": dep_ok,
        u"源头 neoforge.mods.toml 仍是占位符（唯一版本号在 gradle.properties）":
            u"${mod_version}" in io.open(TOML_SRC, encoding="utf-8").read(),
        u"没有探针类（Zf*Check）": not [x for x in n if u"Check.class" in x],
        u"语言键没变（五语种 691 / lzh 693）":
            all(len(json.loads(z.read(u"assets/potato_s_t/lang/%s.json" % f).decode("utf-8"))) == want
                for f, want in ((u"zh_cn", 691), (u"en_us", 691), (u"lzh", 693),
                                (u"ja_jp", 691), (u"ru_ru", 691))),
        u"这几十轮的东西都在（配置 / 召唤费 / 硬上限 / 空手放 / 清除半径 / 近处拆除 / 猛砸 / 装备标签）":
            u"com/potatost/mod/PotatoSTConfig.class" in n
            and b"SUMMON_COST" in grav and b"fired.everything" in grav
            and b"HARD_CAP_TICKS" in hole and b"CLEAR_RADIUS" in hole
            and b"DEMOLISH_START_RADIUS" in hole and b"collapseEat" in hole
            and u"data/potato_s_t/damage_type/vibranium_slam.json" in n
            and all(u"data/minecraft/tags/item/%s.json" % t in n for t in
                    (u"head_armor", u"chest_armor", u"leg_armor", u"foot_armor", u"swords",
                     u"pickaxes", u"axes", u"shovels", u"hoes")),
        u"压缩包本身没坏（testzip）": (z.testzip() is None),
    }
    bad = 0
    for k, v in checks.items():
        print((u"  [OK]   " if v else u"  [FAIL] ") + k + (u"  ｜ " + dep_detail if u"依赖段没动" in k else u""))
        bad += 0 if v else 1
    print(u"  class %d ｜ 配方 %d ｜ 进度 %d"
          % (len([x for x in n if x.endswith(u".class")]),
             len([x for x in n if x.startswith(u"data/potato_s_t/recipe/") and x.endswith(u".json")]),
             len([x for x in n if x.startswith(u"data/potato_s_t/advancement/") and x.endswith(u".json")])))
    z.close()
    if old is not None:
        old.close()
    if bad:
        print(u"体检 %d 项不过 ⇒ **不动 release/**（先判后拷）" % bad)
        return 1

    print(u"== ③ 拷贝进 release/ ==")
    shutil.copy2(LIB, REL)
    h = sha(REL)
    io.open(REL + u".sha1", "w", encoding="ascii", newline=u"\n").write(h + u"\n")
    same = (h == sha(LIB) and sha(REL) == h
            and io.open(REL + u".sha1", encoding="ascii").read().strip() == h)
    print(u"  %s：%d 字节 ｜ sha1 %s ｜ 回读与 .sha1 一致：%s"
          % (os.path.basename(REL), os.path.getsize(REL), h, same))
    if not same:
        print(u"  !! 回读不一致")
        return 1
    if os.path.isfile(OLD_JAR):
        print(u"  历史：%s（%d 字节 / %s）原样留着" % (os.path.basename(OLD_JAR),
                                                    os.path.getsize(OLD_JAR), sha(OLD_JAR)[:12]))
    print(u"\n判词：打包完成；成品 = release/PotatoST-0.15.jar（%d 字节 / sha1 %s）"
          % (os.path.getsize(REL), h))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
