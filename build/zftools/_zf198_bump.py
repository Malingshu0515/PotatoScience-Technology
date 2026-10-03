# -*- coding: utf-8 -*-
u"""_zf198_bump.py —— 版本线 **0.14 → 0.15**（照 ZF181 先例：只碰白名单）。

三个阶段：
  python build\\zftools\\_zf198_bump.py --backup  --write   # §10 改前备份根 zf198_pre
  python build\\zftools\\_zf198_bump.py --phase1  --write   # gradle.properties + 活体门/脚本换名
  （然后 python build\\zftools\\_zf198_repack.py 打 release\\PotatoST-0.15.jar）
  python build\\zftools\\_zf198_bump.py --phase2  --write   # 文档/公告/交接 + §4.159 靶子

要点（与 ZF181 一致）：
- `gradle.properties` 的 `mod_version` 是**全工程唯一一处**版本号；
- **只换"当前成品"的路径**：`os.path.join(ROOT, "release", ...)` 与 `os.path.join(ROOT, "build", "libs", ...)`
  —— 备份里的 `os.path.join(PRE, r"release\\PotatoST-0.14.jar")` 是**历史**，一个字节都不许动；
- **绝不碰**历史轮次的 `_zfNNN_*.py` 与档案/公告里过去那些 `PotatoST-0.14.jar` 字样。
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

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
BIL = os.path.join(ROOT, "docs", u"0.13_0.14更新公告与介绍_中英.md")
V149 = os.path.join(ZT, u"_zf149_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.15.jar")
DEST = os.path.join(ZT, "zf198_pre")

# 白名单：活体门/脚本（脚本名不含历史轮次里那些"当年数字"的持有者）
LIVE = [u"_zf73_verify.py", u"_zf78_verify.py", u"_zf79_verify.py",
        u"_zf149_jar.py", u"_zf149_verify.py", u"_zf155_jarcheck.py", u"_zf156_jarcheck.py",
        u"_zf162_pkg.py", u"_zf166_repack.py", u"_zf180_docs.py",
        u"_zf186_verify.py", u"_zf188_verify.py", u"_zf190_verify.py", u"_zf192_verify.py",
        u"_zf194_verify.py", u"_zf196_verify.py", u"_zf196_repack.py"]

PAIRS = [
    # ① 当前成品的路径（**不碰** PRE 里那些历史备份路径）
    (u'"release", u"PotatoST-0.14.jar"', u'"release", u"PotatoST-0.15.jar"'),
    (u'"release", "PotatoST-0.14.jar"', u'"release", "PotatoST-0.15.jar"'),
    (u'"libs", u"potato_s_t-0.14.jar"', u'"libs", u"potato_s_t-0.15.jar"'),
    (u'release\\\\PotatoST-0.14.jar', u'release\\\\PotatoST-0.15.jar'),
    (u'release/PotatoST-0.14.jar', u'release/PotatoST-0.15.jar'),
    # ② 三份"钉 mod_version"的老门（判据不放宽，还是逐字比常量）
    (u'u"C1 mod_version = 0.14"', u'u"C1 mod_version = 0.15"'),
    (u'r"mod_version=0\\.14"', u'r"mod_version=0\\.15"'),
    (u"mod_version 现在是 0.14（ZF181 抬的版本线）", u"mod_version 现在是 0.15（ZF198 抬的版本线）"),
    (u'u"mod_version=0.14"', u'u"mod_version=0.15"'),
    (u"props is not None and u\"mod_version=0.14\" in props",
     u"props is not None and u\"mod_version=0.15\" in props"),
    # ③ 其它活体里的版本字样
    (u'version="0.14"', u'version="0.15"'),
    (u"版本 0.14", u"版本 0.15"),
    (u"mods.toml 里版本是 0.14", u"mods.toml 里版本是 0.15"),
    # ④ gradle.properties
    (u"mod_version=0.14", u"mod_version=0.15"),
]
PROPS = os.path.join(ROOT, "gradle.properties")


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def backup(write):
    files = [u"gradle.properties"] + [os.path.join("build", "zftools", n) for n in LIVE]
    files += [r"docs\开发档案.md", r"docs\多会话协作交接.md", r"docs\UpdateAnnouncement_EN.md",
              r"docs\0.13_0.14更新公告与介绍_中英.md", r"release\PotatoST-0.15.jar" if False else
              r"release\PotatoST-0.14.jar", r"release\PotatoST-0.14.jar.sha1"]
    files += [os.path.join("src", "main", "resources", "META-INF", "neoforge.mods.toml")]
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    os.makedirs(DEST)
    manifest, fails = [], []
    for rel in files:
        src = os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            fails.append(u"不在盘上：%s" % rel)
            continue
        dst = os.path.join(DEST, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        ok = sha(src) == sha(dst) and os.path.getsize(src) == os.path.getsize(dst)
        manifest.append(u"%s  %d  %s  %s" % (sha(src), os.path.getsize(src), u"OK" if ok else u"**不符**", rel))
        if not ok:
            fails.append(u"回读不符：%s" % rel)
    if write:
        io.open(os.path.join(DEST, "MANIFEST.txt"), "w", encoding="utf-8", newline=u"\n").write(
            u"\n".join(manifest) + u"\n")
    print(u"备份根 %s：%d 份，失败 %d" % (DEST, len(manifest), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


def phase1(write):
    fails, changed = [], 0
    for name in [u"gradle.properties"] + LIVE:
        p = os.path.join(ROOT, name) if name == u"gradle.properties" else os.path.join(ZT, name)
        if not os.path.isfile(p):
            fails.append(u"不在：%s" % name)
            continue
        text = read(p)
        before = text
        for a, b in PAIRS:
            if a in text:
                text = text.replace(a, b)
        n = sum(1 for l1, l2 in zip(before.split(u"\n"), text.split(u"\n")) if l1 != l2)
        if n:
            changed += 1
            print(u"  %-24s 改 %d 行" % (name, n))
        if write and text != before:
            io.open(p, "w", encoding="utf-8", newline=u"").write(text)
    props = read(PROPS)
    cnt = len(re.findall(u"mod_version", props))
    print(u"  校验：gradle.properties 里 mod_version 出现 %d 次（应为 1）、值 = %s"
          % (cnt, re.search(u"mod_version=(\\S+)", props).group(1)))
    if cnt != 1:
        fails.append(u"mod_version 不是唯一一处")
    if u"mod_version=0.15" not in props:
        fails.append(u"gradle.properties 没抬到 0.15")
    # 历史备份路径必须原样留在 0.14（改了就是篡改历史）
    keep = 0
    for name in LIVE:
        t = read(os.path.join(ZT, name))
        keep += len(re.findall(u'release\\\\PotatoST-0\\.14\\.jar', t))
    print(u"  历史备份路径（PRE 里的 0.14）保留 %d 处" % keep)
    print(u"阶段一：动过 %d 份，失败 %d" % (changed, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


def phase2(write):
    fails = []
    if not os.path.isfile(JAR):
        print(u"!! 成品不在：%s（先跑 _zf198_repack.py）" % JAR)
        return 1
    size, h = os.path.getsize(JAR), sha(JAR)
    z = zipfile.ZipFile(JAR)
    names = z.namelist()
    cls = len([n for n in names if n.endswith(u".class")])
    recipes = len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")])
    adv = len([n for n in names if n.startswith(u"data/potato_s_t/advancement/") and n.endswith(u".json")])
    toml = z.read(u"META-INF/neoforge.mods.toml").decode("utf-8")
    z.close()
    print(u"成品 %s：%d 字节 / sha1 %s / class %d / 配方 %d / 进度 %d / mods.toml version=%s"
          % (os.path.basename(JAR), size, h, cls, recipes, adv,
             re.search(u'^version="([^"]+)"', toml, re.M).group(1)))

    # §4.159 靶子
    v149 = read(V149)
    n149 = re.sub(u'WANT_SHA = u?"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, v149, count=1)
    n149 = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, n149, count=1)
    if n149 != v149:
        print(u"  `_zf149_verify.py`：靶子换到 0.15")
        if write:
            io.open(V149, "w", encoding="utf-8", newline=u"").write(n149)
    elif v149 == n149 and (u'WANT_SHA = u"%s"' % h) in v149:
        print(u"  `_zf149_verify.py`：靶子已经就是这份成品，跳过")
    else:
        fails.append(u"_zf149_verify.py：靶子没换到")

    # §5 表格加 ZF198 一行（本轮自己的账；也是六道常驻门 D4「档案里有当前成品哈希」的落点）
    doc = read(DOC)
    if u"| ZF198 |" not in doc:
        anchor = u"（class 410；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.196 |\n"
        if doc.count(anchor) != 1:
            fails.append(u"档案 ZF196 行尾锚点 %d 次" % doc.count(anchor))
        else:
            row = (u"| ZF198 | **新建 `zf198_pre`**（**25 份**改前件：`gradle.properties` + 17 份活体门/脚本 + "
                   u"3 份文档 + 源码 `neoforge.mods.toml` + 旧成品与 `.sha1`；逐份核 sha1 + 回读，失败 0；"
                   u"⚠ 轮号 `_zf198_*` 开工前查过没人占（§4.147）） | **版本线 0.14 → 0.15**"
                   u"（用户原话：「好了！现在打包成0.15jar」；照 ZF181 先例**只碰白名单**）。"
                   u"① `gradle.properties` 的 `mod_version=0.14` → **0.15**（**全工程唯一一处**版本号，"
                   u"改完校验只出现一次；`neoforge.mods.toml` 仍是 `${mod_version}` 占位符，渲染出来 "
                   u"`version=\"0.15\"`）。② 三份**钉 `mod_version`** 的老门跟到 0.15（`_zf73` / `_zf78` / "
                   u"`_zf79_verify.py`），**判据没放宽**（仍是逐字比常量）。③ **只换「当前成品」的路径**"
                   u"（`os.path.join(ROOT, \"release\", …)` 与 `build/libs` 那两处）：六道常驻门 + "
                   u"`_zf149_jar` / `_zf149_verify` / `_zf155_jarcheck` / `_zf156_jarcheck` / `_zf162_pkg` / "
                   u"`_zf166_repack` / `_zf180_docs` / `_zf196_repack` 共 **17 份**；⚠ 备份里 "
                   u"`zfNNN_pre\\release\\PotatoST-0.14.jar` 那处**历史**一个字节没动。④ ⚠ `_zf186_verify.py` "
                   u"的 D3 是拿**渲染后的** mods.toml 跟旧 jar 逐字节比的 ⇒ 抬版本号必然变红，跟平成"
                   u"「除版本号那一行外逐字节相同」（意图没变：依赖段没动）。⑤ **重打**："
                   u"`release\\PotatoST-0.15.jar` = **{size} 字节 / sha1 `{sha}`**（jar 内 `version=\"0.15\"`、"
                   u"class {cls}、零探针类；`release\\PotatoST-0.14.jar` 原样留在盘上作历史）。"
                   u"⑥ §4.159 三处联动跟到新成品（`_zf149_verify.py` 的靶子）。 | 见 §9 ｜ 见 §4.196 |\n")
            row = row.replace(u"{size}", u"{:,}".format(size)).replace(u"{sha}", h).replace(u"{cls}", str(cls))
            doc = doc.replace(anchor, anchor + row, 1)
            if write:
                io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)
            print(u"  档案 §5 已加 ZF198 行")
    else:
        print(u"  档案 §5 已有 ZF198 行，跳过")

    # 交接 §1 的"已发布成品"行（**只动这一行**，其余历史字样一律不碰）
    hand = read(HAND)
    m = re.search(u"(?m)^\\| \\*\\*已发布成品\\*\\* \\|.*$", hand)
    if not m:
        fails.append(u"交接 §1「已发布成品」行找不到")
    else:
        old_line = m.group(0)
        new_line = (u"| **已发布成品** | `release\\PotatoST-0.15.jar` = `%s`（%s B，"
                    u"**最新一次重打**：版本线 **ZF198 抬到 0.15**；上一版 `release\\PotatoST-0.14.jar` = "
                    u"`3baf857e0cfc02a7af26f32ebc4447363f4c56bb` 留在盘上作历史） |"
                    % (h, u"{:,}".format(size)))
        hand = hand.replace(old_line, new_line, 1)
        print(u"  交接 §1 成品行已换（旧行 %d 字符 → 新行 %d 字符）" % (len(old_line), len(new_line)))
        if write:
            io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)

    # 交接新增第 51 条
    hand = read(HAND)
    if u"51. **ZF198 的账" not in hand:
        anchor = u"## 7. ZF146 这一轮的交接"
        if hand.count(anchor) != 1:
            fails.append(u"交接 §7 锚点 %d 次" % hand.count(anchor))
        else:
            item = (u"51. **ZF198 的账（版本线 0.14 → 0.15）**：照 ZF181 先例只碰白名单。① `gradle.properties` 的 "
                    u"`mod_version=0.15`（**全工程唯一一处**；改完校验只出现一次）。② 三份钉 `mod_version` 的老门"
                    u"（`_zf73` / `_zf78` / `_zf79_verify.py`）跟到 0.15，**判据没放宽**（仍是逐字比常量）。"
                    u"③ **只换「当前成品」的路径**（`os.path.join(ROOT, \"release\", …)` 与 `build/libs` 那两处）—— "
                    u"备份里的 `zfNNN_pre\\release\\PotatoST-0.14.jar` 是**历史**，一个字节没动。"
                    u"④ 六道常驻门 + 7 份活体脚本一起换名（共 17 份）。⑤ `release\\PotatoST-0.15.jar` 重打，"
                    u"0.14 留在盘上作历史。⑥ ⚠ 老门 `_zf186_verify.py` 的 D3 是拿**渲染后的 mods.toml** 跟"
                    u"旧 jar 逐字节比的 —— 抬版本号必然让它变红 ⇒ 判据跟平成「除版本号那一行外逐字节相同」"
                    u"（意图没变：依赖段没动）。⑦ 门 `_zf198_verify.py` 与反证刀跟着走；§4.159 靶子换到新成品。\n")
            hand = hand.replace(anchor, item + u"\n" + anchor, 1)
            if write:
                io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)
            print(u"  交接第 51 条已写")

    # 英文公告：新增 "## Version 0.15" 段（下载行指新成品）
    ann = read(ANN)
    if u"## Version 0.15" not in ann:
        anchor = u"## New in 0.14 ZF196 - Collapse mode now visibly tears the area apart"
        if ann.count(anchor) != 1:
            fails.append(u"公告 ZF196 段锚点 %d 次" % ann.count(anchor))
        else:
            block = (u"## Version 0.15\n\n"
                     u"This release rolls up everything from the 0.14 line (config screen + optional "
                     u"`Configured` support, the flat 8M summon price, the **Collapse mode - DANGER**, "
                     u"empty-offhand firing, blocks flying into the singularity, and the new "
                     u"near-first demolishing that finally makes Collapse mode *look* like an explosion) "
                     u"into version **0.15**.\n\n"
                     u"- The mod version is now **0.15** (`gradle.properties` -> `mod_version`), and the "
                     u"jar is `release/PotatoST-0.15.jar`.\n"
                     u"- Nothing else changed in this step: same dependencies, same translation keys "
                     u"(691 / lzh 693), same 410 classes, same {adv} advancements, same {rec} recipes.\n"
                     u"- **Download:** `release/PotatoST-0.15.jar` - **{size} bytes**, sha1 **`{sha}`**.\n\n"
                     ).format(adv=adv, rec=recipes, size=u"{:,}".format(size), sha=h)
            ann = ann.replace(anchor, block + anchor, 1)
            if write:
                io.open(ANN, "w", encoding="utf-8", newline=u"").write(ann)
            print(u"  英文公告已加「## Version 0.15」")

    # 中英双语公告：顶部加一小段 0.15
    bil = read(BIL)
    if u"## 0.15" not in bil:
        lines = bil.split(u"\n")
        ins = 0
        for i, l in enumerate(lines[:40]):
            if l.startswith(u"## "):
                ins = i
                break
        block = [u"## 0.15（版本线抬升）", u"",
                 u"0.14 那一线的全部内容（配置界面 + 可选的「配置界面」支持、固定 8M 召唤费、",
                 u"**坍缩模式-危险**、空手也能放、方块飞进奇点、以及让坍缩模式**真的像爆炸那样**",
                 u"从近到远拆开的新机制）整体抬版本为 **0.15**；成品 = `release/PotatoST-0.15.jar`",
                 u"（%s 字节 / sha1 `%s`）。依赖、语言键（691 / lzh 693）、类数（%d）都没变。" % (
                     u"{:,}".format(size), h, cls), u""]
        lines[ins:ins] = block
        if write:
            io.open(BIL, "w", encoding="utf-8", newline=u"").write(u"\n".join(lines))
        print(u"  双语公告已在第 %d 行插入 0.15 段" % ins)

    # ② `_zf186_verify.py` 的 D3 跟平：它是拿**渲染后的 mods.toml** 跟旧 jar 逐字节比的 ——
    #    抬版本号必然让它变红；改成"除版本号那一行外逐字节相同"（意图没变：依赖段没动）。
    v186 = os.path.join(ZT, u"_zf186_verify.py")
    t186 = read(v186)
    old_d3 = (u"        a = zipfile.ZipFile(JAR).read(u\"META-INF/neoforge.mods.toml\").decode(u\"utf-8\")\n"
              u"        b = zipfile.ZipFile(pre_jar).read(u\"META-INF/neoforge.mods.toml\").decode(u\"utf-8\")\n"
              u"        dep_ok = (a == b)\n"
              u"        dep_detail = u\"依赖段%s（mods.toml 逐字节相同）\" % (u\"没动\" if dep_ok else u\"被改过\")")
    new_d3 = (u"        a = zipfile.ZipFile(JAR).read(u\"META-INF/neoforge.mods.toml\").decode(u\"utf-8\")\n"
              u"        b = zipfile.ZipFile(pre_jar).read(u\"META-INF/neoforge.mods.toml\").decode(u\"utf-8\")\n"
              u"        # 0.14→0.15 抬版本（ZF198）：渲染出来的 version=\"…\" 那一行本来就该变 ⇒ 比之前先把它抹平。\n"
              u"        dep_ok = (re.sub(u'(?m)^version=\"[^\"]*\"$', u'version=\"X\"', a)\n"
              u"                   == re.sub(u'(?m)^version=\"[^\"]*\"$', u'version=\"X\"', b))\n"
              u"        dep_detail = u\"依赖段%s（mods.toml 除版本号那一行外逐字节相同）\" % (u\"没动\" if dep_ok else u\"被改过\")")
    if old_d3 in t186:
        io.open(v186, "w", encoding="utf-8", newline=u"").write(t186.replace(old_d3, new_d3, 1))
        print(u"  `_zf186_verify.py`：D3 判据已跟平（除版本号那一行外逐字节相同）")
    elif u'version="X"' in t186:
        print(u"  `_zf186_verify.py`：D3 已经是新判据，跳过")
    else:
        fails.append(u"_zf186_verify.py：D3 锚点找不到（跟平失败）")

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
