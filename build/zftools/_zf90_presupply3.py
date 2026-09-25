# -*- coding: utf-8 -*-
u"""_zf90_presupply3.py —— 给 zf90_pre 补第三批改前件（§10；用户又丢了汽油桶）

`汽油桶.png`（3266 B，16×16 RGBA）落在 **23:16:52**，比第二批补账（23:19 之前）晚，
要动的是 `gasoline_bucket.json`（现在借原版水桶）与那两处活体数字（6 → 5）。
先把它和模型抄进快照。
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
BK = r"C:\PotatoST救援\zf90_pre"
FILES = [
    r"src\main\resources\assets\potato_s_t\models\item\gasoline_bucket.json",
    r"src\main\resources\assets\potato_s_t\textures\item\汽油桶.png",
]
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    lines = [u"zf90_pre 补账（第三批，§10）", u"",
             u"用户又放了汽油桶的图（`汽油桶.png`，落盘 23:16:52）⇒ 动 `gasoline_bucket.json`",
             u"与英文公告 / `_zf71_verify.py` 里那句活体数字（借原版贴图 6 → 5）之前，先抄一份。", u""]
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
            print(u"  [OK]   %s  %s…（%d 字节）" % (rel, after[:8], os.path.getsize(dst)))
    io.open(os.path.join(BK, u"_补说明3.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"补账 %d 份 → %s\\_补说明3.txt" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
