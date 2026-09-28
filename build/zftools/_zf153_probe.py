# -*- coding: utf-8 -*-
u"""_zf153_probe.py —— ZF153 的临时探针挂载 / 起服取证 / 摘除（一条命令一件）

子命令：
    status            看现在挂着没有、server.properties 的 level-name 是什么
    mount             把 check\\Zf153Check.java 拷进 src 并挂上 register()（只加自己那一行）
    unmount           摘掉（逐字节核对回改前件）
    set-world <名字>   改 run\\server\\server.properties 的 level-name（先备份原文件）
    restore-world     还原 server.properties
    run [tag]         起真服务端跑取证，日志落 check\\zf153_<tag>.log

⚠ 三条纪律（全是往轮踩出来的）：
  ① 挂载点**不许**碰别人的行：ZF151/ZF152 那条线也在这份文件上挂过探针
     （本轮开工时 `PotatoST.java:78` 就挂着他们的 `Zf151Check.register();`，我等到它撤了才动），
     所以挂载/摘除都只认**我自己那一行**，逐行处理，不做整块替换。
  ② `runServer` **不能带 `--args`**：那会把 run 配置里的 `--nogui` 顶掉，直接
     `NullPointerException at ImmediateWindowHandler.load`（ZF140/ZF146 两次踩到，见 §4.153）；
     换世界要改 `server.properties` 的 `level-name`（ZF77 的做法）。
  ③ 摘除之后必须**逐字节**等于改前件（`C:\\PotatoST救援\\zf153_pre\\...\\PotatoST.java`），
     少一个字节都不算摘干净。
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
MOD = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
MAIN = os.path.join(MOD, "PotatoST.java")
PROBE = os.path.join(ROOT, "build", "zftools", "check", "Zf153Check.java")
DEST = os.path.join(MOD, "Zf153Check.java")
CHECK = os.path.join(ROOT, "build", "zftools", "check")
BK_MAIN = r"C:\PotatoST救援\zf153_pre\src\main\java\com\potatost\mod\PotatoST.java"
# ⚠ 两份基准，各管一件事：
#   ① 改前件（zf153_pre）= **这一轮开工之前**的样子 —— 拿它比"摘干净了没"是错的：
#      本轮功能本身就在这份文件里加了两处监听（12 行），摘掉探针也不会变回改前件。
#   ② 功能改完、探针未挂（zf153_PotatoST_noprobe.java）= 摘除后**必须逐字节等于**的那一份。
#      第一版只拿了 ①，当场报红 —— 红得对（判据没错），但它量的不是"摘干净了没"。
BK_NOPROBE = os.path.join(CHECK, "zf153_PotatoST_noprobe.java")
PROPS = os.path.join(ROOT, "run", "server", "server.properties")
PROPS_BAK = os.path.join(CHECK, "zf153_server.properties.bak")

ANCHOR = u"Zf153Check.register();"
MOUNT_LINE = (u"        // ⚠⚠ 临时探针（ZF153）：振金剑取证（属性 / 无法破坏 / 免疫三效果 / 猛击）。\n"
              u"        //    跑完由 _zf153_probe.py unmount 摘掉 —— 摘除后 PotatoST.java 必须逐字节\n"
              u"        //    等于改前件（zf153_pre）。\n"
              u"        Zf153Check.register();\n")
MARK = u"// ===== ZF153 探针挂载（unmount 会连这一行一起删） ====="
# ⚠ 挂载点：**构造函数里**最后一行（星轨坠那两个监听之后）。
#   第一版我是"从后往前找 `    }` + 前面空行"，结果插到了**最后一个方法**的收尾里
#   （那个方法只在事件里跑 ⇒ 探针永远不会注册，起服一看日志才知道）。
#   现在改成**点名锚点**（这一行在文件里唯一），并加一条结构性守卫：
#   插入位置必须在第一个方法定义之前 —— 那才叫"在构造函数里"。
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


def cmd_status():
    print(u"探针文件在源码树里：%s" % os.path.exists(DEST))
    print(u"PotatoST.java 里挂着 Zf153Check.register()：%s" % mounted())
    others = [l.strip() for l in read(MAIN).split(u"\n") if u"Check.register()" in l]
    print(u"这份文件里所有 *Check.register() 行：%s" % (others if others else u"（无）"))
    if os.path.exists(PROPS):
        for line in read(PROPS).split(u"\n"):
            if line.startswith(u"level-name"):
                print(u"server.properties: %s" % line)
    print(u"server.properties 备份在：%s（%s）" % (PROPS_BAK, os.path.exists(PROPS_BAK)))
    return 0


def mount_text(base):
    u"""在「功能改完、探针未挂」那份文本上插入挂载块（**唯一**的挂载写法，挂/摘共用）。"""
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


def cmd_mount():
    if mounted() or os.path.exists(DEST):
        print(u"  [STOP] 已经挂着了（先 unmount）")
        return 1
    src = read(MAIN)
    # 别人的探针必须先撤（LF：两个人同时挂会让"谁的红是谁的"说不清，ZF151 那条线还在跑时尤其危险）
    others = [l.strip() for l in src.split(u"\n") if u"Check.register()" in l]
    if others:
        print(u"  [STOP] 这份文件里还有别人的探针：%s —— 等他们撤了再挂" % others)
        return 1
    if not os.path.exists(BK_NOPROBE):
        cmd_snapshot()
    base = read(BK_NOPROBE)
    if src != base:
        print(u"  [STOP] 盘上的 PotatoST.java 与「功能改完、探针未挂」基准不同 —— "
              u"先看清是谁改的（可能别的线动过）再挂")
        return 1
    try:
        write(MAIN, mount_text(base))
    except ValueError as e:
        print(u"  [STOP] %s" % e)
        return 1
    shutil.copy2(PROBE, DEST)
    ok = mounted() and os.path.exists(DEST)
    # 结构守卫：挂载行必须在第一个方法定义**之前**
    now = read(MAIN).split(u"\n")
    mi = [i for i, l in enumerate(now) if ANCHOR in l]
    gi = [i for i, l in enumerate(now) if CTOR_END_GUARD in l]
    guard_ok = bool(mi) and bool(gi) and mi[0] < gi[0]
    print(u"  [%s] 挂载：%s + %s" % (u"OK" if (ok and guard_ok) else u"!!", MARK, DEST))
    print(u"  [%s] 结构守卫：挂载行在第 %s 行、第一个方法在第 %s 行（必须在构造函数里）"
          % (u"OK" if guard_ok else u"!!", (mi[0] + 1) if mi else u"?",
             (gi[0] + 1) if gi else u"?"))
    print(u"  挂载后 PotatoST.java sha1 = %s" % sha1(MAIN))
    return 0 if (ok and guard_ok) else 1


def cmd_snapshot():
    u"""把"功能改完、探针未挂"这一刻的 PotatoST.java 存成基准（挂载前跑一次）。"""
    if mounted() or os.path.exists(DEST):
        print(u"  [STOP] 探针还挂着 —— 先 unmount 再 snapshot")
        return 1
    shutil.copy2(MAIN, BK_NOPROBE)
    print(u"  [OK] 基准 → %s（sha1 %s）" % (BK_NOPROBE, sha1(BK_NOPROBE)))
    return 0


def cmd_unmount():
    u"""摘除 = **按基准整份还原**（不再逐行增删）。

    ⚠ 第一版逐行删：漏认一行就叠层（实测挂第三次时那一行出现了 3 份），而且挂载块末尾
       多出来的那行空行也删不掉（摘完与基准差一行空行）。两份完整状态之间来回切，
       才是"摘干净"这件事的确定性做法。安全阀：盘上那份必须**正好等于**"基准 + 挂载块"，
       否则拒绝动它（说明别人改过）。
    """
    if os.path.exists(DEST):
        os.remove(DEST)
        print(u"  [OK] 删掉源码树里的 Zf153Check.java")
    if not os.path.exists(MAIN) or not os.path.exists(BK_NOPROBE):
        print(u"  [STOP] 缺文件（PotatoST.java 或基准）")
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
        print(u"  [!!] 盘上那份既不是基准、也不是「基准 + 挂载块」—— **不碰它**，先看清是谁改的")
        for line in list(difflib.unified_diff(base.split(u"\n"), cur.split(u"\n"),
                                              u"基准", u"现在", lineterm=u""))[:20]:
            print(u"      " + line)
        return 1
    same = sha1(MAIN) == sha1(BK_NOPROBE)
    print(u"  [%s] 摘除后与「功能改完、探针未挂」逐字节相同（sha1 %s）"
          % (u"OK" if same else u"!!", sha1(MAIN)))
    if not same:
        import difflib
        a = read(BK_NOPROBE).split(u"\n")
        b = read(MAIN).split(u"\n")
        for line in list(difflib.unified_diff(a, b, u"基准", u"现在", lineterm=u""))[:24]:
            print(u"      " + line)
    # ② 附带信息：与改前件比，差的必须**只有本轮功能那 12 行**（证明摘除没顺手带走别的）
    if os.path.exists(BK_MAIN):
        import difflib
        pre = read(BK_MAIN).split(u"\n")
        now = read(MAIN).split(u"\n")
        diff = [l for l in difflib.unified_diff(pre, now, lineterm=u"")
                if l.startswith(u"+") and not l.startswith(u"+++")]
        added = [l for l in diff if l.strip() != u"+"]
        print(u"  [%s] 与改前件的差 = %d 行正文新增（本轮功能那两处监听 = 11 行正文 + 1 行空行；"
              u"探针行 0 条）"
              % (u"OK" if (len(added) == 11 and not any(ANCHOR in l for l in now)) else u"!!",
                 len(added)))
        for l in added:
            print(u"      " + l)
    return 0 if same else 1


def cmd_set_world(name):
    if not os.path.exists(PROPS_BAK):
        shutil.copy2(PROPS, PROPS_BAK)
        print(u"  [OK] 备份 server.properties → %s（sha1 %s）" % (PROPS_BAK, sha1(PROPS_BAK)))
    lines = read(PROPS).split(u"\n")
    hit = 0
    for i, line in enumerate(lines):
        if line.startswith(u"level-name"):
            lines[i] = u"level-name=" + name
            hit += 1
    if hit != 1:
        print(u"  [STOP] level-name 出现 %d 次" % hit)
        return 1
    write(PROPS, u"\n".join(lines))
    print(u"  [OK] level-name = %s" % name)
    return 0


def cmd_set_port(port):
    u"""给自己的探针换一个端口。

    ⚠ 为什么要有这一步：本轮开工时**另一条线的专用服务端正占着 25565**
    （`forgeserverdev`，13:56 起就在跑）。我的第一次探针就是**绑定失败**、
    没取到任何证（日志里 `FAILED TO BIND TO PORT`）。**不去掐别人的进程** ——
    换端口是代价最小、也不破坏别人取证的做法；跑完把 server.properties 逐字节还原。
    """
    if not os.path.exists(PROPS_BAK):
        shutil.copy2(PROPS, PROPS_BAK)
        print(u"  [OK] 备份 server.properties → %s（sha1 %s）" % (PROPS_BAK, sha1(PROPS_BAK)))
    lines = read(PROPS).split(u"\n")
    hit = 0
    for i, line in enumerate(lines):
        if line.startswith(u"server-port"):
            lines[i] = u"server-port=" + str(port)
            hit += 1
    if hit != 1:
        print(u"  [STOP] server-port 出现 %d 次" % hit)
        return 1
    write(PROPS, u"\n".join(lines))
    print(u"  [OK] server-port = %s" % port)
    return 0


def cmd_restore_world():
    if not os.path.exists(PROPS_BAK):
        print(u"  [STOP] 没有备份，不还原")
        return 1
    shutil.copy2(PROPS_BAK, PROPS)
    print(u"  [OK] server.properties 还原（sha1 %s）" % sha1(PROPS))
    return 0


def cmd_run(tag):
    if not mounted():
        print(u"  [STOP] 探针没挂上")
        return 1
    log = os.path.join(CHECK, u"zf153_%s.log" % tag)
    env = dict(os.environ)
    env["GRADLE_USER_HOME"] = r"E:\gradle-home"
    cmd = [os.path.join(ROOT, "gradlew.bat"), "runServer", "--offline", "--no-build-cache"]
    print(u"  起服：%s（日志 → %s）" % (u" ".join(cmd), log))
    with open(log, "wb") as fh:
        p = subprocess.Popen(cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, env=env)
        rc = p.wait()
    print(u"  服务端进程退出码 = %d" % rc)
    txt = io.open(log, encoding="utf-8", errors="replace").read()
    lines = [l for l in txt.split(u"\n") if u"[A153] " in l]
    for l in lines:
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
    if c == u"mount":
        sys.exit(cmd_mount())
    if c == u"unmount":
        sys.exit(cmd_unmount())
    if c == u"snapshot":
        sys.exit(cmd_snapshot())
    if c == u"set-world":
        sys.exit(cmd_set_world(sys.argv[2]))
    if c == u"set-port":
        sys.exit(cmd_set_port(sys.argv[2]))
    if c == u"restore-world":
        sys.exit(cmd_restore_world())
    if c == u"run":
        sys.exit(cmd_run(sys.argv[2] if len(sys.argv) > 2 else u"after"))
    print(u"未知子命令：%s" % c)
    sys.exit(2)
