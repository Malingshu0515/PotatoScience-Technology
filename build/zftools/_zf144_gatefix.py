# -*- coding: utf-8 -*-
r'''_zf144_gatefix.py —— ZF144 的「跟平」（可重复跑，第二次幂等）

**A. 语言键数 487 → 492**（四语言各 +5：锹名 + 剑的三行说明 + 剑气死亡文案）

  口径与 `_zf139/_zf141_gatefix.py` 完全一样：
    · 只改 `_zf*_verify.py` 这类**活着的门**；
    · 只改**带键数标记**的那些行（`EXPECT_KEYS` / `KEYS_BEFORE` / `KEYS_AFTER` / `键` /
      `keys each` / `counts` / `len(...)` …）；
    · sha1 里恰好含 "487" 的那种（十六进制相邻）**先筛掉**；
    · 带 "487" 但没有键数标记的行 ⇒ 停手不写这一份，先看清；
    · 跳过本轮自己那道门（`_zf144_verify.py`）。

**B. 配方数（活体数字）72 → 73 / shaped 62 → 63**

  本轮加了锹那一张（原版锹图纸：1 锭 + 2 棍）。钉住这个数的有四处：
  `_zf100_recipe_guard.py`（**新增名单**要补 `star_steel_shovel.json`，计数是 `len(EXPECT_NEW)`
  自动跟；另有两处写死的 62/59 说明文字）、`_zf134_verify.py`（`EXPECT_SHAPED`）、
  `_zf139_verify.py`（反向：配方份数）、`_zf141_verify.py`（`RECIPES, SHAPED`）。

**C. 成品键数不动**：`_zf93_verify.py` 的 `RELEASE_KEYS = 487` 保持 ——
  本轮**没有重新打包**（release 里那份是别的线 23:22 打的、里面就是 487 键）。

跑法：
    python build\zftools\_zf144_gatefix.py            # 只算不写
    python build\zftools\_zf144_gatefix.py --write
'''
import glob
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
OLD, NEW = u"487", u"492"

MARKERS = [u"EXPECT_KEYS", u"KEYS_BEFORE", u"KEYS_AFTER", u"KEY_NEW", u"KEY_OLD", u"键",
           u"keys each", u"counts", u"len(table)", u"len(t)", u"len(tables", u"len(now)",
           u"len(inside)", u"len(jload"]

fails, notes, plan = [], [], []


def want(text, old, new, label, path):
    # ⚠ 幂等：上一次跑到一半（写盘后断言失败）时可能已经改过这一处
    #   ⇒ 只要"新文本已在、旧文本已不在"就跳过，别报成"命中 0 次"。
    if new in text and old not in text:
        notes.append(u"  [跳过] %s（已经改过，幂等）" % label)
        return text
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


def current(path):
    u'''取"这份文件**在本次计划里**最新的内容"（没被规划过就读盘）。

    ⚠ 这是第一版写坏之后补的：同一份文件可能被 A 段（键数）与 B 段（配方数）**各改一次**，
       而 B 段是从**盘上**重读的 ⇒ 它写出去的版本里没有 A 段的改动，最后落盘的是 B 段那一份，
       A 段的改动被**静默丢掉**（回读断言当场把它抓出来了：`_zf139_verify.py` 对不上）。
    '''
    for p, _old, new in reversed(plan):
        if p == path:
            return new
    return io.open(path, encoding=u"utf-8", newline=u"").read()


def main(argv):
    write = u"--write" in argv

    # ---------------- A. 键数链 ----------------
    for p in sorted(glob.glob(os.path.join(ZT, u"_zf*_verify.py"))):
        name = os.path.basename(p)
        # ⚠ 跳过两份：
        #   ① `_zf144_verify.py` —— 本轮自己那道门（里面的 487 是"改前是多少"，是参照系）；
        #   ② `_zf142_verify.py` —— **另一条线正在用 ZF142**（星图极带模糊），那份在途，
        #      不该被我改（§4.7）。我把轮号改成 ZF144 就是为了不碰他们。
        #   ③ `_zf141_verify.py` —— 上一轮我自己的门，它把键数写成 `KEYS = 487`（不带标记词），
        #      A 段的安全网会把它当"独立 487"顶住 ⇒ 由**下面的 B 段**显式改（那份文件里
        #      只有这一处字面量 487），A 段整份跳过，免得同一份文件被规划两次、后者覆盖前者。
        if name in (u"_zf144_verify.py", u"_zf142_verify.py", u"_zf141_verify.py"):
            continue
        raw = io.open(p, encoding=u"utf-8", newline=u"").read()
        if OLD not in raw:
            continue
        out_lines, hits, bad = [], 0, []
        for line in raw.split(u"\n"):
            # ⚠ `RELEASE_KEYS` 是**成品 jar 里**的键数，不是盘上源码的键数 ——
            #   本轮没打包 ⇒ 它必须留在 487（第一版没排除它，安全网当场把它顶成"独立 487"）。
            if u"RELEASE_KEYS" in line:
                out_lines.append(line)
                continue
            if OLD in line:
                real, idx = False, 0
                while True:
                    i = line.find(OLD, idx)
                    if i < 0:
                        break
                    idx = i + 3
                    if not hexok(line, i):
                        real = True
                        break
                if not real:
                    out_lines.append(line)
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
            fails.append(u"%s：有独立 487 但不带键数标记 —— 停手不写这份：%s"
                         % (name, u" ／ ".join(bad)))
            continue
        if hits:
            plan.append((p, raw, u"\n".join(out_lines)))
            notes.append(u"  [跟平] %-24s %d 处" % (name, hits))

    ann = io.open(ANN, encoding=u"utf-8", newline=u"").read()
    if u"(%s keys each)" % OLD in ann:
        plan.append((ANN, ann, ann.replace(u"(%s keys each)" % OLD, u"(%s keys each)" % NEW)))
        notes.append(u"  [跟平] UpdateAnnouncement_EN.md 的 (487 keys each) → (492 keys each)")
    elif u"(%s keys each)" % NEW in ann:
        notes.append(u"  [跳过] 英文公告的键数已经是 492（幂等）")
    else:
        fails.append(u"英文公告里既没有 (487 keys each) 也没有 (492 keys each)")

    # ---------------- B. 配方数 ----------------
    rguard = os.path.join(ZT, u"_zf100_recipe_guard.py")
    t = current(rguard)
    if u"star_steel_shovel.json" in t:
        notes.append(u"  [跳过] _zf100_recipe_guard.py 的名单已经补过（幂等）")
    else:
        t = want(t, u'    u"star_steel_hoe.json",\n',
                 u'    u"star_steel_hoe.json",\n'
                 u'    # ---- ZF144 加的锹 ----\n'
                 u'    u"star_steel_shovel.json",\n',
                 u"_zf100_recipe_guard.py：新增名单补锹（计数 len(EXPECT_NEW) 自动跟）", rguard)
        t = want(t, u'    shaped == 62)',
                 u'    # ZF144：星璨钢锹 +1 ⇒ 62 → 63\n    shaped == 63)',
                 u"_zf100_recipe_guard.py：shaped 62 → 63", rguard)
        t = want(t, u'**ZF141 三把工具 +3 = 62**',
                 u'**ZF141 三把工具 +3 = 62**；**ZF144 锹 +1 = 63**',
                 u"_zf100_recipe_guard.py：说明文字跟到 63", rguard)
        plan.append((rguard, io.open(rguard, encoding=u"utf-8", newline=u"").read(), t))

    z134 = os.path.join(ZT, u"_zf134_verify.py")
    t = current(z134)
    t2 = want(t, u"EXPECT_SHAPED = 62",
              u"# ⚠ ZF144：星璨钢锹 +1（62 → 63）；活体数字，加配方就要跟\nEXPECT_SHAPED = 63",
              u"_zf134_verify.py：EXPECT_SHAPED 62 → 63", z134)
    if t2 != t:
        plan.append((z134, t, t2))

    z139 = os.path.join(ZT, u"_zf139_verify.py")
    t = current(z139)
    t2 = want(t, u'check(n_recipe == 72, u"反向：配方份数 72（活体数字；ZF141 起 +3）"',
              u'# ⚠ ZF144 跟平：72 → 73（星璨钢锹）\n'
              u'    check(n_recipe == 73, u"反向：配方份数 73（活体数字；ZF144 起 +4）"',
              u"_zf139_verify.py：配方份数 72 → 73", z139)
    if t2 != t:
        plan.append((z139, t, t2))

    z141 = os.path.join(ZT, u"_zf141_verify.py")
    t = current(z141)
    t = want(t, u"KEYS = 487",
             u"# ⚠ ZF144 跟平：锹名 + 剑三行说明 + 剑气死亡文案（487 → 492）\nKEYS = 492",
             u"_zf141_verify.py：KEYS 487 → 492（它没写成 EXPECT_KEYS，安全网逮到了）", z141)
    t2 = want(t, u"RECIPES, SHAPED = 72, 62",
              u"# ⚠ ZF144 跟平：星璨钢锹 +1（配方 73 / shaped 63）\nRECIPES, SHAPED = 73, 63",
              u"_zf141_verify.py：RECIPES/SHAPED 跟到 73 / 63", z141)
    if t2 != t:
        plan.append((z141, t, t2))
    # `_zf141_verify.py` 的 D10/D11 文案里也写着 72/62
    t = io.open(z141, encoding=u"utf-8", newline=u"").read()
    t3 = want(t, u'ok(u"D10 配方总数 %d（得 %d）" % (RECIPES, len(recs))',
              u'ok(u"D10 配方总数 %d（得 %d；ZF141 的 72 + ZF144 的锹 = 73）" % (RECIPES, len(recs))',
              u"_zf141_verify.py：D10 文案说明来源", z141)
    if t3 != t:
        plan.append((z141, t, t3))

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
