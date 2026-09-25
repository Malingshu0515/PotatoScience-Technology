# -*- coding: utf-8 -*-
r"""_zf90_preserve_ebf.py —— 把 `电力高炉.原名件` 从**资源目录**挪到 `build/用户素材/`（§4.24 的正解）

为什么：本轮新加的那条「成品里 assets/ 与 data/ 的条目名必须全是 `[a-z0-9/._-]`」当场抓到
`assets/potato_s_t/textures/block/电力高炉.原名件` —— ZF79 把用户原图改名后**留在了资源目录里**，
于是它从 ZF79 起一直被打进 jar：既是一条**非 ASCII 路径**，又是 18 KB 的死文件。

做法（§4.24 的原意就是"原件放 `build/用户素材/`、资源目录里不留中文名"）：
  ① 逐字节抄到 `build/用户素材/electric_blast_furnace_original.png` 并核 sha1；
  ② 在 `_来源凭据.json` 里记一条（含**原名** `电力高炉.png`、sha1、字节数、说明）；
  ③ 删掉资源目录里那份 `.原名件`；
  ④ 断言：`src\main\resources` 下再没有任何非 ASCII 文件名。
"""
import hashlib
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BLK = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block")
SRC = os.path.join(BLK, u"电力高炉.原名件")
LIVE = os.path.join(BLK, "electric_blast_furnace.png")
USERART = os.path.join(ROOT, "build", u"用户素材")
KEEP = os.path.join(USERART, "electric_blast_furnace_original.png")
RES = os.path.join(ROOT, r"src\main\resources")
fails = []


def sha1b(b):
    return hashlib.sha1(b).hexdigest()


def main():
    if not os.path.exists(SRC):
        print(u"  [SKIP] 资源目录里已经没有 %s 了" % os.path.basename(SRC))
    else:
        raw = open(SRC, "rb").read()
        h = sha1b(raw)
        print(u"  %s：%d 字节  sha1 %s…" % (os.path.basename(SRC), len(raw), h[:8]))
        os.makedirs(USERART, exist_ok=True)
        io.open(KEEP, "wb").write(raw)
        if sha1b(open(KEEP, "rb").read()) != h:
            fails.append(u"留档副本与原件哈希不一致")
        else:
            print(u"  [OK]   留档到 build/用户素材/%s（sha1 %s…）" % (os.path.basename(KEEP), h[:8]))
        # 与"现在在用的那张"是否同一份（ZF79 的记录说改名前后逐字节相同）
        same_as_live = os.path.exists(LIVE) and open(LIVE, "rb").read() == raw
        print(u"         与在用的 electric_blast_furnace.png 逐字节相同：%s" % (u"是" if same_as_live else u"否"))
        prov_p = os.path.join(USERART, u"_来源凭据.json")
        prov = json.loads(io.open(prov_p, encoding="utf-8").read()) if os.path.exists(prov_p) else {}
        prov[os.path.basename(KEEP)] = {
            "原名": u"电力高炉.png",
            "sha1": h, "bytes": len(raw),
            "说明": (u"用户 ZF79 放进 textures/block 的 256×256 电力高炉原图。ZF79 当时按 §4.24 改名成 "
                     u"electric_blast_furnace.png，但把原件以 `电力高炉.原名件` **留在了资源目录里** ⇒ 从那时起"
                     u"一直被打进 jar（非 ASCII 路径 + 18 KB 死文件）。ZF90 挪到这里，资源目录里不再有它；"
                     u"与在用贴图逐字节相同 = %s") % (u"是" if same_as_live else u"否")}
        io.open(prov_p, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(prov, indent=2, ensure_ascii=False) + u"\n")
        print(u"  [OK]   来源凭据里记了一条（原名 电力高炉.png）")
        os.remove(SRC)
        print(u"  [OK]   已从资源目录删除 %s" % os.path.basename(SRC))

    left = []
    for dp, dn, fn in os.walk(RES):
        for n in fn:
            if any(ord(c) > 127 for c in n):
                left.append(os.path.relpath(os.path.join(dp, n), ROOT))
    if left:
        fails.append(u"src\\main\\resources 下还有非 ASCII 文件名：%s" % left)
    else:
        print(u"  [OK]   src\\main\\resources 下已无任何非 ASCII 文件名")
    check = os.path.join(USERART, os.path.basename(KEEP))
    print(u"  [OK]   留档存在：%s（%s…）" % (os.path.exists(check), sha1b(open(check, "rb").read())[:8]
                                            if os.path.exists(check) else u"无"))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
