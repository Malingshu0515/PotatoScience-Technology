# -*- coding: utf-8 -*-
u"""_zf184_falsify.py —— ZF184 的**反证刀**：砍一刀，`_zf184_verify.py` 必须当场变红。

跑法：python build\\zftools\\_zf184_falsify.py
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
SWORD = os.path.join(ROOT, r"src\main\java\com\potatost\mod\VibraniumSwordItem.java")
GATE = os.path.join(ZT, u"_zf184_verify.py")
TMP = os.path.join(ZT, u"_zf184_falsify_bak")

KNIVES = [
    dict(id=u"K1", why=u"把基数换回 baseAttackDamage（不含手持武器那条；A1/A2 要抓到）", path=SWORD,
         old=u"        double n = player.getAttributeValue(net.minecraft.world.entity.ai.attributes.Attributes.ATTACK_DAMAGE);",
         new=u"        double n = ShockwaveManager.baseAttackDamage(player);", want=u"A"),
    dict(id=u"K2", why=u"把附魔加成那一句删掉（A3 要抓到）", path=SWORD,
         old=u"            float damage = net.minecraft.world.item.enchantment.EnchantmentHelper.modifyDamage(\n"
             u"                    level, player.getMainHandItem(), target, source, baseDamage);",
         new=u"            float damage = baseDamage;", want=u"A3"),
    dict(id=u"K3", why=u"把附魔加成挪到循环**外**（A4「逐目标」要抓到）", path=SWORD,
         old=u"        float baseDamage = (float) (n + SLAM_EXTRA_DAMAGE);",
         new=u"        float baseDamage = (float) (n + SLAM_EXTRA_DAMAGE);\n"
             u"        baseDamage = net.minecraft.world.item.enchantment.EnchantmentHelper.modifyDamage(\n"
             u"                level, player.getMainHandItem(), player, source, baseDamage);",
         want=u"A4"),
]


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_gate():
    r = subprocess.run([sys.executable, GATE], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=300)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def main():
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)
    ok, bad = 0, []
    for k in KNIVES:
        path = k[u"path"]
        bak = os.path.join(TMP, k[u"id"] + u"__" + os.path.basename(path))
        shutil.copy2(path, bak)
        before = sha1(path)
        cut = True
        try:
            text = io.open(path, encoding="utf-8", newline=u"").read()
            if k[u"old"] not in text:
                cut = False
                bad.append(k[u"id"] + u"(锚点找不到)")
                print(u"  [FAIL] %s 刀砍不下去 —— %s" % (k[u"id"], k[u"why"]))
            else:
                io.open(path, "w", encoding="utf-8", newline=u"").write(
                    text.replace(k[u"old"], k[u"new"], 1))
            if cut:
                rc, out = run_gate()
                caught = [l.strip() for l in out.split(u"\n")
                          if l.strip().startswith(u"[FAIL]") and k[u"want"] in l]
                if rc != 0 and caught:
                    ok += 1
                    print(u"  [OK]   %s 门红了，抓到：%s" % (k[u"id"], caught[0][:64]))
                else:
                    bad.append(k[u"id"])
                    print(u"  [FAIL] %s 门没抓到（rc=%d，想看到 %s）" % (k[u"id"], rc, k[u"want"]))
        finally:
            if cut:
                shutil.copy2(bak, path)
            if sha1(path) != before:
                bad.append(k[u"id"] + u"(还原不一致)")
    print(u"\n反证刀：%d/%d 抓到（漏网 %s）" % (ok, len(KNIVES), u" / ".join(bad) if bad else u"无"))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
