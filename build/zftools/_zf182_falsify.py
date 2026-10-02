# -*- coding: utf-8 -*-
u"""_zf182_falsify.py —— ZF182 的**反证刀**：砍一刀，`_zf182_verify.py` 必须当场变红。

跑法：python build\\zftools\\_zf182_falsify.py
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
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
DTYPE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\damage_type")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang\zh_cn.json")
GATE = os.path.join(ZT, u"_zf182_verify.py")
TMP = os.path.join(ZT, u"_zf182_falsify_bak")

SWORD = os.path.join(JAVA, u"VibraniumSwordItem.java")
BEHEAD = os.path.join(JAVA, u"VibraniumBeheading.java")

KNIVES = [
    dict(id=u"K1", why=u"把猛砸的伤害换回原版 player_attack（口径 B 就废了；A3 要抓到）", path=SWORD,
         old=u"        DamageSource source = slamSource(player);",
         new=u"        DamageSource source = level.damageSources().playerAttack(player);", want=u"A3"),
    dict(id=u"K2", why=u"把处理器的判据从伤害类型改成「总是放行」（A4 要抓到）", path=BEHEAD,
         old=u"        if (!event.getSource().is(VibraniumSwordItem.VIBRANIUM_SLAM)) {",
         new=u"        if (false) {", want=u"A4"),
    dict(id=u"K3", why=u"删掉 damage_type JSON 里的 id（A1 要抓到）", path=os.path.join(DTYPE, u"vibranium_slam.json"),
         old=u"potato_s_t.vibranium_slam", new=u"potato_s_t.renamed", want=u"A1"),
    dict(id=u"K4", why=u"把 tooltip 行数改回 3（C1 要抓到）", path=SWORD,
         old=u"    private static final int TOOLTIP_LINES = 4;",
         new=u"    private static final int TOOLTIP_LINES = 3;", want=u"C1"),
    dict(id=u"K5", why=u"从 zh_cn 删掉斩首那行说明（C2 要抓到）", path=LANG,
         old=u'  "tooltip.potato_s_t.vibranium_sword.4":', new=u'  "tooltip.potato_s_t.vibranium_sword.4_DEL":',
         want=u"C2"),
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
        if not os.path.isfile(path):
            bad.append(k[u"id"] + u"(文件不在)")
            continue
        bak = os.path.join(TMP, k[u"id"] + u"__" + os.path.basename(path))
        shutil.copy2(path, bak)
        before = sha1(path)
        cut = True
        try:
            text = io.open(path, encoding="utf-8", newline=u"").read()
            if k[u"old"] not in text:
                cut = False
                bad.append(k[u"id"] + u"(锚点找不到)")
                print(u"  [FAIL] %s 刀砍不下去：找不到锚点 —— %s" % (k[u"id"], k[u"why"]))
            else:
                io.open(path, "w", encoding="utf-8", newline=u"").write(
                    text.replace(k[u"old"], k[u"new"], 1))
            if cut:
                rc, out = run_gate()
                caught = [l.strip() for l in out.split(u"\n")
                          if l.strip().startswith(u"[FAIL]") and k[u"want"] in l]
                if rc != 0 and caught:
                    ok += 1
                    print(u"  [OK]   %s 门红了，抓到：%s" % (k[u"id"], caught[0][:66]))
                else:
                    bad.append(k[u"id"])
                    print(u"  [FAIL] %s 门没抓到（rc=%d，想看到 %s）—— %s" % (k[u"id"], rc, k[u"want"], k[u"why"]))
        finally:
            if cut:
                shutil.copy2(bak, path)
            if not os.path.isfile(path) or sha1(path) != before:
                bad.append(k[u"id"] + u"(还原不一致)")
    print(u"\n反证刀：%d/%d 抓到（漏网 %s）" % (ok, len(KNIVES), u" / ".join(bad) if bad else u"无"))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
