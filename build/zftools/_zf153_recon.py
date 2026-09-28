# -*- coding: utf-8 -*-
r"""ZF153 侦察（**只读，一个字节都不改**）：振金剑开工前必须钉死的事实。

本轮要做**振金剑**（用户给了一张素材 `振金剑_001.png`），需求逐字：
「加个振金剑材质在素材 无法破坏 拿在手里免疫凋零，缓慢，挖掘疲劳 24点伤害 1.4攻击速度
  1附魔权重 shift+右键猛击地面 击飞6x6除自己的所有生物 并对其造成n+12点伤害
  n为玩家基础伤害 和4s的失明 4s的缓慢效果 冷却6s」。

开工前要钉死的四件事（全是"我以为"最容易出错的地方）：

  ① **素材身份** —— 文件名是「振金剑」，但 16x16 上剑/镐/锄肉眼不保险。判据用**形状**：
     素材 alpha 掩码 vs 原版六档 × 五种工具贴图的 **IoU**（ZF136 认锭、ZF141 认四把工具
     用的是同一招）。顺带体检：真 PNG 吗 / 尺寸 / 位深 / 有没有 alpha。
  ② **原版剑的属性算式** —— 用户给的「24点伤害 1.4攻击速度」是**游戏里显示的总值**，
     落到 `createAttributes(tier, 参数, 攻速参数)` 上要反推参数。逐字从 sources.jar 现抠
     `SwordItem.createAttributes` 与 `Items.java` 里 diamond_sword 那一行，不凭记忆写 3 / -2.4。
  ③ **「拿在手里免疫三种效果」的挂点** —— 到底是每 tick 把效果抹掉，还是从**源头**拒绝？
     NeoForge 有没有 `MobEffectEvent.Applicable` 这个"能不能挂上"的事件、签名是什么，
     从 sources.jar 现读（这条决定实现方式，也决定探针怎么验）。
  ④ **「击飞」与「n」的现成口径** —— 击飞用哪个原版方法（`LivingEntity.knockback` 的签名与
     参数方向）；`n`（玩家基础伤害）本工程已经有 `ShockwaveManager.baseAttackDamage`
     这个**已过探针**的实现，本轮必须复用它而不是另写一份。

跑法：python build\zftools\_zf153_recon.py
产出：_zf153_recon.txt（UTF-8，给人看）+ 控制台同一份
"""

import io
import json
import os
import sys
import zipfile

PROJ = r"E:\PotatoST"
ZFTOOLS = os.path.join(PROJ, "build", "zftools")
USER_ASSETS = os.path.join(PROJ, "build", u"\u7528\u6237\u7d20\u6750")
RES = os.path.join(PROJ, "src", "main", "resources")
ASSETS = os.path.join(RES, "assets", "potato_s_t")
ITEM_TEX = os.path.join(ASSETS, "textures", "item")
ITEM_MODELS = os.path.join(ASSETS, "models", "item")
LANG_DIR = os.path.join(ASSETS, "lang")

CLIENT_EXTRA = (r"E:\gradle-home\caches\ng_execute"
                r"\b618213606478f4c62e6974e895a173b103a054e4a7be1bf630f2feeb65c5c3b"
                r"\client-extra.jar")
SOURCES_JAR = os.path.join(PROJ, "build", "neoForm",
                           "neoFormJoined1.21.1-20240808.144430", "sources.jar")

OUT = []
OUTF = None


def w(line=u""):
    OUT.append(line)


def flush():
    text = u"\n".join(OUT) + u"\n"
    with io.open(os.path.join(ZFTOOLS, "_zf153_recon.txt"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    sys.stdout.write(text)


# 复用 ZF141 的 PNG 解码器（本工程已过探针的那一份，不另写）
sys.path.insert(0, ZFTOOLS)
import _zf141_recon as R  # noqa: E402


# ---------------------------------------------------------------- ① 素材身份
VANILLA_MATS = [u"wooden", u"stone", u"iron", u"golden", u"diamond", u"netherite"]
TOOL_KINDS = [u"sword", u"pickaxe", u"axe", u"shovel", u"hoe"]

USER_FILES = [(u"\u632f\u91d1\u5251_001.png", u"sword")]   # 振金剑_001.png


def section1():
    w(u"=" * 78)
    w(u"① 素材身份：形状 IoU（vs 原版六档 x 五种工具）+ 体检")
    w(u"=" * 78)
    with zipfile.ZipFile(CLIENT_EXTRA) as zf:
        van = {}
        for mat in VANILLA_MATS:
            for kind in TOOL_KINDS:
                p = u"assets/minecraft/textures/item/%s_%s.png" % (mat, kind)
                try:
                    _w, _h, px = R.decode_png(zf.read(p))
                except KeyError:
                    continue
                van[(mat, kind)] = R.alpha_mask(px)
        w(u"原版贴图取到 %d 张（client-extra.jar）" % len(van))

        for fname, guess in USER_FILES:
            path = os.path.join(USER_ASSETS, fname)
            if not os.path.exists(path):
                w(u"!! 素材不存在：%s" % path)
                continue
            with open(path, "rb") as fh:
                data = fh.read()
            iw, ih, ipx = R.decode_png(data)
            imask = R.alpha_mask(ipx)
            opaque = sum(1 for p in ipx if p[3] == 255)
            semi = sum(1 for p in ipx if 0 < p[3] < 255)
            colors = len(set(ipx))
            import hashlib
            sha1 = hashlib.sha1(data).hexdigest()
            w(u"")
            w(u"【%s】 %dx%d  sha1=%s" % (fname, iw, ih, sha1))
            w(u"    非空像素 %d / %d  全不透明 %d  半透明 %d  独立颜色 %d"
              % (sum(imask), iw * ih, opaque, semi, colors))
            scores = []
            for (mat, kind), mask in van.items():
                if len(mask) != len(imask):
                    continue
                scores.append((R.iou(imask, mask), mat, kind))
            scores.sort(reverse=True)
            for s, mat, kind in scores[:6]:
                mark = u"  <== 文件名猜的" if kind == guess else u""
                w(u"    IoU %.4f  原版 %-9s %-8s%s" % (s, mat, kind, mark))
            best = scores[0]
            w(u"    => 形状最像：%s_%s（IoU %.4f）；与文件名推断 %s"
              % (best[1], best[2], best[0],
                 u"**一致**" if best[2] == guess else u"**不一致，要问用户**"))
            # 同尺寸的"同族"对照：盘上已有星璨钢剑，看两张剑像不像（都是剑则应当偏高）
            for other in (u"star_steel_sword.png", u"vibranium_ingot.png"):
                op = os.path.join(ITEM_TEX, other)
                if not os.path.exists(op):
                    continue
                with open(op, "rb") as fh:
                    ow, oh, opx = R.decode_png(fh.read())
                if (ow, oh) == (iw, ih):
                    w(u"    对照：与盘上 %s 的 alpha IoU = %.4f"
                      % (other, R.iou(imask, R.alpha_mask(opx))))
                else:
                    w(u"    对照：盘上 %s 是 %dx%d，尺寸不同不做 IoU" % (other, ow, oh))


# ---------------------------------------------------------------- ② 原版源码
def src_of(zf, want):
    names = zf.namelist()
    hit = [n for n in names if n.endswith(want)]
    if not hit:
        return None
    return zf.read(hit[0]).decode("utf-8", "replace")


def dump_method(src, needles, label, max_lines=40):
    """把含 needle 的行的**整个方法体**打出来（按大括号配平，够用即可）。"""
    lines = src.split(u"\n")
    printed = 0
    for i, line in enumerate(lines, 1):
        if not any(n in line for n in needles):
            continue
        w(u"  %5d | %s" % (i, line.rstrip()))
        depth = line.count(u"{") - line.count(u"}")
        j = i
        while depth > 0 and j < len(lines) and printed < max_lines:
            j += 1
            if j - 1 >= len(lines):
                break
            w(u"  %5d | %s" % (j, lines[j - 1].rstrip()))
            depth += lines[j - 1].count(u"{") - lines[j - 1].count(u"}")
            printed += 1
    if printed == 0:
        w(u"  !! %s：一行都没匹配到（needles=%s）" % (label, needles))


def section2():
    w(u"")
    w(u"=" * 78)
    w(u"② 原版事实（sources.jar 现抠）")
    w(u"=" * 78)
    if not os.path.exists(SOURCES_JAR):
        w(u"!! 找不到 sources.jar：%s" % SOURCES_JAR)
        return
    with zipfile.ZipFile(SOURCES_JAR) as zf:
        # --- ②.1 剑的属性算式
        w(u"")
        w(u"---- SwordItem.java：构造器 + createAttributes ----")
        s = src_of(zf, u"net/minecraft/world/item/SwordItem.java")
        if s is None:
            w(u"  !! 没有 SwordItem.java")
        else:
            for i, line in enumerate(s.split(u"\n"), 1):
                t = line.strip()
                if t.startswith(u"public SwordItem") or u"createAttributes" in line:
                    w(u"  %5d | %s" % (i, t))
            dump_method(s, [u"public static Multimap"], u"SwordItem.createAttributes")
        w(u"")
        w(u"---- Items.java：diamond_sword / netherite_sword 两行 ----")
        s = src_of(zf, u"net/minecraft/world/item/Items.java")
        if s is not None:
            for i, line in enumerate(s.split(u"\n"), 1):
                if u"diamond_sword" in line or u"netherite_sword" in line:
                    w(u"  %5d | %s" % (i, line.strip()))
        w(u"")
        w(u"---- Item.java：createAttributes(float,float) 那个重载 ----")
        s = src_of(zf, u"net/minecraft/world/item/Item.java")
        if s is not None:
            dump_method(s, [u"public static ItemAttributeModifiers createAttributes(float"],
                        u"Item.createAttributes")

        # --- ②.2 三种效果与"能不能挂上"的事件
        w(u"")
        w(u"---- MobEffects.java：凋零 / 缓慢 / 挖掘疲劳 三个常量 ----")
        s = src_of(zf, u"net/minecraft/world/effect/MobEffects.java")
        if s is not None:
            for i, line in enumerate(s.split(u"\n"), 1):
                if any(k in line for k in (u"WITHER", u"MOVEMENT_SLOWDOWN", u"DIG_SLOWDOWN")):
                    w(u"  %5d | %s" % (i, line.strip()))
        w(u"")
        w(u"---- MobEffectEvent.java：有哪些子类、Applicable 长什么样 ----")
        s = src_of(zf, u"net/neoforged/neoforge/event/entity/living/MobEffectEvent.java")
        if s is None:
            w(u"  !! sources.jar 里没有 MobEffectEvent.java")
        else:
            for i, line in enumerate(s.split(u"\n"), 1):
                t = line.strip()
                if (t.startswith(u"public static class") or t.startswith(u"public static final class")
                        or t.startswith(u"public class") or t.startswith(u"@Cancelable")
                        or t.startswith(u"@HasResult")):
                    w(u"  %5d | %s" % (i, t))
            dump_method(s, [u"public static class Applicable"], u"Applicable", max_lines=60)
        w(u"")
        w(u"---- LivingEntity.java：removeEffect / knockback / hurt 的签名 ----")
        s = src_of(zf, u"net/minecraft/world/entity/LivingEntity.java")
        if s is not None:
            for i, line in enumerate(s.split(u"\n"), 1):
                t = line.strip()
                if t.startswith(u"public boolean removeEffect(") \
                        or t.startswith(u"public void knockback(") \
                        or t.startswith(u"public boolean hurt(") \
                        or t.startswith(u"public boolean addEffect("):
                    w(u"  %5d | %s" % (i, t))
        w(u"")
        w(u"---- LivingEntity.java：knockback 的实现（击飞拿它当基准） ----")
        if s is not None:
            dump_method(s, [u"public void knockback(double"], u"knockback", max_lines=45)
        w(u"")
        w(u"---- Player.java：getCooldowns / ItemCooldowns.addCooldown ----")
        s = src_of(zf, u"net/minecraft/world/entity/player/Player.java")
        if s is not None:
            for i, line in enumerate(s.split(u"\n"), 1):
                if u"getCooldowns" in line:
                    w(u"  %5d | %s" % (i, line.strip()))
        s = src_of(zf, u"net/minecraft/world/item/ItemCooldowns.java")
        if s is not None:
            for i, line in enumerate(s.split(u"\n"), 1):
                if u"addCooldown" in line or u"isOnCooldown" in line:
                    w(u"  %5d | %s" % (i, line.strip()))
        w(u"")
        w(u"---- Level.java：圈生物用的两个方法签名 ----")
        s = src_of(zf, u"net/minecraft/world/level/Level.java")
        if s is not None:
            for i, line in enumerate(s.split(u"\n"), 1):
                t = line.strip()
                if t.startswith(u"public List<Entity> getEntities(") \
                        or t.startswith(u"public <T extends Entity> List<T> getEntitiesOfClass("):
                    w(u"  %5d | %s" % (i, t))
        w(u"")
        w(u"---- AABB.java：inflate 的两个重载 ----")
        s = src_of(zf, u"net/minecraft/world/phys/AABB.java")
        if s is not None:
            for i, line in enumerate(s.split(u"\n"), 1):
                t = line.strip()
                if t.startswith(u"public AABB inflate("):
                    w(u"  %5d | %s" % (i, t))


# ---------------------------------------------------------------- ③ 盘上现状
def section3():
    w(u"")
    w(u"=" * 78)
    w(u"③ 盘上现状（照着写的那几份）")
    w(u"=" * 78)
    w(u"")
    w(u"---- models/item/ 里所有 vibranium_* / star_steel_sword ----")
    if os.path.isdir(ITEM_MODELS):
        for n in sorted(os.listdir(ITEM_MODELS)):
            if n.startswith(u"vibranium") or n == u"star_steel_sword.json":
                with io.open(os.path.join(ITEM_MODELS, n), encoding="utf-8") as fh:
                    w(u"  %-34s %s" % (n, fh.read().replace(u"\n", u"").replace(u"  ", u" ")))
    w(u"")
    w(u"---- textures/item/ 里所有 vibranium_* / star_steel_* ----")
    if os.path.isdir(ITEM_TEX):
        for n in sorted(os.listdir(ITEM_TEX)):
            # ⚠ 必须限定 .png：vibranium_ingot.png.mcmeta 也以 vibranium 开头
            #   （ZF132 的动画描述文件），第一版没限定就在它上面炸了
            if not n.endswith(u".png"):
                continue
            if n.startswith(u"vibranium") or n.startswith(u"star_steel"):
                p = os.path.join(ITEM_TEX, n)
                with open(p, "rb") as fh:
                    _w2, _h2, px2 = R.decode_png(fh.read())
                w(u"  %-34s %dx%d  非空 %d" % (n, _w2, _h2, sum(R.alpha_mask(px2))))
    w(u"")
    w(u"---- lang：与振金 / 星璨钢剑有关的全部键（zh_cn 与 en_us 并排） ----")
    langs = {}
    for code in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"):
        p = os.path.join(LANG_DIR, code + u".json")
        if os.path.exists(p):
            with io.open(p, encoding="utf-8") as fh:
                langs[code] = json.load(fh)
    w(u"  语言文件：%s" % u", ".join(u"%s(%d 键)" % (c, len(v)) for c, v in sorted(langs.items())))
    zh = langs.get(u"zh_cn", {})
    en = langs.get(u"en_us", {})
    for k in sorted(zh):
        if u"vibranium" in k or u"star_steel_sword" in k or u"star_steel_tool" in k:
            w(u"  %s" % k)
            w(u"      zh: %s" % zh.get(k))
            if k in en:
                w(u"      en: %s" % en[k])
            if k not in en:
                w(u"      en: **缺**")
    w(u"")
    w(u"---- 键集合：四份（zh/en/ja/ru）与 lzh 的差集 ----")
    four = [langs.get(c, {}) for c in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru")]
    if all(four):
        base = set(four[0])
        for i, c in enumerate((u"en_us", u"ja_jp", u"ru_ru"), 1):
            d1 = base - set(four[i])
            d2 = set(four[i]) - base
            w(u"  zh_cn vs %s：只在 zh 有 %s / 只在对方有 %s"
              % (c, sorted(d1) or u"无", sorted(d2) or u"无"))
    lzh = langs.get(u"lzh")
    if lzh is not None and four[0]:
        w(u"  lzh 独有：%s" % (sorted(set(lzh) - set(four[0])) or u"无"))
        w(u"  lzh 缺少（相对 zh_cn）：%s" % (sorted(set(four[0]) - set(lzh))[:20] or u"无"))


# ---------------------------------------------------------------- ④ 素材凭据表
def section4():
    w(u"")
    w(u"=" * 78)
    w(u"④ build/用户素材/_来源凭据.json 的结构（照抄一条）")
    w(u"=" * 78)
    p = os.path.join(USER_ASSETS, u"_来源凭据.json")
    if not os.path.exists(p):
        w(u"!! 没有 %s" % p)
        return
    with io.open(p, encoding="utf-8") as fh:
        data = json.load(fh)
    w(u"顶层类型：%s；键：%s" % (type(data).__name__,
                             sorted(data.keys()) if isinstance(data, dict) else u"—"))
    items = data.get(u"素材") if isinstance(data, dict) else None
    if items is None and isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) and any(u".png" in kk for kk in v.keys()):
                items = v
                w(u"（条目挂在顶层键 %s 下面）" % k)
                break
    if isinstance(items, dict):
        w(u"条目数：%d；键名示例：%s" % (len(items), sorted(items)[:4]))
        for key in sorted(items):
            if u"剑" in key and u"星璨" in key:
                w(u"")
                w(u"---- 样板条目：%s ----" % key)
                w(json.dumps(items[key], ensure_ascii=False, indent=2))
                break


if __name__ == u"__main__":
    section1()
    section2()
    section3()
    section4()
    flush()
