# -*- coding: utf-8 -*-
u"""_zf198_falsify.py —— ZF198 的**反证刀**：砍一刀，`_zf198_verify.py` 必须当场变红。

刀刀都砍在"本轮真正做的事"上：版本号唯一处 / 三份老门跟平 / 占位符 / 活体路径换名 /
历史路径不许动 / 档案那一行 / 旧成品不许动 / 依赖段不许动。

⚠ 为了跑得动，刀下面把 `ZF198_FAST=1` 传给门（跳过那十道老门的内嵌重跑）——
   被砍的判据（A/B/C1/C3/D）全都不在跳过范围里。
跑法：python build\\zftools\\_zf198_falsify.py
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
GATE = os.path.join(ZT, u"_zf198_verify.py")
TMP = os.path.join(ZT, u"_zf198_falsify_bak")

KNIVES = [
    dict(id=u"K1", why=u"版本号又退回 0.14（A1 要抓到）", path=os.path.join(ROOT, "gradle.properties"),
         old=u"mod_version=0.15", new=u"mod_version=0.14", want=u"A1"),
    dict(id=u"K2", why=u"`_zf78_verify.py` 的版本断言退回 0.14（A2 要抓到）", path=os.path.join(ZT, u"_zf78_verify.py"),
         old=u"mod_version 现在是 0.15", new=u"mod_version 现在是 0.14", want=u"A2"),
    dict(id=u"K3", why=u"把占位符写死成 0.15（版本号不再只有一处源头 —— A3 要抓到）",
         path=os.path.join(ROOT, r"src\main\resources\META-INF\neoforge.mods.toml"),
         old=u'version="${mod_version}"', new=u'version="0.15"', want=u"A3"),
    dict(id=u"K4", why=u"某道活体门的成品路径没换干净（还指 0.14 —— B1 要抓到）",
         path=os.path.join(ZT, u"_zf196_verify.py"),
         old=u'"release", u"PotatoST-0.15.jar"', new=u'"release", u"PotatoST-0.14.jar"', want=u"B1"),
    dict(id=u"K5", why=u"把备份里的**历史**路径也改了（B2 要抓到）",
         path=os.path.join(ZT, u"_zf186_verify.py"),
         old=u'r"release\\PotatoST-0.14.jar"', new=u'r"release\\PotatoST-0.15.jar"', want=u"B2"),
    dict(id=u"K6", why=u"把档案里 ZF198 那一行抹掉（D3 要抓到）",
         path=os.path.join(ROOT, "docs", u"开发档案.md"),
         old=u"| ZF198 |", new=u"| ZF198x |", want=u"D3"),
    dict(id=u"K7", why=u"偷偷动了依赖段（D4 要抓到）",
         path=os.path.join(ROOT, r"src\main\resources\META-INF\neoforge.mods.toml"),
         old=u"[[dependencies.potato_s_t]]", new=u"[[dependencies.potato_s_t]]\nmodId=\"zf198_fake\"", want=u"D4"),
    dict(id=u"K8", why=u"抬版本时顺手改了 0.14 那份历史成品（C3 要抓到）",
         path=os.path.join(ROOT, "release", u"PotatoST-0.14.jar"),
         old=u"", new=None, want=u"C3"),   # 二进制：直接追加一个字节
]


def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def run_gate():
    env = dict(os.environ)
    env[u"ZF198_FAST"] = u"1"
    r = subprocess.run([sys.executable, GATE], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=1200, env=env)
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
            if k[u"old"] == u"":
                with open(path, "ab") as fh:      # 二进制刀：追加一个字节
                    fh.write(b"X")
            else:
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
