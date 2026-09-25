# -*- coding: utf-8 -*-
u"""_zf85_backup.py —— ZF85 **动手前**的改前件（§10；用户诉求：清掉 ModFluids.java 的 25 条 IDE 警告/报错）

预计改动：
  · `ModFluids.java`（5 处弃用的 `initializeClient` 覆盖搬走、`liquidType` 去掉恒为 300 的形参、
    删掉从未使用的 `idOf/byId/GAS_COUNT`、注释里的空行与 "-ise" 拼写）
  · `PotatoSTClient.java`（用 `RegisterClientExtensionsEvent` 注册 8 种流体的客户端贴图；
    顺手去掉已弃用的 `bus =` 参数）
  · `_zf72_verify.py`（B9 那条断言的是"ModFluids.idOf 只认 3 种气体"——该方法本轮删除，要改成新事实）
  · `_zf78_falsify.py`（加刀）与 4 份文档、成品 jar
"""
import hashlib
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf85_pre"
FILES = [
    r"src\main\java\com\potatost\mod\ModFluids.java",
    r"src\main\java\com\potatost\mod\PotatoSTClient.java",
    r"src\main\java\com\potatost\mod\TankContents.java",
    r"build\zftools\_zf72_verify.py",
    r"build\zftools\_zf78_falsify.py",
    r"build\zftools\_zf83_verify.py",
    r"build\zftools\_zf84_verify.py",
    r"docs\开发档案.md",
    r"docs\v0.11规划.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [SKIP] 备份根已存在：%s" % BK)
    lines = []
    ok = 0
    for rel in FILES:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            fails.append(u"缺文件：%s" % rel)
            lines.append(u"MISSING  %s" % rel)
            continue
        dst = os.path.join(BK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        before = sha1(src)
        shutil.copy2(src, dst)
        after = sha1(dst)
        if before != after:
            fails.append(u"%s：拷贝后哈希不一致" % rel)
        else:
            ok += 1
            lines.append(u"%s  %10d  %s" % (after, os.path.getsize(dst), rel))
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
