# -*- coding: utf-8 -*-
u"""_zf149_falsify.py —— ZF149 反证刀（静态，**不开游戏**）：成品那几项判据必须真咬人。

每把刀：改一处 ⇒ `_zf149_verify.py` 必须变红（**指定那一行**打 [FAIL]）⇒ **逐字节还原** ⇒ 必须回绿。
⚠ 刀只会改**小文件**（`.sha1` / 文档 / 公告）；成品 jar 那一把用"临时替换成 0.11 那份"来实现
（改完立刻换回来，且用 sha1 自证）。

跑法：python build\\zftools\\_zf149_falsify.py
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
V = os.path.join(ZT, u"_zf149_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.12.jar")
SHA = JAR + u".sha1"
JAR11 = os.path.join(ROOT, "release", u"PotatoST-0.11.jar")
DOC = os.path.join(ROOT, "docs", "开发档案.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")

KNIVES = [
    (u"K1 把成品换成 0.11 那一份（= 发布走样）", u"__JAR__", None, None, u"A2 成品 sha1"),
    (u"K2 .sha1 写错一个字符", SHA, u"59894a9e", u"59894a9f", u"A4 .sha1 记录"),
    (u"K3 档案里的新哈希抹掉", DOC, u"59894a9efb7ba45cc811a558f1fea4a8dac56863", u"59894a9e（省略）",
     u"C1 档案里有新哈希"),
    (u"K4 公告 Download 段的类数/配方数改回旧值", ANN, u"**358 classes, 43 advancements, 74 recipes**",
     u"**357 classes, 43 advancements, 73 recipes**", u"C7 公告 Download 段"),
    (u"K5 交接 §1 的成品行换回旧哈希", HAND, u"59894a9efb7ba45cc811a558f1fea4a8dac56863",
     u"45c061dfc9c171aeea783b64c05ca0e3d884871b", u"C2 交接里有新哈希"),
    (u"K6 把成品 jar 里的书定义抠掉（= 用户遇到的那件事）", u"__NOBOOK__", None, None,
     u"B8 成品里有书定义"),
]

fails, rows = [], []


def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def run_gate():
    r = subprocess.run([sys.executable, V], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=600)
    return r.returncode, r.stdout.decode(u"utf-8", "replace")


def rewrite_jar_toml():
    """把成品 jar 里的 mods.toml 改成 optional（其余条目原样复制）。"""
    import zipfile
    tmp = JAR + u".tmp"
    with zipfile.ZipFile(JAR) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == u"META-INF/neoforge.mods.toml":
                data = data.replace(b'modId="patchouli"\ntype="required"',
                                    b'modId="patchouli"\ntype="optional"')
            zout.writestr(item, data)
    return tmp


def rewrite_jar_nobook():
    """把成品 jar 里的**书定义**抠掉（其余条目原样）—— 复现用户遇到的『jar 里没有书』。"""
    import zipfile
    tmp = JAR + u".tmp"
    with zipfile.ZipFile(JAR) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == u"data/potato_s_t/patchouli_books/guide/book.json":
                continue
            zout.writestr(item, zin.read(item.filename))
    return tmp


def main():
    for label, target, old, new, marker in KNIVES:
        original = None
        if target == u"__JAR__":
            original = open(JAR, "rb").read()
            h0 = hashlib.sha1(original).hexdigest()
            shutil.copy2(JAR11, JAR)
        elif target == u"__TOML__":
            original = open(JAR, "rb").read()
            h0 = hashlib.sha1(original).hexdigest()
            tmp = rewrite_jar_toml()
            shutil.move(tmp, JAR)
        elif target == u"__NOBOOK__":
            original = open(JAR, "rb").read()
            h0 = hashlib.sha1(original).hexdigest()
            tmp = rewrite_jar_nobook()
            shutil.move(tmp, JAR)
        else:
            original = open(target, "rb").read()
            h0 = hashlib.sha1(original).hexdigest()
            text = io.open(target, encoding=u"utf-8", newline=u"").read()
            if text.count(old) != 1:
                fails.append(u"%s：改前串命中 %d 次" % (label, text.count(old)))
                open(target, "wb").write(original)
                continue
            io.open(target, u"w", encoding=u"utf-8", newline=u"").write(text.replace(old, new, 1))

        rc, out = run_gate()
        hit = any(marker in l and u"[FAIL]" in l for l in out.split(u"\n"))
        red = (rc != 0) and hit

        # 还原
        if target in (u"__JAR__", u"__TOML__", u"__NOBOOK__"):
            open(JAR, "wb").write(original)
        else:
            open(target, "wb").write(original)
        restored = sha1(JAR if target in (u"__JAR__", u"__TOML__", u"__NOBOOK__") else target) == h0
        rc2, out2 = run_gate()
        green = rc2 == 0

        rows.append((label, red, restored, green))
        if not red:
            fails.append(u"%s：改坏后**没红**（rc=%d，命中=%s）" % (label, rc, hit))
        if not restored:
            fails.append(u"%s：还原后不是逐字节相同" % label)
        if not green:
            fails.append(u"%s：还原后没回绿" % label)

    print(u"================ ZF149 反证刀（%d 把） ================" % len(KNIVES))
    print(u"%-54s %-6s %-8s %-8s" % (u"刀", u"变红", u"逐字节还原", u"回绿"))
    for label, a, b, c in rows:
        print(u"%-54s %-6s %-8s %-8s" % (label[:52], u"OK" if a else u"!!", u"OK" if b else u"!!",
                                         u"OK" if c else u"!!"))
    print(u"")
    ok = len([r for r in rows if r[1] and r[2] and r[3]])
    print(u"刀数 = %d   全中 = %d   失败 = %d" % (len(KNIVES), ok, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
