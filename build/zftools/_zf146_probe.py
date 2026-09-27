# -*- coding: utf-8 -*-
u"""_zf146_probe.py —— ZF146 的「两次开服」取证台（挂探针 / 换改前件 / 跑两趟 / 摘探针）

别人反馈的 bug（用户转述）：「星轨坠 中途退出游戏就不会落下 再次进入就不能使用了」

要证的东西只有一句话：**第一次开服起的仪式，退出之后还在不在、倒计时是不是接着走。**
所以证据必须是"两次开服"的，判据必须只吃外部行为（改前 / 改后同一份探针都要能跑）。
两个坑（都吃过）写在函数注释里。

子命令：
    status          只体检：探针挂没挂、源码现在是改前还是改后、存档文件在不在
    mount           挂临时探针（`PotatoST.java` 只加一块 + 拷 `Zf146Check.java` 进源码树）
    unmount         摘探针，并**逐字节**核对 `PotatoST.java` 回到 `zf146_pre`
    swap-before     把 `StarfallRitualManager.java` 换成改前件（改前那版没有存档数据）
    swap-after      换回本轮成品（核 sha256）
    run <标签>      删 phase/报告 → 开第一趟 → 验存档 .dat → 开第二趟 → 报告存成
                    `check\\zf146_<标签>_run1.log` / `_run2.log`

跑法：
    python build\\zftools\\_zf146_probe.py status
    python build\\zftools\\_zf146_probe.py mount
    python build\\zftools\\_zf146_probe.py swap-before
    python build\\zftools\\_zf146_probe.py run before
    ...（swap-after 后）...
    python build\\zftools\\_zf146_probe.py run after
    python build\\zftools\\_zf146_probe.py unmount
"""
import gzip
import hashlib
import io
import os
import re
import shutil
import struct
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, r"build\zftools")
CHECK = os.path.join(TOOLS, "check")
MOD = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
POT = os.path.join(MOD, "PotatoST.java")
MGR = os.path.join(MOD, "StarfallRitualManager.java")
PROBE_SRC = os.path.join(CHECK, "Zf146Check.java")
PROBE_DST = os.path.join(MOD, "Zf146Check.java")
PRE = r"C:\PotatoST救援\zf146_pre"
PRE_MGR = os.path.join(PRE, r"src\main\java\com\potatost\mod\StarfallRitualManager.java")
PRE_POT = os.path.join(PRE, r"src\main\java\com\potatost\mod\PotatoST.java")
FIXED_MGR = os.path.join(PRE, u"_改后_StarfallRitualManager.java")     # 本轮成品的留底（仓外）
FIXED_SHA = os.path.join(PRE, u"_改后_StarfallRitualManager.sha256")

REPORT = os.path.join(CHECK, u"zf146_星轨坠重启取证.log")
PHASE = os.path.join(CHECK, u"_zf146_phase.txt")
LOG = os.path.join(TOOLS, u"_zf146_runSrv.log")
DAT = os.path.join(ROOT, r"run\server\zf146restart\data\potato_s_t_starfall.dat")
SRV_LOG = os.path.join(ROOT, r"run\server\logs\latest.log")
PROPS = os.path.join(ROOT, r"run\server\server.properties")
PROPS_BAK = os.path.join(PRE, u"server.properties.bak")
WORLD = u"zf146restart"

ANCHOR = (u"        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener("
          u"StarfallRitualManager::onPlayerLogin);\n\n    }\n")
BLOCK = (u"\n        // \u26a0\u26a0 临时探针（ZF146）：星轨坠「中途退出游戏」取证，"
         u"跑完由 _zf146_probe.py 摘掉\n        Zf146Check.register();")

KILL_PS = (
    "Get-CimInstance Win32_Process -Filter \"Name='java.exe'\" | "
    "Where-Object { $_.CommandLine -match 'forge.logging.console.level|gradle-wrapper.jar' } | "
    "ForEach-Object { Write-Output ('kill ' + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force }"
)


def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def read(p):
    return io.open(p, encoding=u"utf-8", newline=u"").read()


def write(p, t):
    io.open(p, u"w", encoding=u"utf-8", newline=u"").write(t)


# ---------------------------------------------------------------- 进程
def kill():
    subprocess.run(["powershell", "-NoProfile", "-Command", KILL_PS], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for attempt in range(30):
        time.sleep(1)
        try:
            f = io.open(SRV_LOG, "r+b")
            f.close()
            print(u"  [OK] 服务端日志已可独占打开（第 %d 秒）" % (attempt + 1))
            return True
        except Exception:
            pass
    print(u"  [FAIL] 30 秒了还占着 %s" % SRV_LOG)
    return False


# ---------------------------------------------------------------- 挂 / 摘
def status():
    pot = read(POT)
    print(u"PotatoST.java 里挂了探针：%s" % (u"Zf146Check" in pot))
    print(u"源码树里有 Zf146Check.java：%s" % os.path.exists(PROBE_DST))
    if os.path.exists(MGR):
        s = sha256(MGR)
        tag = u"?"
        if os.path.exists(FIXED_SHA):
            tag = u"改后（本轮成品）" if s == read(FIXED_SHA).strip() else tag
        if s == sha256(PRE_MGR):
            tag = u"改前（zf146_pre 的旧版）"
        print(u"StarfallRitualManager.java sha256 = %s  ⇒ %s" % (s[:16], tag))
    print(u"存档数据文件 %s：%s" % (DAT, os.path.exists(DAT)))
    print(u"phase 文件：%s；报告：%s" % (os.path.exists(PHASE), os.path.exists(REPORT)))
    return 0


def mount():
    text = read(POT)
    if u"Zf146Check" in text:
        print(u"  [跳过] PotatoST.java 里已经有 Zf146Check（幂等）")
    else:
        if text.count(ANCHOR) != 1:
            print(u"!! 锚点命中 %d 次（应为 1）—— 停手" % text.count(ANCHOR))
            return 1
        new = text.replace(ANCHOR, ANCHOR.replace(u"\n\n    }\n", BLOCK + u"\n\n    }\n"), 1)
        write(POT, new)
        assert read(POT) == new
        print(u"  [OK] 已挂上；PotatoST.java sha256 = %s" % sha256(POT)[:16])
    shutil.copyfile(PROBE_SRC, PROBE_DST)
    print(u"  [OK] 探针源码就位：%s（%d B）" % (PROBE_DST, os.path.getsize(PROBE_DST)))
    return 0


def unmount():
    text = read(POT)
    if u"Zf146Check" not in text:
        print(u"  [跳过] PotatoST.java 里没有探针")
    else:
        if text.count(BLOCK + u"\n\n    }\n") != 1:
            print(u"!! 卸载块命中 %d 次（应为 1）—— 停手" % text.count(BLOCK + u"\n\n    }\n"))
            return 1
        write(POT, text.replace(BLOCK + u"\n\n    }\n", u"\n\n    }\n", 1))
    if os.path.exists(PROBE_DST):
        os.remove(PROBE_DST)
        print(u"  [OK] 源码树里的 Zf146Check.java 已删")
    ok = sha256(POT) == sha256(PRE_POT)
    print(u"  %s PotatoST.java 与改前件逐字节%s" % (u"[OK]" if ok else u"[FAIL]",
                                                 u"相同" if ok else u"**不同**"))
    return 0 if ok else 1


# ---------------------------------------------------------------- 换版本
def save_fixed():
    if not os.path.exists(FIXED_MGR):
        shutil.copyfile(MGR, FIXED_MGR)
        write(FIXED_SHA, sha256(MGR) + u"\n")
        print(u"  [OK] 本轮成品留底 → %s（sha256 %s）" % (FIXED_MGR, sha256(MGR)[:16]))


def swap_before():
    save_fixed()
    shutil.copyfile(PRE_MGR, MGR)
    ok = sha256(MGR) == sha256(PRE_MGR)
    print(u"  %s 已换成改前件（sha256 %s）" % (u"[OK]" if ok else u"[FAIL]", sha256(MGR)[:16]))
    return 0 if ok else 1


def swap_after():
    if not os.path.exists(FIXED_MGR):
        print(u"!! 没有成品留底，停手")
        return 1
    shutil.copyfile(FIXED_MGR, MGR)
    want = read(FIXED_SHA).strip()
    got = sha256(MGR)
    ok = got == want
    print(u"  %s 已换回成品（sha256 %s / 应为 %s）" % (u"[OK]" if ok else u"[FAIL]", got[:16], want[:16]))
    return 0 if ok else 1


def compile_java():
    print(u"  --- 编译 ---")
    p = subprocess.run([os.path.join(ROOT, u"gradlew.bat"), "compileJava", "--offline",
                        "--no-build-cache"], cwd=ROOT, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    out = p.stdout.decode(u"utf-8", u"replace")
    bad = [l for l in out.split(u"\n") if u"错误:" in l or u"error:" in l]
    if p.returncode != 0 or bad:
        print(u"  [FAIL] 编译不过（%d 行错误）" % len(bad))
        for l in bad[:12]:
            print(u"     " + l)
        return 1
    print(u"  [OK] 编译通过")
    return 0


# ---------------------------------------------------------------- 开服
def start_server(tag, timeout):
    ok_lock = kill()
    if not ok_lock:
        return False
    before = os.path.getmtime(REPORT) if os.path.exists(REPORT) else None
    print(u"  --- 启动真服务端（%s）---" % time.strftime(u"%H:%M:%S"))
    with io.open(LOG, u"w", encoding=u"utf-8") as out:
        # ⚠ 不许用 `--args=`：那会把 run 配置里本来带的 `--nogui` 顶掉，
        #   1.21.1 的 ImmediateWindowHandler 会当场 NPE（ZF140 在 runClient 上踩过同一个坑）。
        #   要换存档名就改 run/server/server.properties 的 level-name（ZF77 就是这么干的）。
        subprocess.run([os.path.join(ROOT, u"gradlew.bat"), "runServer", "--offline",
                        "--no-build-cache"],
                       cwd=ROOT, stdout=out, stderr=subprocess.STDOUT)
    print(u"  --- gradle 壳退出（真服务端可能还在跑），等报告落地 ---")
    deadline = time.time() + timeout
    fresh = False
    while time.time() < deadline:
        time.sleep(2)
        if os.path.exists(REPORT) and (before is None or os.path.getmtime(REPORT) > before):
            fresh = True
            print(u"  [OK] 报告已更新")
            break
    if not fresh:
        print(u"  [FAIL] %d 秒内报告没更新 —— 看 %s" % (timeout, LOG))
    kill()
    if os.path.exists(REPORT):
        dst = os.path.join(CHECK, u"zf146_%s.log" % tag)
        shutil.copyfile(REPORT, dst)
        body = io.open(dst, encoding=u"utf-8", errors=u"replace").read()
        verdict = [l for l in body.split(u"\n") if u"verdict" in l]
        fails = len([l for l in body.split(u"\n") if u"[FAIL]" in l])
        print(u"  ⇒ %s：%s（[FAIL] %d 条）" % (tag, verdict[-1] if verdict else u"没有 verdict 行", fails))
    return fresh


def inspect_dat():
    u"""第一趟之后的正脸：存档里到底写了什么（gzip 解出来，按 NBT 的字节序找 uuid / 维度 / 截止时刻）。"""
    print(u"  --- 验存档数据文件 ---")
    if not os.path.exists(DAT):
        print(u"  [FAIL] %s 不存在（改前那版就该是这样）" % DAT)
        return False
    raw = gzip.open(DAT, "rb").read()
    dst = os.path.join(CHECK, u"zf146_starfall.dat")
    shutil.copyfile(DAT, dst)
    end = None
    if os.path.exists(PHASE):
        for line in read(PHASE).split(u"\n"):
            if line.startswith(u"endTick="):
                end = int(line.split(u"=")[1])
    hit_dim = b"minecraft:overworld" in raw
    hit_end = end is not None and struct.pack(">q", end) in raw
    print(u"  大小 = %d B（gzip 解开 %d B）；含维度名 %s；含 endTick=%s 的大端 int64 %s"
          % (os.path.getsize(DAT), len(raw), hit_dim, end, hit_end))
    return hit_dim and hit_end


def set_world():
    u"""把 run/server/server.properties 的 level-name 指到探针专用存档（改前先留底）。"""
    text = read(PROPS)
    if not os.path.exists(PROPS_BAK):
        shutil.copyfile(PROPS, PROPS_BAK)
        print(u"  [OK] server.properties 留底 → %s" % PROPS_BAK)
    new = re.sub(u"(?m)^level-name=.*$", u"level-name=" + WORLD, text)
    if new == text:
        print(u"  [跳过] level-name 已经是 %s" % WORLD)
        return 0
    if u"level-name=" not in text:
        print(u"!! server.properties 里没有 level-name，停手")
        return 1
    write(PROPS, new)
    assert read(PROPS) == new
    print(u"  [OK] level-name → %s" % WORLD)
    return 0


def restore_world():
    u"""把 server.properties 换回原样（逐字节核对）。"""
    if not os.path.exists(PROPS_BAK):
        print(u"  [跳过] 没有留底")
        return 0
    shutil.copyfile(PROPS_BAK, PROPS)
    ok = sha256(PROPS) == sha256(PROPS_BAK)
    print(u"  %s server.properties 已还原（%s）" % (u"[OK]" if ok else u"[FAIL]", sha256(PROPS)[:16]))
    return 0 if ok else 1


def run(tag):
    if not os.path.exists(PROBE_DST) or u"Zf146Check" not in read(POT):
        print(u"!! 探针没挂，先 mount")
        return 1
    if set_world() != 0:
        return 1
    for p in (REPORT, PHASE):
        if os.path.exists(p):
            os.remove(p)
    print(u"=== 第一趟（起手 → 第 300 tick 正常退出）===")
    if not start_server(tag + u"_run1", 420):
        return 1
    ok_dat = inspect_dat()
    print(u"  ⇒ 存档里有仪式记录：%s" % ok_dat)
    print(u"=== 第二趟（重进世界 → 等陨石）===")
    if not start_server(tag + u"_run2", 300):
        return 1
    return 0


def main(argv):
    if not argv:
        print(__doc__)
        return 0
    cmd = argv[0]
    if cmd == u"status":
        return status()
    if cmd == u"mount":
        return mount()
    if cmd == u"unmount":
        return unmount()
    if cmd == u"swap-before":
        return swap_before()
    if cmd == u"swap-after":
        return swap_after()
    if cmd == u"compile":
        return compile_java()
    if cmd == u"run":
        return run(argv[1] if len(argv) > 1 else u"x")
    if cmd == u"set-world":
        return set_world()
    if cmd == u"restore-world":
        return restore_world()
    print(u"不认识的子命令：%s" % cmd)
    return 1


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
