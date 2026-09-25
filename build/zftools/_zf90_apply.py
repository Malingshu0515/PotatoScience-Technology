# -*- coding: utf-8 -*-
u"""_zf90_apply.py —— ZF90 动手那一半（§4.53：不拿 PowerShell 拼脚本，全部走文件）

三步，每步都要断言，任何一条不过就停：
  ① 确认**没有任何模型**还引用 `potato_s_t:item/plate`（四个模型已经改成 iron_plate）；
  ② 确认改前件 `zf90_pre` 里那张 `plate.png` 与盘上**逐字节相同**（删之前先能还原）；
  ③ 删掉 `textures/item/plate.png`（用户 ZF83 起就有的口径：「换一下 然后删除原来的贴图」）。
"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
MODELS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models")
TEXI = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
PLATE = os.path.join(TEXI, "plate.png")
BK_PLATE = os.path.join(r"C:\PotatoST救援\zf90_pre",
                        r"src\main\resources\assets\potato_s_t\textures\item\plate.png")
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    print(u"== ① 还有谁引用 item/plate ==")
    hits = []
    for dp, dn, fn in os.walk(MODELS):
        for f in fn:
            p = os.path.join(dp, f)
            t = io.open(p, encoding="utf-8", errors="replace").read()
            if u"potato_s_t:item/plate\"" in t or u"potato_s_t:item/plate" + u"}" in t \
                    or t.count(u"item/plate") > 0:
                hits.append(os.path.relpath(p, ROOT))
    if hits:
        fails.append(u"还有引用：%s" % hits)
        print(u"  [FAIL] 还有引用：%s" % hits)
    else:
        print(u"  [OK]   没有任何模型再用 item/plate（四个已指向 iron_plate）")

    print(u"\n== ② 改前件里那张 plate.png 与盘上是否逐字节相同 ==")
    if not os.path.exists(BK_PLATE):
        fails.append(u"改前件里没有 plate.png，不敢删")
    elif not os.path.exists(PLATE):
        print(u"  [SKIP] 盘上已经没有了")
    else:
        a, b = sha1(BK_PLATE), sha1(PLATE)
        if a != b:
            fails.append(u"改前件 %s ≠ 盘上 %s" % (a[:8], b[:8]))
        else:
            print(u"  [OK]   两份相同（%s…，%d 字节）—— 删了能还原"
                  % (a[:8], os.path.getsize(PLATE)))

    print(u"\n== ③ 删掉通用 plate.png ==")
    if fails:
        print(u"  [STOP] 上面有 %d 条不过 ⇒ 一个字节都不动" % len(fails))
    elif not os.path.exists(PLATE):
        print(u"  [SKIP] 盘上已经没有了")
    else:
        os.remove(PLATE)
        print(u"  [OK]   已删除 textures/item/plate.png（exists = %s）"
              % os.path.exists(PLATE))
        left = [n for n in os.listdir(TEXI) if u"plate" in n]
        print(u"  现在 textures/item 里的板：%s" % sorted(left))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
