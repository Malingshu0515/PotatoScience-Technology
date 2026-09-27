# -*- coding: utf-8 -*-
u"""_zf148_pre.py —— ZF148 动手前备份（§10：第一个字节改动之前先备份）。

清单口径与 ZF145/ZF146 一致：
  · 本轮要改的**源码 / 资源 / 元数据**（改前件）
  · **全部常驻门**（`_zf*_verify.py` + `_zf100_recipe_guard.py`）—— 活体数字要跟平
  · `_zf104_gates.*`（跑全部门的 ps1 / 清单 / 计数脚本）
  · 三份文档（档案 / 交接 / 英文公告）
  · `PotatoST.java`（⚠ 探针挂载点 —— 动手前就写进清单，§6 第 9/14/18 条那三次漏账的教训）
  · 文言文那条线的同步门（`_rzh_*.py`，只要带 verify 语义）

落到 `C:\\PotatoST救援\\zf148_pre\\`，逐份核 sha1 + 回读。
跑法：python build\\zftools\\_zf148_pre.py
"""
import hashlib
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

PROJ = r"E:\PotatoST"
DST = r"C:\PotatoST救援\zf148_pre"
TOOLS = os.path.join(PROJ, "build", "zftools")

# ---- ① 明确点名（源码 / 资源 / 元数据 / 文档 / 门基建） ----
EXPLICIT = [
    r"build.gradle",
    r"src\main\resources\META-INF\neoforge.mods.toml",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"src\main\resources\assets\potato_s_t\lang\lzh.json",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"_zf94_gatecount.py",
]

# ---- ② 目录里按名字捞（门与计数基建） ----
SCAN_DIRS = [(os.path.join(PROJ, "build", "zftools"), None)]


def want(fn):
    if fn.startswith(u"_zf148_"):
        return False          # 本轮自己的侦察脚本，不用备
    if fn.endswith(u"_verify.py") and fn.startswith(u"_zf"):
        return True
    if fn == u"_zf100_recipe_guard.py":
        return True
    if fn.startswith(u"_zf104_gates.") or fn == u"_zf104_gatecount.py":
        return True
    if fn.startswith(u"_rzh_") and fn.endswith(u".py"):
        return True
    return False


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    items = []
    for rel in EXPLICIT:
        items.append(rel)
    for d, _ in SCAN_DIRS:
        for fn in sorted(os.listdir(d)):
            if want(fn):
                items.append(os.path.join(u"build", u"zftools", fn))
    items = sorted(set(items))

    if not os.path.isdir(DST):
        os.makedirs(DST)
    fails = []
    total = 0
    for rel in items:
        src = os.path.join(PROJ, rel)
        if not os.path.isfile(src):
            fails.append(u"改前件不在：%s" % rel)
            continue
        dst = os.path.join(DST, rel)
        d = os.path.dirname(dst)
        if not os.path.isdir(d):
            os.makedirs(d)
        shutil.copy2(src, dst)
        a, b = sha(src), sha(dst)
        if a != b:
            fails.append(u"%s 回读不一致 %s != %s" % (rel, a[:12], b[:12]))
            continue
        total += 1
    print(u"备份根：%s" % DST)
    print(u"备份成功 %d 份" % total)
    print(u"清单：")
    for rel in items:
        print(u"   " + rel)
    print(u"")
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
