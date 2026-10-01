# -*- coding: utf-8 -*-
u"""_zf156_commit.py —— ZF156 提交（**只提交自己点名的路径**，绝不 `git add -A`）。

跑法：python build\\zftools\\_zf156_commit.py [--write|--push]
  --write = 真的 git add + commit；不加只看清单。
"""
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
RES = os.path.join(ROOT, r"src\main\resources")
ZT = os.path.join(ROOT, "build", "zftools")
MSG = os.path.join(ZT, u"_zf156_commit_msg.txt")

# ---- 我这一轮动过的路径（全部写死，不用通配符去扫别人的东西）----
MINE = [
    r"gradle.properties",
    r"src\main\java\com\potatost\mod\ModAttachments.java",
    r"src\main\java\com\potatost\mod\GuideBook.java",
    r"src\main\java\com\potatost\mod\TerminalBlockEntity.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"build\zftools\check\Zf156Check.java",
    r"build\zftools\_zf149_verify.py",
    r"build\zftools\_zf149_jar.py",
    r"build\zftools\_zf73_verify.py",
    r"build\zftools\_zf78_verify.py",
    r"build\zftools\_zf79_verify.py",
    r"build\zftools\_zf155_verify.py",
    r"build\zftools\_zf155_jarcheck.py",
    r"build\zftools\_zf156_probe_utf8.txt",
    r"build\zftools\_zf156_falsify_probe_red.txt",
    r"build\zftools\_zf156_falsify_probe_green.txt",
    r"build\zftools\_zf156_recon.txt",
    r"build\zftools\_zf156_gatesnap.txt",
]

MSG_TEXT = u"""ZF156 0.13：端子连线不再因区块卸载断开 + 手册只发一次 + 金属板配方认 #c:plates/*（0.13）

用户原话：「0.13 先简单修一下bug和一些小建议 1.有些时候端子上已经连接的线会消失
（不知道是不是刷新没的问题）2.potatoST手册每回进游戏都会给一本 过于冗杂 改成只有玩家第一次
进入游戏才会给 3.本mod配方里的金属板可以兼容别的mod金属板（板子确实通用 但是咱们的合成配方
只认本mod板）」。

① 端子连线：
   - 根因（源码）：区块卸载走 ServerLevel.unload → LevelChunk.clearAllBlockEntities()
     （:616-618），它对每个方块实体先 onChunkUnloaded()、再 setRemoved()；
     而旧的 setRemoved() 不分青红皂白通知对端删连接 ⇒ 走远一次双方就互相划账，
     且每根线只由坐标小的那一端画 ⇒ 那半边的线**永久**消失（用户说的「有些时候」）。
   - 修法：onChunkUnloaded() 打标记，setRemoved() 见标记只消费不拆线；真挖掉/被替换/
     崩掉移除三条路照旧通知对端。早退排在 isClientSide 判断之前（客户端重收区块包也走这条）。
   - 证据：真开服探针 A1-A5（含"真挖掉仍然断"的负对照）；活体反证刀把这一行改坏后
     A2/A3 当场变红、拔刀回到 ALL OK。

② 手册只发一次：
   - 根因（源码）：换维度（ServerGamePacketListenerImpl:1669 CHANGED_DIMENSION）与死亡（:1676
     KILLED）都走 PlayerList.respawn → ServerPlayer.restoreFrom（:1437），而 restoreFrom
     只搬 PERSISTED_NBT_TAG 一个键（:1483-1484）⇒ 0.12 写在玩家持久化数据里的标记每换一次
     维度/每死一次就丢。真实存档取证：同一玩家在"新的世界"（没死过）带标记、
     在"新的世界 (1)"（有 LastDeathLocation + SpawnDimension）标记就没了。
   - 修法：标记搬进 NeoForge 附件 ModAttachments.GUIDE_GIVEN（serialize(Codec.BOOL) +
     copyOnDeath()）；restoreFrom:1485 的 PlayerEvent.Clone 会让 NeoForge 把附件拷到新玩家。
     老标记只读迁移（已拿过书的不补发）。

③ 金属板跨 mod：
   - 29 处原料从 {"item": "potato_s_t:<金属>_plate"} 换成 {"tag": "c:plates/<金属>"}（21 份配方），
     液压机那 7 份产物一字未动；靠社区约定 + IE/Create 自己挂好的标签，不硬写别人的物品 id。
   - 附带上车：ZF152 那条线只在盘上、没进 git 的 15 份数据（7 张 c:plates/* 子标签 + 父标签 +
     7 条 create:pressing）—— 本轮配方引用它们，不带上车 HEAD 里就是"配方指向空标签 = 死配方"。
     ⚠ 那 15 份是 ZF152 的产物，不是我写的。

版本与判据：mod_version 0.12 → 0.13（唯一一处）；_zf73/_zf78/_zf79_verify.py 的版本断言、
_zf149_verify.py 的成品靶子与 build\\libs 名、_zf149_jar.py 的默认 jar 与 mods.toml 版本、
_zf155_jarcheck.py 的 jar 名、_zf155_verify.py 的 E2（「最大」改「唯一」）一起跟平；
_zf152_plates_gate.py 一个字没动、仍然全过。

成品：release\\PotatoST-0.13.jar = 5,865,661 字节 / sha1
9be8488c877baf445ae68a2d0ed385b338503b1f（旧的 0.12 那份留在盘上不动）；哈希三处联动已跟平。

顺手修：交接 §1 成品行在 HEAD（57423ee）里就是坏字符（反引号被吃成 \\、`release` 成了 `elease`），
本轮整行重写修好。

证据清单：探针 20 项 ALL OK（_zf156_probe_utf8.txt：A1-A5 / B1-B7 / C1-C8）；
常驻 _zf156_verify.py 37 项 0 失败；静态反证 11/11 把刀全咬住；活体反证上刀变红、拔刀回绿；
_zf149_jar.py 26/0、_zf149_verify.py 28/0、_zf156_jarcheck.py ALL OK、_zf155_jarcheck.py ALL OK；
探针挂载/摘除与"改前件 + 本轮真实改动"逐字节一致（77f7ae8101424e30）。
"""


def sh(args):
    return subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def main(argv):
    write = u"--write" in argv
    push = u"--push" in argv

    # 配方里带 #c:plates/ 的那 21 份
    recipe_dir = os.path.join(RES, r"data\potato_s_t\recipe")
    tags = []
    for dirpath, _d, filenames in os.walk(recipe_dir):
        for fn in filenames:
            if not fn.endswith(".json"):
                continue
            p = os.path.join(dirpath, fn)
            if u"#c:plates/" not in io.open(p, encoding="utf-8").read() and u'"c:plates/' not in io.open(p, encoding="utf-8").read():
                continue
            tags.append(os.path.relpath(p, ROOT))
    # ZF152 的 15 份数据（本轮的依赖）
    plates_dir = os.path.join(RES, r"data\c\tags\item\plates")
    zf152 = [r"src\main\resources\data\c\tags\item\plates.json"]
    zf152 += [os.path.relpath(os.path.join(plates_dir, fn), ROOT) for fn in sorted(os.listdir(plates_dir))]
    pressing = os.path.join(recipe_dir, "pressing")
    zf152 += [os.path.relpath(os.path.join(pressing, fn), ROOT) for fn in sorted(os.listdir(pressing))]

    paths = list(MINE) + sorted(tags) + sorted(zf152)
    # 本轮的脚本（py 全带；日志类不带）
    for fn in sorted(os.listdir(ZT)):
        if fn.startswith(u"_zf156_") and fn.endswith(u".py"):
            paths.append(os.path.join(r"build\zftools", fn))
    paths = sorted(set(paths))

    print(u"要 add 的路径 %d 条：" % len(paths))
    missing = []
    for p in paths:
        if not os.path.exists(os.path.join(ROOT, p)):
            missing.append(p)
    if missing:
        print(u"  ⚠ 不存在的路径 %d 条（跳过）：" % len(missing))
        for m in missing:
            print(u"     " + m)
        paths = [p for p in paths if p not in missing]
    for p in paths:
        print(u"   " + p)

    if not write:
        print(u"（没加 --write：只列清单，不 add/commit）")
        return 0

    io.open(MSG, "w", encoding="utf-8", newline="\n").write(MSG_TEXT)
    r = sh(["git", "add", "--"] + paths)
    print(r.stdout.decode("utf-8", "replace")[-500:])
    # ⚠ 用 `git diff --cached --name-only -z`：`git status --short` 对**非 ASCII 路径**
    #   会加引号 + 八进制转义（`"docs/\345\244\232..."`），第一版就是被这个绊住的。
    #   `-z` 给的是 NUL 分隔的**原样**路径，不用再解转义。
    staged = [p for p in sh(["git", "diff", "--cached", "--name-only", "-z"])
              .stdout.decode("utf-8", "replace").split(u"\0") if p]
    allowed = set(p.replace(u"\\", u"/") for p in paths)
    bad = [s for s in staged if s.replace(u"\\", u"/") not in allowed]
    if bad:
        print(u"!! 暂存区里有**不在清单里**的路径（停手）：")
        for b in bad[:20]:
            print(u"   " + b)
        return 2
    print(u"暂存区核对：%d 条，全部在清单里" % len(staged))
    r = sh(["git", "commit", "-F", MSG])
    out = r.stdout.decode("utf-8", "replace")
    print(out[-1200:])
    if r.returncode != 0:
        return 1
    if push:
        for attempt in range(4):
            r = sh(["git", "push", "origin", "HEAD"])
            out = r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
            print(u"push 第 %d 次 rc=%d\n%s" % (attempt + 1, r.returncode, out[-400:]))
            if r.returncode == 0:
                break
        else:
            print(u"!! push 四次都没成（网络老毛病，稍后重试）")
            return 1
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
