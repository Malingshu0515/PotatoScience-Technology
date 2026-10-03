# -*- coding: utf-8 -*-
u"""_zf188_falsify.py —— ZF188 的**反证刀**：砍一刀，`_zf188_verify.py` 必须当场变红。

刀刀都砍在"本轮真正做的事"上：让位策略 / 调用点用真实查询且先于注册 /
「configured」不许出现在非客户端代码里 / 依赖清单不许变 / 两份探针报告的判词要真读。

跑法：python build\\zftools\\_zf188_falsify.py
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
GATE = os.path.join(ZT, u"_zf188_verify.py")
TMP = os.path.join(ZT, u"_zf188_falsify_bak")

CFG = os.path.join(SRC, u"PotatoSTConfig.java")
SCREEN = os.path.join(SRC, u"client", u"PotatoSTConfigScreen.java")
TOML = os.path.join(ROOT, r"src\main\resources\META-INF\neoforge.mods.toml")
P188 = os.path.join(ZT, u"_zf188_probe_utf8.txt")
P186 = os.path.join(ZT, u"_zf186_probe_utf8.txt")

KNIVES = [
    dict(id=u"K1", why=u"策略改成「一律自己注册」（A1 要抓到）", path=CFG,
         old=u"        return !configuredModPresent;", new=u"        return true;", want=u"A1"),
    dict(id=u"K2", why=u"调用点不再问真实 mod 列表，写死 false（A2 要抓到）", path=SCREEN,
         old=u"PotatoSTConfig.shouldRegisterOwnConfigScreen(ModList.get().isLoaded(CONFIGURED_MODID))",
         new=u"PotatoSTConfig.shouldRegisterOwnConfigScreen(false)", want=u"A2"),
    dict(id=u"K3", why=u"让位分支不 return（等于照旧自己注册 —— A2 的「先 return」要抓到）", path=SCREEN,
         old=u"                    + \"客户端日志里应当出现 Registering config factory for mod potato_s_t\");\n"
             u"            return;",
         new=u"                    + \"客户端日志里应当出现 Registering config factory for mod potato_s_t\");",
         want=u"A2"),
    dict(id=u"K4", why=u"把 modid 字符串漏进公共类（A3「只许出现在客户端类」要抓到）", path=CFG,
         old=u"    private PotatoSTConfig() {",
         new=u"    public static final String CONFIGURED_MODID = \"configured\";\n\n"
             u"    private PotatoSTConfig() {", want=u"A3"),
    dict(id=u"K5", why=u"给 mods.toml 加一条对 configured 的必需依赖（A3 的逐字节比要抓到）", path=TOML,
         old=u"[[dependencies.potato_s_t]]",
         new=u"[[dependencies.potato_s_t]]\nmodId=\"configured\"\ntype=\"required\"\nversionRange=\"[1,)\"\n"
             u"ordering=\"NONE\"\nside=\"BOTH\"\n\n[[dependencies.potato_s_t]]", want=u"A3"),
    dict(id=u"K6", why=u"把本轮探针报告的判词改坏（B1 要真读报告）", path=P188,
         old=u"通过 = 4   失败 = 0", new=u"通过 = 3   失败 = 1", want=u"B1"),
    dict(id=u"K7", why=u"把上一轮回归探针的判词改坏（B2 要真读回归证据）", path=P186,
         old=u"通过 = 20   失败 = 0", new=u"通过 = 19   失败 = 1", want=u"B2"),
]


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_gate():
    r = subprocess.run([sys.executable, GATE], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=600)
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
                          % (k[u"id"], len(pre_red), new_red, caught[0][:56]))
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
