# -*- coding: utf-8 -*-
u"""_zf148_gatefix.py —— ZF148 门跟平（活体数字 508 → 579 / 配方 73 → 74 / 配方守卫白名单）。

**A. 语言键数 508 → 579**（四语言各 +71：手册 71 键）
      · 只动 `_zf*_verify.py`（常驻门），历史脚本（`_zfNNN_docs.py` / `_zfNNN_commit.py`）**不碰**
        —— 它们记的是**自己那一轮**的数字，不是活体数字。
      · ⚠ 不动 `_rzh_*.py`：那是**文言文那条线自己的**脚本，而且此刻他们正在跑
        （`_rzh_jar012_check.py` 12:57 才写过盘）⇒ 按「别人在途的门一律不碰」办（§4.7）。
      · 排除：`RELEASE_KEYS` 行（成品 jar 还是 0.11 那一份，里面就是 508 键）；
        十六进制串里的 508/510（sha1）；以及**按整行点名**排除的 `_zf81_verify.py` 那条
        —— 它数的是**成品 jar 内部**的键数，同样属于"等打包那一轮再说"。
**B. 配方总数 73 → 74**（`_zf139_verify.py` / `_zf141_verify.py`）：手册那条是 shapeless，
     所以 `SHAPED = 63` **不变**。
**C. `_zf100_recipe_guard.py`**：新配方必须进白名单（`EXPECT_NEW`），否则
     「盘上 = jar 内 + 新增」这条恒等式当场不成立。
**D. 英文公告**：`(508 keys each)` → `(579 keys each)`。

跑法：python build\\zftools\\_zf148_gatefix.py           （默认 dry-run）
      python build\\zftools\\_zf148_gatefix.py --write
"""
import glob
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
OLD, NEW = u"508", u"579"

MARKERS = [u"EXPECT_KEYS", u"KEY_NEW", u"KEY_OLD", u"KEYS", u"键", u"keys each",
           u"counts", u"len("]

# 说的不是「盘上现在的键数」的行 —— 按 strip() 后的整行点名排除
DENY = {
    (u"_zf81_verify.py",
     u'eq(u"语言键数（ZF112 起 508）", 508, len(inside))'),
}

SKIP_FILES = {u"_zf148_verify.py"}

fails, notes, plan = [], [], []


def want(text, old, new, label):
    """幂等口径：**新文本已经在**就跳过（§4.148：别拿 old not in text 当判据）。"""
    if new in text:
        notes.append(u"  [跳过] %s（已经是新值，幂等）" % label)
        return text
    n = text.count(old)
    if n != 1:
        fails.append(u"%s：命中 %d 次（应为 1）" % (label, n))
        return text
    notes.append(u"  [改] %s" % label)
    return text.replace(old, new, 1)


def hexok(line, idx, ln=3):
    hexd = u"0123456789abcdefABCDEF"
    left = line[idx - 1] if idx > 0 else u" "
    right = line[idx + ln] if idx + ln < len(line) else u" "
    return left in hexd or right in hexd


def current(path):
    """⚠ A 段可能已经给这份文件排过一版计划（`_zf139` / `_zf141` 两段都要动）
    ⇒ B/C 段必须接着**计划里的那一版**往下改，不能从盘上重新读 —— 否则写盘时
    后一版会把前一版的改动整份盖掉（本节第一版就是这么错的，dry-run 时发现）。"""
    for p, _old, new in reversed(plan):
        if p == path:
            return new
    return io.open(path, encoding=u"utf-8", newline=u"").read()


def main(argv):
    write = u"--write" in argv

    # ---------------- A. 键数链 508 → 579 ----------------
    for p in sorted(glob.glob(os.path.join(ZT, u"_zf*_verify.py"))):
        name = os.path.basename(p)
        if name in SKIP_FILES:
            continue
        raw = io.open(p, encoding=u"utf-8", newline=u"").read()
        if OLD not in raw:
            continue
        out_lines, hits, bad = [], 0, []
        for line in raw.split(u"\n"):
            if OLD in line and (u"RELEASE_KEYS" in line or (name, line.strip()) in DENY):
                out_lines.append(line)
                notes.append(u"  [点名排除] %-22s %s" % (name, line.strip()[:60]))
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
            fails.append(u"%s：有独立 508 但不带键数标记 —— 停手不写这份：%s"
                         % (name, u" ／ ".join(bad)))
            continue
        if hits:
            plan.append((p, raw, u"\n".join(out_lines)))
            notes.append(u"  [跟平] %-24s %d 处" % (name, hits))

    # ---------------- B. 配方 73 → 74 ----------------
    p139 = os.path.join(ZT, u"_zf139_verify.py")
    t = current(p139)
    t2 = want(t, u"check(n_recipe == 73,", u"check(n_recipe == 74,", u"_zf139 配方数断言 73 → 74")
    t2 = want(t2, u'u"反向：配方份数 73（活体数字；ZF143 起 +4）"',
              u'u"反向：配方份数 74（活体数字；ZF148 帕秋莉手册 +1）"', u"_zf139 配方数文案")
    if t2 != t:
        plan.append((p139, t, t2))

    p141 = os.path.join(ZT, u"_zf141_verify.py")
    t = current(p141)
    t2 = want(t, u"RECIPES, SHAPED = 73, 63", u"RECIPES, SHAPED = 74, 63", u"_zf141 RECIPES 73 → 74")
    t2 = want(t2, u"；ZF141 的 72 + ZF143 的锹 = 73）", u"；ZF141 的 72 + ZF143 的锹 = 73 + ZF148 手册 = 74）",
              u"_zf141 D10 文案")
    t2 = want(t2, u"# ⚠ ZF143 跟平：星璨钢锹 +1（配方 73 / shaped 63）",
              u"# ⚠ ZF143 跟平：星璨钢锹 +1（配方 73 / shaped 63）\n"
              u"# ⚠ ZF148 跟平：帕秋莉手册 +1 ⇒ 配方 74；**shaped 仍是 63**（手册那条是 crafting_shapeless）",
              u"_zf141 注释补一行")
    if t2 != t:
        plan.append((p141, t, t2))

    # ---------------- C. 配方守卫白名单 ----------------
    pg = os.path.join(ZT, u"_zf100_recipe_guard.py")
    t = io.open(pg, encoding=u"utf-8", newline=u"").read()
    t2 = want(t, u'    u"vibranium_leggings_smithing.json",\n}',
              u'    u"vibranium_leggings_smithing.json",\n'
              u'    # ---- ZF148 加的帕秋莉手册（书 + 铁锭，shapeless）----\n'
              u'    u"guide_book.json",\n}',
              u"_zf100_recipe_guard 白名单 + guide_book.json")
    if t2 != t:
        plan.append((pg, t, t2))

    # ---------------- D. 英文公告 ----------------
    ann = io.open(ANN, encoding=u"utf-8", newline=u"").read()
    if u"(%s keys each)" % OLD in ann:
        plan.append((ANN, ann, ann.replace(u"(%s keys each)" % OLD, u"(%s keys each)" % NEW)))
        notes.append(u"  [跟平] UpdateAnnouncement_EN.md 的 (508 keys each) → (579 keys each)")
    elif u"(%s keys each)" % NEW in ann:
        notes.append(u"  [跳过] 英文公告的键数已经是 579（幂等）")
    else:
        fails.append(u"英文公告里既没有 (508 keys each) 也没有 (579 keys each)")

    # ---------------- E. 「成品 jar 里的键数」那一类：拆出 RELEASE_KEYS ----------------
    # ⚠ A 段把 EXPECT_KEYS 抬到 579 是**对**的（那是盘上活体数字），
    #   但有几道门拿**同一个常量**去卡**成品 jar 内部**的键数 ——
    #   成品还是 0.11 那一份（508 键），于是这几条被我一抬就红了。
    #   按 `_zf93_verify.py` 已有的惯例拆成两个常量：EXPECT_KEYS（盘上）/ RELEASE_KEYS（成品），
    #   打包那一轮负责把 RELEASE_KEYS 一起抬上去（交接 §6 已记）。
    JAR_CASES = [
        (u"_zf80_verify.py",
         u'eq(u"成品里的中文语言文件也是 %d 键" % EXPECT_KEYS, EXPECT_KEYS, len(inside))',
         u'RELEASE_KEYS = 508         # ⚠ 成品 jar 还是 0.11 那一份（508 键）；打包那一轮连它一起抬\n'
         u'        eq(u"成品里的中文语言文件也是 %d 键" % RELEASE_KEYS, RELEASE_KEYS, len(inside))'),
        (u"_zf82_verify.py",
         u'eq(u"成品里中文键数 = %d" % EXPECT_KEYS, EXPECT_KEYS, len(inside))',
         u'RELEASE_KEYS = 508         # ⚠ 成品 jar 还是 0.11 那一份（508 键）；打包那一轮连它一起抬\n'
         u'        eq(u"成品里中文键数 = %d" % RELEASE_KEYS, RELEASE_KEYS, len(inside))'),
        (u"_zf100_verify.py",
         u'            check(u"成品里 zh_cn 仍是 %d 键" % EXPECT_KEYS,\n'
         u'                  len(json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))\n'
         u'                  == EXPECT_KEYS)',
         u'            # ⚠ ZF148 拆常量：成品 jar 还是 0.11 那一份（508 键）——\n'
         u'            #   盘上活体数字走 EXPECT_KEYS，成品走 RELEASE_KEYS（打包那一轮负责抬它）。\n'
         u'            RELEASE_KEYS = 508\n'
         u'            check(u"成品里 zh_cn 仍是 %d 键" % RELEASE_KEYS,\n'
         u'                  len(json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))\n'
         u'                  == RELEASE_KEYS)'),
        (u"_zf101_verify.py",
         u'            check(u"成品里 zh_cn 仍是 %d 键" % EXPECT_KEYS,\n'
         u'                  len(json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))\n'
         u'                  == EXPECT_KEYS)',
         u'            # ⚠ ZF148 拆常量：成品 jar 还是 0.11 那一份（508 键）。\n'
         u'            RELEASE_KEYS = 508\n'
         u'            check(u"成品里 zh_cn 仍是 %d 键" % RELEASE_KEYS,\n'
         u'                  len(json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))\n'
         u'                  == RELEASE_KEYS)'),
        (u"_zf102_verify.py",
         u'            check(u"成品里 zh_cn 是 %d 键" % EXPECT_KEYS,\n'
         u'                  len(json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))\n'
         u'                  == EXPECT_KEYS)',
         u'            # ⚠ ZF148 拆常量：成品 jar 还是 0.11 那一份（508 键）。\n'
         u'            RELEASE_KEYS = 508\n'
         u'            check(u"成品里 zh_cn 是 %d 键" % RELEASE_KEYS,\n'
         u'                  len(json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))\n'
         u'                  == RELEASE_KEYS)'),
    ]
    for name, old_line, new_line in JAR_CASES:
        p = os.path.join(ZT, name)
        t = current(p)
        if u"RELEASE_KEYS = 508" in t:
            notes.append(u"  [跳过] %s 已拆过 RELEASE_KEYS（幂等）" % name)
            continue
        if old_line not in t:
            fails.append(u"%s：找不到成品那行（%s）" % (name, old_line[:44]))
            continue
        plan.append((p, t, t.replace(old_line, new_line, 1)))
        notes.append(u"  [拆常量] %s：成品那行改用 RELEASE_KEYS = 508" % name)

    # ---------------- F. 「相对改前件只多了这些键」那一类：把本轮 71 键算进「后续轮次」 ----------------
    p125 = os.path.join(ZT, u"_zf125_verify.py")
    t = current(p125)
    t2 = want(t,
              u'        later = {u"item.potato_s_t.silver_wire", u"item.potato_s_t.silver_wire_spool"}\n',
              u'        later = {u"item.potato_s_t.silver_wire", u"item.potato_s_t.silver_wire_spool"}\n'
              u'        # ⚠ ZF148 跟平：帕秋莉手册又加了 71 个键（`_zf148_text.py`）——\n'
              u'        #   按前缀认出来，判据强度不变（仍然是「新增 == 本轮 + 后续轮次」）。\n'
              u'        later |= {k for k in c if k.startswith(u"potato_s_t.guide.")}\n'
              u'        later |= {u"item.potato_s_t.guide_book", u"message.potato_s_t.guide_book.received"}\n',
              u"_zf125 E18：把 ZF148 的 71 键算进「后续轮次加的」")
    if t2 != t:
        plan.append((p125, t, t2))

    p145 = os.path.join(ZT, u"_zf145_verify.py")
    t = current(p145)
    t2 = want(t, u'        eq(u"E6 %s：相对改前件只多了这 16 个键" % l, sorted(keys), sorted(added))',
              u'        # ⚠ ZF148 跟平：帕秋莉手册加了 71 个键 ⇒ 期望 = 本轮 16 个 + 后续轮次那 71 个\n'
              u'        later148 = ({k for k in lang[l] if k.startswith(u"potato_s_t.guide.")}\n'
              u'                     | {u"item.potato_s_t.guide_book",\n'
              u'                        u"message.potato_s_t.guide_book.received"})\n'
              u'        eq(u"E6 %s：相对改前件只多了本轮 16 个 + ZF148 的 71 个" % l,\n'
              u'           sorted(set(keys) | later148), sorted(added))',
              u"_zf145 E6：把 ZF148 的 71 键算进期望")
    if t2 != t:
        plan.append((p145, t, t2))

    # ---------------- G. `_zf73_repro` 的「不该出现在改前件里」名单 ----------------
    p73 = os.path.join(ZT, u"_zf73_repro.py")
    t = current(p73)
    t2 = want(t, u'          u"combustion_chamber.json", u"acidic_reaction_chamber.json"}',
              u'          u"combustion_chamber.json", u"acidic_reaction_chamber.json",\n'
              u'          # ---- ZF148 帕秋莉手册（书 + 铁锭）----\n'
              u'          u"guide_book.json"}',
              u"_zf73_repro 白名单 + guide_book.json")
    if t2 != t:
        plan.append((p73, t, t2))

    print(u"\n".join(notes))
    print(u"")
    print(u"计划写盘 %d 份文件" % len(plan))
    if fails or not write:
        print(u"失败项 = %d" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        if not write:
            print(u"（没加 --write，只算不写）")
        return 1 if fails else 0

    for p, old, new in plan:
        io.open(p, u"w", encoding=u"utf-8", newline=u"").write(new)
        assert io.open(p, encoding=u"utf-8", newline=u"").read() == new, p
    print(u"已写盘 %d 份" % len(plan))
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
