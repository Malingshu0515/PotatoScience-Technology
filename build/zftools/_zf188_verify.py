# -*- coding: utf-8 -*-
u"""_zf188_verify.py —— ZF188 常驻门（0.14：配置界面归属 —— 装了「配置界面」Configured 就让位）。

看四类东西：
  A 代码：策略是纯函数 / 调用点用真实查询且**在注册之前** / "configured" 这个 modid 只出现在客户端类里
          （永远变不成硬依赖）/ mods.toml 与改前逐字节一样 / 客户端隔离没破；
  B 证据：`Zf188Check` 4/0 **且** 上一轮的 `Zf186Check` 回归再跑一遍 20/0；报告里有"没验 GUI"的诚实声明；
  C 回归：五份 lang 键数没被碰坏 + 上一轮那道门仍然全绿；
  D 交付：成品 == build 产物 / 没有探针类 / 新类在 / `_zf149_verify.py` 哈希靶子联动 / 公告与档案跟到新哈希。

跑法：python build\\zftools\\_zf188_verify.py
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
PRE = os.path.join(ZT, "zf188_pre")
CFG = os.path.join(SRC, "PotatoSTConfig.java")
SCREEN = os.path.join(SRC, "client", "PotatoSTConfigScreen.java")
TOML = os.path.join(ROOT, "src", "main", "resources", "META-INF", "neoforge.mods.toml")
P188 = os.path.join(ZT, u"_zf188_probe_utf8.txt")
P186 = os.path.join(ZT, u"_zf186_probe_utf8.txt")
V149 = os.path.join(ZT, u"_zf149_verify.py")
G186 = os.path.join(ZT, u"_zf186_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")
LIB = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.14.jar")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

PASS, FAIL = [], []


def check(ok, label, detail=u""):
    (PASS if ok else FAIL).append(label)
    print(u"  %s %s%s" % (u"[OK]  " if ok else u"[FAIL]", label, (u" ｜ " + detail) if detail else u""))
    return ok


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def strip_comments(t):
    t = re.sub(u"/\\*.*?\\*/", u"", t, flags=re.S)
    t = re.sub(u"(?m)//.*$", u"", t)
    return t


def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def main():
    cfg, screen = read(CFG), read(SCREEN)
    cfg_c, screen_c = strip_comments(cfg), strip_comments(screen)

    print(u"== A 代码 ==")
    check(u"public static boolean shouldRegisterOwnConfigScreen(boolean configuredModPresent) {" in cfg_c
          and u"return !configuredModPresent;" in cfg_c,
          u"A1 「让不让位」抽成纯函数，且就是入参取反（可被真值表验）")

    i_call = screen_c.find(u"shouldRegisterOwnConfigScreen(ModList.get().isLoaded(CONFIGURED_MODID))")
    i_reg = screen_c.find(u"registerExtensionPoint")
    check(i_call >= 0 and i_reg > i_call and u"return;" in screen_c[i_call:i_reg],
          u"A2 调用点用**真实查询**（ModList.isLoaded(CONFIGURED_MODID)）且**在注册之前就 return**",
          u"调用位置 %d ｜ 注册位置 %d" % (i_call, i_reg))

    foreign = []
    for dirpath, _dirs, files in os.walk(SRC):
        if os.path.basename(dirpath) == u"client":
            continue
        for fn in files:
            # ⚠ 判据要钉**字符串字面量** `"configured"`，不能只搜 'configured' 这个词 ——
            #   别的文件里本来就有英文单词 configured（"not configured" 之类），
            #   我们的形参名也叫 configuredModPresent ⇒ 搜词必假红（本轮真踩过）。
            if fn.endswith(u".java") and u'"configured"' in strip_comments(read(os.path.join(dirpath, fn))):
                foreign.append(fn)
    same_toml = sha1(TOML) == sha1(os.path.join(PRE, r"src\main\resources\META-INF\neoforge.mods.toml"))
    check(not foreign and same_toml and u'CONFIGURED_MODID = "configured"' in screen_c,
          u"A3 「configured」只作为**可选字符串**出现在客户端类里；mods.toml 依赖段一字未动",
          u"越界文件 %s ｜ mods.toml 同上版：%s" % (foreign, same_toml))

    bad_ref = [fn for fn in os.listdir(SRC)
               if fn.endswith(u".java")
               and (u"IConfigScreenFactory" in strip_comments(read(os.path.join(SRC, fn)))
                    or u"ConfigurationScreen" in strip_comments(read(os.path.join(SRC, fn))))]
    check(u"value = Dist.CLIENT" in screen_c and not bad_ref,
          u"A4 客户端隔离没破（非 client 代码里仍然没有界面类）", u"越界 %s" % bad_ref)

    print(u"== B 证据 ==")
    def verdict(p):
        if not os.path.isfile(p):
            return None, u"报告不在盘上"
        t = read(p)
        m = re.search(u"通过 = (\\d+)\\s+失败 = (\\d+)", t)
        return (int(m.group(1)), int(m.group(2))) if m else (None, u"没有判词行")

    z188, z186 = verdict(P188), verdict(P186)
    check(z188 == (4, 0), u"B1 本轮探针 Zf188Check 4/0（策略真值表 + 现场事实 + 11 项回归）",
          u"读到 %s" % (z188,))
    check(z186 == (20, 0), u"B2 上一轮探针 Zf186Check **回归再跑一遍**仍 20/0（重构没碰坏配置行为）",
          u"读到 %s" % (z186,))
    honest = os.path.isfile(P188) and u"探针没验 GUI" in read(P188)
    check(honest, u"B3 报告里写明「GUI 那一半只能你自己在客户端日志看」——不谎称验过界面")

    print(u"== C 回归 ==")
    keys = {f: len(json.loads(read(os.path.join(
        ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang", f))))
        for f in (u"zh_cn.json", u"en_us.json", u"lzh.json", u"ja_jp.json", u"ru_ru.json")}
    check(keys == {u"zh_cn.json": 690, u"en_us.json": 690, u"lzh.json": 692,
                   u"ja_jp.json": 690, u"ru_ru.json": 690},
          u"C1 五份 lang 键数没被碰坏", u"、".join(u"%s=%d" % kv for kv in sorted(keys.items())))
    r = subprocess.run([sys.executable, G186], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
    out = r.stdout.decode("utf-8", "replace")
    last = [l.strip() for l in out.split(u"\n") if l.strip().startswith(u"通过 =")]
    check(r.returncode == 0, u"C2 上一轮那道门 `_zf186_verify.py` 仍然全绿",
          last[-1] if last else u"rc=%d" % r.returncode)

    print(u"== D 交付 ==")
    same_jar = os.path.isfile(JAR) and os.path.isfile(LIB) and sha1(JAR) == sha1(LIB)
    h = sha1(JAR) if os.path.isfile(JAR) else u"-"
    size = os.path.getsize(JAR) if os.path.isfile(JAR) else -1
    check(same_jar, u"D1 成品 == build 产物（逐字节）", u"%d 字节 / sha1 %s" % (size, h[:12]))

    jar_ok, detail = False, u"成品不在盘上"
    if os.path.isfile(JAR):
        z = zipfile.ZipFile(JAR)
        names = z.namelist()
        checks_ = [n for n in names if u"Check.class" in n]
        jar_ok = (not checks_
                  and u"com/potatost/mod/PotatoSTConfig.class" in names
                  and u"com/potatost/mod/client/PotatoSTConfigScreen.class" in names)
        detail = u"探针类 %d ｜ 两个新类都在 %s" % (len(checks_), jar_ok)
        z.close()
    check(jar_ok, u"D2 成品里没有探针类、含两个新类", detail)

    v149 = read(V149)
    m_sha = re.search(u'WANT_SHA = u?"([0-9a-f]{40})"', v149)
    m_size = re.search(u"WANT_SIZE = (\\d+)", v149)
    check(bool(m_sha) and bool(m_size) and m_sha.group(1) == h and int(m_size.group(1)) == size,
          u"D3 §4.159 三处联动：`_zf149_verify.py` 靶子指向这份成品",
          u"WANT_SHA=%s WANT_SIZE=%s" % (m_sha.group(1)[:12] if m_sha else u"-",
                                        m_size.group(1) if m_size else u"-"))
    doc, ann = read(DOC), read(ANN)
    check(h in doc and h in ann and u"### 4.188 " in doc and u"## New in 0.14 ZF188" in ann,
          u"D4 档案 §4.188 + 英文公告都写了这一轮，且哈希跟到新成品",
          u"档案命中 %s ｜ 公告命中 %s" % (h[:12] in doc, h[:12] in ann))

    print(u"\n通过 = %d   失败 = %d" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print(u"  !! " + f)
    return 1 if FAIL else 0


if __name__ == u"__main__":
    sys.exit(main())
