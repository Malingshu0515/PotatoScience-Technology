# -*- coding: utf-8 -*-
"""_zf201_falsify.py —— 0.16 ZF201 **反证刀**（证明 `_zf201_verify.py` 真的会失败）

只砍 NeoForge 1.21.1 一侧（另一侧的判据与它同形，且 Forge 工程没有 Python 工具链）。
五刀都砍"用户第二轮点名的数"，每一刀都必须被探针当场咬住：

  K1 钢剑档位的挖掘等级改成钻石（用户没提剑 ⇒ 剑该保持铁）
  K2 钢斧挖掘速度 12.0 → 6.0（用户点名"金挖掘速度"）
  K3 钢镐挖掘等级改成铁（用户点名"钻石挖掘等级"）
  K4 钢剑自带附魔的横扫等级 3 → 1（用户点名 III）
  K5 把 onCraftedBy 里挂附魔那两行删掉（"做出来自带"整条失效，但游戏里不报错）

跑法：
    python build/zftools/_zf201_falsify.py            # 全部
    python build/zftools/_zf201_falsify.py K4         # 只跑名字含 K4 的
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

ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
ZT = os.path.join(ROOT, "build", "zftools")
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
BAK = os.path.join(ROOT, "build", "tmp", "zf201_falsify_bak_%d" % os.getpid())

TIERS = os.path.join(SRC, "ModTiers.java")
SWORD = os.path.join(SRC, "SteelSwordItem.java")

KNIVES = [
    (u"K1 钢剑档位挖钻石等级（用户没提剑，剑该保持铁）",
     TIERS, u"STEEL_SWORD = build(STEEL_USES, STEEL_DAMAGE_BONUS, STEEL_SPEED,\n"
            u"            BlockTags.INCORRECT_FOR_IRON_TOOL",
     u"STEEL_SWORD = build(STEEL_USES, STEEL_DAMAGE_BONUS, STEEL_SPEED,\n"
     u"            BlockTags.INCORRECT_FOR_DIAMOND_TOOL"),
    (u"K2 钢斧挖掘速度 12.0 → 6.0（用户点名金挖掘速度）",
     TIERS, u"STEEL_AXE_SPEED = 12.0F;", u"STEEL_AXE_SPEED = 6.0F;"),
    (u"K3 钢镐挖掘等级改成铁（用户点名钻石等级）",
     TIERS, u"STEEL_PICKAXE = build(STEEL_USES, STEEL_DAMAGE_BONUS, STEEL_SPEED,\n"
             u"            BlockTags.INCORRECT_FOR_DIAMOND_TOOL",
     u"STEEL_PICKAXE = build(STEEL_USES, STEEL_DAMAGE_BONUS, STEEL_SPEED,\n"
     u"            BlockTags.INCORRECT_FOR_IRON_TOOL"),
    (u"K4 钢剑自带的横扫等级 III → I",
     SWORD, u"public static final int SWEEPING_EDGE_LEVEL = 3;",
     u"public static final int SWEEPING_EDGE_LEVEL = 1;"),
    (u"K5 删掉 onCraftedBy 里挂附魔的两行（游戏里不报错，只是「自带」没了）",
     SWORD, u"        apply(stack, level, Enchantments.SHARPNESS, SHARPNESS_LEVEL);\n"
            u"        apply(stack, level, Enchantments.SWEEPING_EDGE, SWEEPING_EDGE_LEVEL);",
     u"        // 反证：把附魔挂载整段拿掉"),
]

fails = []


def sha(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


def run_verify():
    p = subprocess.run([sys.executable, os.path.join(ZT, u"_zf201_verify.py")],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def run_compile():
    log = os.path.join(ZT, u"_zf201_falsify_compile.log")
    with open(log, "wb") as fh:
        p = subprocess.run(["cmd", "/c", "cd /d %s && .\\gradlew.bat compileJava --offline" % ROOT],
                           stdout=fh, stderr=subprocess.STDOUT)
    return p.returncode


def main():
    only = sys.argv[1:] or None
    if os.path.isdir(BAK):
        shutil.rmtree(BAK)
    os.makedirs(BAK)
    manifest = []
    for t in sorted(set(k[1] for k in KNIVES)):
        dst = os.path.join(BAK, os.path.basename(t))
        shutil.copy2(t, dst)
        manifest.append((t, dst, sha(t)))
        print(u"  [OK]   备份 %-18s %s" % (os.path.basename(t), sha(t)[:16]))

    def restore():
        for t, dst, h in manifest:
            shutil.copy2(dst, t)
            os.utime(t, None)      # 顶 mtime，逼 gradle 重编（并发构建下 copy2 会留旧 mtime）
            if sha(t) != h:
                fails.append(u"还原后哈希不符：%s" % os.path.basename(t))

    rc0, out0 = run_verify()
    print(u"\n基线：探针退出码 %s（必须 0）" % rc0)
    if rc0 != 0:
        print(u"  [FAIL] 基线不是绿的，先修好再做反证")
        return 1

    print(u"\n================ 逐刀 ================")
    for name, path, old, new in KNIVES:
        if only and not any(o in name for o in only):
            continue
        before = sha(path)
        text = io.open(path, encoding="utf-8").read()
        if text.count(old) != 1:
            print(u"  [FAIL] %s —— 锚点命中 %d 次" % (name, text.count(old)))
            fails.append(u"锚点不唯一：%s" % name)
            continue
        io.open(path, "w", encoding="utf-8", newline=u"").write(text.replace(old, new))
        rc_c = run_compile()
        rc, out = run_verify()
        gate_ok = (rc != 0) and (rc_c == 0)
        print(u"  [%s] %s" % (u"OK" if gate_ok else u"FAIL", name))
        print(u"         ↳ 编译退出码 %s，探针退出码 %s（要求非 0）" % (rc_c, rc))
        for l in [x for x in out.split(u"\n") if x.strip().startswith(u"!!")][:2]:
            print(u"         ↳ %s" % l.strip()[:110])
        if not gate_ok:
            fails.append(name)
        restore()
        rc_c2 = run_compile()
        rc2, out2 = run_verify()
        if rc2 != 0:                       # 并发编译偶发假红：再编一次复核
            print(u"         ↳ 第一次重编后探针仍红，再编一次复核")
            run_compile()
            rc2, out2 = run_verify()
        back = sha(path) == before
        print(u"         ↳ 还原后哈希一致 %s，探针回到全绿 %s"
              % (u"✓" if back else u"✗", u"✓" if rc2 == 0 else u"✗"))
        if not (back and rc2 == 0):
            fails.append(u"还原失败：%s" % name)
        print(u"")

    print(u"================ 收尾 ================")
    for t, _d, h in manifest:
        same = sha(t) == h
        print(u"  [%s] %s 回到备份状态" % (u"OK" if same else u"FAIL", os.path.basename(t)))
        if not same:
            fails.append(u"收尾哈希不符：%s" % os.path.basename(t))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
