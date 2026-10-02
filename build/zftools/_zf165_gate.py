#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ZF165 常驻门：Curios 饰品栏联动的只读校验（0.13）。

跑法：python build/zftools/_zf165_gate.py
输出：build/zftools/_zf165_gate.log（UTF-8），控制台一行摘要。

设计口径（沿用本工程既有的门：只读、不修文件、失败列清楚）：
  组 A  Java 侧：两类桥的常量、注册方式、单一 import 面
  组 B  数据侧：四个数据文件的路径/形状/合并语义/必需项
  组 C  负面对照：不许出现的写法（conditions in tags、datapack 覆盖式 replace、写死 5.5 等）
  组 D  mods.toml：curios 依赖声明与它的理由注释
  组 E  读活体 jar（可选，若 build/libs 里有）：产包里真的带上了那四个数据文件

⚠ 这个脚本**永远只读**；它不改任何文件，所以可以随时重跑。
"""

import io
import json
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
LOG = os.path.join(ROOT, "build", "zftools", "_zf165_gate.log")

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


def jload(path):
    return json.loads(read(path))


def java(rel):
    return read(os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", rel))


def res(rel):
    return os.path.join(ROOT, "src", "main", "resources", rel)


def must_exist(rel):
    p = res(rel)
    if os.path.exists(p):
        ok("存在 " + rel)
        return True
    bad("缺少文件 " + rel)
    return False


# ============================================================
#  组 A：Java 侧
# ============================================================

BRIDGE = "CuriosBridge.java"

if must_exist_ok := os.path.exists(
        os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", BRIDGE)):
    b = java(BRIDGE)

    # A1 三个常量必须与 ModArmorSet 那边相等（§4.51：判据只有一份）
    m = java("ModArmorSet.java")
    pairs = [
        ("NIGHT_VISION_TICKS", "HELMET_NIGHT_VISION_TICKS"),
        ("NIGHT_VISION_MARGIN", "NIGHT_VISION_MARGIN"),
        ("NIGHT_VISION_AMPLIFIER", "NIGHT_VISION_III"),
    ]
    for mine, theirs in pairs:
        a = re.search(r"\b%s\s*=\s*(\d+)\s*;" % mine, b)
        c = re.search(r"\b%s\s*=\s*(\d+)\s*;" % theirs, m)
        if not a or not c:
            bad("A1 找不到常量 %s / %s" % (mine, theirs))
        elif a.group(1) != c.group(1):
            bad("A1 %s=%s 与 ModArmorSet.%s=%s 不一致" % (mine, a.group(1), theirs, c.group(1)))
        else:
            ok("A1 %s = ModArmorSet.%s = %s" % (mine, theirs, a.group(1)))

    a = re.search(r"ARMOR_BONUS\s*=\s*([0-9.]+)\s*;", b)
    if not a:
        bad("A1 找不到 ARMOR_BONUS")
    elif float(a.group(1)) != 2.0:
        bad("A1 ARMOR_BONUS 不是 2.0，而是 %s（用户原话「只+2护甲值」）" % a.group(1))
    else:
        ok("A1 ARMOR_BONUS = 2.0")

    # A2 能力注册：必须走 CuriosCapability.ITEM + ItemizedCurioCapability 胶水
    if "CuriosCapability.ITEM" not in b:
        bad("A2 没有注册 curios:item 能力")
    else:
        ok("A2 注册的是 CuriosCapability.ITEM")
    if "ItemizedCurioCapability" not in b:
        bad("A2 没有用 Curios 自己的 ICurioItem→ICurio 胶水（自己写桥会静默过时）")
    else:
        ok("A2 用了 ItemizedCurioCapability 胶水")

    # A3 注册前必须问对端在不在（物品 id 会是 air）
    if not re.search(r'ModList\.get\(\)\.isLoaded\("mekanism"\)', b):
        bad("A3 没有先问 Mek 在不在就注册喷气背包的能力")
    else:
        ok("A3 注册喷气背包能力前问了 ModList.isLoaded(\"mekanism\")")
    if "Items.AIR" not in b:
        bad("A3 没有挡「物品 id 解析成 air」的入口")
    else:
        ok("A3 挡了 air 入口")

    # A4 护甲修饰符的 id 必须用**Curios 传进来的那一个**（`curios:<槽位名><序号>`）。
    #    ⚠ 这一条被复核改过口径：第一版我们自己起了个固定常量，复核指出
    #      `AttributeInstance#removeModifier(AttributeModifier)` **只按 modifier.id() 删**
    #      （原版源码 AttributeInstance:114-123），固定 id 在 head 只有 1 格时没事，
    #      一旦被调成 ≥2 格两个头盔就会互相顶掉对方那条。
    if re.search(r"new AttributeModifier\(id, ARMOR_BONUS", b):
        ok("A4 护甲修饰符用的是 Curios 传进来的 id（每个槽位天然唯一）")
    else:
        bad("A4 护甲修饰符没有用 Curios 传进来的 id —— "
            "head 槽一旦扩到 ≥2 格，两个头盔会互相顶掉对方的修饰符")
    if "ARMOR_MODIFIER_ID" in b:
        bad("A4 还留着自造的 ARMOR_MODIFIER_ID 常量（应当直接用参数 id）")
    else:
        ok("A4 没有自造的固定修饰符 id")

    # A5 槽位 id 常量
    for slot in ("head", "back"):
        if not re.search(r'SLOT_%s\s*=\s*"%s"' % (slot.upper(), slot), b):
            bad("A5 缺少槽位常量 SLOT_%s" % slot.upper())
        else:
            ok("A5 SLOT_%s = \"%s\"" % (slot.upper(), slot))

    # A6 头盔只在 head 槽给护甲
    if "SLOT_HEAD.equals(slotContext.identifier())" not in b:
        bad("A6 头盔的护甲修饰符没有按槽位过滤")
    else:
        ok("A6 头盔的护甲修饰符按 SLOT_HEAD 过滤")

    # A7 单一 import 面：全工程只有 CuriosBridge（+ 临时探针）import curios
    #    探针的命名口径：Z<数字>Check.java / *Probe*.java —— 跑完就删，不进产物。
    probe_re = re.compile(r"^(Zf?\d+Check|.*Probe.*)\.java$", re.I)
    offenders = []
    base = os.path.join(ROOT, "src", "main", "java")
    for dirpath, _dirs, files in os.walk(base):
        for fn in files:
            if not fn.endswith(".java"):
                continue
            p = os.path.join(dirpath, fn)
            if "top.theillusivec4.curios" not in read(p):
                continue
            if fn == BRIDGE or probe_re.match(fn):
                continue
            offenders.append(os.path.relpath(p, ROOT))
    if offenders:
        bad("A7 除 %s 外还有文件 import curios" % BRIDGE, ", ".join(sorted(offenders)))
    else:
        ok("A7 全工程只有 CuriosBridge.java import 了 curios（临时探针除外）")

    # A8 公开方法签名里不许出现 Curios 类型（否则没装 Curios 的实例会崩）。
    #    ⚠ 只看**类自己**的成员：匿名内部类里那些 @Override 的方法必然带 Curios 类型，
    #      它们不是对外契约（第一次写这个门就是被它们误报的）。
    pub_lines = []
    prev = ""
    for ln in b.splitlines():
        stripped = ln.strip()
        if stripped.startswith("@Override"):
            prev = stripped
            continue
        if re.match(r"public\s", stripped) and "(" in stripped and not prev.startswith("@Override"):
            pub_lines.append(stripped)
        prev = stripped
    leaked = [ln for ln in pub_lines
              if "ICurio" in ln or "SlotContext" in ln or "SlotResult" in ln or "Curios" in ln]
    if leaked:
        bad("A8 公开方法签名里出现了 Curios 类型：%s" % leaked)
    else:
        ok("A8 公开方法签名里没有 Curios 类型（匿名类里的 @Override 不算对外契约）")

    # A9 头盔槽那条老路必须还在（原版头盔槽 || 饰品槽）
    mat = java("ModArmorMaterials.java")
    hm = re.search(r"hasStarSteelHelmet\s*\(LivingEntity[^)]*\)\s*\{(.*?)\n    \}", mat, re.S)
    if not hm:
        bad("A9 解析不到 hasStarSteelHelmet 的方法体")
    elif "EquipmentSlot.HEAD" not in hm.group(1) or "CuriosBridge.hasEquipped" not in hm.group(1):
        bad("A9 hasStarSteelHelmet 不是「原版头盔槽 || 饰品槽」", hm.group(1).strip()[:200])
    else:
        ok("A9 hasStarSteelHelmet = 原版头盔槽 || 饰品槽")

    # A10 四件套那两条判据不许被改宽（本轮只动头盔这一条）
    for name in ("hasFullStarSteelSet", "hasAnyStarSteelPiece"):
        body = re.search(r"%s\s*\(LivingEntity[^)]*\)\s*\{(.*?)\n    \}" % name, mat, re.S)
        if not body:
            bad("A10 解析不到 %s" % name)
        elif "CuriosBridge" in body.group(1):
            bad("A10 %s 被改宽到认饰品槽了（本轮不该动）" % name)
        else:
            ok("A10 %s 没被改宽" % name)
else:
    bad("缺少 " + BRIDGE)

# ============================================================
#  组 B：数据侧
# ============================================================

# B1 两个物品标签
head_rel = "data/curios/tags/item/head.json"
back_rel = "data/curios/tags/item/back.json"
if must_exist(head_rel):
    d = jload(res(head_rel))
    if d.get("values") != ["potato_s_t:star_steel_helmet"]:
        bad("B1 %s 的内容不是只有头盔" % head_rel, json.dumps(d, ensure_ascii=False))
    else:
        ok("B1 #curios:head ← potato_s_t:star_steel_helmet")
    if d.get("replace") is True:
        bad("B1 #curios:head 用了 replace:true（会把 Create 的护目镜挤掉）")
    else:
        ok("B1 #curios:head 没有 replace:true（与别的数据包合并）")

if must_exist(back_rel):
    d = jload(res(back_rel))
    vals = d.get("values", [])
    # 每一条都必须是 {id, required:false} 的对象；**必需项缺失会让整张标签被丢掉**
    if not vals or any(not isinstance(v, dict) for v in vals):
        bad("B2 %s 的 values 形状不对（每一条都要是 {id, required:false} 对象）" % back_rel,
            json.dumps(d, ensure_ascii=False))
    else:
        bads = [v for v in vals if v.get("required") is not False or not str(v.get("id", "")).strip()]
        if bads:
            bad("B2 %s 里有条目没写 required:false（物品不存在时**整张标签会消失**）" % back_rel,
                json.dumps(bads, ensure_ascii=False))
        else:
            ids = [v["id"] for v in vals]
            ok("B2 #curios:back ← %s（都带 required:false）" % ", ".join(ids))
            if "mekanism:jetpack" not in ids:
                bad("B2 #curios:back 里没有 mekanism:jetpack")
            else:
                ok("B2 含 mekanism:jetpack（普通版）")
    if "neoforge:conditions" in read(res(back_rel)):
        bad("B2 标签文件里写了 neoforge:conditions —— 对标签文件是**静默无效**的"
            "（TagFile 只认 values/replace/remove，TagLoader 不走 ConditionalOps）")
    else:
        ok("B2 标签文件里没有无效的 neoforge:conditions")

# B3 实体槽位分配（本轮最容易漏的一步）
ent_rel = "data/potato_s_t/curios/entities/players.json"
if must_exist(ent_rel):
    d = jload(res(ent_rel))
    ents = d.get("entities", [])
    slots = d.get("slots", [])
    if "minecraft:player" not in ents:
        bad("B3 实体文件没有把槽位分给 minecraft:player", json.dumps(d, ensure_ascii=False))
    elif "head" not in slots or "back" not in slots:
        bad("B3 实体文件没有同时给出 head 与 back", json.dumps(d, ensure_ascii=False))
    else:
        ok("B3 把 head/back 两个槽位分给了 minecraft:player")
    if d.get("replace") is True:
        bad("B3 实体文件用了 replace:true（会把 Create 的 head 分配挤掉）")
    else:
        ok("B3 实体文件没有 replace:true（与 Create 的合并）")

# B4 三个数据文件的格式口径（LF、无 BOM、与工程既有文件一致）
for rel in (head_rel, back_rel, ent_rel):
    p = res(rel)
    if not os.path.exists(p):
        continue
    raw = open(p, "rb").read()
    if raw[:3] == b"\xef\xbb\xbf":
        bad("B4 %s 有 BOM" % rel)
    elif b"\r\n" in raw:
        bad("B4 %s 是 CRLF（工程口径是纯 LF）" % rel)
    else:
        ok("B4 %s 纯 LF、无 BOM" % rel)

# ============================================================
#  组 C：负面对照
# ============================================================

# C1 不许把头盔挂到 #curios:back / 喷气背包挂到 #curios:head
if os.path.exists(res(head_rel)):
    if "mekanism:jetpack" in read(res(head_rel)):
        bad("C1 喷气背包被挂进了 #curios:head")
    else:
        ok("C1 喷气背包没被挂进 #curios:head")
if os.path.exists(res(back_rel)):
    if "star_steel_helmet" in read(res(back_rel)):
        bad("C1 头盔被挂进了 #curios:back")
    else:
        ok("C1 头盔没被挂进 #curios:back")

# C2 不许把我们的物品挂进 #curios:curio（那会让它在**每一个**槽都合法）
curio_rel = "data/curios/tags/item/curio.json"
if os.path.exists(res(curio_rel)) and "potato_s_t:" in read(res(curio_rel)):
    bad("C2 我们的物品被挂进了 #curios:curio（会在每个槽都合法）")
else:
    ok("C2 没有往 #curios:curio 里塞我们的物品")

# C3 头盔的 curio 实现不许再写一份夜视（判据只有一份）
if os.path.exists(os.path.join(ROOT, "src/main/java/com/potatost/mod", BRIDGE)):
    b = java(BRIDGE)
    if "MobEffects.NIGHT_VISION" in b:
        bad("C3 CuriosBridge 里又写了一份夜视（应该只由 ModArmorSet 续）")
    else:
        ok("C3 CuriosBridge 里没有第二份夜视逻辑")

# C4 喷气背包的 curio 不许覆写飞行/燃料相关方法
if os.path.exists(os.path.join(ROOT, "src/main/java/com/potatost/mod", BRIDGE)):
    b = java(BRIDGE)
    seg = b[b.find("mekanismJetpackCurio"):]
    seg = seg[:seg.find("\n    }")]
    if "useJetpackFuel" in seg or "canUseJetpack" in seg or "getJetpackMode" in seg:
        bad("C4 我们覆写了 Mek 的飞行/燃料方法（应该全交回 Mek）")
    else:
        ok("C4 喷气背包的 curio 没覆写任何 Mek 飞行方法")

# ============================================================
#  组 D：mods.toml
# ============================================================

toml = read(res("META-INF/neoforge.mods.toml"))
dep = re.search(r'modId="curios"\s*\n\s*type="(\w+)"\s*\n\s*versionRange="([^"]+)"', toml)
if not dep:
    bad("D1 mods.toml 里没有 curios 依赖")
else:
    if dep.group(1) != "required":
        bad("D1 curios 依赖不是 required（ICurioItem 是接口，可选会崩）", dep.group(1))
    else:
        ok("D1 curios 依赖 = required，versionRange = %s" % dep.group(2))
    if dep.group(2) != "[9.5.1,)":
        bad("D1 curios 版本范围不是 [9.5.1,)（实测过的那一版）", dep.group(2))
    else:
        ok("D1 curios 版本范围 = [9.5.1,)")
if "ICurioItem" not in toml:
    bad("D1 mods.toml 里没写「为什么必须 required」的理由注释")
else:
    ok("D1 mods.toml 里有 required 的理由注释")

# build.gradle 里要有 compileOnly 的 Curios
bg = read(os.path.join(ROOT, "build.gradle"))
if "libs/curios-neoforge-9.5.1+1.21.1.jar" not in bg:
    bad("D2 build.gradle 里没有 Curios 的本地 jar 依赖")
elif "compileOnly files('libs/curios-neoforge-9.5.1+1.21.1.jar')" not in bg:
    bad("D2 Curios 依赖不是 compileOnly（不能进产物 jar）")
else:
    ok("D2 build.gradle: compileOnly libs/curios-neoforge-9.5.1+1.21.1.jar")
if not os.path.exists(os.path.join(ROOT, "libs", "curios-neoforge-9.5.1+1.21.1.jar")):
    bad("D2 libs/ 下没有 Curios 的 jar（离线构建会失败）")
else:
    ok("D2 libs/curios-neoforge-9.5.1+1.21.1.jar 在位")

# ============================================================
#  组 F：ZF165 复核抓出来的"开发运行期"雷（§4.175）
# ============================================================

# F1 CuriosBridge 带 @EventBusSubscriber ⇒ FML 会对它 getDeclaredMethods()，而反射要解析
#    **全部**方法描述符（私有的也算）。本类有四个方法签名里带 Curios 类型 ⇒
#    只要某个 run 配置的 classpath 上没有 Curios，启动就 NoClassDefFoundError。
#    ⇒ build.gradle 必须给运行期也挂一份（localRuntime），且**不能**是 implementation
#      （那会把 Curios 打进产物 / 变成玩家依赖）。
if "localRuntime files('libs/curios-neoforge-9.5.1+1.21.1.jar')" not in bg:
    bad("F1 build.gradle 缺 localRuntime 的 Curios —— "
        "runData / runGameTestServer / runJunit 这些没有 mods 目录的 run 会在启动时"
        "抛 NoClassDefFoundError（§4.175）")
else:
    ok("F1 build.gradle 有 localRuntime 的 Curios（开发运行期 classpath 上也有）")
if re.search(r"^\s*(implementation|api)\s+files\('libs/curios-", bg, re.M):
    bad("F1 Curios 被写成了 implementation/api（会被打进产物 jar / 变成玩家依赖）")
else:
    ok("F1 Curios 没有写成 implementation/api")

# F2 @EventBusSubscriber + 私有方法带 Curios 类型：登记这件事本身是**有意**的，
#    门上只钉住"必须有 F1 那行兜底"，同时把带 Curios 类型的成员数列出来备查。
if os.path.exists(os.path.join(ROOT, "src/main/java/com/potatost/mod", BRIDGE)):
    b = java(BRIDGE)
    sig = [ln.strip() for ln in b.splitlines()
           if ("Curios" in ln or "ICurio" in ln or "SlotContext" in ln)
           and re.match(r"\s*(public|private|protected)\s", ln)]
    info("F2 CuriosBridge 里签名带 Curios 类型的成员 %d 个（F1 就是为它们兜底的）" % len(sig))

# ============================================================
#  组 E：产物 jar（有就查，没有就只记一行 INFO）
# ============================================================

jar_path = os.path.join(ROOT, "build", "libs", "potato_s_t-0.13.jar")
if os.path.exists(jar_path):
    try:
        z = zipfile.ZipFile(jar_path)
        names = set(z.namelist())
        for rel in (head_rel, back_rel, ent_rel):
            if rel in names:
                ok("E1 产物 jar 里有 " + rel)
            else:
                bad("E1 产物 jar 里**没有** " + rel + "（打包那一步要重打）")
        if "com/potatost/mod/CuriosBridge.class" in names:
            ok("E1 产物 jar 里有 CuriosBridge.class")
        else:
            bad("E1 产物 jar 里没有 CuriosBridge.class")
        leaked = [n for n in names if n.startswith("top/theillusivec4/")]
        if leaked:
            bad("E1 产物 jar 里混进了 Curios 的类", ", ".join(sorted(leaked)[:5]))
        else:
            ok("E1 产物 jar 里没有混进 Curios 的类（compileOnly 生效）")
    except Exception as exc:  # noqa: BLE001
        bad("E1 读产物 jar 失败", repr(exc))
else:
    info("E1 没有 build/libs/potato_s_t-0.13.jar —— 还没打包，跳过（打包后重跑本门即可）")

# ============================================================
#  收尾
# ============================================================

lines = []
lines.append("ZF165 常驻门（Curios 饰品栏联动）—— 只读校验")
lines.append("")
lines.append("通过 = %d   失败 = %d" % (len(oks), len(fails)))
lines.append("")
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

text = "\n".join(lines) + "\n"
os.makedirs(os.path.dirname(LOG), exist_ok=True)
with io.open(LOG, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)

print("ZF165 gate: passed=%d failed=%d  -> %s" % (len(oks), len(fails), LOG))
sys.exit(1 if fails else 0)
