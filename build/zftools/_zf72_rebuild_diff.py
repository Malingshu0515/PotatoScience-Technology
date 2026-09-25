# -*- coding: utf-8 -*-
u"""_zf72_rebuild_diff.py —— 「重打包 vs 成品」逐条目对账

为什么要做：本轮的反证第 4/5 刀**动过两个源文件**（`TankContents.java`、`FluidPumpBlockEntity.java`），
虽然脚本自己核过「还原后 SHA1 与改前逐字节相同」，但那只是"脚本自己说的"。
最硬的证据是**重新打包一遍**，把新 jar 与已发布的成品逐条目比对。

同时这一次对账顺手会暴露一件真事：成品 jar 里还留着
`assets/potato_s_t/textures/block/lv_001.png`（用户 2026-09-22 14:13 删掉的那张孤儿贴图）
⇒ 重打包**不再**与成品逐字节相同。本脚本把差异**限定成可解释清单**：
除了这张图，其余条目必须逐条 CRC 相同，否则报警（说明源码树被本不该动的东西动过）。
"""
import hashlib
import io
import os
import sys
import zipfile

PROJ = r"E:\PotatoST"
RELEASE = os.path.join(PROJ, u"release", u"PotatoST-0.10.jar")
# 注意：打包任务产出的文件名是 `potato_s_t-0.10.jar`（archivesBaseName 是小写 mod id），
# `release\PotatoST-0.10.jar` 是发布时**改名**的副本 —— 改名不改字节，所以两边可以逐字节比。
BUILT = os.path.join(PROJ, u"build", u"libs", u"potato_s_t-0.10.jar")
# 已知且可解释的差异（只允许「成品里有、新 jar 里没有」这一种方向）
ALLOWED_ONLY_IN_RELEASE = {u"assets/potato_s_t/textures/block/lv_001.png"}


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def entries(path):
    out = {}
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            out[info.filename] = (info.CRC, info.file_size)
    return out


def main():
    if not os.path.isfile(RELEASE) or not os.path.isfile(BUILT):
        print(u"缺 jar：release=%s  built=%s" % (os.path.isfile(RELEASE), os.path.isfile(BUILT)))
        return 1
    a_sha, b_sha = sha1(RELEASE), sha1(BUILT)
    print(u"成品 release\\PotatoST-0.10.jar : %s  %d B" % (a_sha, os.path.getsize(RELEASE)))
    print(u"新打 build\\libs\\%s: %s  %d B" % (os.path.basename(BUILT), b_sha, os.path.getsize(BUILT)))
    print(u"整包 SHA1 相同 = %s" % (a_sha == b_sha))

    a, b = entries(RELEASE), entries(BUILT)
    print(u"条目数：成品 %d / 新打 %d" % (len(a), len(b)))

    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    diff = sorted(k for k in (set(a) & set(b)) if a[k] != b[k])

    print(u"\n只在成品里有的条目（%d）：" % len(only_a))
    for k in only_a:
        print(u"  - %s  (%d B)" % (k, a[k][1]))
    print(u"只在新 jar 里有的条目（%d）：" % len(only_b))
    for k in only_b:
        print(u"  + %s  (%d B)" % (k, b[k][1]))
    print(u"两边都有但内容不同（%d）：" % len(diff))
    for k in diff:
        print(u"  ! %s  成品 CRC=%s 新 jar CRC=%s" % (k, a[k][0], b[k][0]))

    fails = []
    unexpected = [k for k in only_a if k not in ALLOWED_ONLY_IN_RELEASE]
    if unexpected:
        fails.append(u"成品里有 %d 个条目在新 jar 里不见了、且不在已知清单里：%s"
                     % (len(unexpected), u", ".join(unexpected[:5])))
    if only_b:
        fails.append(u"新 jar 里多出 %d 个条目（源码树里多了东西？）: %s"
                     % (len(only_b), u", ".join(only_b[:5])))
    if diff:
        fails.append(u"%d 个同名条目内容不同 —— 源码树与成品已经不一致" % len(diff))

    print(u"\n结论：")
    if not fails:
        print(u"  [OK] 除已知差异（%s）外，%d 个同名条目**逐条 CRC 相同** ⇒"
              % (u" / ".join(sorted(ALLOWED_ONLY_IN_RELEASE)), len(set(a) & set(b))))
        print(u"       本轮反证动过的那两个源文件**没有留下任何痕迹**，源码树 == 成品。")
    else:
        for f in fails:
            print(u"  !! " + f)
    print(u"\n说明：成品里那张 lv_001.png（%d B）是用户 2026-09-22 14:13 删进回收站的孤儿贴图，"
          u"没人引用、不影响功能；\n      但因此**重打包不再与成品逐字节相同**（成品 SHA1 仍 %s，未作废）。"
          % (a.get(u"assets/potato_s_t/textures/block/lv_001.png", (0, 0))[1], a_sha[:12]))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
