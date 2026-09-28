# -*- coding: utf-8 -*-
u"""_zf153_publish.py —— ZF153 打包发布（本工程是"同版本原地重打"，必须公布作废的旧 SHA1）

四道闸，**一道不过就不拷**（`shutil.copy2` 一律写在 `if fails` **之后** ——
ZF63 那个「先拷后报错」的坑，ToolLint 的 ⑧ 一直在盯）：

  ① **重打**：`gradlew build --offline --no-build-cache`（不许用现成的旧产物）
  ② **产物内容**：`VibraniumSwordItem.class` 在、贴图/模型/语言那几份在、
     **探针 class 不许在**（`Zf153Check`）、旧 SHA1 与自己都打出来
  ③ **不许过期**：jar 的 mtime 必须**晚于**它包含的那些源文件（本轮踩过一次：
     falsify 还原源码之后 jar 变旧，门当场红）
  ④ **发布**：`build/libs/potato_s_t-0.12.jar` → `release/PotatoST-0.12.jar` + `.sha1`，
     并**公布作废的旧 SHA1**（本工程同版本原地重打，不公布就等于让人拿旧的）

跑法：python build\\zftools\\_zf153_publish.py
"""
import hashlib
import io
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
LIBS = os.path.join(ROOT, r"build\libs\potato_s_t-0.12.jar")
REL = os.path.join(ROOT, r"release\PotatoST-0.12.jar")
SHA = os.path.join(ROOT, r"release\PotatoST-0.12.jar.sha1")

WANT_IN = [
    u"com/potatost/mod/VibraniumSwordItem.class",
    u"assets/potato_s_t/textures/item/vibranium_sword.png",
    u"assets/potato_s_t/models/item/vibranium_sword.json",
    u"assets/potato_s_t/lang/zh_cn.json",
    u"assets/potato_s_t/lang/lzh.json",
]
FORBID_IN = [u"Zf153Check", u"Zf151Check", u"Zf152Check", u"Zf146Check"]


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    fails = []
    old = io.open(SHA, encoding="utf-8").read().strip() if os.path.exists(SHA) else u"（没有 .sha1）"
    print(u"发布前 release\\PotatoST-0.12.jar 的 sha1 = %s" % old)

    print(u"\n① 重打（gradlew build --offline --no-build-cache）")
    env = dict(os.environ, GRADLE_USER_HOME=r"E:\gradle-home")
    r = subprocess.run([os.path.join(ROOT, "gradlew.bat"), "build", "--offline", "--no-build-cache"],
                       cwd=ROOT, capture_output=True, env=env)
    out = (r.stdout + r.stderr).decode("utf-8", "replace")
    ok_build = r.returncode == 0 and u"BUILD SUCCESSFUL" in out
    print(u"   exit=%d  %s" % (r.returncode,
                               u"BUILD SUCCESSFUL" if ok_build else u"**BUILD 失败**"))
    if not ok_build:
        fails.append(u"重打失败")
        for l in [x for x in out.split(u"\n") if u"错误" in x or u"error:" in x][:6]:
            print(u"   " + l.strip()[:170])
    if not os.path.exists(LIBS):
        fails.append(u"没有产物 %s" % LIBS)
        print(u"失败项 = %d" % len(fails))
        return 1

    print(u"\n② 产物内容")
    with zipfile.ZipFile(LIBS) as zf:
        names = zf.namelist()
        for w in WANT_IN:
            hit = w in names
            print(u"   [%s] %s" % (u"OK" if hit else u"!!", w))
            if not hit:
                fails.append(u"产物里没有 %s" % w)
        bad = [n for n in names if any(f in n for f in FORBID_IN)]
        print(u"   [%s] 探针 class 不在产物里（%d 条命中）" % (u"OK" if not bad else u"!!", len(bad)))
        if bad:
            fails.append(u"产物里有探针：%s" % bad[:3])
        # 语言键那份要在产物里也是 587/589（防止打包时资源没跟新）
        import json
        for code, want in ((u"zh_cn", 587), (u"lzh", 589)):
            d = json.loads(zf.read(u"assets/potato_s_t/lang/%s.json" % code).decode("utf-8"))
            hit = len(d) == want and u"item.potato_s_t.vibranium_sword" in d
            print(u"   [%s] 产物里 %s.json：%d 键、振金剑那个键在"
                  % (u"OK" if hit else u"!!", code, len(d)))
            if not hit:
                fails.append(u"产物里 %s.json 键数 %d（要 %d）或没有振金剑的键" % (code, len(d), want))

    print(u"\n③ 过期检查（jar 要比它包进去的源文件新）")
    jar_m = os.path.getmtime(LIBS)
    newer = []
    for rel in (r"src\main\java\com\potatost\mod\VibraniumSwordItem.java",
                r"src\main\java\com\potatost\mod\ModTiers.java",
                r"src\main\java\com\potatost\mod\ModItems.java",
                r"src\main\java\com\potatost\mod\PotatoST.java",
                r"src\main\resources\assets\potato_s_t\textures\item\vibranium_sword.png",
                r"src\main\resources\assets\potato_s_t\lang\zh_cn.json"):
        p = os.path.join(ROOT, rel)
        if os.path.exists(p) and os.path.getmtime(p) > jar_m:
            newer.append(rel)
    print(u"   [%s] 没有源文件比 jar 新（%d 个）" % (u"OK" if not newer else u"!!", len(newer)))
    if newer:
        fails.append(u"这些源文件比 jar 新：%s" % newer)
        for rel in newer:
            print(u"       %s" % rel)

    print(u"\n④ 发布")
    if fails:
        print(u"   **有失败项 ⇒ 不拷**（`shutil.copy2` 在 if fails 之后，ZF63 的坑）")
    else:
        shutil.copy2(LIBS, REL)
        new = sha1(REL)
        io.open(SHA, "w", encoding="utf-8", newline=u"\n").write(new)
        back = io.open(SHA, encoding="utf-8").read().strip()
        same = sha1(REL) == new and back == new
        print(u"   [%s] release\\PotatoST-0.12.jar = %d 字节" % (u"OK" if same else u"!!",
                                                                os.path.getsize(REL)))
        print(u"   [%s] 新 sha1 = %s" % (u"OK" if same else u"!!", new))
        print(u"   ⚠ **作废**：%s" % old)
        if not same:
            fails.append(u"发布后校验不一致")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    if not fails:
        print(u"\n下一步：_zf153_docs.py 里那份公告/文档要写上新的 sha1 与作废的旧 sha1")
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
