# -*- coding: utf-8 -*-
"""_zf66_rename.py —— 把用户给的中文贴图名改成 ASCII（§4.24：ResourceLocation 只放行 [a-z0-9/._-]）

改名前后逐份核 SHA1（ZF34 立的做法）：改名只是换文件名，字节不许有任何变化。
"""
import hashlib
import io
import os
import sys

ITEM = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item"

PAIRS = [
    (u"钛合金剑_001.png", u"titanium_alloy_sword.png"),
    (u"钛合金镐_001.png", u"titanium_alloy_pickaxe.png"),
]


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    fails = []
    for old, new in PAIRS:
        src = os.path.join(ITEM, old)
        dst = os.path.join(ITEM, new)
        if not os.path.isfile(src):
            if os.path.isfile(dst):
                print(u"  [SKIP] 已经改过名了: %s" % new)
                continue
            fails.append(u"找不到: %s" % old)
            continue
        before = sha1(src)
        os.replace(src, dst)
        after = sha1(dst)
        ok = before == after
        if not ok:
            fails.append(u"改名后哈希变了: %s" % new)
        print(u"  [%s] %-22s -> %-28s %s" % (u"OK" if ok else u"FAIL", old, new, after[:12]))
    print(u"\n改名 = %d 对   失败项 = %d" % (len(PAIRS), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
