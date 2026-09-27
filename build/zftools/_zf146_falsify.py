# -*- coding: utf-8 -*-
u"""_zf146_falsify.py —— ZF146 的反证：往成品里塞 8 种"看起来还行"的坏法，门必须当场变红

判据要能失败，否则就是摆设。这里逐把刀捅进去、跑一遍常驻校验 `_zf146_verify.py`，
要求**点名的那条断言**出现在失败清单里；每把刀捅完都把文件还原并核 sha256。

  K01 又给仪式记录塞一个 ServerLevel 字段（就是本轮那个 bug 的形状）
  K02 把仪式表缓存回类的 static 字段（同一个 bug 的另一半）
  K03 写入口子忘了 setDirty（改了不存 == 没改）
  K04 读盘漏掉通报进度（重进世界会补发"还剩 20 秒 / 15 秒"）
  K05 维度没了那条不处理（读不懂的数据会把整台服务器拖垮）
  K06 落地后不删记录（僵尸记录 ⇒ 星轨坠永久锁死）
  K07 维度写死成主世界（换维度/换存档就落到错的地方）
  K08 把"改后第二趟"的报告挪走（C 类断言吃的是真报告，不是文件存在与否）

跑法：python build\\zftools\\_zf146_falsify.py
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, r"build\zftools")
CHECK = os.path.join(TOOLS, "check")
MOD = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
MGR = os.path.join(MOD, "StarfallRitualManager.java")
VERIFY = os.path.join(TOOLS, u"_zf146_verify.py")
BAK = os.path.join(TOOLS, u"_zf146_falsify_bak")
RUN2 = os.path.join(CHECK, u"zf146_after_run2.log")

INJECTIONS = [
    (u"K01 又给仪式记录塞一个 ServerLevel 字段",
     MGR, u"literal",
     u"        private final ResourceKey<Level> dimension;",
     u"        private final ResourceKey<Level> dimension;\n        private final ServerLevel level = null;",
     u"A2 仪式记录里没有任何世界对象"),

    (u"K02 把仪式表缓存回类的 static 字段",
     MGR, u"literal",
     u"    private StarfallRitualManager() {\n    }",
     u"    private static final Map<UUID, Ritual> ACTIVE = new HashMap<>();\n\n"
     u"    private StarfallRitualManager() {\n    }",
     u"A3 类里没有 static 的仪式表"),

    (u"K03 写入口子忘了 setDirty",
     MGR, u"literal",
     u"        void put(Ritual ritual) {\n            this.rituals.put(ritual.owner, ritual);\n            setDirty();\n        }",
     u"        void put(Ritual ritual) {\n            this.rituals.put(ritual.owner, ritual);\n        }",
     u"A10 三个写入口子都标脏"),

    (u"K04 读盘漏掉通报进度",
     MGR, u"literal",
     u"                ritual.nextAnnounce = entry.getInt(KEY_NEXT);\n",
     u"",
     u"A9 通报进度也存了"),

    (u"K05 维度没了那条不处理",
     MGR, u"literal",
     u"            if (level == null) {",
     u"            if (false) {",
     u"A6 维度没了就静默丢掉那一条"),

    (u"K06 落地后不删记录",
     MGR, u"literal",
     u"                summonMeteor(server, level, ritual);\n                it.remove();\n                data.setDirty();",
     u"                summonMeteor(server, level, ritual);\n                data.setDirty();",
     u"A14 落地后那条记录确实被删掉"),

    (u"K07 维度写死成主世界",
     MGR, u"literal",
     u"                entry.putString(KEY_DIM, ritual.dimension.location().toString());",
     u"                entry.putString(KEY_DIM, \"minecraft:overworld\");",
     u"A8 维度按名字存取"),

    (u"K08 把「改后第二趟」的报告挪走",
     RUN2, u"move", None, None,
     u"C1 改后第二趟"),
]

files = sorted(set(i[1] for i in INJECTIONS))
shas = {}


def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def backup():
    if os.path.isdir(BAK):
        shutil.rmtree(BAK)
    os.makedirs(BAK)
    for p in files:
        if os.path.exists(p):
            dst = os.path.join(BAK, os.path.basename(p))
            shutil.copyfile(p, dst)
            shas[p] = sha256(p)
    print(u"  留底 %d 份 → %s" % (len(shas), BAK))


def restore():
    bad = []
    for p in files:
        dst = os.path.join(BAK, os.path.basename(p))
        if os.path.exists(dst):
            shutil.copyfile(dst, p)
            if sha256(p) != shas[p]:
                bad.append(os.path.basename(p))
    return bad


def apply(item):
    name, path, mode, anchor, repl, _key = item
    if mode == u"move":
        if os.path.exists(path):
            os.rename(path, path + u".moved")
        return
    if mode == u"bytes":
        open(path, "wb").write(repl)
        return
    text = io.open(path, encoding="utf-8", newline=u"").read()
    if text.count(anchor) != 1:
        raise RuntimeError(u"锚点在 %s 里命中 %d 次（应为 1）" % (os.path.basename(path), text.count(anchor)))
    io.open(path, u"w", encoding=u"utf-8", newline=u"").write(text.replace(anchor, repl, 1))


def undo(item):
    name, path, mode, anchor, repl, _key = item
    if mode == u"move":
        if os.path.exists(path + u".moved"):
            os.rename(path + u".moved", path)
        return
    src = os.path.join(BAK, os.path.basename(path))
    shutil.copyfile(src, path)


def main():
    print(u"=== 反证：%d 把刀 ===" % len(INJECTIONS))
    backup()
    caught, missed = [], []
    for item in INJECTIONS:
        name, path, mode, anchor, repl, key = item
        undo(item)                     # 每把刀都从原样开始
        try:
            apply(item)
        except Exception as exc:       # noqa: BLE001
            missed.append((name, u"锚点没命中：%s" % exc))
            print(u"  [MISS] %s —— %s" % (name, exc))
            continue
        p = subprocess.run([sys.executable, VERIFY], cwd=ROOT, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        out = p.stdout.decode(u"utf-8", u"replace")
        fails = [l.strip() for l in out.split(u"\n") if u"[FAIL]" in l]
        ok = (p.returncode != 0) and any(key in l for l in fails)
        if ok:
            caught.append(name)
            print(u"  [咬住] %-34s ⇒ %s" % (name, [l for l in fails if key in l][0][:60]))
        else:
            missed.append((name, u"exit=%d，失败项=%s" % (p.returncode, fails[:3])))
            print(u"  [漏了] %-34s ⇒ exit=%d %s" % (name, p.returncode, fails[:3]))
        undo(item)

    bad = restore()
    print(u"\n还原：%s" % (u"逐字节相同" if not bad else u"**不一致 %s**" % bad))
    print(u"咬住 %d / 漏 %d（共 %d）" % (len(caught), len(missed), len(INJECTIONS)))
    for n, why in missed:
        print(u"  !! %s —— %s" % (n, why))
    return 1 if (missed or bad) else 0


if __name__ == u"__main__":
    sys.exit(main())
