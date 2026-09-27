# -*- coding: utf-8 -*-
r'''_zf147_version.py —— **版本线 0.11 → 0.12**（用户原话：「从现在开始都是 0.12 版本
   无论是小更新还是修bug 麻烦在日志写一下」）。

一次做完五件事（含**动手前的备份**，§10）：
  ① 备份 → `C:\PotatoST救援\zf147_pre`（本脚本第一步就做，且目录已存在就停手）；
  ② `gradle.properties` 的 `mod_version=0.11` → `0.12`（**版本号只有这一处**）；
  ③ 档案：§5 加 ZF147 行 + §9 加 ZF147（0.12）小节 + §4.150 **日志纪律**（每轮/每个小修都要留一条）；
  ④ 交接：标题 0.11 → 0.12、§1 加一行"版本线"、§6 加第 28 条；
  ⑤ 三份**断言 mod_version** 的门跟平（`_zf73/_zf78/_zf79_verify.py` 里那三条"仍是 0.11"）。

⚠ 不动的东西：所有历史脚本/档案里的 "0.11" 字样（那是记录，§4.132：只碰自己点名的清单）；
  `release\PotatoST-0.11.jar` 的路径引用（成品还是那一份，等打包轮出 0.12）。

跑法：python build\zftools\_zf147_version.py [--write]
'''
import hashlib
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
DEST = os.path.join(r"C:\PotatoST救援", "zf147_pre")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
PROPS = os.path.join(ROOT, "gradle.properties")

FILES = [r"gradle.properties", r"docs\开发档案.md", r"docs\多会话协作交接.md",
         r"docs\UpdateAnnouncement_EN.md",
         r"build\zftools\_zf73_verify.py", r"build\zftools\_zf78_verify.py",
         r"build\zftools\_zf79_verify.py"]

ROW = r'''| ZF147 | ⚠ **没有备份根也要有账**：本轮是**一个常量 + 四份文档**的改动，改前件只列**六份**（`gradle.properties` / 三份文档 / 三份断言 `mod_version` 的门 —— 见 `zf147_pre\_sha1.txt`） | 0.12：**版本线从 0.11 抬到 0.12**（用户原话「从现在开始都是 0.12 版本 无论是小更新还是修bug 麻烦在日志写一下」）。① `gradle.properties` 的 `mod_version=0.11` → **0.12**（**全工程只有这一处**版本号，`neoforge.mods.toml` 引用 `${mod_version}`）；② 立 **§4.150 日志纪律**：**从 ZF147 起，每一轮改动（含小修 / 修 bug）都必须在档案 §5 留一行、在英文公告留一条**，版本号一律写 0.12；③ 三份断言 `mod_version` 的老门（`_zf73/_zf78/_zf79_verify.py` 里"仍是 0.11 / 本轮没有 0.12 任务"）跟着抬到 0.12 —— 判据没放宽（仍是逐字比那一个常量）；④ **`release\PotatoST-0.11.jar` 不动**（成品还是那一份，0.12 的成品等下一次打包；那 40 多份引用它的门届时一起跟） | 见 §9 ｜ 见 §4.150 |
'''

SEC4 = r'''### 4.150 【规矩】版本线与**日志纪律**：从 0.12 起，**每一轮改动都要留一条**（0.11→0.12 ZF147）

用户原话：「**从现在开始都是 0.12 版本 无论是小更新还是修bug 麻烦在日志写一下**」。

落成三条硬规矩，以后每轮开工先看这里：

1. **版本线是 0.12**。版本号**全工程只有一处**：`gradle.properties` 的 `mod_version`；
   `src\main\resources\META-INF\neoforge.mods.toml` 引用 `${mod_version}`，产物是
   `build\libs\potato_s_t-<mod_version>.jar`。谁要再抬版本，只改那一处 + 本节的记录。
2. **日志纪律**：**每一轮改动都记两条**（哪怕只是修一个 bug / 改一个常量）——
   ① `docs\开发档案.md` §5 表格加一行（本轮号 + 备份根 + 做了什么 + 指到 §9/§4）；
   ② `docs\UpdateAnnouncement_EN.md` 末尾加一条（玩家看得懂的话）。
   §9 的详细小节按老规矩：改动大的、有用户要实测的必须写；一行常量级的可以只在 §5 记一行。
3. **§9 小节的版本标签**用**当时的版本线**：`### ZFnnn（0.12）…`。
   ⚠ 历史小节（ZF146 及以前）里写的 `（0.11）` **是记录，不许批量改**（§4.132 同一条）——
   几十份老门正拿 `### ZFnnn（0.11）` 当锚点钉着它们。

⚠ 本轮的边界：`release\PotatoST-0.11.jar`（当前成品）**不动**；0.12 的成品等**下一次打包**，
那 40 多份把 `release\PotatoST-0.11.jar` 写死在路径里的门（`_zf73/_zf74/_zf75/_zf78/_zf79/_zf80`
`_zf81/_zf82/_zf83/_zf84/_zf85/_zf86/_zf88/_zf89/_zf90/_zf91/_zf93/_zf94/_zf95/_zf96/_zf97`
`_zf98/_zf99/_zf100/_zf101/_zf102/_zf117` …）**由打包轮一起跟到 0.12**，并顺带作废
`303c5d46…` / `2c738238…` 那些老哈希链。
'''

SEC9 = r'''### ZF147（0.12）版本线抬到 0.12 + 立日志纪律

用户原话：「从现在开始都是 0.12 版本 无论是小更新还是修bug 麻烦在日志写一下」。

- **改了什么**：`gradle.properties` 的 `mod_version=0.11` → `0.12`（一行）；
  档案立 **§4.150**（版本线 + 日志纪律）；**没有动任何 Java / 资源 / 配方 / 贴图**。
- **从这一刻起的规矩**（§4.150）：每一轮改动都要在 §5 留一行 + 英文公告留一条，
  版本号写 0.12；§9 详细小节按改动大小决定要不要写。
- **没动的**：`release\PotatoST-0.11.jar` 与它的 `.sha1`（成品还是那一份）；
  40 多份把成品路径写死的门等**打包轮**一起跟。
- 自证：`_zf73/_zf78/_zf79_verify.py` 里那三条"mod_version 仍是 0.11"已跟到 0.12，
  判据没放宽（仍是逐字比那一个常量）。
'''

HAND_VERSION = u'''| **版本线** | **0.12**（ZF147 起；用户点名：「从现在开始都是 0.12 版本 无论是小更新还是修bug 麻烦在日志写一下」）。版本号**只有一处**：`gradle.properties` 的 `mod_version`；⚠ **每一轮改动都要在档案 §5 + 英文公告各留一条**（§4.150 日志纪律） | 主项目线 |
'''

ANN_NOTE = u'''
---

## Version line: 0.11 → 0.12 (ZF147)

The mod version is now **0.12**. Every change from here on — including small fixes — gets an entry in
this file and a row in the development log, as requested.

⚠ The downloadable jar currently on disk is still the **0.11** build (`release/PotatoST-0.11.jar`); the
first 0.12 build will be produced by the next packaging pass, and all content described above carries
over unchanged.
'''


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def backup():
    if os.path.exists(DEST):
        print(u"!! 备份根已存在，停手：%s" % DEST)
        return False
    os.makedirs(DEST, exist_ok=True)
    rows = []
    for rel in FILES:
        src = os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            print(u"  [警告] 不在盘上：%s" % rel)
            continue
        dst = os.path.join(DEST, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        assert sha1(src) == sha1(dst), rel
        rows.append(u"%s  %s" % (sha1(src), rel.replace(u"\\", u"/")))
    io.open(os.path.join(DEST, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"").write(u"\n".join(rows) + u"\n")
    io.open(os.path.join(DEST, u"_说明.txt"), "w", encoding="utf-8", newline=u"").write(
        u"ZF147 改前件（版本线 0.11 → 0.12 + 日志纪律）\n\n份数：%d\n"
        u"⚠ 本轮**没有探针**（只改一个常量 + 文档），所以 PotatoST.java 不在清单里。\n" % len(rows))
    print(u"  [备份] %s（%d 份 + _sha1.txt）" % (DEST, len(rows)))
    return True


def main(argv):
    write = u"--write" in argv
    fails, notes, plan = [], [], []

    if write and not backup():
        return 1
    if not write:
        print(u"（没加 --write：只算不写、也不建备份根）")

    # ---- ① gradle.properties ----
    t = io.open(PROPS, encoding="utf-8", newline="").read()
    if u"mod_version=0.12" in t:
        notes.append(u"  [跳过] gradle.properties 已经是 0.12（幂等）")
    elif t.count(u"mod_version=0.11") == 1:
        plan.append((PROPS, t, t.replace(u"mod_version=0.11", u"mod_version=0.12", 1)))
        notes.append(u"  [改] gradle.properties：mod_version=0.11 → 0.12")
    else:
        fails.append(u"gradle.properties 里 `mod_version=0.11` 命中 %d 次"
                     % t.count(u"mod_version=0.11"))

    # ---- ② 档案 ----
    doc = io.open(DOC, encoding="utf-8", newline="").read()
    if u"| ZF147 |" in doc:
        notes.append(u"  [跳过] 档案已经有 ZF147 行（幂等）")
    else:
        lines = doc.split(u"\n")
        rows = [i for i, l in enumerate(lines) if l.startswith(u"| ZF14")]
        if not rows:
            fails.append(u"档案 §5 找不到 `| ZF14x |` 行")
        else:
            lines.insert(rows[-1] + 1, ROW.rstrip(u"\n"))
            doc = u"\n".join(lines)
            notes.append(u"  [插] 档案 §5 加 ZF147 行")
    for anchor, block, label in ((u"## 7. 权威情报来源", SEC4, u"档案 §4 加 4.150"),
                                 (u"## 10. 备份策略", SEC9, u"档案 §9 加 ZF147 小节")):
        if block.strip().split(u"\n")[0] in doc:
            notes.append(u"  [跳过] %s（幂等）" % label)
        elif doc.count(anchor) != 1:
            fails.append(u"%s：锚点命中 %d 次" % (label, doc.count(anchor)))
        else:
            doc = doc.replace(anchor, block + anchor, 1)
            notes.append(u"  [插] " + label)
    plan.append((DOC, io.open(DOC, encoding="utf-8", newline="").read(), doc))

    # ---- ③ 交接 ----
    hand = io.open(HAND, encoding="utf-8", newline="").read()
    if u"# 多会话协作交接：PotatoS&T 0.12" in hand:
        notes.append(u"  [跳过] 交接标题已经是 0.12（幂等）")
    elif hand.count(u"# 多会话协作交接：PotatoS&T 0.11") == 1:
        hand = hand.replace(u"# 多会话协作交接：PotatoS&T 0.11",
                            u"# 多会话协作交接：PotatoS&T 0.12", 1)
        notes.append(u"  [改] 交接标题 0.11 → 0.12")
    else:
        fails.append(u"交接标题锚点命中 %d 次" % hand.count(u"# 多会话协作交接：PotatoS&T 0.11"))
    if u"| **版本线** |" in hand:
        notes.append(u"  [跳过] 交接已有版本线那一行（幂等）")
    elif hand.count(u"| 语言键数 | **508 键 × 4**") == 1:
        hand = hand.replace(u"| 语言键数 | **508 键 × 4**",
                            HAND_VERSION + u"| 语言键数 | **508 键 × 4**", 1)
        notes.append(u"  [插] 交接 §1 加「版本线」一行")
    else:
        fails.append(u"交接 §1 的语言键数锚点命中 %d 次"
                     % hand.count(u"| 语言键数 | **508 键 × 4**"))
    NEW28 = (u"28. **ZF147 的账（版本线 0.11 → 0.12）**：① 用户原话「从现在开始都是 0.12 版本\n"
             u"    无论是小更新还是修bug 麻烦在日志写一下」⇒ `gradle.properties` 的 `mod_version`\n"
             u"    抬到 **0.12**（全工程唯一一处版本号），并立 **§4.150 日志纪律**：\n"
             u"    **每一轮改动（含小修 / 修 bug）都要在档案 §5 + 英文公告各留一条**，版本号写 0.12。\n"
             u"    ② ⚠ **成品没换**：`release\\PotatoST-0.11.jar` 还是那一份（0.12 的成品等下一次打包）；\n"
             u"    40 多份把 `PotatoST-0.11.jar` 写死在路径里的门**由打包轮一起跟到 0.12**。\n"
             u"    ③ 三份断言 `mod_version` 的老门（`_zf73/_zf78/_zf79_verify.py` 的「仍是 0.11 /\n"
             u"    本轮没有 0.12 任务」）已跟平到 0.12，判据没放宽。\n\n")
    if u"28. **ZF147 的账" in hand:
        notes.append(u"  [跳过] 交接 §6 已有第 28 条（幂等）")
    elif hand.count(u"24. **⚠ ZF139 的归档探针与它自己的报告对不上") == 1:
        hand = hand.replace(u"24. **⚠ ZF139 的归档探针与它自己的报告对不上",
                            NEW28 + u"24. **⚠ ZF139 的归档探针与它自己的报告对不上", 1)
        notes.append(u"  [插] 交接 §6 加第 28 条")
    else:
        fails.append(u"交接 §6 的第 24 条锚点命中 %d 次"
                     % hand.count(u"24. **⚠ ZF139 的归档探针与它自己的报告对不上"))
    plan.append((HAND, io.open(HAND, encoding="utf-8", newline="").read(), hand))

    # ---- ④ 英文公告 ----
    ann = io.open(ANN, encoding="utf-8", newline="").read()
    if u"Version line: 0.11" in ann or u"(ZF147)" in ann:
        notes.append(u"  [跳过] 公告已有 0.12 那一节（幂等）")
    else:
        if ann.count(u"# PotatoS&T — 0.11 Content Overview & Update Notes") != 1:
            fails.append(u"公告标题锚点命中 %d 次"
                         % ann.count(u"# PotatoS&T — 0.11 Content Overview & Update Notes"))
        else:
            ann = ann.replace(u"# PotatoS&T — 0.11 Content Overview & Update Notes",
                              u"# PotatoS&T — 0.12 Content Overview & Update Notes", 1)
            notes.append(u"  [改] 公告标题 0.11 → 0.12")
        ann = ann.rstrip(u"\n") + u"\n" + ANN_NOTE
        notes.append(u"  [插] 公告末尾补「版本线 0.11 → 0.12」一节")
    plan.append((ANN, io.open(ANN, encoding="utf-8", newline="").read(), ann))

    # ---- ⑤ 三份门里的 mod_version 断言 ----
    for fn, old, new in (
        (u"_zf73_verify.py",
         u'check(u"C1 mod_version = 0.11", re.search(r"mod_version=0\\.11", props) is not None)',
         u'# ⚠ ZF147：用户把版本线抬到 0.12（「从现在开始都是 0.12 版本」）⇒ 判据跟到 0.12；\n'
         u'#   判据没放宽：仍是逐字比 `mod_version` 那一个常量。\n'
         u'check(u"C1 mod_version = 0.12", re.search(r"mod_version=0\\.12", props) is not None)'),
        (u"_zf78_verify.py",
         u'check(u"mod_version 仍是 0.11（本轮没有 0.12 任务）",',
         u'# ⚠ ZF147：0.12 任务来了（用户点名）⇒ 跟到 0.12。\n'
         u'check(u"mod_version 现在是 0.12（ZF147 抬的版本线）",'),
        (u"_zf79_verify.py",
         u'check(u"mod_version 仍是 0.11（本轮没有 0.12 任务）",',
         u'# ⚠ ZF147：0.12 任务来了（用户点名）⇒ 跟到 0.12。\n'
         u'check(u"mod_version 现在是 0.12（ZF147 抬的版本线）",')):
        p = os.path.join(ZT, fn)
        s = io.open(p, encoding="utf-8", newline="").read()
        if u"0.12" in s and old not in s:
            notes.append(u"  [跳过] %s 的 mod_version 断言已经是 0.12（幂等）" % fn)
            continue
        if s.count(old) != 1:
            fails.append(u"%s：锚点命中 %d 次" % (fn, s.count(old)))
            continue
        plan.append((p, s, s.replace(old, new, 1)))
        notes.append(u"  [改] %s 的 mod_version 断言 0.11 → 0.12" % fn)

    print(u"")
    for n in notes:
        print(n)
    print(u"")
    if fails:
        print(u"失败项 = %d（一个字节都没写）" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    print(u"待写：%d 份" % len(plan))
    if not write:
        print(u"（没加 --write，只算不写）")
        return 0
    final = {}
    for p, _o, new in plan:
        final[p] = new
    for p, _o, new in plan:
        io.open(p, u"w", encoding=u"utf-8", newline=u"").write(new)
    for p, want in final.items():
        assert io.open(p, encoding=u"utf-8", newline=u"").read() == want, p
    print(u"已写盘；回读 %d 份逐字节一致" % len(final))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
