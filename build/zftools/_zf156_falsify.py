# -*- coding: utf-8 -*-
r'''_zf156_falsify.py —— ZF156 常驻校验的**反证刀**（§4：门自己也得被咬过才算门）。

每把刀：改一处 → 跑 `_zf156_verify.py` → 必须**红**、且红在预期的那个判据上 → 原样还回去 → 核哈希。
⚠ 只动列出来的那一处，逐把恢复并逐把回读校验（刀口不对/没咬住都要报出来）。

跑法：python build\zftools\_zf156_falsify.py
'''
import hashlib
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
RES = os.path.join(ROOT, r"src\main\resources")
ZT = os.path.join(ROOT, "build", "zftools")
VERIFY = os.path.join(ZT, u"_zf156_verify.py")

TB = os.path.join(JAVA, u"TerminalBlockEntity.java")
GB = os.path.join(JAVA, u"GuideBook.java")
MA = os.path.join(JAVA, u"ModAttachments.java")
MAIN = os.path.join(JAVA, u"PotatoST.java")
PROPS = os.path.join(ROOT, u"gradle.properties")
CAP = os.path.join(RES, r"data\potato_s_t\recipe\capacitor.json")
PRESS = os.path.join(RES, r"data\potato_s_t\recipe\pressing\iron_plate.json")
TAG_IRON = os.path.join(RES, r"data\c\tags\item\plates\iron.json")
REPORT = os.path.join(ZT, u"_zf156_probe_utf8.txt")

# (刀号, 文件, 原文, 改成, 预期变红的判据片段)
KNIVES = [
    (u"K1", TB, u"public void onChunkUnloaded() {\n        super.onChunkUnloaded();\n        this.unloadedWithChunk = true;\n    }",
     u"public void onChunkUnloaded() {\n        super.onChunkUnloaded();\n    }",
     u"A2 onChunkUnloaded 里把卸载标记置真"),
    (u"K2", TB, u"        if (this.unloadedWithChunk) {", u"        if (false) {",
     u"A3 setRemoved 里「卸载早退」"),
    (u"K3", TB, u"                    other.removeConnection(this.getBlockPos());\n",
     u"", u"A4 真被挖掉时"),
    (u"K4", MA, u".copyOnDeath()\n", u"",
     u"B3 声明了 copyOnDeath"),
    (u"K5", MA, u".serialize(Codec.BOOL)\n", u"",
     u"B4 有序列化器"),
    (u"K6", MAIN, u"        ModAttachments.ATTACHMENT_TYPES.register(modEventBus);",
     u"        ModAttachments.ATTACHMENT_TYPES.get();",
     u"B6 PotatoST 构造期把附件表注册进模组总线"),
    (u"K7", GB, u"    public static boolean hasLegacyMark(ServerPlayer player) {",
     u"    public static boolean hasLegacyMark(ServerPlayer player) {\n        player.getPersistentData().putBoolean(GIVEN_TAG, true);",
     u"B7 GuideBook 不再往玩家持久化数据里写标记"),
    (u"K8", CAP, u'"tag": "c:plates/aluminum"', u'"item": "potato_s_t:aluminum_plate"',
     u"C1 配方里「写死自家板当原料」的地方 = 0"),
    (u"K9", PRESS, u'"id": "potato_s_t:iron_plate"', u'"tag": "c:plates/iron"',
     u"C3 液压机那 7 份产出"),
    (u"K10", PROPS, u"mod_version=0.13", u"mod_version=0.12",
     u"D1 gradle.properties 的 mod_version = 0.13"),
    (u"K11", TAG_IRON, u'"potato_s_t:iron_plate"', u'"potato_s_t:iron_plate_x"',
     u"C6 每张标签都收着自家那块板"),
]


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_verify():
    r = subprocess.run([sys.executable, VERIFY], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=600)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def main():
    print("=" * 78)
    print(u"_zf156_falsify.py —— 反证刀（每把都必须把门咬红）")
    print("=" * 78)
    ok, bad = 0, []
    for kid, path, old, new, expect in KNIVES:
        if not os.path.isfile(path):
            bad.append(u"%s 目标不在：%s" % (kid, path))
            continue
        before = sha(path)
        # ⚠ 换行符要跟着文件走：`TerminalBlockEntity.java` 是 **CRLF**（本工程里少数几份），
        #   而按 `\n` 写死锚点的刀在 CRLF 文件上"命中 0 次" —— 第一版 K1 就是这么漏的。
        text = io.open(path, encoding="utf-8", newline="").read()
        nl = u"\r\n" if u"\r\n" in text else u"\n"
        old_n = old.replace(u"\n", nl)
        new_n = new.replace(u"\n", nl)
        if text.count(old_n) != 1:
            bad.append(u"%s 刀口没对准（命中 %d 次，换行=%r）：%s"
                       % (kid, text.count(old_n), nl, old[:40]))
            continue
        try:
            io.open(path, "w", encoding="utf-8", newline="").write(text.replace(old_n, new_n, 1))
            rc, out = run_verify()
            hit = expect in out and u"[FAIL] " + expect in out
            if rc != 0 and hit:
                ok += 1
                print(u"  [咬住] %-4s %s" % (kid, expect))
            else:
                bad.append(u"%s 没咬住（退出码 %d / 预期红：%s）" % (kid, rc, expect))
                print(u"  [漏]   %-4s 退出码=%d 预期=%s" % (kid, rc, expect))
        finally:
            io.open(path, "w", encoding="utf-8", newline="").write(text)
            if sha(path) != before:
                bad.append(u"%s 恢复后哈希不一致：%s" % (kid, path))
    print("-" * 78)
    print(u"咬住 %d / %d 把" % (ok, len(KNIVES)))
    for b in bad:
        print(u"  !! " + b)
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
