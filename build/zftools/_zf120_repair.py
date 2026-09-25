# -*- coding: utf-8 -*-
r"""_zf120_repair.py —— 紧急修复：25 份 `_zf*_verify.py` 被**清成 0 字节**（0.11 ZF122 那次提交带进去的）

## 事故

2026-09-26 01:25:38，盘上 25 份 `build\zftools\_zf*_verify.py` **同时变成 0 字节**，
紧接着被 `0489cf9`（"0.11 ZF122：星仪图之章"）**当成正常内容提交进仓库**
（⇒ `HEAD` 上它们也是空的，`git status` 因此显示"干净"，`git checkout` 救不回来）。

被清掉的正好是"含语言键数断言"的那一批文件（`_zf71 _zf73 _zf75 _zf78 _zf79 _zf80 _zf81 _zf82
_zf93 _zf96 _zf97 _zf98 _zf100 _zf101 _zf102 _zf103 _zf107 _zf109 _zf111 _zf112 _zf114 _zf117
_zf118 _zf119 _zf121`）—— 与"活体数字重定目标"那张名单**完全重合**。
最可能的原因：某个重定目标脚本先以 `w` 模式打开文件再读（`open(p, 'w').read()` 这种写法会**先截断**），
一次把整张名单清零；也可能是两个 falsify 实例并发互相覆盖。**无论哪种，修复路径一样。**

## 修法

逐份找出**最近一次非空的 blob**（`git log --format=%h -- <path>` 从上往下找第一个长度 > 0 的），
`git show <rev>:<path>` 取回来写盘；然后：

  ① 每份都 `compile()` 过一遍（语法必须没问题）；
  ② 跑 `_zf120_retarget.py` 把 `449 → 454`（键数）重新跟平
     —— 取回的那一版可能停在 449，也可能已经是 454，脚本按"独立 449"匹配，幂等）；
  ③ 再扫一遍全仓 0 字节的文本文件，确认没有漏网的。

跑法：
    python build/zftools/_zf120_repair.py            # 只诊断
    python build/zftools/_zf120_repair.py --write
"""
import io
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\bin\git.exe"
TOOLS = os.path.join(ROOT, "build", "zftools")

# 事故清单（0 字节的那些；按盘上现场扫出来的）
NAMES = [
    "_zf71_verify", "_zf73_verify", "_zf75_verify", "_zf78_verify", "_zf79_verify",
    "_zf80_verify", "_zf81_verify", "_zf82_verify", "_zf93_verify", "_zf96_verify",
    "_zf97_verify", "_zf98_verify", "_zf100_verify", "_zf101_verify", "_zf102_verify",
    "_zf103_verify", "_zf107_verify", "_zf109_verify", "_zf111_verify", "_zf112_verify",
    "_zf114_verify", "_zf117_verify", "_zf118_verify", "_zf119_verify", "_zf121_verify",
]

fails = []


def git(*args):
    return subprocess.run([GIT, "-C", ROOT] + list(args), stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL).stdout


def newest_nonempty(rel):
    u"""最近一次非空的 blob：(rev, bytes)。找不到返回 (None, b"")。"""
    revs = git("log", "--format=%h", "--", rel).decode().split()
    for r in revs:
        blob = git("show", u"%s:%s" % (r, rel))
        if blob:
            return r, blob
    return None, b""


def main(argv):
    write = u"--write" in argv
    print(u"================ 诊断：25 份被清零的校验器 ================")
    plan = []
    for n in NAMES:
        rel = u"build/zftools/%s.py" % n
        p = os.path.join(TOOLS, n + u".py")
        now = os.path.getsize(p) if os.path.isfile(p) else -1
        rev, blob = newest_nonempty(rel)
        if rev is None:
            fails.append(u"%s：git 历史里**没有**非空版本（只能从备份目录找）" % n)
            print(u"  [FAIL] %-20s 现状 %d B，历史里无内容" % (n, now))
            continue
        ok = True
        try:
            compile(blob.decode("utf-8"), rel, "exec")
        except SyntaxError as e:
            ok = False
            fails.append(u"%s：取回的那版语法就错（%s @%s）" % (n, e, rev))
        print(u"  [%s] %-20s 现状 %6d B ← %s 的 %6d B%s"
              % (u"OK" if ok else u"FAIL", n, now, rev, len(blob), u"" if ok else u"（语法错）"))
        plan.append((p, blob, rev))

    if not write:
        print(u"\n（只诊断；加 --write 才会写盘）")
        return 1 if fails else 0

    print(u"\n================ 写回 ================")
    for p, blob, rev in plan:
        io.open(p, "wb").write(blob)
        back = io.open(p, "rb").read()
        same = back == blob
        print(u"  [%s] %s ← %s（%d B）"
              % (u"OK" if same else u"FAIL", os.path.basename(p), rev, len(back)))
        if not same:
            fails.append(u"写回后不一致：%s" % p)

    print(u"\n================ 全仓再扫一遍 0 字节文本文件 ================")
    zero = []
    for sub in ("src", "docs", "build/zftools", "build/用户素材"):
        base = os.path.join(ROOT, sub.replace(u"/", os.sep))
        for dirpath, _dirs, files in os.walk(base):
            if u"__pycache__" in dirpath:
                continue
            for f in files:
                fp = os.path.join(dirpath, f)
                try:
                    if os.path.getsize(fp) == 0:
                        zero.append(os.path.relpath(fp, ROOT))
                except OSError:
                    pass
    for z in zero:
        print(u"  [WARN] 0 字节：%s" % z)
    if not zero:
        print(u"  [OK]   一个 0 字节文件都没有了")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
