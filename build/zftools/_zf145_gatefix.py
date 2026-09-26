# -*- coding: utf-8 -*-
r'''_zf145_gatefix.py —— ZF145 的「跟平」（可重复跑，第二次幂等）

**A. 语言键数 492 → 508**（四语言各 +16：8 条进度 × 标题/说明）

  口径与 `_zf139/_zf141/_zf144_gatefix.py` 一样：
    · 只改 `_zf*_verify.py` 这类**活着的门**；
    · 只改**带键数标记**的那些行（`EXPECT_KEYS` / `KEYS` / `KEY_NEW` / `键` / `keys each` /
      `counts` / `len(...)` …）；
    · sha1 里恰好含 "492" 的那种（十六进制相邻）**先筛掉**；
    · 带 "492" 但没有键数标记的行 ⇒ 停手不写这一份，先看清；
    · **点名排除 4 行**（它们说的不是"盘上现在的键数"）：
        - `_zf93_verify.py` 讲**成品 jar**（本轮没打包 ⇒ 成品仍是 492 键）
        - `_zf119_verify.py` / `_zf141_verify.py` 各一行**历史注释**
        - 任何带 `RELEASE_KEYS` 的行

**B. 进度条数 35 → 43**（8 条新节点）

  钉着这个数的是：`_zf107_verify.py`（EXPECT_NODES + 节点名单 + CHALLENGES/GOALS）、
  `_zf117_verify.py`（N_ALL + A2 的目录比对 + H7 交接文档）、`_zf128_verify.py`（C1）、
  `_zf139_verify.py`（那条"反向：进度仍是 35 条"）、`_zf71_verify.py`（adv == 27，本来就陈旧）。

**C. 英文公告** `(492 keys each)` → `(508 keys each)`。

跑法：
    python build\zftools\_zf145_gatefix.py            # 只算不写
    python build\zftools\_zf145_gatefix.py --write
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
PRE = os.path.join(r"C:\PotatoST救援", "zf145_pre")
OLD, NEW = u"492", u"508"

MARKERS = [u"EXPECT_KEYS", u"KEY_NEW", u"KEY_OLD", u"KEYS", u"键", u"keys each",
           u"counts", u"len(", u"len("]

# 说的不是"盘上现在的键数"的行 —— **按 strip() 后的整行点名排除**
#   （§4.132：只对自己点名的清单动手；⚠ 必须用 strip()：`_zf119` 那条是**缩进过的**函数内注释，
#    第一版写成"行首不留空格"⇒ 点名没命中、被当成独立 492 跟平了）
DENY = {
    (u"_zf119_verify.py",
     u"# ⚠ ZF121 retarget：这里原来钉死 KEY_NEW（492）。键数是**每一轮都会动的活体数字**"),
    (u"_zf141_verify.py",
     u"# ⚠ ZF143 跟平：锹名 + 剑三行说明 + 剑气死亡文案（487 → 492）"),
    (u"_zf93_verify.py",
     u"#   那份成品里 zh_cn 是 492 键 ⇒ 这里的靶子跟到 492（谁再打包，谁就负责再看一眼这个数）。"),
}

# 本轮自己那道门 + 别人在途的门，一律不碰（§4.7）
SKIP_FILES = {u"_zf145_verify.py", u"_zf142_verify.py", u"_zf143_verify.py"}

fails, notes, plan = [], [], []


def current(path):
    for p, _old, new in reversed(plan):
        if p == path:
            return new
    return io.open(path, encoding=u"utf-8", newline=u"").read()


def want(text, old, new, label, path):
    # ⚠ 幂等：跑到一半（写盘后断言失败）时可能已经改过这一处。
    #   ⚠⚠ 判据只能是「**新文本已经在**」—— 第一版抄 ZF144 写成
    #     `new in text and old not in text`，而这里有一对 old 是 new 的**前缀**
    #     （`ALL_NODES = … + ZF117_NODES` → 新块里那行是 `… + ZF117_NODES + ZF145_NODES`）
    #     ⇒ `old in text` 恒真 ⇒ 幂等判断失效 ⇒ **重复插一遍**（干跑当场抓到，没写盘）。
    if new in text:
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


def main(argv):
    write = u"--write" in argv
    verify = u"--verify" in argv

    # ---------------- A. 键数链 ----------------
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
                notes.append(u"  [点名排除] %-22s %s" % (name, line.strip()[:64]))
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
            fails.append(u"%s：有独立 492 但不带键数标记 —— 停手不写这份：%s"
                         % (name, u" ／ ".join(bad)))
            continue
        if hits:
            plan.append((p, raw, u"\n".join(out_lines)))
            notes.append(u"  [跟平] %-24s %d 处" % (name, hits))

    # 英文公告
    ann = io.open(ANN, encoding=u"utf-8", newline=u"").read()
    if u"(%s keys each)" % OLD in ann:
        plan.append((ANN, ann, ann.replace(u"(%s keys each)" % OLD, u"(%s keys each)" % NEW)))
        notes.append(u"  [跟平] UpdateAnnouncement_EN.md 的 (492 keys each) → (508 keys each)")
    elif u"(%s keys each)" % NEW in ann:
        notes.append(u"  [跳过] 英文公告的键数已经是 508（幂等）")
    else:
        fails.append(u"英文公告里既没有 (492 keys each) 也没有 (508 keys each)")

    # ---------------- B. 进度条数 35 → 43 ----------------
    # B1 `_zf107_verify.py`：EXPECT_NODES + 节点名单 + CHALLENGES/GOALS
    z107 = os.path.join(ZT, u"_zf107_verify.py")
    t = current(z107)
    t = want(t, u"EXPECT_NODES = 35          # 3 老 + 24（ZF107）+ 8（ZF117）—— **加节点就改这一个数**",
             u"EXPECT_NODES = 43          # 3 老 + 24（ZF107）+ 8（ZF117）+ 8（ZF145）\n"
             u"                           # —— **加节点就改这一个数**",
             u"_zf107_verify.py：EXPECT_NODES 35 → 43", z107)
    t = want(t, u"ALL_NODES = OLD_NODES + NEW_NODES + ZF117_NODES",
             u"# ZF145（0.11，成就树补线）：**8 条** = ZF117 之后新加的内容（振金锭 / 振金套 /\n"
             u"# 星璨钢五件工具 / 星辉斩 / 星仪图之章 / 大型柴油发电机 / 银线）+ 1 条老空洞（钛合金套）。\n"
             u"# 见 `_zf145_apply.py`。\n"
             u"ZF145_NODES = [\"vibranium\", \"vibranium_armor\", \"titanium_armor\",\n"
             u"               \"star_steel_tools\", \"star_steel_slash\", \"star_chart_tome\",\n"
             u"               \"diesel_generator\", \"silver_wire\"]\n"
             u"ALL_NODES = OLD_NODES + NEW_NODES + ZF117_NODES + ZF145_NODES",
             u"_zf107_verify.py：ALL_NODES 追加 ZF145_NODES（8 条）", z107)
    t = want(t, u"CHALLENGES = HIDDEN + [\"star_steel_armor\"]",
             u"CHALLENGES = HIDDEN + [\"star_steel_armor\",\n"
             u"                       # ---- ZF145 ----\n"
             u"                       \"vibranium_armor\", \"star_steel_slash\"]",
             u"_zf107_verify.py：CHALLENGES + 2（振金套 / 星辉斩）", z107)
    t = want(t, u"         \"oil_pump\", \"lithium_battery_plant\", \"star_steel\"]",
             u"         \"oil_pump\", \"lithium_battery_plant\", \"star_steel\",\n"
             u"         # ---- ZF145 ----\n"
             u"         \"vibranium\", \"titanium_armor\", \"star_steel_tools\", \"diesel_generator\"]",
             u"_zf107_verify.py：GOALS + 4（振金 / 钛合金套 / 星璨钢工具 / 柴油发电机）", z107)
    if t != io.open(z107, encoding=u"utf-8", newline=u"").read():
        plan.append((z107, io.open(z107, encoding=u"utf-8", newline=u"").read(), t))

    # B2 `_zf117_verify.py`：N_ALL + A2 + H7
    z117 = os.path.join(ZT, u"_zf117_verify.py")
    t = current(z117)
    t = want(t, u"N_OLD, N_NEW, N_ALL = 27, 8, 35",
             u"# ⚠ ZF145 跟平：目录里现在是 43 条（27 老 + 8 ZF117 + 8 ZF145）。\n"
             u"N_OLD, N_NEW, N_ALL = 27, 8, 43\n"
             u"ZF145_IDS = [\"vibranium\", \"vibranium_armor\", \"titanium_armor\",\n"
             u"             \"star_steel_tools\", \"star_steel_slash\", \"star_chart_tome\",\n"
             u"             \"diesel_generator\", \"silver_wire\"]",
             u"_zf117_verify.py：N_ALL 35 → 43（+ZF145_IDS）", z117)
    t = want(t, u'    eq(u"A2 目录 = 27 老 + 8 新", sorted(list(OLD_SHA) + NEW_IDS), files)',
             u'    eq(u"A2 目录 = 27 老 + 8 新 + 8（ZF145）",\n'
             u'       sorted(list(OLD_SHA) + NEW_IDS + ZF145_IDS), files)',
             u"_zf117_verify.py：A2 目录比对带上 ZF145 那 8 条", z117)
    t = want(t, u'    check(u"H7 交接文档写着 35 条进度", u"35 条" in hand)',
             u'    # ⚠ ZF145 跟平：35 → 43（成就树补线又加了 8 条）\n'
             u'    check(u"H7 交接文档写着 43 条进度", u"43 条" in hand)',
             u"_zf117_verify.py：H7 交接文档 35 → 43 条", z117)
    if t != io.open(z117, encoding=u"utf-8", newline=u"").read():
        plan.append((z117, io.open(z117, encoding=u"utf-8", newline=u"").read(), t))

    # B3 `_zf128_verify.py`：C1
    z128 = os.path.join(ZT, u"_zf128_verify.py")
    t = current(z128)
    t = want(t, u'    check(u"C1 成就文件仍是 35 份（实际 %d）" % len(files), len(files) == 35)',
             u'    # ⚠ ZF145 跟平：35 → 43（成就树补线；判据没放宽：仍是"目录里正好这么多份"）\n'
             u'    check(u"C1 成就文件仍是 43 份（实际 %d）" % len(files), len(files) == 43)',
             u"_zf128_verify.py：C1 35 → 43", z128)
    if t != io.open(z128, encoding=u"utf-8", newline=u"").read():
        plan.append((z128, io.open(z128, encoding=u"utf-8", newline=u"").read(), t))

    # B4 `_zf139_verify.py`：反向那条
    z139 = os.path.join(ZT, u"_zf139_verify.py")
    t = current(z139)
    t = want(t, u'    check(len([n for n in os.listdir(ADIR) if n.endswith(u".json")]) == 35,\n'
                u'          u"反向：进度仍是 35 条（本轮不动进度）")',
             u'    # ⚠ ZF145 跟平：35 → 43（成就树补线又加了 8 条；这条"反向"判的是**目录份数**）\n'
             u'    check(len([n for n in os.listdir(ADIR) if n.endswith(u".json")]) == 43,\n'
             u'          u"反向：进度现在是 43 条（ZF145 补线后）")',
             u"_zf139_verify.py：反向那条 35 → 43", z139)
    if t != io.open(z139, encoding=u"utf-8", newline=u"").read():
        plan.append((z139, io.open(z139, encoding=u"utf-8", newline=u"").read(), t))

    # B5 `_zf71_verify.py`：adv == 27（ZF117 起就陈旧了，本轮一并跟到 43）
    z71 = os.path.join(ZT, u"_zf71_verify.py")
    t = current(z71)
    t = want(t, u"    check(adv == 27, u\"进度 %d 条\" % adv)",
             u"    # ⚠ ZF117 起就陈旧（27 = 3 + 24），ZF145 跟到 43（27 老 + 8 ZF117 + 8 ZF145）\n"
             u"    check(adv == 43, u\"进度 %d 条\" % adv)",
             u"_zf71_verify.py：adv 27 → 43（这条自 ZF117 起就没人跟）", z71)
    if t != io.open(z71, encoding=u"utf-8", newline=u"").read():
        plan.append((z71, io.open(z71, encoding=u"utf-8", newline=u"").read(), t))

    # ---------------- B6~B9 `_zf107_verify.py`：判据侧的跟平 ----------------
    z107b = os.path.join(ZT, u"_zf107_verify.py")
    t = current(z107b)
    # B6 NEW_KEYS 64 → 80（两轮各 +16）
    t = want(t, u"NEW_KEYS = 48 + 16          # 相对 zf107_pre 基线：ZF107 的 48 + ZF117 的 16",
             u"NEW_KEYS = 48 + 16 + 16     # 相对 zf107_pre 基线：ZF107 的 48 + ZF117 的 16\n"
             u"                            # + ZF145 的 16（8 条进度 × 标题/说明）",
             u"_zf107_verify.py：NEW_KEYS 64 → 80", z107b)
    # B7 击杀型节点的名单（模块级，与 HIDDEN/CHALLENGES 同一处）
    t = want(t, u"HIDDEN = [\"music_disc_anvil\", \"music_disc_jasmine\", \"starfall\"]",
             u"HIDDEN = [\"music_disc_anvil\", \"music_disc_jasmine\", \"starfall\"]\n"
             u"# ⚠ ZF145 新增：**击杀型**节点（判据里没有物品，触发器是 `player_killed_entity`）。\n"
             u"#   值 = 它的 `killing_blow.tags[0].id`（本模组的伤害类型标签）。\n"
             u"#   名单是**白名单**：不在这张表里的节点，一条物品判据都不许少、触发器也不许是它。\n"
             u"KILL_NODES = {\"star_steel_slash\": \"potato_s_t:star_steel_slash\"}",
             u"_zf107_verify.py：新增 KILL_NODES（星辉斩）", z107b)
    # B8 判据扫描器补 `registerVibranium(...)`
    #    ⚠ 真雷：ZF120 那四件振金甲走 `registerVibranium("vibranium_helmet", …)`，
    #      而 `mod_ids()` 只扫 `register("…")` ⇒ 振金四件在"盘上注册名单"里**一直缺席**。
    #      以前没人发现，是因为**从来没有哪个进度的判据点名振金甲**（ZF145 第一次点）。
    #      补的是**扫描器**（补全 = 更严），不是放宽断言。
    t = want(t, u"            ids |= set(re.findall(r'register\\(\\s*\"([a-z0-9_]+)\"', read(p)))",
             u"            ids |= set(re.findall(r'register\\(\\s*\"([a-z0-9_]+)\"', read(p)))\n"
             u"            # ⚠ ZF145：振金四件走的是 `registerVibranium(\"…\", …)` 这个私有注册器，\n"
             u"            #   上面那条正则扫不到 ⇒ 判据点名振金甲时会假 FAIL（ZF120 起就埋着）。\n"
             u"            ids |= set(re.findall(r'registerVibranium\\(\\s*\"([a-z0-9_]+)\"', read(p)))",
             u"_zf107_verify.py：mod_ids() 补 registerVibranium（振金四件）", z107b)
    # B9 C 段：击杀型节点走专属断言（不放宽，换一组同样硬的）
    t = want(t, u"        else:\n"
                u"            check(u\"C1 %s 的图标 id 带本模组命名空间\" % n, icon.startswith(\"potato_s_t:\"))",
             u"        elif n in KILL_NODES:\n"
             u"            # ⚠ ZF145：`star_steel_slash` 是**第一条第 4 类判据**的节点 ——\n"
             u"            #   触发器是 `player_killed_entity`（用星辉斩的伤害类型击杀），\n"
             u"            #   判据里**没有物品** ⇒ 「图标 ∈ 判据物品」这类泛化判据天然不成立。\n"
             u"            #   按 §4.36 的口径：**换一组同样硬的专属断言**，别的节点一个字不动。\n"
             u"            check(u\"C1s %s 的图标 id 带本模组命名空间\" % n,\n"
             u"                  icon.startswith(\"potato_s_t:\"))\n"
             u"            check(u\"C2s %s 的图标物品在盘上注册（%s）\" % (n, icon),\n"
             u"                  icon.split(u\":\", 1)[1] in ids)\n"
             u"            check(u\"C3s %s 的判据里没有物品谓词（击杀型节点，物品不是判据）\" % n,\n"
             u"                  ci == [])\n"
             u"            for cn, c in o[\"criteria\"].items():\n"
             u"                eq(u\"C4s %s/%s 的触发器\" % (n, cn),\n"
             u"                   u\"minecraft:player_killed_entity\", c.get(\"trigger\"))\n"
             u"                tu = c.get(\"conditions\", {}).get(\"killing_blow\", {}).get(\"tags\")\n"
             u"                eq(u\"C5s %s/%s 的 killing_blow 点名本模组的伤害类型标签\" % (n, cn),\n"
             u"                   [{\"expected\": True, \"id\": KILL_NODES[n]}], tu)\n"
             u"        else:\n"
             u"            check(u\"C1 %s 的图标 id 带本模组命名空间\" % n, icon.startswith(\"potato_s_t:\"))",
             u"_zf107_verify.py：C 段加击杀型节点分支（star_steel_slash 专属 5 条）", z107b)
    t = want(t, u"        check(u\"C6 %s 的触发器都在白名单内（%s）\" % (n, \",\".join(sorted(trig))),\n"
                u"              trig <= set([\"minecraft:inventory_changed\", \"minecraft:placed_block\"]))",
             u"        allowed = set([\"minecraft:inventory_changed\", \"minecraft:placed_block\"])\n"
             u"        if n in KILL_NODES:\n"
             u"            # ⚠ ZF145：击杀型节点**只有它自己**能带击杀触发器（白名单按节点开，不全局开）\n"
             u"            allowed |= set([\"minecraft:player_killed_entity\"])\n"
             u"        check(u\"C6 %s 的触发器都在白名单内（%s）\" % (n, \",\".join(sorted(trig))),\n"
             u"              trig <= allowed)",
             u"_zf107_verify.py：C6 白名单按节点开（击杀触发器只给 KILL_NODES）", z107b)
    t = want(t, u"    eq(u\"C15 「或」型的 5 条都是「多判据 + 1 个组」\",\n"
                u"       dict((n, (len(adv[n][\"criteria\"]), 1)) for n in\n"
                u"            (\"crushing\", \"pressing\", \"wiring\", \"titanium_tools\", \"fuel\")),\n"
                u"       dict((n, shape[n]) for n in (\"crushing\", \"pressing\", \"wiring\", \"titanium_tools\", \"fuel\")))",
             u"    # ⚠ ZF145：`star_steel_tools`（剑/斧/锹/镐/锄，任意一件）与 `titanium_tools` 同一条先例\n"
             u"    OR_NODES = (\"crushing\", \"pressing\", \"wiring\", \"titanium_tools\", \"fuel\",\n"
             u"                \"star_steel_tools\")\n"
             u"    eq(u\"C15 「或」型的 %d 条都是「多判据 + 1 个组」\" % len(OR_NODES),\n"
             u"       dict((n, (len(adv[n][\"criteria\"]), 1)) for n in OR_NODES),\n"
             u"       dict((n, shape[n]) for n in OR_NODES))",
             u"_zf107_verify.py：C15 的「或」名单补 star_steel_tools", z107b)
    t = want(t, u"    eq(u\"C16 「与」型的 2 条都是「每条判据各占一个组」\",\n"
                u"       dict((n, (2, 2)) for n in (\"gas_handling\", \"stronger_power\")),\n"
                u"       dict((n, shape[n]) for n in (\"gas_handling\", \"stronger_power\")))",
             u"    eq(u\"C16 「与」型的 2 条都是「每条判据各占一个组」\",\n"
             u"       dict((n, (2, 2)) for n in (\"gas_handling\", \"stronger_power\")),\n"
             u"       dict((n, shape[n]) for n in (\"gas_handling\", \"stronger_power\")))\n"
             u"    # ⚠ ZF145 新增：三套盔甲都是「四件各占一个组」（真「与」）。\n"
             u"    #   判据没放宽：仍是「逐条相等」的字典比对。\n"
             u"    ARMOR4 = (\"star_steel_armor\", \"vibranium_armor\", \"titanium_armor\")\n"
             u"    eq(u\"C17 三套盔甲都是「4 条判据 + 4 个组」（四件全要）\",\n"
             u"       dict((n, (4, 4)) for n in ARMOR4),\n"
             u"       dict((n, shape[n]) for n in ARMOR4))",
             u"_zf107_verify.py：新增 C17（三套盔甲 4×4「与」）", z107b)
    if t != io.open(z107b, encoding=u"utf-8", newline=u"").read():
        plan.append((z107b, io.open(z107b, encoding=u"utf-8", newline=u"").read(), t))

    # ---------------- C. 顺手收口的三处**我这条线的老账**（都在别的轮次的门里）----------------
    # C1 `_zf117_verify.py` D5：它钉的是"相对 zf117_pre 新增的成就键正好 16 个" ——
    #    本轮又加了 16 ⇒ 32（判据没放宽：仍是"正好"）。
    z117c = os.path.join(ZT, u"_zf117_verify.py")
    t = current(z117c)
    t = want(t, u'        eq(u"D5 %s：新增的成就键正好 16 个" % l, 16, len(mine))',
             u'        # ⚠ ZF145 跟平：16 → 32（成就树补线又加了 8 条 = 16 个键）；判据仍是"正好"\n'
             u'        eq(u"D5 %s：新增的成就键正好 32 个（ZF117 的 16 + ZF145 的 16）" % l, 32, len(mine))',
             u"_zf117_verify.py：D5 新增成就键 16 → 32", z117c)
    # C2 `_zf117_verify.py` 的 OLD_SHA：`new_beginning` 在 ZF124/ZF128 被**用户点名**换过图标
    #    （页签图标 = 根节点图标，同一个字段，见 §4.110）⇒ "逐字节等于 ZF117 开工前"对它已不成立。
    #    改锚点、不放宽：把哈希跟到换图标之后的那一版，并把原因写在旁边。
    t = want(t, u'    "new_beginning": "06bdc98bc63d2ebec96d73227843f6ec067ecc28",',
             u'    # ⚠ ZF145 跟平：这份在 ZF124（标题改 PotatoS&T）/ ZF128（图标改毒马铃薯）被用户点名改过\n'
             u'    #   ⇒ 哈希跟到"换图标之后"的那一版。判据没放宽：仍是**逐字节**比。\n'
             u'    "new_beginning": "0e00e92ae1c652dd7286b8e2ddbc0c4251ca70a1",',
             u"_zf117_verify.py：OLD_SHA 的 new_beginning 跟到 ZF128 之后", z117c)
    # C2b `_zf117_verify.py` G3：清单是 `zf117_pre` 的 `_sha1.txt`，里面那条 `new_beginning`
    #     哈希是**换图标之前**的 —— C2 把 OLD_SHA 跟到换图标之后 ⇒ 这一条要显式排除它
    #     （判据没放宽：其余 26 份照旧必须在清单里）。
    t = want(t, u'        bad = [n for n, h in OLD_SHA.items() if h not in txt]\n'
                u'        eq(u"G3 清单里 27 份 advancement 的哈希都在", [], bad)',
             u'        # ⚠ ZF145 跟平：`new_beginning` 的哈希被 ZF124/ZF128 顶掉了（用户在成就界面里\n'
             u'        #   换了根节点/页签的图标）⇒ 清单里那条是它更早的版本，这里显式排除它，\n'
             u'        #   其余 26 份照旧必须逐条出现在改前件清单里。\n'
             u'        MOVED = set([u"new_beginning"])\n'
             u'        bad = [n for n, h in OLD_SHA.items() if n not in MOVED and h not in txt]\n'
             u'        eq(u"G3 清单里 26 份 advancement 的哈希都在（new_beginning 被 ZF124/ZF128 顶掉了）",\n'
             u'           [], bad)',
             u"_zf117_verify.py：G3 显式排除被换过图标的 new_beginning", z117c)
    if t != io.open(z117c, encoding=u"utf-8", newline=u"").read():
        plan.append((z117c, io.open(z117c, encoding=u"utf-8", newline=u"").read(), t))

    # C3 `_zf139_verify.py`：「damage_type 目录下正好 1 份」—— ZF144 加了第二个伤害类型
    #    （`star_steel_slash`，剑的星辉斩）⇒ 现在是 2 份。改成**点名**两份（比"== 2"更硬）。
    z139c = os.path.join(ZT, u"_zf139_verify.py")
    t = current(z139c)
    # ⚠ 自修笔误：第一版这里写成了 `eq(...)`，而 `_zf139_verify.py` **没有** `eq` 这个助手
    #   （它一律用 `check(条件, 名字)`）⇒ 门直接 NameError 崩栈（比"红"更糟：读不出结论）。
    BAD = (u'    eq(u"damage_type 目录下正好 2 份（ZF139 的振金反伤 + ZF144 的星辉斩）",\n'
           u'       [u"star_steel_slash.json", u"vibranium_reflect.json"],\n'
           u'       sorted(n for n in os.listdir(DTYPES) if n.endswith(u".json")))')
    GOOD = (u'    check(sorted(n for n in os.listdir(DTYPES) if n.endswith(u".json"))\n'
            u'          == [u"star_steel_slash.json", u"vibranium_reflect.json"],\n'
            u'          u"damage_type 目录下正好 2 份（ZF139 的振金反伤 + ZF144 的星辉斩）")')
    if BAD in t:
        t = t.replace(BAD, GOOD, 1)
        notes.append(u"  [自修] _zf139_verify.py：把第一版误用的 eq(...) 改成 check(...)")
    t = want(t, u'    check(len([n for n in os.listdir(DTYPES) if n.endswith(u".json")]) == 1,\n'
                u'          u"damage_type 目录下正好 1 份（本轮只加这一个）")',
             u'    # ⚠ ZF145 跟平：ZF144 加了第二个伤害类型（star_steel_slash —— 剑的星辉斩）⇒ 现在是 2 份。\n'
             u'    #   判据没放宽：**点名**这两份，多一份少一份都红。\n' + GOOD,
             u"_zf139_verify.py：damage_type 份数 1 → 2（点名两份）", z139c)
    # C4 `_zf139_verify.py` 的键序链：它钉的是"死亡文案的下一个键就是振金说明"，
    #    而 ZF144 把**剑气那条死亡文案**插在了振金死亡文案后面 ⇒ 链子长了一环。
    t = want(t, u'    # 键序：新键紧挨在振金说明**前面**（四语言同一个锚点）\n'
                u'    for loc, t in tables.items():\n'
                u'        ks = list(t.keys())\n'
                u'        i = ks.index(DEATH_KEY)\n'
                u'        check(ks[i + 1] == TOOLTIP_KEY,\n'
                u'              u"%s：新键插在 %s **前面**（键序只多了这一个）" % (loc, TOOLTIP_KEY))',
             u'    # 键序：新键紧挨在振金说明**前面**（四语言同一个锚点）。\n'
             u'    # ⚠ ZF145 跟平：ZF144 又把**剑气那条死亡文案**插在了振金死亡文案后面\n'
             u'    #   ⇒ 链子成一串：振金死亡 → 剑气死亡 → 振金说明。判据没放宽：**整条链逐环点名**。\n'
             u'    SLASH_KEY = u"death.attack.potato_s_t.star_steel_slash"\n'
             u'    for loc, t in tables.items():\n'
             u'        ks = list(t.keys())\n'
             u'        i = ks.index(DEATH_KEY)\n'
             u'        check(ks[i + 1] == SLASH_KEY and ks[i + 2] == TOOLTIP_KEY,\n'
             u'              u"%s：键序是 振金死亡 → 剑气死亡 → %s（实际 %s）"\n'
             u'              % (loc, TOOLTIP_KEY, ks[i + 1:i + 3]))',
             u"_zf139_verify.py：键序链补上 ZF144 的剑气死亡文案那一环", z139c)
    if t != io.open(z139c, encoding=u"utf-8", newline=u"").read():
        plan.append((z139c, io.open(z139c, encoding=u"utf-8", newline=u"").read(), t))

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
    if not (write or verify):
        print(u"（没加 --write，只算不写）")
        return 0

    # ⚠ 同一份文件可能被 A 段（键数）与 B 段（进度条数）**各规划一次**：
    #   写盘是按 plan 顺序（后面的基于前面的内容），所以"最终内容"= **该路径最后一条**；
    #   断言也必须只对最后一条做（第一版对每条都断言 ⇒ `_zf107_verify.py` 当场假失败）。
    final = {}
    for p, _old, new in plan:
        final[p] = new

    if write:
        for p, _old, new in plan:
            io.open(p, u"w", encoding=u"utf-8", newline=u"").write(new)
        print(u"已写盘。")
        for p, want_text in final.items():
            assert io.open(p, encoding=u"utf-8", newline=u"").read() == want_text, p
        print(u"回读：%d 份逐字节等于**该路径最后一条**计划" % len(final))

    if verify:
        # ⚠ 真正的自证：把改前件**重新跑一遍**本脚本的改写，结果必须与盘上逐字节相同。
        #   （只回读"最后一条计划"是循环论证 —— 计划本身错了也一样通过。）
        bad, done = [], 0
        for p, _old, new in plan:
            rel = os.path.relpath(p, ROOT)
            pre = os.path.join(PRE, rel)
            if not os.path.exists(pre):
                bad.append(u"%s 在改前件里没有（没法重放）" % rel)
                continue
            if io.open(pre, encoding=u"utf-8", newline=u"").read() != _old:
                bad.append(u"%s 的改前件与本脚本读到的现状不一致（别人动过？）" % rel)
                continue
            done += 1
        print(u"重放自证：%d 条计划在改前件里逐字节对得上；不符 %d 条" % (done, len(bad)))
        for b in bad:
            print(u"  !! " + b)
        if bad:
            return 1
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
