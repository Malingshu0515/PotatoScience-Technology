# -*- coding: utf-8 -*-
u"""_zf137_tick5.py —— 用户改口：星璨钢头盔的夜视 **4 s → 5 s**

用户原话：「星璨钢头盔改成5s夜视」。

80 tick → **100 tick**（5 s × 20）。这不是新的一轮，所以**不占新号**：
改的是 ZF137 那一轮做过的东西，脚本名跟着那一轮（`_zf137_*`）。

**4 s → 5 s 只是换个数字，但它会牵动五处** —— 少改一处就是"游戏里 5 秒、说明里写 4 秒"：

  ① `ModArmorSet.java` 的常量（`HELMET_NIGHT_VISION_TICKS = 80` → `100`）与它周围的注释；
  ② 类注释里那张表（"每次 4 s"）；
  ③ 四语言 `tooltip.potato_s_t.star_steel_set` 里那句「每次 4 秒」（**只改值、不加键**）；
  ④ 本轮探针 `_zf137_verify.py` 的 `SECONDS`（它自己算 TICKS = SECONDS × 20，
     所以真正的判据只有 SECONDS 一个数字 —— 这就是"期望值不抄被测常量"的好处，§4.27）；
  ⑤ 反证刀里两处**锚点**（K1 的 `= 80;`、K8 的「每次 4 秒」）—— 锚点不跟着走，刀就成了假绿。

跑法：
    python build/zftools/_zf137_tick5.py            # 只体检
    python build/zftools/_zf137_tick5.py --write
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
SRC = os.path.join(PROJ, r"src\main\java\com\potatost\mod")
LANG = os.path.join(PROJ, r"src\main\resources\assets\potato_s_t\lang")
ZT = os.path.join(PROJ, "build", "zftools")
ARCH = os.path.join(PROJ, "docs", "开发档案.md")

OLD_S, NEW_S = u"4", u"5"
OLD_T, NEW_T = u"80", u"100"

# (文件, [(原文, 改成)], 说明)
PLAN = [
    (os.path.join(SRC, u"ModArmorSet.java"), [
        (u"星璨钢**头盔**给的夜视时长（tick）：80 = **4 s**",
         u"星璨钢**头盔**给的夜视时长（tick）：100 = **5 s**"),
        (u"最后一次给的那 4 s 到点自己就没了", u"最后一次给的那 5 s 到点自己就没了"),
        (u"（所以摘头盔后最多再亮 4 s，这与用户给的\"4s\"同时是**单次时长**和**退场时间**）。",
         u"（所以摘头盔后最多再亮 5 s，这与用户给的\"5s\"同时是**单次时长**和**退场时间**）。"),
        (u"：80 tick 的效果在剩 40 tick 时被续上", u"：100 tick 的效果在剩 40 tick 时被续上"),
        (u"    private static final int HELMET_NIGHT_VISION_TICKS = 80;",
         u"    private static final int HELMET_NIGHT_VISION_TICKS = 100;"),
        (u"// ---- 只头盔：夜视 I（4 s，穿着就一直续）----",
         u"// ---- 只头盔：夜视 I（5 s，穿着就一直续）----"),
        (u"<tr><td><b>只头盔</b>（ZF135 加的那条）</td><td>夜视 I，每次 4 s、穿着就一直续（不分昼夜与维度）</td></tr>",
         u"<tr><td><b>只头盔</b>（ZF137 加的那条）</td><td>夜视 I，每次 5 s、穿着就一直续（不分昼夜与维度）</td></tr>"),
    ], u"常量 + 注释 + 类注释表"),
    (os.path.join(SRC, u"ModArmorMaterials.java"), [
        (u"0.11 ZF135 的\"夜视 I\"那条用", u"0.11 ZF137 的\"夜视 I\"那条用"),
    ], u"判据注释里的轮次号（上轮改号时漏了这一处）"),
    # ⚠ 这四条的锚点**不是**我当初写的那句了：翻译线后来又重写了一遍星璨钢说明
    #   （「星璨钢套：与夜同频。」那套文风），夜视那句被改写成
    #   「夜视 I，每次 4 秒，戴着便一直续」。以**盘上现文**为锚点，别照抄旧句子。
    (os.path.join(LANG, u"zh_cn.json"), [(u"夜视 I，每次 4 秒，戴着便一直续", u"夜视 I，每次 5 秒，戴着便一直续")], u"zh"),
    (os.path.join(LANG, u"en_us.json"), [(u"Night Vision I, 4 s at a time", u"Night Vision I, 5 s at a time")], u"en"),
    (os.path.join(LANG, u"ja_jp.json"), [(u"暗視 I、1 回 4 秒", u"暗視 I、1 回 5 秒")], u"ja"),
    (os.path.join(LANG, u"ru_ru.json"), [(u"Ночное зрение I, по 4 с,", u"Ночное зрение I, по 5 с,")], u"ru"),
    (os.path.join(ZT, u"_zf137_verify.py"), [
        (u"SECONDS = 4", u"SECONDS = 5"),
        (u"# 4 s = 80 tick", u"# 5 s = 100 tick"),
        (u"夜视 I / 4 s）的常驻校验", u"夜视 I / 5 s）的常驻校验"),
        (u"1级 4s」", u"1级 5s（后来改口成 5s）」"),
        (u"③ **4 s 是\"单次时长 + 退场时间\"**：给 80 tick", u"③ **5 s 是\"单次时长 + 退场时间\"**：给 100 tick"),
        (u"亮 4 秒、黑 4 秒", u"亮 5 秒、黑 5 秒"),
        (u"================ ① 效果本身：夜视 I / 4 s ================",
         u"================ ① 效果本身：夜视 I / 5 s ================"),
        (u"# ★ 调用点取证：ensure(player, NIGHT_VISION, 0, 80, 40)",
         u"# ★ 调用点取证：ensure(player, NIGHT_VISION, 0, 100, 40)"),
    ], u"探针的期望值（只有 SECONDS 一个数字）"),
    (os.path.join(ZT, u"_zf137_falsify.py"), [
        (u"u\"K1 夜视时长 80 → 400（4 s 变成 20 s）\"", u"u\"K1 夜视时长 100 → 500（5 s 变成 25 s）\""),
        (u"u\"HELMET_NIGHT_VISION_TICKS = 80;\", u\"HELMET_NIGHT_VISION_TICKS = 400;\"",
         u"u\"HELMET_NIGHT_VISION_TICKS = 100;\", u\"HELMET_NIGHT_VISION_TICKS = 500;\""),
        (u"K1 时长 80 → 400（4 s 变成 20 s）", u"K1 时长 100 → 500（5 s 变成 25 s）"),
        # ⚠ K8 的锚点也得跟着**翻译线重写后的现文**走 —— 它原来钉的是我当初写的那句
        #   （「头盔还额外给夜视 I：每次 4 秒，戴着就一直续。」），翻译线把说明整段重写之后
        #   那句已经不在盘上了 ⇒ 这一刀会因为"锚点命中 0 次"变成**假绿**（刀还在，咬不到东西）。
        (u"u\"头盔还额外给夜视 I：每次 4 秒，戴着就一直续。\"", u"u\"夜视 I，每次 5 秒，戴着便一直续。\""),
    ], u"反证刀的两处锚点 + 名字（K8 跟着翻译线的新文风）"),
]

fails = []


def main(argv):
    write = u"--write" in argv
    for path, pairs, why in PLAN:
        name = os.path.basename(path)
        text = io.open(path, encoding="utf-8").read()
        miss = [a for a, _b in pairs if a not in text]
        # K8 那条只是"重写一次同名"，允许命中 0 次（它本来就是占位）
        miss = [m for m in miss if u"K8 zh_cn" not in m]
        if miss:
            for m in miss:
                fails.append(u"%s：锚点没命中 —— %s" % (name, m[:70]))
            print(u"  [FAIL] %s：%d 个锚点没命中" % (name, len(miss)))
            continue
        new = text
        n = 0
        for a, b in pairs:
            if a not in new:
                continue
            if new.count(a) != 1:
                fails.append(u"%s：锚点 %s 命中 %d 次" % (name, a[:40], new.count(a)))
                continue
            new = new.replace(a, b)
            n += 1
        try:
            if name.endswith(u".py"):
                compile(new, path, "exec")
        except SyntaxError as e:
            fails.append(u"%s 改完语法坏：%s" % (name, e))
            continue
        print(u"  [%s] %-24s %d 处（%s）" % (u"改" if write else u"将改", name, n, why))
        if write:
            io.open(path, "w", encoding="utf-8", newline=u"").write(new)

    # 档案那一节：把"4 s / 80 tick"跟平，并留一句"用户改口"的记号
    text = io.open(ARCH, encoding="utf-8").read()
    i = text.find(u"### ZF137（0.11）星璨钢头盔给夜视 I")
    j = text.find(u"### ZF13", i + 10)
    if i < 0:
        fails.append(u"档案里找不到 ZF137 那一节")
    else:
        end = j if j > 0 else len(text)
        sec = text[i:end]
        pairs = [
            (u"星璨钢头盔给夜视 I（4 s）", u"星璨钢头盔给夜视 I（**5 s**）"),
            (u"「星璨钢头盔穿戴加个夜视效果 1级 4s」",
             u"「星璨钢头盔穿戴加个夜视效果 1级 4s」→ 随后改口「星璨钢头盔改成5s夜视」"),
            (u"| 4 s 是什么意思 | **单次时长 80 tick**", u"| 5 s 是什么意思 | **单次时长 100 tick**"),
            (u"摘下来最多再亮 4 s", u"摘下来最多再亮 5 s"),
            (u"（效果, 等级 0, 时长 80, 余量 40）", u"（效果, 等级 0, 时长 100, 余量 40）"),
            (u"把头盔**摘下来** → 最多再亮 **4 秒**", u"把头盔**摘下来** → 最多再亮 **5 秒**"),
            (u"80→400 / 等级 0→1", u"100→500 / 等级 0→1"),
        ]
        n = 0
        for a, b in pairs:
            if a in sec:
                sec = sec.replace(a, b)
                n += 1
        print(u"  [%s] 开发档案.md：那一节 %d 处" % (u"改" if write else u"将改", n))
        if write:
            io.open(ARCH, "w", encoding="utf-8", newline=u"").write(text[:i] + sec + text[end:])

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
