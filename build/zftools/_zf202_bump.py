# -*- coding: utf-8 -*-
u"""_zf202_bump.py —— 1.21.1 NeoForge 版本线 **0.15 → 0.16**（照 ZF198 先例，只碰白名单）。

三段：
  python build\\zftools\\_zf202_bump.py --backup --write   # §10 改前备份根 zf202_pre
  python build\\zftools\\_zf202_bump.py --phase1 --write   # gradle.properties + 活体门/脚本换到 0.16
  （然后 python build\\zftools\\_zf202_repack.py 打 release\\PotatoST-0.16.jar）
  python build\\zftools\\_zf202_bump.py --phase2 --write   # 档案/公告/交接 + §4.159 靶子

只碰**当前成品**的路径与版本常量；历史轮次脚本（含 `_zf198_bump/repack/falsify.py`）与档案/公告里的
历史字样**一律不动**。`_zf198_verify.py` 例外：它是**常驻门**，跟 `_zf73/_zf78/_zf79` 一样每轮跟平。
"""
import hashlib
import io
import json
import os
import re
import shutil
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

NEW = r"E:\PotatoST\PotatoSTneoforge1.21.1"
ZT = os.path.join(NEW, "build", "zftools")
PROPS = os.path.join(NEW, "gradle.properties")
DOC = os.path.join(NEW, "docs", u"开发档案.md")
HAND = os.path.join(NEW, "docs", u"多会话协作交接.md")
ANN = os.path.join(NEW, "docs", "UpdateAnnouncement_EN.md")
V149 = os.path.join(ZT, u"_zf149_verify.py")
JAR16 = os.path.join(NEW, "release", u"PotatoST-0.16.jar")
JAR15 = os.path.join(NEW, "release", u"PotatoST-0.15.jar")
DEST = os.path.join(ZT, "zf202_pre")

LIVE = [u"_zf73_verify.py", u"_zf78_verify.py", u"_zf79_verify.py",
        u"_zf149_jar.py", u"_zf149_verify.py", u"_zf155_jarcheck.py", u"_zf156_jarcheck.py",
        u"_zf162_pkg.py", u"_zf166_repack.py", u"_zf180_docs.py",
        u"_zf186_verify.py", u"_zf188_verify.py", u"_zf190_verify.py", u"_zf192_verify.py",
        u"_zf194_verify.py", u"_zf196_verify.py", u"_zf196_repack.py",
        u"_zf198_verify.py"]

PAIRS = [
    (u"PotatoST-0.15.jar", u"PotatoST-0.16.jar"),
    (u"potato_s_t-0.15.jar", u"potato_s_t-0.16.jar"),
    (u"mod_version=0.15", u"mod_version=0.16"),
    (u"mod_version=0\\.15", u"mod_version=0\\.16"),
    (u"mod_version = 0.15", u"mod_version = 0.16"),
    (u"mod_version 现在是 0.15（ZF198 抬的版本线）", u"mod_version 现在是 0.16（ZF202 抬的版本线）"),
    (u'u"mod_version=0.15"', u'u"mod_version=0.16"'),
    (u'"mod_version=0.15" in props', u'"mod_version=0.16" in props'),
    (u'm.group(1) == u"0.15"', u'm.group(1) == u"0.16"'),
    (u'version="0.15"', u'version="0.16"'),
    (u"## Version 0.15", u"## Version 0.16"),
    # `_zf198_verify.py`（常驻门）的"上一版原样留盘"判据：从 0.14 跟到 0.15
    (u"PotatoST-0.14.jar", u"PotatoST-0.15.jar"),
    (u"3baf857e0cfc02a7af26f32ebc4447363f4c56bb", u"78b469cb671413b99b7d64aaa8998cc26f3167bb"),
    (u"C3 0.14 那份", u"C3 0.15 那份"),
    (u"0.14 那份原样留盘", u"0.15 那份原样留盘"),
]


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def files():
    return [PROPS] + [os.path.join(ZT, n) for n in LIVE] + [DOC, HAND, ANN]


def backup(write):
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    os.makedirs(DEST)
    man, fails = [], []
    for p in files():
        rel = os.path.relpath(p, NEW)
        dst = os.path.join(DEST, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(p, dst)
        ok = sha(p) == sha(dst) and os.path.getsize(p) == os.path.getsize(dst)
        man.append(u"%s  %d  %s  %s" % (sha(p), os.path.getsize(p), u"OK" if ok else u"**不符**", rel))
        if not ok:
            fails.append(rel)
    if write:
        io.open(os.path.join(DEST, "MANIFEST.txt"), "w", encoding="utf-8", newline=u"\n").write(
            u"\n".join(man) + u"\n")
    print(u"备份根 %s：%d 份，失败 %d" % (DEST, len(man), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


def apply_pairs(text):
    """逐行套 PAIRS；⚠ **`OLD_JAR` 那一行必须跳过** —— 它是"上一版原样留盘"的判据，
    本来就该指向上一版（0.15），不能被 0.15→0.16 的替换波击（第一版没跳，重跑会把判据改坏）。"""
    out, n = [], 0
    for line in text.split(u"\n"):
        if u"OLD_JAR" in line:
            out.append(line)
            continue
        for a, b in PAIRS:
            c = line.count(a)
            if c:
                line = line.replace(a, b)
                n += c
        out.append(line)
    return u"\n".join(out), n


def phase1(write):
    fails, changed, total = [], 0, 0
    for p in files():
        if p in (DOC, HAND, ANN):
            continue
        text = read(p)
        before = text
        text, n = apply_pairs(text)
        if text != before:
            changed += 1
            total += n
            print(u"  %-22s %d 处" % (os.path.basename(p), n))
            if write:
                io.open(p, "w", encoding="utf-8", newline=u"").write(text)
    props = read(PROPS)
    cnt = len(re.findall(u"mod_version", props))
    m = re.search(u"mod_version=(\\S+)", props)
    print(u"  校验：mod_version 出现 %d 次（应 1），值 = %s" % (cnt, m.group(1) if m else u"-"))
    if cnt != 1 or not m or m.group(1) != u"0.16":
        fails.append(u"gradle.properties 没抬到 0.16")
    # 当前成品路径：不许再有 0.15 的活体引用（历史备份路径 `zfNNN_pre` 例外）
    left = []
    for n in LIVE:
        t = read(os.path.join(ZT, n))
        for mm in re.finditer(u"PotatoST-0\\.15\\.jar", t):
            line_start = t.rfind(u"\n", 0, mm.start()) + 1
            line = t[line_start:t.find(u"\n", mm.end()) if t.find(u"\n", mm.end()) > 0 else len(t)]
            if u"OLD_JAR" in line:
                continue          # "上一版原样留盘"的判据：本来就该是 0.15
            left.append(n)
            break
    print(u"  活体里还指向 0.15 的文件：%s" % (sorted(set(left)) or u"无"))
    if left:
        fails.append(u"还有活体引用 0.15：%s" % sorted(set(left)))
    print(u"阶段一：动过 %d 份 / %d 处，失败 %d" % (changed, total, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


def phase2(write):
    fails = []
    if not os.path.isfile(JAR16):
        print(u"!! 成品不在：%s（先跑 _zf202_repack.py）" % JAR16)
        return 1
    size, h = os.path.getsize(JAR16), sha(JAR16)
    z = zipfile.ZipFile(JAR16)
    names = z.namelist()
    cls = len([n for n in names if n.endswith(u".class")])
    recipes = len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")])
    adv = len([n for n in names if n.startswith(u"data/potato_s_t/advancement/") and n.endswith(u".json")])
    toml = z.read(u"META-INF/neoforge.mods.toml").decode("utf-8")
    z.close()
    ver = re.search(u'^version="([^"]+)"', toml, re.M)
    print(u"成品 PotatoST-0.16.jar：%d 字节 / sha1 %s / class %d / 配方 %d / 进度 %d / mods.toml version=%s"
          % (size, h, cls, recipes, adv, ver.group(1) if ver else u"-"))

    # §4.159 靶子
    v149 = read(V149)
    n149 = re.sub(u'WANT_SHA = u?"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, v149, count=1)
    n149 = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, n149, count=1)
    if n149 != v149:
        print(u"  `_zf149_verify.py`：靶子换到 0.16")
        if write:
            io.open(V149, "w", encoding="utf-8", newline=u"").write(n149)
    elif (u'WANT_SHA = u"%s"' % h) in v149:
        print(u"  `_zf149_verify.py`：靶子已经就是这份成品")
    else:
        fails.append(u"_zf149_verify.py：靶子没换到")

    # 档案 §5 加 ZF202 行（插在 ZF200 行之后）
    doc = read(DOC)
    if u"| ZF202 |" not in doc:
        lines = doc.split(u"\n")
        idx = [i for i, l in enumerate(lines) if l.startswith(u"| ZF200 |")]
        if len(idx) != 1:
            fails.append(u"档案 ZF200 行锚点 %d 个" % len(idx))
        else:
            old15 = u""
            if os.path.isfile(JAR15):
                old15 = u"`release\\PotatoST-0.15.jar` = `%s`（%s B）原样留在盘上作历史；" % (
                    sha(JAR15), u"{:,}".format(os.path.getsize(JAR15)))
            row = (u"| ZF202 | **新建 `zf202_pre`**（改前件：`gradle.properties` + 18 份活体门/脚本 + 3 份文档；"
                   u"逐份核 sha1 + 回读，失败 0。⚠ 轮号 `_zf202_*` 开工前查过没人占（§4.147）） | "
                   u"**1.21.1 NeoForge 版本线 0.15 → 0.16 并重打**（用户原话：「先打包1.21.1neo的jar文件 0.16版本」；"
                   u"1.20.1 那条线本轮不碰）。① `gradle.properties` 的 `mod_version=0.15` → **0.16**"
                   u"（全工程唯一一处；改完校验只出现一次）。② 活体门/脚本（18 份）里的当前成品路径与版本常量跟到 0.16；"
                   u"`_zf198_verify.py` 作为**常驻门**跟平（连同它「上一版原样留盘」的判据：0.14 → 0.15）。"
                   u"③ ⚠ 历史轮次脚本（`_zf198_bump/repack/falsify.py`）与档案/公告里的历史字样**一个字没动**。"
                   u"④ **重打**：`release\\PotatoST-0.16.jar` = **{size} 字节 / sha1 `{sha}`**"
                   u"（jar 内 `version=\"0.16\"`、class {cls}、配方 {rec}、进度 {adv}、零探针类、语言键 698 / lzh 700）；"
                   u"{old15}依赖清单与改前**除版本号那一行外逐字节相同**。 | 见 §9 ｜ 见 §4.150 |"
                   ).format(size=u"{:,}".format(size), sha=h, cls=cls, rec=recipes, adv=adv, old15=old15)
            lines[idx[0]:idx[0] + 1] = [lines[idx[0]], row]
            doc = u"\n".join(lines)
            if write:
                io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)
            print(u"  档案 §5 已加 ZF202 行")

    # 交接 §1 成品行 + 第 53 条
    hand = read(HAND)
    m = re.search(u"(?m)^\\| \\*\\*已发布成品\\*\\* \\|.*$", hand)
    if not m:
        fails.append(u"交接 §1「已发布成品」行找不到")
    else:
        newline = (u"| **已发布成品** | `release\\PotatoST-0.16.jar` = `%s`（%s B，"
                   u"**最新一次重打**：版本线 **ZF202 抬到 0.16**；上一版 `release\\PotatoST-0.15.jar` = "
                   u"`78b469cb671413b99b7d64aaa8998cc26f3167bb` 留在盘上作历史） |"
                   % (h, u"{:,}".format(size)))
        hand = hand.replace(m.group(0), newline, 1)
        print(u"  交接 §1 成品行已换")
    if u"53. **ZF202 的账" not in hand:
        anchor = u"## 7. ZF146 这一轮的交接"
        if hand.count(anchor) != 1:
            fails.append(u"交接 §7 锚点 %d 次" % hand.count(anchor))
        else:
            item = (u"53. **ZF202 的账（1.21.1 NeoForge 0.15 → 0.16 打包）**：① 用户原话：「先打包1.21.1neo的jar文件 "
                    u"0.16版本」+「1.20的暂时不用你管」⇒ 只碰 `PotatoSTneoforge1.21.1` 这棵树。"
                    u"② `mod_version=0.16`（唯一一处）；18 份活体门/脚本的当前成品路径与版本常量跟平；"
                    u"`_zf198_verify.py`（常驻门）一起跟平。③ 历史脚本与档案/公告历史字样没动。"
                    u"④ `release\\PotatoST-0.16.jar` 重打，`0.15` 那份留在盘上作历史。"
                    u"⑤ ⚠ 这棵树里另有一条线（ZF201 钢制工具属性）的两个提交没推 —— 本轮推的时候会一起上去。\n")
            hand = hand.replace(anchor, item + u"\n" + anchor, 1)
            if write:
                io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)
            print(u"  交接第 53 条已写")

    # 英文公告：加 "## Version 0.16"
    ann = read(ANN)
    if u"## Version 0.16" not in ann:
        anchor = u"## Version 0.15"
        if ann.count(anchor) != 1:
            fails.append(u"公告 Version 0.15 段锚点 %d 次" % ann.count(anchor))
        else:
            block = (u"## Version 0.16\n\n"
                     u"- The mod version is now **0.16**; the jar is `release/PotatoST-0.16.jar`.\n"
                     u"- Includes the steel-tool tuning from this line (steel axe = gold mining speed, "
                     u"steel pickaxe = diamond mining tier, steel sword comes with Sharpness II + Sweeping "
                     u"Edge III) plus everything from the 0.14/0.15 lines.\n"
                     u"- Dependencies unchanged, translation keys unchanged (698 / lzh 700), "
                     u"{cls} classes / {rec} recipes / {adv} advancements.\n"
                     u"- **Download:** `release/PotatoST-0.16.jar` - **{size} bytes**, sha1 **`{sha}`**.\n\n"
                     ).format(cls=cls, rec=recipes, adv=adv, size=u"{:,}".format(size), sha=h)
            ann = ann.replace(anchor, block + anchor, 1)
            if write:
                io.open(ANN, "w", encoding="utf-8", newline=u"").write(ann)
            print(u"  英文公告已加「## Version 0.16」")

    print(u"阶段二：失败 %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


def main(argv):
    write = u"--write" in argv
    if u"--backup" in argv:
        return backup(write)
    if u"--phase1" in argv:
        return phase1(write)
    if u"--phase2" in argv:
        return phase2(write)
    print(u"用法：--backup | --phase1 | --phase2 [--write]")
    return 2


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
