# -*- coding: utf-8 -*-
u"""_zf90_publish.py —— ZF90 出成品（作废 ZF89 那版 `05895f2d…`）+ 把 §9 的占位填实

照老规矩（§5 ZF63 教训）：**先核对旧哈希、再核对新产物内容，全过了才动文件**；
任何一条不过就一个字节都不动。
"""
import hashlib
import io
import os
import shutil
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "build", "libs", "potato_s_t-0.11.jar")
DST = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
SHA = DST + ".sha1"
PUB = os.path.join(ROOT, "build", "zftools", "_zf90_publish.py")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
TEXI = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
VOID = "c625f20c17d5efa7c846d609600f6cdec1d14b71"
# ⚠ §4.59 ④：文档里"**成品** → **当时的成品**"那句重命名，锚点必须用**上一轮**的哈希，
#   不能用自更新的 VOID —— 否则同一轮重跑一次，就把**刚发布的这一版**标成"当时的成品"（ZF90 踩过）。
PREV_ROUND_SHA = "05895f2d72a0f363bf1b311ff231d9c75f313aa4"
FOUR = [u"silver_plate", u"aluminum_plate", u"nickel_plate", u"cobalt_plate"]
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def patch(path, old, new, label, expect=1, optional=False):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != expect:
        if optional and hits == 0:
            print(u"  [SKIP] %s（锚点已不在 = 之前填过了，幂等放行）" % label)
            return
        fails.append(u"%s：锚点命中 %d 次（必须 %d 次）" % (label, hits, expect))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def main():
    old = sha1(DST) if os.path.exists(DST) else u"(缺)"
    if old != VOID:
        fails.append(u"当前成品 %s ≠ 预期要作废的 %s" % (old, VOID))
    if not os.path.exists(SRC):
        fails.append(u"没有构建产物 %s" % SRC)
        new, size, entries = u"(缺)", 0, 0
    else:
        new = sha1(SRC)
        size = os.path.getsize(SRC)
        with zipfile.ZipFile(SRC) as zf:
            names = zf.namelist()
            entries = len(names)
            bad = [n for n in names if "Check" in n.split("/")[-1] and n.endswith(".class")]
            if bad:
                fails.append(u"成品里带探针：%s" % bad)
            # plate.png 必须没了
            if u"assets/potato_s_t/textures/item/plate.png" in names:
                fails.append(u"成品里还带着 plate.png（应当已删）")
            else:
                print(u"  [OK]   成品里没有 plate.png")
            # 四个模型指向 iron_plate
            for nm in FOUR:
                e = u"assets/potato_s_t/models/item/%s.json" % nm
                inside = zf.read(e).decode("utf-8") if e in names else u""
                if u"potato_s_t:item/iron_plate" not in inside:
                    fails.append(u"成品里的 %s.json 没有指向 iron_plate" % nm)
                else:
                    print(u"  [OK]   %s.json → iron_plate" % nm)
            # iron_plate.png 与盘上一致
            ip = u"assets/potato_s_t/textures/item/iron_plate.png"
            if ip not in names or zf.read(ip) != open(os.path.join(TEXI, u"iron_plate.png"), "rb").read():
                fails.append(u"成品里的 iron_plate.png 与盘上不一致")
            else:
                print(u"  [OK]   iron_plate.png 与盘上一致")
        if new == old:
            fails.append(u"新旧哈希相同 ⇒ 源码没变？")

    if fails:
        print(u"  [FAIL] 以上 %d 条没过 ⇒ 一个字节都不动" % len(fails))
        for f in fails:
            print(u"    !! " + f)
        return 1

    shutil.copy2(SRC, DST)
    io.open(SHA, "w", encoding="ascii", newline=u"\n").write(new + u"\n")
    print(u"① 已发布 release\\PotatoST-0.11.jar = %s（%d B / %d 条目）" % (new, size, entries))
    print(u"   作废 %s（ZF89）" % VOID[:8])

    patch(DOC, u"__ZF90_SHA1__", new, u"§9 ZF90 条目：成品哈希填实", expect=1, optional=True)
    patch(DOC, u"__ZF90_BYTES__", str(size), u"§9 ZF90 条目：字节数填实", expect=1, optional=True)
    patch(DOC, u"__ZF90_ENTRIES__", str(entries), u"§9 ZF90 条目：条目数填实", expect=1, optional=True)
    # ⚠ 锚点用**上一轮**的哈希（PREV_ROUND_SHA），不是自更新的 VOID —— 见 §4.59 ④ 与文件头的说明
    patch(DOC, u"**成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"**当时的成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"§9 ZF89 条目：成品 → 当时的成品", expect=1, optional=True)
    patch(PUB, u'VOID = "%s"' % VOID, u'VOID = "%s"' % new, u"发布脚本 VOID 跟到最新")
    print(u"   ⚠ 本轮若重跑：占位补丁命中 0 次是正常的（已经填过）；"
          u"文档与产物的**一致性**由 `_zf90_verify.py` H 段常驻盯着。")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
