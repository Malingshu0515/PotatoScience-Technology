# -*- coding: utf-8 -*-
u"""_zf139_gatefix.py —— ZF139 的「跟平」两件事（都能重复跑，第二次幂等）

**A. 语言键数 482 → 483**（四语言各 +1：`death.attack.potato_s_t.vibranium_reflect`）

  盘上的门里有 **28 份**把键数写死在断言里（ZF133 加 4 键时跟到 482 的那一批）。
  它们不改就会集体变红，而且会**盖住**本轮真正要看的东西。
  口径照 `_zf134_keys.py`（上一轮同一件事的脚本）：
    · 只改 `_zf*_verify.py` 与 `_zf71_verify.py` 这类**活着的门**；
    · 只改**带键数标记**的那些行（`EXPECT_KEYS` / `键` / `keys each` / `KEY_NEW` /
      `counts` / `len(table)` …），以及英文公告的 `(482 keys each)`；
    · **不动**历史脚本（`_zf*_docs.py` / `_zf*_lang.py` / `_zf127_*` / `_zf134_*` 之类）——
      那里的 482 是"当时是多少"，改了就把历史改成假的了；
    · 任何一行里出现"独立 482"但**不带**键数标记 ⇒ 停手不写，先看清楚（怕误伤 sha1 / 坐标）。

**B. `_zf120_verify.py`（振金那条门）的期望值跟到 ZF139**

  · 护甲值：`want_def` 从"下界合金那一行"改成"各 +1"（4/9/7/4）；
  · 满套判据计数：4 → **7**（新加的三个 handler 每人也判一次）；
  · handler 名单：补上三条（PlayerTickEvent$Post / LivingFallEvent / LivingDamageEvent$Post）。

跑法：
    python build\\zftools\\_zf139_gatefix.py            # 只算不写
    python build\\zftools\\_zf139_gatefix.py --write
"""
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
OLD, NEW = u"482", u"483"

# 键数断言的"标记词"：这一行里出现任何一个，才认为那个 482 是键数
MARKERS = [u"EXPECT_KEYS", u"KEY_NEW", u"KEY_OLD", u"键", u"keys each", u"counts",
           u"len(table)", u"len(t)", u"len(tables", u"len(now)", u"len(inside)", u"len(jload"]

# 纯叙述行（说的是"那一轮当时是多少"）：`482` 是历史，**不许改**，也不报错。
# 这是安全网逼出来的名单 —— 第一版跑出来 4 条"有独立 482 但不带键数标记"，
# 逐条看过之后：三条是文档串里的历史叙述，一条是 `len(tables[l])` 没被标记词覆盖。
PROSE_SKIP = [u"ZF120 并行线一加就是 482",
              u"F 往轮判据里的活体数字跟上（464 → 482）",
              u"F 活体数字：往轮门都跟到 482"]

SKIP_FILES = set()          # 历史脚本靠文件名规则排除，见 MAIN

fails, notes = [], []
plan = []


def want(text, old, new, label, path):
    u"""精确替换一次；命中数不是 1 就记失败。"""
    n = text.count(old)
    if n != 1:
        fails.append(u"%s：命中 %d 次（应为 1）" % (label, n))
        return text
    notes.append(u"  [改] %s" % label)
    return text.replace(old, new, 1)


def hexok(line, idx):
    u"""482 两边是不是十六进制字符（sha1 里的 482 不算键数）。"""
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
        # ⚠ 跳过**本轮自己**那道门：它里面的 482 是"改前是多少"（KEYS_BEFORE）
        #   以及"扫别人还有没有残留 482"的判据本身 —— 那是参照系，不是跟平的目标。
        #   （第一版没跳过 ⇒ 安全网把它当成"有独立 482 但不带键数标记"，一个字节都没写。）
        if name == u"_zf139_verify.py":
            continue
        raw = io.open(p, encoding=u"utf-8", newline=u"").read()
        if OLD not in raw:
            continue
        out_lines, hits, bad = [], 0, []
        for line in raw.split(u"\n"):
            if OLD in line and any(s in line for s in PROSE_SKIP):
                notes.append(u"  [留] %s：叙述行里的 482 是历史，不动 —— %s"
                             % (name, line.strip()[:60]))
                out_lines.append(line)
                continue
            if OLD in line:
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
            fails.append(u"%s：有独立 482 但不带键数标记 —— 停手不写这份：%s"
                         % (name, u" ／ ".join(bad)))
            continue
        if hits:
            plan.append((p, raw, u"\n".join(out_lines)))
            notes.append(u"  [跟平] %-24s %d 处" % (name, hits))

    # 英文公告
    ann = io.open(ANN, encoding=u"utf-8", newline=u"").read()
    if u"(%s keys each)" % OLD in ann:
        plan.append((ANN, ann, ann.replace(u"(%s keys each)" % OLD, u"(%s keys each)" % NEW)))
        notes.append(u"  [跟平] UpdateAnnouncement_EN.md 的 (482 keys each) → (483 keys each)")
    else:
        fails.append(u"英文公告里找不到 (482 keys each)")

    # ---------------- B. _zf120_verify.py ----------------
    z120 = os.path.join(ZT, u"_zf120_verify.py")
    t = io.open(z120, encoding=u"utf-8", newline=u"").read()
    if u"VIBRANIUM_DEFENSE" not in t:
        t = want(t,
                 u'NETHERITE_DEFENSE = {u"helmet": 3, u"chestplate": 8, u"leggings": 6, u"boots": 3}',
                 u'NETHERITE_DEFENSE = {u"helmet": 3, u"chestplate": 8, u"leggings": 6, u"boots": 3}\n'
                 u'# ⚠ ZF139：振金不再"与下界合金一致"，而是**各 +1**（用户拍板的"乙方案"）——\n'
                 u'#   这两个表都留着：NETHERITE_* 是"原版那一行"的取证底稿，VIBRANIUM_* 才是本轮期望值。\n'
                 u'VIBRANIUM_DEFENSE = {u"helmet": 4, u"chestplate": 9, u"leggings": 7, u"boots": 4}',
                 u"_zf120_verify.py：加 VIBRANIUM_DEFENSE 表", z120)
        t = want(t, u'    want_def = [NETHERITE_DEFENSE[p] for p in PARTS]',
                 u'    want_def = [VIBRANIUM_DEFENSE[p] for p in PARTS]',
                 u"_zf120_verify.py：② 期望护甲值改用 VIBRANIUM_DEFENSE", z120)
        t = want(t, u'    print(u"================ ② 基础数据 = 下界合金（材料里） ================")',
                 u'    print(u"================ ② 基础数据 = 下界合金各 +1（材料里，ZF139）================")',
                 u"_zf120_verify.py：② 标题跟到 ZF139", z120)
        t = want(t, u'    check(src_set.count(u"hasFullVibraniumSet(") == 4,\n'
                    u'          u"四个 handler 各判了一次满套（共 4 次调用）",',
                 u'    # ZF139 起是 **7** 处：弹射物 / 兜底+爆炸 / 受击击退 / 爆炸击退 /\n'
                 u'    #                        常驻抗性 / 免摔落 / 反伤\n'
                 u'    check(src_set.count(u"hasFullVibraniumSet(") == 7,\n'
                 u'          u"七个 handler 各判了一次满套（共 7 次调用）",',
                 u"_zf120_verify.py：满套判据计数 4 → 7", z120)
        t = want(t, u'        (u"onExplosionKnockback",\n'
                    u'         u"(Lnet/neoforged/neoforge/event/level/ExplosionKnockbackEvent;)V",\n'
                    u'         u"③ 爆炸击退"),\n    ]',
                 u'        (u"onExplosionKnockback",\n'
                 u'         u"(Lnet/neoforged/neoforge/event/level/ExplosionKnockbackEvent;)V",\n'
                 u'         u"③ 爆炸击退"),\n'
                 u'        # ---- ZF139 加的三条 ----\n'
                 u'        (u"onPlayerTick",\n'
                 u'         u"(Lnet/neoforged/neoforge/event/tick/PlayerTickEvent$Post;)V",\n'
                 u'         u"④ 满套常驻抗性提升 I"),\n'
                 u'        (u"onFall",\n'
                 u'         u"(Lnet/neoforged/neoforge/event/entity/living/LivingFallEvent;)V",\n'
                 u'         u"⑤ 满套免疫摔落伤害"),\n'
                 u'        (u"onDamagePost",\n'
                 u'         u"(Lnet/neoforged/neoforge/event/entity/living/LivingDamageEvent$Post;)V",\n'
                 u'         u"⑥ 10% 反伤"),\n    ]',
                 u"_zf120_verify.py：handler 名单补三条", z120)
        plan.append((z120, io.open(z120, encoding=u"utf-8", newline=u"").read(), t))
    else:
        notes.append(u"  [跳过] _zf120_verify.py 已经跟平过（幂等）")

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
        # 回读
        for p, _old, new in plan:
            assert io.open(p, encoding=u"utf-8", newline=u"").read() == new, p
        print(u"回读：%d 份逐字节等于写出去的内容" % len(plan))
    else:
        print(u"（没加 --write，只算不写）")
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
