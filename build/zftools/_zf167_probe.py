# -*- coding: utf-8 -*-
u"""_zf167_probe.py —— ZF167 的临时探针挂载 / 起服取证 / 摘除（一条命令一件）

子命令：
    status            看现在挂着没有、server.properties 的 level-name / server-port 是什么
    snapshot          把"功能改完、探针未挂"这一刻的 PotatoST.java 存成基准
    mount / unmount   挂 / 摘（摘 = **按基准整份还原**，不是逐行删）
    set-world <名>    改 run\\server\\server.properties 的 level-name（先备份原文件）
    set-port <端口>    改 server-port（别的线占着 25565 时用）
    restore-world     还原 server.properties
    run [tag]         起真服务端跑取证，日志落 check\\zf167_<tag>.log

⚠ ZF153 那一轮踩出来的四条（这里照抄，别重踩）：
  ① 挂载点**点名唯一锚点**（`…onPlayerLogin);` 那一行）+ **结构守卫**（插入位置必须在第一个
     方法定义之前）—— 结构猜测会插到最后一个方法里，探针永远不注册；
  ② 「摘干净」的基准是**功能改完、探针未挂**那一份，不是改前件；
  ③ 摘除按基准**整份还原**（逐行删会漏行、会叠层、会多出空行）；
  ④ `runServer` **不能带 `--args`**（会把 `--nogui` 顶掉 ⇒ NPE），换世界改 server.properties。
"""
import glob
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
MOD = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
MAIN = os.path.join(MOD, "PotatoST.java")
PROBE = os.path.join(ROOT, "build", "zftools", "check", "Zf167Check.java")
DEST = os.path.join(MOD, "Zf167Check.java")
CHECK = os.path.join(ROOT, "build", "zftools", "check")
PROPS = os.path.join(ROOT, "run", "server", "server.properties")
PROPS_BAK = os.path.join(CHECK, "zf167_server.properties.bak")
BK_NOPROBE = os.path.join(CHECK, "zf167_PotatoST_noprobe.java")

ANCHOR = u"Zf167Check.register();"
MOUNT_LINE = (u"        // ⚠⚠ 临时探针（ZF167）：空铝罐 / 可乐 / 饮料罐装机取证。\n"
              u"        //    跑完由 _zf167_probe.py unmount 摘掉 —— 摘除后 PotatoST.java 必须逐字节\n"
              u"        //    等于「功能改完、探针未挂」那份基准。\n"
              u"        Zf167Check.register();\n")
MARK = u"// ===== ZF167 探针挂载（unmount 会连这一行一起删） ====="
ANCHOR_LINE = u"addListener(StarfallRitualManager::onPlayerLogin);"
CTOR_END_GUARD = u"private void registerCapabilities("


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)


def mounted():
    return ANCHOR in read(MAIN)


def mount_text(base):
    lines = base.split(u"\n")
    hits = [i for i, l in enumerate(lines) if ANCHOR_LINE in l]
    if len(hits) != 1:
        raise ValueError(u"锚点行出现 %d 次（要 1 次）" % len(hits))
    idx = hits[0] + 1
    guard = [i for i, l in enumerate(lines) if CTOR_END_GUARD in l]
    if not guard or idx > guard[0]:
        raise ValueError(u"插入点第 %d 行不在构造函数里（第一个方法在第 %s 行）"
                         % (idx + 1, (guard[0] + 1) if guard else u"?"))
    block = (MARK + u"\n" + MOUNT_LINE).rstrip(u"\n").split(u"\n")
    lines[idx:idx] = block
    return u"\n".join(lines)


def cmd_status():
    print(u"探针文件在源码树里：%s" % os.path.exists(DEST))
    print(u"PotatoST.java 里挂着 Zf167Check.register()：%s" % mounted())
    others = [l.strip() for l in read(MAIN).split(u"\n") if u"Check.register()" in l]
    print(u"这份文件里所有 *Check.register() 行：%s" % (others if others else u"（无）"))
    if os.path.exists(PROPS):
        for line in read(PROPS).split(u"\n"):
            if line.startswith(u"level-name") or line.startswith(u"server-port"):
                print(u"server.properties: %s" % line)
    return 0


def cmd_snapshot():
    if mounted() or os.path.exists(DEST):
        print(u"  [STOP] 探针还挂着 —— 先 unmount 再 snapshot")
        return 1
    shutil.copy2(MAIN, BK_NOPROBE)
    print(u"  [OK] 基准 → %s（sha1 %s）" % (BK_NOPROBE, sha1(BK_NOPROBE)))
    return 0


def cmd_mount():
    if mounted() or os.path.exists(DEST):
        print(u"  [STOP] 已经挂着了（先 unmount）")
        return 1
    src = read(MAIN)
    others = [l.strip() for l in src.split(u"\n") if u"Check.register()" in l]
    if others:
        print(u"  [STOP] 这份文件里还有别人的探针：%s —— 等他们撤了再挂" % others)
        return 1
    if not os.path.exists(BK_NOPROBE):
        cmd_snapshot()
    base = read(BK_NOPROBE)
    if src != base:
        print(u"  [STOP] 盘上的 PotatoST.java 与基准不同 —— 先看清是谁改的再挂")
        return 1
    try:
        write(MAIN, mount_text(base))
    except ValueError as e:
        print(u"  [STOP] %s" % e)
        return 1
    shutil.copy2(PROBE, DEST)
    now = read(MAIN).split(u"\n")
    mi = [i for i, l in enumerate(now) if ANCHOR in l]
    gi = [i for i, l in enumerate(now) if CTOR_END_GUARD in l]
    guard_ok = bool(mi) and bool(gi) and mi[0] < gi[0]
    ok = mounted() and os.path.exists(DEST)
    print(u"  [%s] 挂载：%s + %s" % (u"OK" if (ok and guard_ok) else u"!!", MARK, DEST))
    print(u"  [%s] 结构守卫：挂载行第 %s 行、第一个方法第 %s 行"
          % (u"OK" if guard_ok else u"!!", (mi[0] + 1) if mi else u"?",
             (gi[0] + 1) if gi else u"?"))
    return 0 if (ok and guard_ok) else 1


def cmd_unmount():
    if os.path.exists(DEST):
        os.remove(DEST)
        print(u"  [OK] 删掉源码树里的 Zf167Check.java")
    if not os.path.exists(MAIN) or not os.path.exists(BK_NOPROBE):
        print(u"  [STOP] 缺文件（MAIN 或基准）")
        return 1
    base = read(BK_NOPROBE)
    cur = read(MAIN)
    want = mount_text(base)
    if cur == base:
        print(u"  [OK] 已经是基准状态（探针行 0 条）")
    elif cur == want:
        write(MAIN, base)
        print(u"  [OK] 按基准整份还原（摘掉挂载块）")
    else:
        import difflib
        print(u"  [!!] 盘上那份既不是基准、也不是「基准 + 挂载块」—— **不碰它**")
        for line in list(difflib.unified_diff(base.split(u"\n"), cur.split(u"\n"),
                                              u"基准", u"现在", lineterm=u""))[:20]:
            print(u"      " + line)
        return 1
    same = sha1(MAIN) == sha1(BK_NOPROBE)
    print(u"  [%s] 与基准逐字节相同（sha1 %s）" % (u"OK" if same else u"!!", sha1(MAIN)))
    return 0 if same else 1


def set_prop(key, value):
    if not os.path.exists(PROPS_BAK):
        shutil.copy2(PROPS, PROPS_BAK)
        print(u"  [OK] 备份 server.properties → %s" % PROPS_BAK)
    lines = read(PROPS).split(u"\n")
    hit = 0
    for i, line in enumerate(lines):
        if line.startswith(key + u"="):
            lines[i] = key + u"=" + str(value)
            hit += 1
    if hit != 1:
        print(u"  [STOP] %s 出现 %d 次" % (key, hit))
        return 1
    write(PROPS, u"\n".join(lines))
    print(u"  [OK] %s = %s" % (key, value))
    return 0


def cmd_restore_world():
    if not os.path.exists(PROPS_BAK):
        print(u"  [STOP] 没有备份，不还原")
        return 1
    shutil.copy2(PROPS_BAK, PROPS)
    print(u"  [OK] server.properties 还原")
    return 0


def cmd_run(tag):
    if not mounted():
        print(u"  [STOP] 探针没挂上")
        return 1
    log = os.path.join(CHECK, u"zf167_%s.log" % tag)
    env = dict(os.environ, GRADLE_USER_HOME=r"E:\gradle-home")
    cmd = [os.path.join(ROOT, "gradlew.bat"), "runServer", "--offline", "--no-build-cache"]
    print(u"  起服：%s（日志 → %s）" % (u" ".join(cmd), log))
    with open(log, "wb") as fh:
        p = subprocess.Popen(cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, env=env)
        rc = p.wait()
    print(u"  服务端进程退出码 = %d" % rc)
    txt = io.open(log, encoding="utf-8", errors="replace").read()
    lines = [l for l in txt.split(u"\n") if u"[A167] " in l]
    for l in lines[-40:]:
        print(u"  " + l)
    verdict = [l for l in lines if u"verdict:" in l]
    print(u"  verdict 行：%s" % (verdict[-1] if verdict else u"（没有 —— 探针可能没跑到收尾）"))
    return 0 if (verdict and u"ALL OK" in verdict[-1]) else 1


if __name__ == u"__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    c = sys.argv[1]
    if c == u"status":
        sys.exit(cmd_status())
    if c == u"snapshot":
        sys.exit(cmd_snapshot())
    if c == u"mount":
        sys.exit(cmd_mount())
    if c == u"unmount":
        sys.exit(cmd_unmount())
    if c == u"set-world":
        sys.exit(set_prop(u"level-name", sys.argv[2]))
    if c == u"set-port":
        sys.exit(set_prop(u"server-port", sys.argv[2]))
    if c == u"restore-world":
        sys.exit(cmd_restore_world())
    if c == u"run":
        sys.exit(cmd_run(sys.argv[2] if len(sys.argv) > 2 else u"after"))
    print(u"未知子命令：%s" % c)
    sys.exit(2)
