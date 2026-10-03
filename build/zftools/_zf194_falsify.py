# -*- coding: utf-8 -*-
u"""_zf194_falsify.py —— ZF194 的**反证刀**：砍一刀，`_zf194_verify.py` 必须当场变红。

刀刀都砍在"本轮真正做的事"上：坍缩分支走下落方块 / 天上飞的预算 / 拉向中心 / 到中心清除 /
清除半径 / 不禁用重力 / 取消禁采区 / 探针判词。

跑法：python build\\zftools\\_zf194_falsify.py
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
GATE = os.path.join(ZT, u"_zf194_verify.py")
TMP = os.path.join(ZT, u"_zf194_falsify_bak")
P194 = os.path.join(ZT, u"_zf194_probe_utf8.txt")

KNIVES = [
    dict(id=u"K1", why=u"坍缩分支又改回「码放」（用户要的「看得见」没了 —— A1 要抓到）", path=HOLE,
         old=u"                if (launchFalling(hole, p, state)) {",
         new=u"                if (placeAt(hole, p, moved)) {", want=u"A1"),
    dict(id=u"K2", why=u"天上飞的预算不再管（一 tick 放几百个实体 —— A1 要抓到）", path=HOLE,
         old=u"                if (flyingLeft <= 0) {\n                    break;", new=u"                if (false) {\n                    break;",
         want=u"A1"),
    dict(id=u"K3", why=u"不再把下落方块拉向中心（飞出去就不管了 —— A2 要抓到）", path=HOLE,
         old=u"                fb.setDeltaMovement(dir.normalize().scale(flySpeed(dist)));",
         new=u"                fb.setDeltaMovement(fb.getDeltaMovement());", want=u"A2"),
    dict(id=u"K4", why=u"到中心也不清除（方块会一直飞 —— A2 要抓到）", path=HOLE,
         old=u"            if (dist <= CLEAR_RADIUS) {", new=u"            if (false) {", want=u"A2"),
    dict(id=u"K5", why=u"清除半径改成 25 格（离老远就没了 —— A3 要抓到）", path=HOLE,
         old=u"    public static final double CLEAR_RADIUS = 2.5D;",
         new=u"    public static final double CLEAR_RADIUS = 25.0D;", want=u"A3"),
    dict(id=u"K6", why=u"给下落方块关掉重力（黑洞没了它们就永远飞下去 —— A4 要抓到）", path=HOLE,
         old=u"        falling.setStartPos(pos);",
         new=u"        falling.setNoGravity(true);\n        falling.setStartPos(pos);", want=u"A4"),
    dict(id=u"K7", why=u"禁采区又对坍缩模式生效（脚边那圈不吸 —— A5 要抓到）", path=HOLE,
         old=u"            if (!collapse && Math.abs(dx) <= PILE_GUARD",
         new=u"            if (Math.abs(dx) <= PILE_GUARD", want=u"A5"),
    dict(id=u"K8", why=u"把本轮探针报告的判词改坏（C1 要真读报告）", path=P194,
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
