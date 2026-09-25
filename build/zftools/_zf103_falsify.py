# -*- coding: utf-8 -*-
u"""_zf103_falsify.py —— **本轮自己的反证刀**：证明 `_zf103_verify.py` 真的会失败

档案 §4.17 的口径：**"能失败的检查"才算检查**。
所以这里对每个关键数值各砍一刀（改坏 → 重编 → 跑本轮探针），
要求"探针必须报错"，然后逐字还原并复核哈希 + 探针回到全绿。

⚠ 每刀都**先从备份还原再砍下一刀**（刀与刀之间不能叠加，否则分不清是谁被抓到）。
⚠ 备份用 `Copy-Item` 逐份拷贝并**核对副本自己的哈希**（档案 §10 的 ZF29 事故）。
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
ZT = os.path.join(PROJ, "build", "zftools")
# ⚠ 目录名带进程号：两条并行流程各用各的备份，不互相踩（见 restore() 的说明）
BAK = os.path.join(ZT, "_zf103_falsify_bak_%d" % os.getpid())
CLS = os.path.join(PROJ, "build", "classes", "java", "main", "com", "potatost", "mod")
SRC = os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod")

fails = []


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def run_verify():
    u"""跑本轮探针，返回 (退出码, 尾部输出)。"""
    p = subprocess.run([sys.executable, os.path.join(ZT, "_zf103_verify.py")],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", "replace")
    return p.returncode, out


def run_compile():
    log = os.path.join(ZT, "_zf103_falsify_compile.log")
    with open(log, "wb") as fh:
        p = subprocess.run(["cmd", "/c", "cd /d %s && .\\gradlew.bat compileJava --offline "
                            "--no-build-cache" % PROJ], stdout=fh, stderr=subprocess.STDOUT)
    return p.returncode


# 每把刀：(名字, 要改的文件, 原文, 改成, 需要重编吗)
KNIVES = [
    (u"K1 钛合金头盔耐久 2801 → 2802",
     os.path.join(SRC, "ModArmorItems.java"), u"2801, 2.5", u"2802, 2.5", True),
    (u"K2 钛合金套附魔权重 25 → 22（掉到与金同级）",
     os.path.join(SRC, "ModArmorMaterials.java"),
     u"TITANIUM_ENCHANTMENT_VALUE = 25", u"TITANIUM_ENCHANTMENT_VALUE = 22", True),
    (u"K3 星璨钢胸甲护甲值 9.5 → 9（小数被丢掉）",
     os.path.join(SRC, "ModArmorItems.java"), u"3876, 9.5, 1.0", u"3876, 9.0, 1.0", True),
    (u"K4 星璨钢胸甲韧性 1.0 → 0.0",
     os.path.join(SRC, "ModArmorItems.java"), u"3876, 9.5, 1.0", u"3876, 9.5, 0.0", True),
    (u"K5 夜晚不掉耐久那条语义被抽掉（覆写还在，但只 super 转发）",
     os.path.join(SRC, "ModArmorPiece.java"),
     u"""            if (entity.level().isNight()) {
                return 0;                                   // 规则 ①：夜晚，每件各自生效
            }
""", u"", True),
    (u"K6 盔甲 Layer 从自己的贴图改成 gold（借原版）",
     os.path.join(SRC, "ModArmorMaterials.java"),
     u"""        ArmorMaterial.Layer layer = new ArmorMaterial.Layer(
                ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, name));""",
     u"""        ArmorMaterial.Layer layer = new ArmorMaterial.Layer(
                ResourceLocation.withDefaultNamespace("gold"));""", True),
    (u"K7 四语言里把 zh_cn 的 14 个新键之一删掉",
     os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "lang", "zh_cn.json"),
     u'  "item.potato_s_t.star_steel_ingot":  "星璨钢锭",\n', u"", False),
    (u"K8 钛合金头盔的背包模型 layer0 改成自己的贴图（不再借原版铁）",
     os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "models", "item",
                  "titanium_alloy_helmet.json"),
     u"minecraft:item/iron_helmet", u"potato_s_t:item/iron_helmet", False),
    # ---- ZF106 追加：用户自己给的盔甲图层贴图 ----
    #   K9 用的是"删文件"形态（old=None）：备份里会留一份，还原时拷回去
    (u"K9 删掉钛合金护腿的内层盔甲图（layer_2）",
     os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t",
                  "textures", "models", "armor", "titanium_alloy_layer_2.png"),
     None, None, False),
    (u"K10 盔甲 Layer 改回借原版铁",
     os.path.join(SRC, "ModArmorMaterials.java"),
     u"""        ArmorMaterial.Layer layer = new ArmorMaterial.Layer(
                ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, name));""",
     u"""        ArmorMaterial.Layer layer = new ArmorMaterial.Layer(
                ResourceLocation.withDefaultNamespace("iron"));""", True),
    # ---- ZF106 追加：用户本轮的两条修正 ----
    (u"K11 传送前不再免除摔落伤害（删掉 preventFallDamage 的调用）",
     os.path.join(SRC, "ModArmorSet.java"),
     u"            preventFallDamage(player);\n", u"", True),
    (u"K12 末地永久不掉耐久那条分支被抽掉",
     os.path.join(SRC, "ModArmorPiece.java"),
     u"""            if (entity.level().dimension() == Level.END
                    && ModArmorMaterials.hasFullStarSteelSet(entity)) {
                return 0;                                   // 规则 ②：末地 + 满套星璨钢，永久
            }
""", u"", True),
    # ---- ZF106 追加之二：伤害吸收不许提前续 ----
    (u"K13 伤害吸收变成提前 2 s 就续（护盾永远满着）",
     os.path.join(SRC, "ModArmorSet.java"),
     u"    private static final int ABSORPTION_REFRESH = 0;",
     u"    private static final int ABSORPTION_REFRESH = KNOCKBACK_MARGIN;", True),
]


def main():
    only = sys.argv[1:] or None
    if os.path.isdir(BAK):
        shutil.rmtree(BAK)
    os.makedirs(BAK)

    # ---- ① 备份 + 核对副本自己的哈希（§10）----
    print(u"================ 备份 ================")
    targets = sorted(set([k[1] for k in KNIVES]
                         + [os.path.join(CLS, "ModArmorItems.class"),
                            os.path.join(CLS, "ModArmorMaterials.class"),
                            os.path.join(CLS, "ModArmorPiece.class")]))

    manifest = []
    for t in targets:
        if not os.path.isfile(t):
            print(u"  [SKIP] %s（不存在）" % t)
            continue
        dst = os.path.join(BAK, os.path.basename(t) + u"." + hashlib.md5(
            t.encode("utf-8")).hexdigest()[:8])
        shutil.copy2(t, dst)
        h_src, h_dst = sha(t), sha(dst)
        ok = h_src == h_dst
        manifest.append((t, dst, h_dst))
        print(u"  [%s] %-46s %s" % (u"OK" if ok else u"FAIL", os.path.basename(t), h_dst[:16]))
        if not ok:
            fails.append(u"备份哈希不符：%s" % t)

    def restore():
        u"""逐份还原并核对副本自己的哈希。

        ⚠ 本轮真出过一次事故：跑到 K2 还原时抛 `FileNotFoundError: [WinError 3]`，
        整个脚本带着 traceback 退出、后面的刀全没跑。
        成因是**同一个备份目录被另一条并行流程清掉/移动**（两条线都在动 `_zf10*` 这批文件）。
        ⇒ 两条加固：① 备份目录名带**进程号**（两条线各用各的，不互相踩）；
                  ② 还原前先确认副本还在，缺了就**大声报错并把该刀判 FAIL**，不能静默。
        """
        for t, dst, h in manifest:
            if not os.path.isfile(dst):
                fails.append(u"备份副本不见了（另一条流程动过？）：%s" % dst)
                print(u"         ↳ [FAIL] 备份副本不见了：%s" % dst)
                continue
            shutil.copy2(dst, t)
            if sha(t) != h:
                fails.append(u"还原后哈希不符：%s" % t)

    # ---- ② 逐刀 ----
    print(u"")
    print(u"================ 逐刀 ================")
    for name, path, old, new, recompile in KNIVES:
        if only and not any(o in name for o in only):
            continue
        # `old is None` ⇒ 这把刀是"删文件"（用于"贴图必须存在"那类断言）
        before = sha(path) if os.path.isfile(path) else None
        if old is None:
            if before is None:
                print(u"  [SKIP] %s —— 目标文件本来就不存在" % name)
                fails.append(u"目标缺失：%s" % name)
                continue
            os.remove(path)
        else:
            text = io.open(path, encoding="utf-8").read()
            if text.count(old) != 1:
                print(u"  [SKIP] %s —— 锚点命中 %d 次（应为 1）" % (name, text.count(old)))
                fails.append(u"锚点不唯一：%s" % name)
                continue
            io.open(path, "w", encoding="utf-8", newline=u"").write(text.replace(old, new))

        rc_c = 0
        if recompile:
            rc_c = run_compile()
        rc_v, out = run_verify()
        caught = (rc_v != 0)
        # 抓到的必须是"数值/资源不对"这一类断言，不是编译失败导致的假捕获
        gate_ok = caught and (rc_c == 0 or not recompile)
        print(u"  [%s] %s" % (u"OK" if gate_ok else u"FAIL", name))
        print(u"         ↳ 编译退出码 %s，探针退出码 %s（要求非 0）" % (rc_c, rc_v))
        tail = [l for l in out.split(u"\n") if l.strip().startswith(u"!!")][:2]
        for l in tail:
            print(u"         ↳ %s" % l.strip()[:110])
        if not gate_ok:
            fails.append(name)

        # 还原
        restore()
        if recompile:
            run_compile()
        rc_v2, out2 = run_verify()
        # ⚠ `before is None` ⇒ 这把刀删过文件：还原后要求它**重新存在**（不能再算哈希）
        if before is None:
            back = os.path.isfile(path)
        else:
            back = os.path.isfile(path) and sha(path) == before
        back_ok = (rc_v2 == 0 and back)
        print(u"         ↳ 还原后%s %s，探针回到全绿 %s" %
              (u"文件回来了" if before is None else u"哈希一致",
               u"✓" if back else u"✗", u"✓" if rc_v2 == 0 else u"✗"))
        if not back_ok:
            fails.append(u"还原失败：%s" % name)
        print(u"")

    # ---- ③ 收尾：再核一遍所有被碰过的文件都回到原样 ----
    print(u"================ 收尾 ================")
    for t, _dst, h in manifest:
        # ⚠ 被 K9 删过的那份现在应重新存在；`manifest` 里的哈希就是它的原值
        same = os.path.isfile(t) and sha(t) == h
        print(u"  [%s] %s 回到备份状态" % (u"OK" if same else u"FAIL", os.path.basename(t)))
        if not same:
            fails.append(u"收尾哈希不符：%s" % t)

    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
