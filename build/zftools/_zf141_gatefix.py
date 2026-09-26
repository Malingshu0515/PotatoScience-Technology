# -*- coding: utf-8 -*-
r"""_zf141_gatefix.py —— ZF141 的「跟平」（可重复跑，第二次幂等）

**A. 语言键数 483 → 487**（四语言各 +4：三件工具名 + 一句共用的技能说明）

  键数是**活体数字**：全工程有一批常驻门把它写死在断言里，不跟平就会集体变红，
  而且会**盖住**本轮真正要看的东西。口径沿用 `_zf139_gatefix.py` / `_zf134_keys.py`：
    · 只改 `_zf*_verify.py` 这类**活着的门**；
    · 只改**带键数标记**的那些行（`EXPECT_KEYS` / `KEY_NEW` / `键` / `keys each` /
      `counts` / `len(...)` …），以及英文公告的 `(483 keys each)`；
    · **不动**历史脚本（`_zf*_docs.py` / `_zf*_lang.py` / `_zf141_lang.py` /
      `_zf139_commit.py` 之类）—— 那里的 483 是"那一轮当时是多少"，改了就是把历史改成假的；
    · 任何一行出现 483 但**不带**键数标记 ⇒ 停手不写这一份，先看清（怕误伤 sha1 / 坐标）。
    · 跳过本轮自己那道门（`_zf141_verify.py`）：它里面的 483 是"改前是多少"，
      是**参照系**不是跟平目标。

**B. `_zf133_verify.py` 的贴图取证靶子换个文件**

  那一轮的 D4 断言"在用贴图与用户素材逐字节一致"，素材写死的是
  `build\用户素材\星璨钢斧.png`。本轮用户拿 `星璨钢斧子新贴图.png` **换掉**了斧子那张、
  并把旧素材文件删了 ⇒ 那条断言变成 **静默跳过**（`if os.path.isfile(src)` 不成立，
  D2~D5 一个都不跑，"绿"是空的）。靶子改指新素材 ⇒ 判据重新生效（且更严格）。

跑法：
    python build\zftools\_zf141_gatefix.py            # 只算不写
    python build\zftools\_zf141_gatefix.py --write
"""
import glob
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
OLD, NEW = u"483", u"487"

MARKERS = [u"EXPECT_KEYS", u"KEYS_BEFORE", u"KEYS_AFTER", u"KEY_NEW", u"KEY_OLD", u"键",
           u"keys each", u"counts", u"len(table)", u"len(t)", u"len(tables", u"len(now)",
           u"len(inside)", u"len(jload"]

# 纯叙述行（说的是"那一轮当时是多少"）：483 是历史，**不许改**，也不报错。
# 安全网逼出来的名单：第一版跑出来 N 条"有独立 483 但不带键数标记"，逐条看过之后才放行。
PROSE_SKIP = []

fails, notes = [], []
plan = []


def want(text, old, new, label, path):
    n = text.count(old)
    if n != 1:
        fails.append(u"%s：命中 %d 次（应为 1）" % (label, n))
        return text
    notes.append(u"  [改] %s" % label)
    return text.replace(old, new, 1)


def hexok(line, idx):
    hexd = u"0123456789abcdefABCDEF"
    left = line[idx - 1] if idx > 0 else u" "
    right = line[idx + 3] if idx + 3 < len(line) else u" "
    return left in hexd or right in hexd


def main(argv):
    write = u"--write" in argv

    # ---------------- A. 键数链 ----------------
    files = sorted(glob.glob(os.path.join(ZT, u"_zf*_verify.py")))
    for p in files:
        name = os.path.basename(p)
        if name == u"_zf141_verify.py":
            continue
        raw = io.open(p, encoding=u"utf-8", newline=u"").read()
        if OLD not in raw:
            continue
        out_lines, hits, bad = [], 0, []
        for line in raw.split(u"\n"):
            if OLD in line and any(s in line for s in PROSE_SKIP):
                notes.append(u"  [留] %s：叙述行里的 483 是历史，不动" % name)
                out_lines.append(line)
                continue
            if OLD in line:
                # ⚠ 安全网要**先认出"这只是 sha1 里的一段十六进制"**。
                #   第一版把这一层放在"标记词"之后 ⇒ `_zf117_verify.py` 里那行
                #   `"oil": "6546ccc4aed1948303e8804ff78437454f79650f",` 里的 `483`
                #   被当成"有独立 483 但不带键数标记" ⇒ 整份文件拒绝写。
                #   正确顺序：先按十六进制相邻筛掉，再看有没有标记词。
                real = False
                idx = 0
                while True:
                    i = line.find(OLD, idx)
                    if i < 0:
                        break
                    idx = i + 3
                    if not hexok(line, i):
                        real = True
                        break
                if not real:
                    out_lines.append(line)      # 只是 sha1 里的一段，原样留
                    continue
                if not any(m in line for m in MARKERS):
                    bad.append(line.strip()[:90])
                else:
                    cur, idx = line, 0
                    while True:
                        i = cur.find(OLD, idx)
                        if i < 0:
                            break
                        idx = i + 3
                        if hexok(cur, i):
                            continue
                        cur = cur[:i] + NEW + cur[i + 3:]
                        hits += 1
                    line = cur
            out_lines.append(line)
        if bad:
            fails.append(u"%s：有独立 483 但不带键数标记 —— 停手不写这份：%s"
                         % (name, u" ／ ".join(bad)))
            continue
        if hits:
            plan.append((p, raw, u"\n".join(out_lines)))
            notes.append(u"  [跟平] %-24s %d 处" % (name, hits))

    # 英文公告
    # ⚠ 这一步必须**幂等**：脚本第一次跑就已经把 483 改成 487 了，再跑一次时
    #   "(483 keys each)" 当然找不到了 —— 第一版把它当成失败，整份脚本一个字节都不写
    #   （"安全网比正文更容易骗人"的又一个小号版本）。
    ann = io.open(ANN, encoding=u"utf-8", newline=u"").read()
    if u"(%s keys each)" % OLD in ann:
        plan.append((ANN, ann, ann.replace(u"(%s keys each)" % OLD,
                                           u"(%s keys each)" % NEW)))
        notes.append(u"  [跟平] UpdateAnnouncement_EN.md 的 (483 keys each) → (487 keys each)")
    elif u"(%s keys each)" % NEW in ann:
        notes.append(u"  [跳过] 英文公告的键数已经是 487（幂等）")
    else:
        fails.append(u"英文公告里既没有 (%s keys each) 也没有 (%s keys each)" % (OLD, NEW))

    # ---------------- B. _zf133_verify.py 的贴图靶子 ----------------
    z133 = os.path.join(ZT, u"_zf133_verify.py")
    t = io.open(z133, encoding=u"utf-8", newline=u"").read()
    if u"星璨钢斧子新贴图.png" in t:
        notes.append(u"  [跳过] _zf133_verify.py 的贴图靶子已经换过（幂等）")
    else:
        t2 = want(t,
                  u'src = os.path.join(ROOT, r"build\\用户素材\\星璨钢斧.png")',
                  # ⚠ 插进去的注释**必须与被替换的那一行同缩进**：第一版顶格写了，
                  #   `_zf133_verify.py` 当场 IndentationError（整道门跑不起来 ⇒ 假红）。
                  u'    # ⚠ ZF141：用户拿 `星璨钢斧子新贴图.png` 换掉了斧子那张图，并删掉了旧素材\n'
                  u'    #   `星璨钢斧.png` ⇒ 原来这个靶子会让 D2~D5 **静默跳过**（"绿"是空的）。\n'
                  u'    #   靶子改指新素材，判据重新生效。\n'
                  u'    src = os.path.join(ROOT, r"build\\用户素材\\星璨钢斧子新贴图.png")',
                  u"_zf133_verify.py：D4 的素材靶子换成新贴图", z133)
        if t2 != t:
            plan.append((z133, t, t2))

    # ---------------- C. 配方数（活体数字）+ 成品键数 ----------------
    # 本轮**加了三张 shaped 配方**（69 → 72 / shaped 59 → 62），有 4 道门把它写死了。
    # 口径与 A 段一样：只改"带标记"的那几行，改完逐份回读。
    rguard = os.path.join(ZT, u"_zf100_recipe_guard.py")
    t = io.open(rguard, encoding=u"utf-8", newline=u"").read()
    if u"star_steel_sword.json" in t:
        notes.append(u"  [跳过] _zf100_recipe_guard.py 的名单已经补过（幂等）")
    else:
        t = want(t, u'    u"star_steel_axe.json",\n',
                 u'    u"star_steel_axe.json",\n'
                 u'    # ---- ZF141 加的三把工具 ----\n'
                 u'    u"star_steel_sword.json",\n'
                 u'    u"star_steel_pickaxe.json",\n'
                 u'    u"star_steel_hoe.json",\n',
                 u"_zf100_recipe_guard.py：新增名单补三条（计数用的是 len(EXPECT_NEW)，自动跟）", rguard)
        t = want(t, u'    shaped == 59)',
                 u'    # ZF141：星璨钢剑/镐/锄 +3 ⇒ 59 → 62\n    shaped == 62)',
                 u"_zf100_recipe_guard.py：shaped 59 → 62", rguard)
        t = want(t, u'**ZF134 星璨钢斧 +1 = 59**', u'**ZF134 星璨钢斧 +1 = 59**；**ZF141 三把工具 +3 = 62**',
                 u"_zf100_recipe_guard.py：说明文字跟到 62", rguard)
        plan.append((rguard, io.open(rguard, encoding=u"utf-8", newline=u"").read(), t))

    z134 = os.path.join(ZT, u"_zf134_verify.py")
    t = io.open(z134, encoding=u"utf-8", newline=u"").read()
    t2 = want(t, u"EXPECT_SHAPED = 59",
              u"# ⚠ ZF141：星璨钢剑/镐/锄 +3 张 shaped（59 → 62）；活体数字，加配方就要跟\nEXPECT_SHAPED = 62",
              u"_zf134_verify.py：EXPECT_SHAPED 59 → 62", z134)
    if t2 != t:
        plan.append((z134, t, t2))

    z139 = os.path.join(ZT, u"_zf139_verify.py")
    t = io.open(z139, encoding=u"utf-8", newline=u"").read()
    t2 = want(t, u'check(n_recipe == 69, u"反向：配方份数 69（活体数字；本轮 +0）"',
              u'# ⚠ ZF141 跟平：69 → 72（星璨钢剑/镐/锄三张）—— 活体数字，加配方就要跟\n'
              u'    check(n_recipe == 72, u"反向：配方份数 72（活体数字；ZF141 起 +3）"',
              u"_zf139_verify.py：配方份数 69 → 72", z139)
    if t2 != t:
        plan.append((z139, t, t2))

    # `_zf93_verify.py` 两件事：
    #   ① 它第 50 行那句**注释**里带着一个"独立的 482"，`_zf139_verify.py` 的扫描会把它数进去
    #      ⇒ 换个说法（注释里别写那个数）；
    #   ② 另一条线**在 23:22 重新打包了 0.11**（`release\PotatoST-0.11.jar` 的 SHA1
    #      303c5d46… → 276e9eff…，`.sha1` 副档同步重写），那份成品里 zh_cn 已经是 **487** 键
    #      ⇒ `RELEASE_KEYS` 必须跟到 487，否则本门会因为"别人打了包"变红。
    z93 = os.path.join(ZT, u"_zf93_verify.py")
    t = io.open(z93, encoding=u"utf-8", newline=u"").read()
    t2 = want(t, u'#   （本轮 gatefix 把所有带"键数"的 482 一律改成 487 时，就是这么把它顶红的）。',
              u'#   （某轮 gatefix 把"带键数标记"的那些旧数字一律改成新数字时，就是这么把它顶红的）。',
              u"_zf93_verify.py：注释里不再留那个独立的旧数字（会被上一轮那道门数进去）", z93)
    t3 = want(t2, u"RELEASE_KEYS = 482",
              u"# ⚠ ZF141 跟平：另一条线在 23:22 重新打包了 0.11（SHA1 303c5d46… → 276e9eff…），\n"
              u"#   那份成品里 zh_cn 是 487 键 ⇒ 这里的靶子跟到 487（谁再打包，谁就负责再看一眼这个数）。\n"
              u"RELEASE_KEYS = 487",
              u"_zf93_verify.py：RELEASE_KEYS 482 → 487（成品已被重新打包）", z93)
    if t3 != t:
        plan.append((z93, t, t3))

    print(u"")
    for n in notes:
        print(n)
    print(u"")
    if fails:
        print(u"失败项 = %d（一个字节都没写）" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    print(u"待写：%d 份文件" % len(plan))
    if write:
        for p, _old, new in plan:
            io.open(p, u"w", encoding=u"utf-8", newline=u"").write(new)
        print(u"已写盘。")
        for p, _old, new in plan:
            assert io.open(p, encoding=u"utf-8", newline=u"").read() == new, p
        print(u"回读：%d 份逐字节等于写出去的内容" % len(plan))
    else:
        print(u"（没加 --write，只算不写）")
    return 0

if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
