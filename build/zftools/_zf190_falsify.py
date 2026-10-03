# -*- coding: utf-8 -*-
u"""_zf190_falsify.py —— ZF190 的**反证刀**：砍一刀，`_zf190_verify.py` 必须当场变红。

刀刀都砍在"本轮真正做的事"上：召唤费（固定 8M / 容量封顶 / 闸门）/ 第三模式（循环、红色、价格）/
电费与找回 / 硬上限与真爆炸 / 无差别的边界 / 掉落物销毁 / 强度伤害递增 / 先摘后播报 / 语言键 / 依赖 / 探针判词。

跑法：python build\\zftools\\_zf190_falsify.py
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
GATE = os.path.join(ZT, u"_zf190_verify.py")
TMP = os.path.join(ZT, u"_zf190_falsify_bak")

GRAV = os.path.join(SRC, u"GravityDeviceItem.java")
HOLE = os.path.join(SRC, u"BlackHoleManager.java")
LANG_EN = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang\en_us.json")
TOML = os.path.join(ROOT, r"src\main\resources\META-INF\neoforge.mods.toml")
P190 = os.path.join(ZT, u"_zf190_probe_utf8.txt")

KNIVES = [
    dict(id=u"K1", why=u"fire() 又抽干整条电力（用户报的 bug 回来了 —— A2 要抓到）", path=GRAV,
         old=u"        setEnergy(stack, getEnergy(stack) - cost);", new=u"        setEnergy(stack, 0);",
         want=u"A2"),
    dict(id=u"K2", why=u"召唤费不再按容量封顶（容量 1M 时永远攒不够 8M —— A1 要抓到）", path=GRAV,
         old=u"        return Math.min(want, PotatoSTConfig.gravityCapacity());", new=u"        return want;",
         want=u"A1"),
    dict(id=u"K3", why=u"use() 的闸门退回「必须充满」（A3 要抓到）", path=GRAV,
         old=u"        int cost = summonCost(getMode(stack));",
         new=u"        int cost = PotatoSTConfig.gravityCapacity();", want=u"A3"),
    dict(id=u"K4", why=u"坍缩模式也走一次性损坏（装置坏了黑洞立刻没电 —— A4 要抓到）", path=GRAV,
         old=u"        if (PotatoSTConfig.oneShotBlackHole() && mode != MODE_COLLAPSE) {",
         new=u"        if (PotatoSTConfig.oneShotBlackHole()) {", want=u"A4"),
    dict(id=u"K5", why=u"模式循环退回两档（第三档点不到 —— B1 要抓到）", path=GRAV,
         old=u"            case MODE_TOW -> MODE_COLLAPSE;", new=u"            case MODE_TOW -> MODE_SWALLOW;",
         want=u"B1"),
    dict(id=u"K6", why=u"坍缩模式那行字不再是红色（B1 要抓到）", path=GRAV,
         old=u"            msg = msg.withStyle(net.minecraft.ChatFormatting.RED);",
         new=u"            msg = msg.withStyle(net.minecraft.ChatFormatting.WHITE);", want=u"B1"),
    dict(id=u"K7", why=u"每 tick 电费从 50k 改成 5k（B2 要抓到）", path=GRAV,
         old=u"    public static final int COLLAPSE_COST_PER_TICK = 50_000;",
         new=u"    public static final int COLLAPSE_COST_PER_TICK = 5_000;", want=u"B2"),
    dict(id=u"K8", why=u"电费不再在 tick 最前面交（没电也能继续吃 —— B3 要抓到）", path=HOLE,
         old=u"                if (hole.mode == GravityDeviceItem.MODE_COLLAPSE && !payCollapsePower(hole)) {",
         new=u"                if (hole.mode == GravityDeviceItem.MODE_COLLAPSE && false) {", want=u"B3"),
    dict(id=u"K9", why=u"2 分钟硬上限被改掉（B4 要抓到）", path=HOLE,
         old=u"    public static final int HARD_CAP_TICKS = 2 * 60 * 20;",
         new=u"    public static final int HARD_CAP_TICKS = 999_999;", want=u"B4"),
    dict(id=u"K10", why=u"爆炸改成「不破坏方块」（不是用户要的 30 威力 —— B4 要抓到）", path=HOLE,
          old=u"                net.minecraft.world.level.Level.ExplosionInteraction.TNT);",
          new=u"                net.minecraft.world.level.Level.ExplosionInteraction.NONE);", want=u"B4"),
    dict(id=u"K11", why=u"「无差别」不再排除不可破坏方块（基岩也会被吸走 —— B5 要抓到）", path=HOLE,
          old=u"                && state.getBlock().defaultDestroyTime() >= 0.0F;",
          new=u"                && state.getBlock().defaultDestroyTime() >= -1.0F;", want=u"B5"),
    dict(id=u"K12", why=u"掉落物不再销毁（B6 要抓到）", path=HOLE,
          old=u"                item.discard();   // 不掉落、不留痕",
          new=u"                item.setDeltaMovement(0.0D, 0.0D, 0.0D);", want=u"B6"),
    dict(id=u"K13", why=u"吸引强度不再随年龄涨（B7 要抓到）", path=HOLE,
          old=u"                    double strength = 1.6D / (dist / CORE + 1.0D) * ramp;",
          new=u"                    double strength = 1.6D / (dist / CORE + 1.0D);", want=u"B7"),
    dict(id=u"K14", why=u"把「先摘后播报」改回旧顺序（刚结束的黑洞又被写回存档 —— B8 要抓到）", path=HOLE,
          old=u"                    it.remove();        // ⚠ 先摘再播报：collapse() 里会 saveInto（见下面 ③ 的注释）\n"
              u"                    collapse(hole);",
          new=u"                    collapse(hole);\n                    it.remove();", want=u"B8"),
    dict(id=u"K15", why=u"把 en_us 里那个新模式语言键改名（等于删掉 —— B9 要抓到）", path=LANG_EN,
          old=u'"message.potato_s_t.gravity.mode.collapse": "Collapse mode - DANGER"',
          new=u'"message.potato_s_t.gravity.mode.collapse_RENAMED": "Collapse mode - DANGER"', want=u"B9"),
    dict(id=u"K16", why=u"给 mods.toml 偷偷加一条依赖（B10 要抓到）", path=TOML,
          old=u"[[dependencies.potato_s_t]]",
          new=u"[[dependencies.potato_s_t]]\nmodId=\"zf190_fake\"\ntype=\"required\"\nversionRange=\"[1,)\"\n"
              u"ordering=\"NONE\"\nside=\"BOTH\"\n\n[[dependencies.potato_s_t]]", want=u"B10"),
    dict(id=u"K17", why=u"把本轮探针报告的判词改坏（C1 要真读报告）", path=P190,
          old=u"通过 = 16   失败 = 0", new=u"通过 = 15   失败 = 1", want=u"C1"),
]


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_gate():
    r = subprocess.run([sys.executable, GATE], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=900)
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
