# -*- coding: utf-8 -*-
u"""_zf196_falsify.py —— ZF196 的**反证刀**：砍一刀，`_zf196_verify.py` 必须当场变红。

刀刀都砍在"本轮真正做的事"上：近处分派 / 近处优先的取样 / 半径随年龄涨 / 露着与埋着的分岔 /
"像爆炸那样"的 2001 事件 / 不超过配置扫描半径 / 上限 / 探针判词。

跑法：python build\\zftools\\_zf196_falsify.py
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
HOLE = os.path.join(ROOT, r"src\main\java\com\potatost\mod\BlackHoleManager.java")
GATE = os.path.join(ZT, u"_zf196_verify.py")
TMP = os.path.join(ZT, u"_zf196_falsify_bak")
P196 = os.path.join(ZT, u"_zf196_probe_utf8.txt")

KNIVES = [
    dict(id=u"K1", why=u"坍缩模式不再走「近处优先」那条路（A1 要抓到）", path=HOLE,
         old=u"            collapseEat(hole);\n", new=u"            // collapseEat(hole);\n", want=u"A1"),
    dict(id=u"K2", why=u"取样改成体积均匀（不再「先从身边啃」—— A2 要抓到）", path=HOLE,
         old=u"            double rr = radius * u;", new=u"            double rr = radius * Math.cbrt(u);",
         want=u"A2"),
    dict(id=u"K3", why=u"拆除半径不随年龄涨（永远只拆 3 格 —— A2 要抓到）", path=HOLE,
         old=u"        return Math.min(DEMOLISH_MAX_RADIUS, DEMOLISH_START_RADIUS + age * DEMOLISH_GROWTH_PER_TICK);",
         new=u"        return DEMOLISH_START_RADIUS;", want=u"A2"),
    dict(id=u"K4", why=u"不再分「露着/埋着」（埋着的也硬飞 ⇒ 卡住 —— A3 要抓到）", path=HOLE,
         old=u"            if (!exposed(level, p)) {", new=u"            if (false) {", want=u"A3"),
    dict(id=u"K5", why=u"拆方块不发「方块破坏」事件（看不出碎裂 = 又回到「没效果」—— A4 要抓到）", path=HOLE,
         old=u"        level.levelEvent(net.minecraft.world.level.block.LevelEvent.PARTICLES_DESTROY_BLOCK, p,\n"
             u"                Block.getId(state));",
         new=u"        // 事件不发了", want=u"A4"),
    dict(id=u"K6", why=u"拆除半径不再受配置的扫描半径约束（配置说 8 格它也拆 24 格 —— A5 要抓到）", path=HOLE,
         old=u"        return Math.min(demolishRadiusAt(hole.age), (double) PotatoSTConfig.blackHoleScanRadius());",
         new=u"        return demolishRadiusAt(hole.age);", want=u"A5"),
    dict(id=u"K7", why=u"取样循环不再看搬运上限（想拆多少拆多少 —— A6 要抓到）", path=HOLE,
         old=u"        for (int i = 0; i < DEMOLISH_SAMPLES && done < BLOCKS_PER_TICK && hole.pulled < maxBlocks(); i++) {",
         new=u"        for (int i = 0; i < DEMOLISH_SAMPLES && done < BLOCKS_PER_TICK; i++) {", want=u"A6"),
    dict(id=u"K8", why=u"把本轮探针报告的判词改坏（C1 要真读报告）", path=P196,
         old=u"通过 = 5   失败 = 0", new=u"通过 = 4   失败 = 1", want=u"C1"),
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
