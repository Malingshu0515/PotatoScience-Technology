#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ZF169 常驻门：硫 / 硫磺粉统一到 `#c:dusts/sulfur`、酸性反应室认别人的硫磺。

跑法：python build/zftools/_zf169_gate.py
输出：build/zftools/_zf169_gate.log（UTF-8），控制台一行摘要。

设计口径（沿用本工程既有的门：只读、不修文件、失败列清楚）：
  组 A  数据：那条标签文件存在、内容对、父标签引用对
  组 B  源码：三道门禁都转调同一个判据（§4.51），且**没有**第二处写死 ModItems.SULFUR
  组 C  负面对照：不许挂 c:sulfur / 不许留旧的写死比较 / 不许有反向配方闭环
  组 D  探针报告：把真服务端跑出来的证据读回来（28 项 0 失败）
  组 E  文档：档案 / 交接 / 公告三处都记了账
"""

import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
LOG = os.path.join(ROOT, "build", "zftools", "_zf169_gate.log")

fails = []
oks = []
infos = []


def ok(label):
    oks.append(label)


def bad(label, detail=""):
    fails.append(label + ("" if not detail else "  —— " + detail))


def info(text):
    infos.append(text)


def read(path):
    with io.open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def java(rel):
    return read(os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", rel))


def res(rel):
    return os.path.join(ROOT, "src", "main", "resources", rel)


# ============================================================
#  组 A：数据
# ============================================================

TAG_REL = "data/c/tags/item/dusts/sulfur.json"
if os.path.exists(res(TAG_REL)):
    d = json.loads(read(res(TAG_REL)))
    vals = d.get("values", [])
    if vals == ["potato_s_t:sulfur"]:
        ok("A1 %s = [potato_s_t:sulfur]" % TAG_REL)
    else:
        bad("A1 %s 的内容不对" % TAG_REL, json.dumps(d, ensure_ascii=False))
    if d.get("replace") is True:
        bad("A1 用了 replace:true（会把 Mek/IE 的硫粉挤掉）")
    else:
        ok("A1 没有 replace:true（与 Mek/IE 的同名文件合并）")
    raw = open(res(TAG_REL), "rb").read()
    if raw[:3] == b"\xef\xbb\xbf":
        bad("A1 该文件有 BOM")
    elif b"\r\n" in raw:
        bad("A1 该文件是 CRLF")
    else:
        ok("A1 纯 LF、无 BOM")
else:
    bad("A1 缺少 " + TAG_REL)

PARENT_REL = "data/c/tags/item/dusts.json"
if os.path.exists(res(PARENT_REL)):
    d = json.loads(read(res(PARENT_REL)))
    vals = d.get("values", [])
    if "#c:dusts/sulfur" in vals:
        ok("A2 父标签 #c:dusts 引用了 #c:dusts/sulfur")
    else:
        bad("A2 父标签 #c:dusts 里没有引用 #c:dusts/sulfur", json.dumps(vals, ensure_ascii=False))
    for keep in ("potato_s_t:carbon", "potato_s_t:iron_powder", "potato_s_t:titanium_powder"):
        if keep not in vals:
            bad("A2 父标签里原来的 %s 没了（不该动它）" % keep)
    else:
        ok("A2 父标签里原来那三条都还在")
else:
    bad("A2 缺少 " + PARENT_REL)

# ============================================================
#  组 B：源码 —— 三道门禁只有一份判据（§4.51）
# ============================================================

MI = java("ModItems.java")
BE = java("AcidicReactionChamberBlockEntity.java")
MENU = java("AcidicReactionChamberMenu.java")

# B1 判据本体
m = re.search(r"SULFUR_TAG\s*=\s*\n?\s*TagKey\.create\(Registries\.ITEM,\s*\n?\s*"
              r"ResourceLocation\.fromNamespaceAndPath\(\"c\",\s*\"dusts/sulfur\"\)\)", MI)
if not m:
    bad("B1 ModItems 里没有 SULFUR_TAG = TagKey.create(ITEM, c:dusts/sulfur)")
else:
    ok("B1 SULFUR_TAG 指向 c:dusts/sulfur")
if not re.search(r"public static boolean isSulfur\(ItemStack stack\)\s*\{\s*"
                 r"return !stack\.isEmpty\(\) && stack\.is\(SULFUR_TAG\);", MI):
    bad("B1 ModItems.isSulfur 的实现不是「非空 && 在标签里」")
else:
    ok("B1 ModItems.isSulfur = 非空 && stack.is(SULFUR_TAG)")

# B2 三道门禁都转调它
if not re.search(r"slot == SULFUR_SLOT && ModItems\.isSulfur\(stack\)", BE):
    bad("B2 方块实体的 isItemValid 没有转调 ModItems.isSulfur")
else:
    ok("B2 门禁①方块实体 isItemValid → ModItems.isSulfur")
if not re.search(r"public boolean mayPlace\(ItemStack stack\)\s*\{\s*return ModItems\.isSulfur\(stack\);", MENU):
    bad("B2 菜单槽的 mayPlace 没有转调 ModItems.isSulfur")
else:
    ok("B2 门禁②菜单槽 mayPlace → ModItems.isSulfur")
if not re.search(r"return ModItems\.isSulfur\(stack\) \? AcidicReactionChamberBlockEntity\.SULFUR_SLOT : -1;", MENU):
    bad("B2 Shift 快移的 getMachineSlotFor 没有转调 ModItems.isSulfur")
else:
    ok("B2 门禁③Shift 快移 getMachineSlotFor → ModItems.isSulfur")

# B3 判据只该有一份：全工程不许再有第二处 stack.is(ModItems.SULFUR.get())
#    ⚠ 两个白名单（都是**故意**保留的，不是漏网）：
#      · HydrodesulfurizationChamberBlockEntity：那是**产出**侧（`out.is(...)` 判"输出槽里是不是我们的硫"），
#        它必须写死我方物品 —— 别人的硫粉不该能被塞进输出槽。
#      · ModItems.java：命中在**javadoc**里（注释里引用了旧写法），不是代码。
#    所以扫描前先把注释剥掉，只留真代码。
def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)      # 块注释 + javadoc
    text = re.sub(r"//[^\n]*", "", text)                    # 行注释
    return text


offenders = []
for dirpath, _dirs, files in os.walk(os.path.join(ROOT, "src", "main", "java")):
    for fn in files:
        if not fn.endswith(".java"):
            continue
        p = os.path.join(dirpath, fn)
        txt = strip_comments(read(p))
        for i, line in enumerate(txt.splitlines(), 1):
            if re.search(r"\.is\(ModItems\.SULFUR\.get\(\)\)", line):
                rel = os.path.relpath(p, ROOT)
                if fn == "HydrodesulfurizationChamberBlockEntity.java" and "out.is(" in line:
                    ok("B3 白名单：加氢脱硫反应室的**产出**判定照旧写死我方物品（%s:%d）" % (rel, i))
                    continue
                offenders.append("%s:%d" % (rel, i))
if offenders:
    bad("B3 还有地方写死了 stack.is(ModItems.SULFUR.get())（判据就散成两份了）",
        ", ".join(offenders))
else:
    ok("B3 真代码里没有第二处写死的 stack.is(ModItems.SULFUR.get())")

# B4 硫的产出侧（加氢脱硫反应室）**不该**跟着改宽 —— 它产出的永远是我们自己的物品
HD = java("HydrodesulfurizationChamberBlockEntity.java")
if "ModItems.isSulfur" in HD:
    bad("B4 加氢脱硫反应室被误改成认标签了（它是**产出**侧，产出永远是我们自己的硫）")
else:
    ok("B4 加氢脱硫反应室的产出侧没被改宽（仍然产出 potato_s_t:sulfur）")

# ============================================================
#  组 C：负面对照
# ============================================================

# C1 不许挂 c:sulfur（谁都不用的空标签）
bare = res("data/c/tags/item/sulfur.json")
if os.path.exists(bare) and "potato_s_t:" in read(bare):
    bad("C1 我们往 c:sulfur 里挂了东西（三个对端没有一个用这条标签）")
else:
    ok("C1 没有挂那个谁都不用的 c:sulfur")

# C2 那些真正吃 c:dusts/sulfur 的配方 id 必须仍然存在（写死一份名单，改动时门会红）
KNOWN = [
    ("libs/Mekanism-1.21.1-10.7.19.85.jar", "data/mekanism/recipe/enriching/conversion/sulfur_to_gunpowder.json"),
    ("libs/Mekanism-1.21.1-10.7.19.85.jar", "data/mekanism/recipe/chemical_conversion/sulfur_to_sulfuric_acid.json"),
    ("libs/Mekanism-1.21.1-10.7.19.85.jar", "data/mekanism/recipe/oxidizing/sulfur_dioxide.json"),
    ("release/ImmersiveEngineering-1.21.1-12.4.2-194.jar", "data/immersiveengineering/recipe/crafting/gunpowder_from_dusts.json"),
]
import zipfile  # noqa: E402  （放这里只是为了让上面的读文件逻辑更醒目）
for jar, entry in KNOWN:
    p = os.path.join(ROOT, jar)
    if not os.path.exists(p):
        info("C2 找不到 %s，跳过 %s" % (jar, entry))
        continue
    z = zipfile.ZipFile(p)
    if entry not in z.namelist():
        bad("C2 %s 里没有 %s（上游改过配方路径？门的名单要跟平）" % (jar, entry))
        continue
    body = " ".join(z.read(entry).decode("utf-8").split())
    if '"tag":"c:dusts/sulfur"' in body.replace(" ", "") or '"tag": "c:dusts/sulfur"' in body:
        ok("C2 %s 仍然吃 #c:dusts/sulfur" % os.path.basename(entry))
    else:
        bad("C2 %s 不再吃 #c:dusts/sulfur 了" % os.path.basename(entry),
            body[:200])

# C3 闭环自查：能把"火药/二氧化硫/硫酸"变回硫的配方有没有出现
DANGER = re.compile(r'"(id|tag)"\s*:\s*"[^"]*sulfur', re.I)
found_loops = []
for jar, _ in KNOWN:
    p = os.path.join(ROOT, jar)
    if not os.path.exists(p):
        continue
    z = zipfile.ZipFile(p)
    for n in z.namelist():
        if "/recipe/" not in n or not n.endswith(".json"):
            continue
        body = z.read(n).decode("utf-8", "replace")
        # 该配方如果**吃**火药/二氧化硫/硫酸 又**吐**硫，就是闭环
        if re.search(r'"(gunpowder|sulfur_dioxide|sulfuric_acid)"', body) and DANGER.search(body):
            found_loops.append("%s :: %s" % (os.path.basename(p), n))
if found_loops:
    bad("C3 出现了『吃火药/二氧化硫/硫酸 → 吐硫』的配方，闭环风险（§4.167）",
        "; ".join(found_loops[:5]))
else:
    ok("C3 没找到『吃火药/二氧化硫/硫酸 → 吐硫』的闭环配方")

# ============================================================
#  组 D：探针报告
# ============================================================

PROBE = os.path.join(ROOT, "build", "zftools", "_zf169_probe.txt")
if os.path.exists(PROBE):
    txt = read(PROBE)
    tail = [ln for ln in txt.splitlines() if ln.startswith("通过 = ")]
    if not tail:
        bad("D1 探针报告里没有『通过 = / 失败 = 』那行")
    else:
        n_fail = int(re.search(r"失败 = (\d+)", tail[0]).group(1))
        n_pass = int(re.search(r"通过 = (\d+)", tail[0]).group(1))
        if n_fail != 0:
            bad("D1 探针报告里失败 = %d（必须为 0）" % n_fail)
        else:
            ok("D1 探针 %d/0" % n_pass)
    for needle, label in [
            ("成员 = [immersiveengineering:dust_sulfur, mekanism:dust_sulfur, potato_s_t:sulfur]",
             "D2 三个对端的硫粉在**同一条**标签里"),
            ("test(potato_s_t:sulfur) = true", "D2 上游自己的 Ingredient.test 收了我们的硫"),
            ("test(minecraft:gunpowder) = false", "D3 负对照：同一条成分判据对火药为假")]:
        if needle in txt:
            ok(label)
        else:
            bad("D2/D3 探针报告里没有：%s" % label)
else:
    info("D1 没有探针报告（%s）—— 跑过 Zf169Check 才有" % PROBE)

# ============================================================
#  组 E：文档记账
# ============================================================

ARCH = read(os.path.join(ROOT, "docs", "开发档案.md"))
LEDGER = read(os.path.join(ROOT, "docs", "多会话协作交接.md"))
ANN = read(os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md"))

for needle, label in [
        ("ZF169", "E1 档案里提到了 ZF169"),
        ("c:dusts/sulfur", "E1 档案里写清了挂的是哪条标签")]:
    if needle in ARCH:
        ok(label)
    else:
        bad("E1 开发档案里没有：%s" % label)
if "ZF169" in LEDGER:
    ok("E2 交接页里提到了 ZF169")
else:
    bad("E2 交接页里没有 ZF169")
if "ZF169" in ANN or "sulfur" in ANN.lower():
    ok("E3 英文公告里提到了这一轮")
else:
    bad("E3 英文公告里没提")

# ============================================================
#  收尾
# ============================================================

lines = ["ZF169 常驻门（硫 / 硫磺粉统一到 #c:dusts/sulfur）—— 只读校验", "",
         "通过 = %d   失败 = %d" % (len(oks), len(fails)), ""]
if fails:
    lines.append("== 失败 ==")
    for f in fails:
        lines.append("  [FAIL] " + f)
    lines.append("")
lines.append("== 通过 ==")
for o in oks:
    lines.append("  [OK]   " + o)
if infos:
    lines.append("")
    lines.append("== 说明 ==")
    for i in infos:
        lines.append("  [INFO] " + i)

os.makedirs(os.path.dirname(LOG), exist_ok=True)
with io.open(LOG, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(lines) + "\n")

print("ZF169 gate: passed=%d failed=%d  -> %s" % (len(oks), len(fails), LOG))
sys.exit(1 if fails else 0)
