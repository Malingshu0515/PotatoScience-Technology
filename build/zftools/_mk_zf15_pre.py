# -*- coding: utf-8 -*-
"""_mk_zf15_pre.py —— 补建 zf15_pre，并对每个文件标注**来源**与**校验结果**（0.10 ZF15）

**背景**：本阶段（加锂矿）我又重犯了 ZF14 的流程错误 —— 代码先改完，才想起建 pre 备份。
所以 zf15_pre 里的文件不是"改前抓拍"，而是事后按来源分三级补出来的：

| 来源 | 文件 | 凭什么可信 |
|---|---|---|
| ① B 批 release jar | 4 语言 + 3 标签 + 3 个 c: 标签 | jar 的 SHA1 还是 CF63C5C0…，且里面**没有任何** lithium_ore/raw_lithium 条目 ⇒ 它就是改前的那一份 |
| ② zf12_project 全量快照 | PotatoSTOres.java / ModItems.java | 差分证明：两者差异**只有本阶段新增的行** |
| ③ 减法重建 | MicroCrusherRecipes.java / GenCommonTags.py | 没有可用的改前源码快照（zf12_project 那份**早于 ZF13**，差分当场抓出 8 行 ZF13 代码会被误删），所以只能按"删掉我加的那几段"重建；重建后另有断言：ZF13 的标签规则必须还在 |

**这个脚本的价值就在"抓出第 ③ 类"**：第一次跑的时候，MicroCrusherRecipes.java 用的就是 zf12_project 那份，
差分报出 8 行预期外的消失行（`Map.copyOf(build())`、`⑤ 绿宝石矿石（浅层 / 深层）` 等 = ZF13 之前的旧写法）。
要是当时"复制完就算"，这份备份会在将来回退时**静默抹掉 ZF13 的工作**。

跑法：
    python build/zftools/_mk_zf15_pre.py --check      # 只差分，不落盘
    python build/zftools/_mk_zf15_pre.py              # 全部通过才写 zf15_pre
"""
import difflib
import hashlib
import io
import os
import re
import shutil
import sys
import zipfile

PROJ = "E:\\PotatoST"
BACKUP_ROOT = os.path.join("C:\\Users\\Administrator\\Desktop", "PotatoST救援_20260917_183054")
SNAP = os.path.join(BACKUP_ROOT, "zf12_project")
OUT = os.path.join(BACKUP_ROOT, "zf15_pre")
JAR = os.path.join(PROJ, "release", "PotatoST-0.10.jar")
JAR_SHA1_EXPECT = "CF63C5C0A53C941C2BAF6A27688F65C0CF2A12F8"

# ---- 来源 ①：从 B 批 jar 里按原样取出（jar 内路径 -> 备份文件名）----
FROM_JAR = {
    "assets/potato_s_t/lang/zh_cn.json": "zh_cn.json",
    "assets/potato_s_t/lang/en_us.json": "en_us.json",
    "assets/potato_s_t/lang/ja_jp.json": "ja_jp.json",
    "assets/potato_s_t/lang/ru_ru.json": "ru_ru.json",
    "data/potato_s_t/neoforge/biome_modifier/potato_st_ores.json": "potato_st_ores.json",
    "data/minecraft/tags/block/needs_iron_tool.json": "needs_iron_tool.json",
    "data/minecraft/tags/block/mineable/pickaxe.json": "pickaxe.json",
    "data/c/tags/item/raw_materials.json": "raw_materials.json",
    "data/c/tags/item/ores.json": "ores.json",
    "data/c/tags/block/ores_in_ground/stone.json": "stone.json",
}

# ---- 来源 ②：zf12_project 快照（差分已证明是改前版本）----
FROM_SNAPSHOT = {
    "PotatoSTOres.java": r"src\main\java\com\potatost\mod\PotatoSTOres.java",
    "ModItems.java": r"src\main\java\com\potatost\mod\ModItems.java",
}

# ---- 来源 ③：减法重建。cuts = (起点行标记, 终点行标记)，删 [起点, 终点) 之间的行 ----
RECONSTRUCT = {
    "MicroCrusherRecipes.java": {
        "path": r"src\main\java\com\potatost\mod\MicroCrusherRecipes.java",
        # 本阶段改前该文件**正好 193 行**（本次会话开头 read 过，是硬数字）。
        # 行数对不上就说明有行被多删/少删 —— 这条断言才是真正拦住上面那个 bug 的。
        "expected_lines": 193,
        "cuts": [
            ("import net.minecraft.core.registries.Registries;",
             "import net.minecraft.tags.TagKey;"),
            ("###AFTER###private static final int SEC = 20;",
             '###INCL###ResourceLocation.fromNamespaceAndPath("c", "raw_materials/lithium"));'),
            ("// ⑦ 粗锂", "        table = Map.copyOf(m);"),
        ],
        # 重建完必须仍然存在的东西（证明没把 ZF13 的活儿删掉）
        "must_keep": [
            "record TagRule",
            "Tags.Items.GEMS_AMETHYST",
            "Tags.Items.GEMS_QUARTZ",
            "Tags.Items.ORES_EMERALD",
            "Tags.Items.ORES_DIAMOND",
            "private static List<TagRule> tagRules()",
            "stack.is(rule.tag())",
            # ↓ 这两行是"终点标记写错"的直接受害者，专门盯住
            "import net.minecraft.tags.TagKey;",
            "        table = Map.copyOf(m);",
            "        tagRules = List.copyOf(tags);",
        ],
        "must_lose": ["RAW_MATERIALS_LITHIUM", "lithium"],
    },
    "GenCommonTags.py": {
        "path": r"build\zftools\GenCommonTags.py",
        "expected_lines": 140,
        "cuts": [("# 锂（0.10 ZF15）", '###INCL###("lithium", None, "raw_lithium"')],
        "must_keep": [
            '("manganese", None, "raw_manganese"',
            '("steel", "high_carbon_steel")',
            "def main(argv):",
        ],
        "must_lose": ["lithium"],
    },
}

ALLOWED_TOOLTIP_PREFIX = '"tooltip.potato_s_t.micro_crusher"'


def allowed_removal(line):
    s = line.strip()
    return s == "// ===== 6 个粗矿物品 =====" or s.startswith(ALLOWED_TOOLTIP_PREFIX)


def explain(l, cur_l):
    """一行 pre 中的内容在 cur 里找不到了 —— 给出"为什么可以接受"或 None。"""
    if allowed_removal(l):
        return "白名单（重命名 / tooltip 改写）"
    s = l.rstrip()
    for c in cur_l:
        if c.rstrip() == s + ",":
            return "追加后继条目时给上一行补了逗号"
    return None


def read(path):
    with io.open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def sha256_of_text(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def apply_cuts(text, cuts, name):
    """cuts = (起点标记, 终点标记)。

    标记前缀：`###AFTER###` = 从该行**之后**开始；`###INCL###` = 终点行**也要删**。
    默认终点是**开区间**（保留终点行）—— 这条默认值是有血的：
    一开始代码写成了「终点也删」，于是它顺手把 `import net.minecraft.tags.TagKey;`
    和 `table = Map.copyOf(m);` 一起删掉了。重建出来的文件缺 import、build() 也从不赋值 table，
    **根本编译不过**，而花括号还是平衡的、must_keep 也没覆盖到 —— 差点就当成"重建成功"存进备份。
    抓出它的是"多重集差分"：我加了 27 行，重建却少了 29 行。
    """
    lines = text.splitlines(keepends=True)
    for start_mark, end_mark in cuts:
        after = start_mark.startswith("###AFTER###")
        if after:
            start_mark = start_mark[len("###AFTER###"):]
        incl = end_mark.startswith("###INCL###")
        if incl:
            end_mark = end_mark[len("###INCL###"):]
        starts = [i for i, l in enumerate(lines) if start_mark in l]
        if len(starts) != 1:
            raise SystemExit("[FAIL] {0}：起点标记 {1!r} 命中 {2} 次（要求 1 次）".format(
                name, start_mark, len(starts)))
        i0 = starts[0] + (1 if after else 0)
        ends = [i for i, l in enumerate(lines) if end_mark in l and i >= i0]
        if not ends:
            raise SystemExit("[FAIL] {0}：终点标记 {1!r} 找不到".format(name, end_mark))
        i1 = ends[0] + (1 if incl else 0)
        if i1 <= i0:
            raise SystemExit("[FAIL] {0}：切割区间是空的（{1!r} .. {2!r}）".format(name, start_mark, end_mark))
        del lines[i0:i1]
    return "".join(lines)


def main(argv):
    check_only = "--check" in argv

    for p in (SNAP, JAR):
        if not os.path.exists(p):
            raise SystemExit("[FAIL] 缺少 {0}".format(p))
    jar_sha1 = hashlib.sha1(open(JAR, "rb").read()).hexdigest().upper()
    print("release jar SHA1 = {0}".format(jar_sha1))
    if jar_sha1 != JAR_SHA1_EXPECT:
        raise SystemExit("[FAIL] release jar 不是 B 批那一份（预期 {0}）—— 不能当改前快照用".format(
            JAR_SHA1_EXPECT))
    print("  ✓ 就是 B 批那份（改前状态）")

    results = []          # (备份名, 来源, 文本)
    problems = []

    # ---------- 来源 ① jar ----------
    print("")
    print("== 来源①：从 release jar 提取 ==")
    zf = zipfile.ZipFile(JAR)
    for inner, backup_name in FROM_JAR.items():
        pre = zf.read(inner).decode("utf-8")
        cur = read(os.path.join(PROJ, "src", "main", "resources", inner.replace("/", os.sep)))
        pre_l, cur_l = pre.splitlines(), cur.splitlines()
        added = [l for l in cur_l if l not in pre_l]
        gone = [l for l in pre_l if l not in cur_l]
        unexplained = [(l, explain(l, cur_l)) for l in gone]
        unexplained = [l for l, why in unexplained if why is None]
        print("  {0:<24} +{1:<3} -{2}   {3}".format(
            backup_name, len(added), len(gone),
            "OK" if added and not unexplained else "!! 有问题 !!"))
        if not added:
            problems.append("{0}：jar 版和当前文件一样，那这一阶段没改它？".format(backup_name))
        if unexplained:
            problems.append("{0}：有 {1} 行无法解释的消失内容".format(backup_name, len(unexplained)))
        results.append((backup_name, "①B批release jar", pre))
    zf.close()

    # 反向证据：改前 jar 里**不该**有锂矿相关条目
    print("")
    print("== 反向证据：改前 jar 里有没有锂矿条目 ==")
    zf = zipfile.ZipFile(JAR)
    names = zf.namelist()
    for probe in ("lithium_ore", "raw_lithium", "lithium_concentrate", "lithium_carbonate"):
        hit = [n for n in names if probe in n]
        print("  {0:<22} -> {1}".format(probe, "（无，符合预期）" if not hit else "!! 有 {0} 个 !!".format(len(hit))))
        if hit:
            problems.append("改前 jar 里居然有 {0}".format(probe))
    zf.close()

    # ---------- 来源 ② 快照 ----------
    print("")
    print("== 来源②：zf12_project 全量快照 ==")
    for backup_name, rel in FROM_SNAPSHOT.items():
        pre = read(os.path.join(SNAP, rel))
        cur = read(os.path.join(PROJ, rel))
        pre_l, cur_l = pre.splitlines(), cur.splitlines()
        added = [l for l in cur_l if l not in pre_l]
        gone = [l for l in pre_l if l not in cur_l]
        unexplained = [l for l in gone if explain(l, cur_l) is None]
        print("  {0:<24} +{1:<3} -{2}   {3}".format(
            backup_name, len(added), len(gone), "OK" if not unexplained else "!! 有问题 !!"))
        for l in unexplained[:6]:
            print("      !! 无法解释的消失行：{0}".format(l.strip()[:90]))
        if unexplained:
            problems.append("{0}：快照不是改前版本（{1} 行意外消失）".format(backup_name, len(unexplained)))
        results.append((backup_name, "②zf12_project 快照", pre))

    # ---------- 来源 ③ 重建 ----------
    print("")
    print("== 来源③：减法重建（无改前源码快照）==")
    for backup_name, spec in RECONSTRUCT.items():
        cur = read(os.path.join(PROJ, spec["path"]))
        pre = apply_cuts(cur, spec["cuts"], backup_name)
        n_pre = len(pre.splitlines())
        exp = spec.get("expected_lines")
        ok_lines = exp is None or n_pre == exp
        print("  {0:<24} {1} 行 -> {2} 行   行数断言 {3}".format(
            backup_name, len(cur.splitlines()), n_pre,
            "（没设）" if exp is None else ("✓ ={0}".format(exp) if ok_lines
                                            else "!! 应 {0}，差 {1} !!".format(exp, n_pre - exp))))
        if not ok_lines:
            problems.append("{0}：重建后 {1} 行，改前应是 {2} 行（差 {3}）—— 切割区间写错了".format(
                backup_name, n_pre, exp, n_pre - exp))
        bad = [k for k in spec["must_keep"] if k not in pre]
        leak = [k for k in spec["must_lose"] if k in pre]
        for k in spec["must_keep"]:
            print("      {0} {1}".format("✓ 保留" if k not in bad else "!! 丢了 !!", k))
        for k in spec["must_lose"]:
            print("      {0} {1}".format("✓ 已移除" if k not in leak else "!! 还在 !!", k))
        if bad:
            problems.append("{0}：重建把 ZF13 的东西删掉了 -> {1}".format(backup_name, bad))
        if leak:
            problems.append("{0}：重建后本阶段的东西还在 -> {1}".format(backup_name, leak))
        if pre.count("{") != pre.count("}"):
            problems.append("{0}：重建后花括号不平衡（{1} vs {2}）".format(
                backup_name, pre.count("{"), pre.count("}")))
        results.append((backup_name, "③减法重建", pre))

    print("")
    if problems:
        print("!! 没通过，拒绝写 zf15_pre !!")
        for p in problems:
            print("   " + p)
        return 1
    print("全部通过（{} 个文件）".format(len(results)))
    if check_only:
        print("（--check：未落盘）")
        return 0

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for name, _src, text in results:
        with io.open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as fh:
            fh.write(text)

    lines = ["PotatoS&T zf15_pre（加锂矿之前的版本）", "=" * 60, ""]
    lines.append("⚠ 这不是「改前抓拍」，是事后补建的。来源分三级，逐文件如下：")
    lines.append("")
    lines.append("{0:<28} {1:<20} {2}".format("文件", "来源", "sha256(前16位)"))
    lines.append("-" * 76)
    for name, src, text in results:
        lines.append("{0:<28} {1:<20} {2}".format(name, src, sha256_of_text(text)[:16]))
    lines.append("")
    lines.append("① B 批 release jar：jar 的 SHA1 仍为 {0}，".format(JAR_SHA1_EXPECT))
    lines.append("   且里面没有任何 lithium_ore / raw_lithium / lithium_concentrate / lithium_carbonate 条目")
    lines.append("   ⇒ 可以证明它确实是「加锂之前」的那一份。这份是**逐字节权威**的。")
    lines.append("")
    lines.append("② zf12_project 快照：差分结果 = 只有本阶段新增的行，没有其他消失内容 ⇒ 可信。")
    lines.append("")
    lines.append("③ 减法重建（MicroCrusherRecipes.java / GenCommonTags.py）：")
    lines.append("   没有可用的改前源码快照 —— zf12_project 里那份 MicroCrusherRecipes.java **早于 ZF13**，")
    lines.append("   直接拿来当 pre 会在回退时静默删掉 ZF13 的标签规则（差分当场抓到 8 行）。")
    lines.append("   所以按「删掉本阶段加的那几段」重建，并断言 ZF13 的特征串仍在（见脚本的 must_keep）。")
    lines.append("   这两份是**重建**，不是快照：回退前请再 diff 一次。")
    lines.append("")
    lines.append("回退办法：把本目录文件覆盖回项目对应路径；")
    lines.append("  另外本阶段**新增**的文件直接删掉即可（它们在「改前」根本不存在）：")
    lines.append("    src/main/resources/data/potato_s_t/recipe/lithium_carbonate_from_blasting_lithium_concentrate.json")
    lines.append("    src/main/resources/data/potato_s_t/loot_table/blocks/lithium_ore.json")
    lines.append("    src/main/resources/data/potato_s_t/worldgen/configured_feature/ore_lithium.json")
    lines.append("    src/main/resources/data/potato_s_t/worldgen/placed_feature/ore_lithium_placed.json")
    lines.append("    src/main/resources/data/c/tags/item/raw_materials/lithium.json")
    lines.append("    src/main/resources/data/c/tags/item/ores/lithium.json")
    lines.append("    src/main/resources/data/c/tags/block/ores/lithium.json")
    lines.append("    src/main/resources/assets/potato_s_t/blockstates/lithium_ore.json")
    lines.append("    src/main/resources/assets/potato_s_t/models/block/lithium_ore.json")
    lines.append("    src/main/resources/assets/potato_s_t/models/item/lithium_ore.json")
    lines.append("    src/main/resources/assets/potato_s_t/models/item/raw_lithium.json")
    lines.append("    src/main/resources/assets/potato_s_t/models/item/lithium_concentrate.json")
    lines.append("    src/main/resources/assets/potato_s_t/models/item/lithium_carbonate.json")
    lines.append("    src/main/resources/assets/potato_s_t/textures/block/lithium_ore.png")
    lines.append("    src/main/resources/assets/potato_s_t/textures/item/raw_lithium.png")
    lines.append("  c: 标签里 ores_in_ground/stone.json 也会多一项 —— 那是 GenCommonTags 生成的，")
    lines.append("  把 METALS 里的 lithium 行删掉重跑脚本即可（别手改，会被下次重跑覆盖）。")
    with io.open(os.path.join(OUT, "_说明.txt"), "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write("\n".join(lines) + "\n")

    with io.open(os.path.join(OUT, "_sha256.txt"), "w", encoding="utf-8", newline="\r\n") as fh:
        for name, src, text in results:
            fh.write("{0}  {1}\r\n".format(sha256_of_text(text), name))

    print("已写入 {0}".format(OUT))
    for name, src, text in results:
        print("    {0:<28} {1:<20} {2}".format(name, src, sha256_of_text(text)[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
