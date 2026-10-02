# -*- coding: utf-8 -*-
u"""_zf167_publish.py —— ZF167 打包发布（同版本原地重打 ⇒ 必须公布作废的旧 SHA1）

四道闸，一道不过就不拷（`shutil.copy2` 一律写在 `if fails` **之后** —— ZF63 那个坑）：
  ① 重打 `gradlew build --offline --no-build-cache`；
  ② 产物里该有的（新机器/两个物品的 class、贴图、模型、四份配方、标签）在，
     **探针 class 不许在**；
  ③ jar 比它包进去的源文件新（过期检查）；
  ④ 拷到 `release\\PotatoST-0.13.jar` + 写 `.sha1`，并公布作废的旧哈希。

跑法：python build\\zftools\\_zf167_publish.py
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
LIBS = os.path.join(ROOT, r"build\libs\potato_s_t-0.13.jar")
REL = os.path.join(ROOT, r"release\PotatoST-0.13.jar")
SHA = os.path.join(ROOT, r"release\PotatoST-0.13.jar.sha1")

WANT = [u"com/potatost/mod/ColaItem.class",
        u"com/potatost/mod/CanningMachineRecipes.class",
        u"com/potatost/mod/BeverageCanningMachineBlock.class",
        u"com/potatost/mod/BeverageCanningMachineBlockEntity.class",
        u"com/potatost/mod/BeverageCanningMachineMenu.class",
        u"assets/potato_s_t/textures/block/beverage_canning_machine_top.png",
        u"assets/potato_s_t/models/item/empty_aluminum_can.json",
        u"assets/potato_s_t/models/item/cola.json",
        u"data/potato_s_t/recipe/empty_aluminum_can.json",
        u"data/potato_s_t/recipe/empty_aluminum_can_from_blasting.json",
        u"data/potato_s_t/recipe/beverage_canning_machine.json",
        u"data/c/tags/fluid/ethanol.json"]
FORBID = [u"Zf167Check", u"Zf166Check", u"Zf153Check", u"Zf151Check", u"Zf152Check"]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    old = io.open(SHA, encoding="utf-8").read().strip() if os.path.exists(SHA) else u"（没有 .sha1）"
    print(u"发布前 release\\PotatoST-0.13.jar 的 sha1 = %s" % old)

    print(u"\n① 重打")
    env = dict(os.environ, GRADLE_USER_HOME=r"E:\gradle-home")
    r = subprocess.run([os.path.join(ROOT, "gradlew.bat"), "build", "--offline", "--no-build-cache"],
                       cwd=ROOT, capture_output=True, env=env)
    out = (r.stdout + r.stderr).decode("utf-8", "replace")
    ok = r.returncode == 0 and u"BUILD SUCCESSFUL" in out
    print(u"   exit=%d %s" % (r.returncode, u"BUILD SUCCESSFUL" if ok else u"**失败**"))
    if not ok:
        fails.append(u"重打失败")
        for l in [x for x in out.split(u"\n") if u"错误" in x or u"error:" in x][:6]:
            print(u"   " + l.strip()[:170])
    if not os.path.exists(LIBS):
        fails.append(u"没有产物")
        print(u"失败项 = %d" % len(fails))
        return 1

    print(u"\n② 产物内容")
    with zipfile.ZipFile(LIBS) as zf:
        names = zf.namelist()
        for w in WANT:
            hit = w in names
            print(u"   [%s] %s" % (u"OK" if hit else u"!!", w))
            if not hit:
                fails.append(u"产物里没有 %s" % w)
        bad = [n for n in names if any(f in n for f in FORBID)]
        print(u"   [%s] 探针 class 不在产物里（%d 条命中）" % (u"OK" if not bad else u"!!", len(bad)))
        if bad:
            fails.append(u"产物里有探针：%s" % bad[:3])
        d = json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
        # ⚠ 键数**别写死**：别的线随时会加键（本轮就撞上过一次 620 → 621）。
        #   要守的是"产物里的语言文件与**盘上那份**键数一致"（外加本轮的键确实在里面）。
        live = len(json.loads(io.open(os.path.join(
            ROOT, r"src\main\resources\assets\potato_s_t\lang\zh_cn.json"),
            encoding="utf-8").read()))
        hit = len(d) == live and u"item.potato_s_t.cola" in d
        print(u"   [%s] 产物里 zh_cn.json：%d 键（盘上 %d）、可乐那个键在"
              % (u"OK" if hit else u"!!", len(d), live))
        if not hit:
            fails.append(u"产物里 zh_cn.json 键数 %d ≠ 盘上 %d" % (len(d), live))
        # 顺带记下产物里的类/配方/语言四件（公告与门要这三个数）
        cls = len([n for n in names if n.endswith(u".class")])
        recipes = len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")])
        advs = len([n for n in names if n.startswith(u"data/potato_s_t/advancement/") and n.endswith(u".json")])
        print(u"   产物统计：class %d / 配方 %d / 进度 %d" % (cls, recipes, advs))
        io.open(os.path.join(ROOT, r"build\zftools\_zf167_jarstats.txt"), "w",
                encoding="utf-8", newline=u"\n").write(
            u"class=%d\nrecipes=%d\nadvancements=%d\n" % (cls, recipes, advs))

    print(u"\n③ 过期检查")
    jar_m = os.path.getmtime(LIBS)
    newer = []
    for rel in (r"src\main\java\com\potatost\mod\BeverageCanningMachineBlockEntity.java",
                r"src\main\java\com\potatost\mod\BeverageCanningMachineBlock.java",
                r"src\main\java\com\potatost\mod\CanningMachineRecipes.java",
                r"src\main\java\com\potatost\mod\ColaItem.java",
                r"src\main\java\com\potatost\mod\ModItems.java",
                r"src\main\resources\assets\potato_s_t\lang\zh_cn.json"):
        p = os.path.join(ROOT, rel)
        if os.path.exists(p) and os.path.getmtime(p) > jar_m:
            newer.append(rel)
    print(u"   [%s] 没有源文件比 jar 新（%d 个）" % (u"OK" if not newer else u"!!", len(newer)))
    if newer:
        fails.append(u"比 jar 新的源文件：%s" % newer[:3])

    print(u"\n④ 发布")
    if fails:
        print(u"   **有失败项 ⇒ 不拷**")
    else:
        shutil.copy2(LIBS, REL)
        new = sha1(REL)
        io.open(SHA, "w", encoding="utf-8", newline=u"\n").write(new)
        print(u"   [OK] release\\PotatoST-0.13.jar = %d 字节" % os.path.getsize(REL))
        print(u"   [OK] 新 sha1 = %s" % new)
        print(u"   ⚠ **作废**：%s" % old)
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
