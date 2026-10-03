# -*- coding: utf-8 -*-
u"""_zf192_falsify.py —— ZF192 的**反证刀**：砍一刀，`_zf192_verify.py` 必须当场变红。

刀刀都砍在"本轮真正做的事"上：三处放行 / AIR 哨兵 / 新句子 / loadFrom 的例外 / 语言键 / 依赖 / 探针判词。

跑法：python build\\zftools\\_zf192_falsify.py
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
SRC = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
GATE = os.path.join(ZT, u"_zf192_verify.py")
TMP = os.path.join(ZT, u"_zf192_falsify_bak")

GRAV = os.path.join(SRC, u"GravityDeviceItem.java")
HOLE = os.path.join(SRC, u"BlackHoleManager.java")
LANG_ZH = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang\zh_cn.json")
TOML = os.path.join(ROOT, r"src\main\resources\META-INF\neoforge.mods.toml")
P192 = os.path.join(ZT, u"_zf192_probe_utf8.txt")

KNIVES = [
    dict(id=u"K1", why=u"`use()` 又不让空手开始蓄力（A1 要抓到）", path=GRAV,
         old=u"        if (offhandBlock(player) == null && mode != MODE_COLLAPSE) {",
         new=u"        if (offhandBlock(player) == null) {", want=u"A1"),
    dict(id=u"K2", why=u"`onUseTick()` 又按副手为空取消蓄力（A1 要抓到）", path=GRAV,
         old=u"        if (offhandBlock(player) == null && getMode(stack) != MODE_COLLAPSE) {",
         new=u"        if (offhandBlock(player) == null) {", want=u"A1"),
    dict(id=u"K3", why=u"`fire()` 又拦空手（放得出来才怪 —— A1 要抓到）", path=GRAV,
         old=u"        if (block == null && mode != MODE_COLLAPSE) {",
         new=u"        if (block == null) {", want=u"A1"),
    dict(id=u"K4", why=u"种子里不用 AIR 哨兵而用石头（A2 要抓到）", path=GRAV,
         old=u"                seeded ? block : Blocks.AIR, player, mode, stack);",
         new=u"                seeded ? block : Blocks.STONE, player, mode, stack);", want=u"A2"),
    dict(id=u"K5", why=u"空手那句还用老键（%s 没东西可填 —— A2 要抓到）", path=GRAV,
         old=u'                : Component.translatable("message.potato_s_t.gravity.fired.everything"), true);',
         new=u'                : Component.translatable("message.potato_s_t.gravity.fired", block == null ? "air" : block.getName()), true);',
         want=u"A2"),
    dict(id=u"K6", why=u"`loadFrom` 又把 AIR 洞一律丢掉（空手洞读档就没了 —— A3 要抓到）", path=HOLE,
         old=u"                if (block == net.minecraft.world.level.block.Blocks.AIR\n"
             u"                        && mode != GravityDeviceItem.MODE_COLLAPSE) {",
         new=u"                if (block == net.minecraft.world.level.block.Blocks.AIR) {", want=u"A3"),
    dict(id=u"K7", why=u"给 mods.toml 偷偷加一条依赖（A4 要抓到）", path=TOML,
         old=u"[[dependencies.potato_s_t]]",
         new=u"[[dependencies.potato_s_t]]\nmodId=\"zf192_fake\"\ntype=\"required\"\nversionRange=\"[1,)\"\n"
             u"ordering=\"NONE\"\nside=\"BOTH\"\n\n[[dependencies.potato_s_t]]", want=u"A4"),
    dict(id=u"K8", why=u"把 zh_cn 里那句新文案改名（等于删掉 —— B1 要抓到）", path=LANG_ZH,
         old=u'"message.potato_s_t.gravity.fired.everything": "黑洞成形：它开始吸取周围的一切了"',
         new=u'"message.potato_s_t.gravity.fired.everything_RENAMED": "黑洞成形：它开始吸取周围的一切了"',
         want=u"B1"),
    dict(id=u"K9", why=u"把本轮探针报告的判词改坏（C1 要真读报告）", path=P192,
         old=u"通过 = 6   失败 = 0", new=u"通过 = 5   失败 = 1", want=u"C1"),
]


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_gate():
    r = subprocess.run([sys.executable, GATE], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=1200)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def main():
    rc0, out0 = run_gate()
    pre_red = [l.strip() for l in out0.split(u"\n") if l.strip().startswith(u"!!")]
    print(u"砍之前：rc=%d，红 %d 条：%s" % (rc0, len(pre_red), pre_red))

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
                new_red = len([l for l in out.split(u"\n") if l.strip().startswith(u"!!")])
                if rc != 0 and caught and new_red > len(pre_red):
                    ok += 1
                    print(u"  [OK]   %s 门红了（红 %d→%d），抓到：%s"
                          % (k[u"id"], len(pre_red), new_red, caught[0][:52]))
                else:
                    bad.append(k[u"id"])
                    print(u"  [FAIL] %s 门没抓到（rc=%d，红 %d→%d，想看到 %s）"
                          % (k[u"id"], rc, len(pre_red), new_red, k[u"want"]))
        finally:
            if cut:
                shutil.copy2(bak, path)
            if sha1(path) != before:
                bad.append(k[u"id"] + u"(还原不一致)")
    print(u"\n反证刀：%d/%d 抓到（漏网 %s）" % (ok, len(KNIVES), u" / ".join(bad) if bad else u"无"))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
