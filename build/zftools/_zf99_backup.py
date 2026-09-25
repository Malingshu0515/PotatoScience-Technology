# -*- coding: utf-8 -*-
u"""_zf99_backup.py —— ZF99 **动手前**的改前件（§10）

用户原话（一条）：

  「空气分离器工作时加一点白色的烟雾粒子」

⇒ 给空气分离器加**工作时的白色烟雾粒子**：只在真正干活（status = RUNNING）时，
从顶面轻轻冒几缕 `ParticleTypes.CLOUD`（原版白色烟）。

会动到的：
  · `AirSeparatorBlockEntity.java`（粒子那段代码落在这里 —— 这台机器只有服务端 tick）
  · 3 份文档 + `_zf78_falsify.py` + `_zf98_gates.ps1`（下一轮门的模板）
  · 旧成品 jar 与 `.sha1`
  · ⚠ 本轮**不动任何活体数字**（键数 303 / 配方 38 / JEI 11 / 流体 10 都不变）
    ⇒ 往轮校验一条锚点都不用改
"""
import hashlib
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf99_pre"
JAVA = r"src\main\java\com\potatost\mod"
FILES = [
    JAVA + r"\AirSeparatorBlockEntity.java",
    JAVA + r"\AirSeparatorBlock.java",
    r"build\zftools\_zf97_verify.py",
    r"build\zftools\_zf78_falsify.py",
    r"build\zftools\_zf98_gates.ps1",
    r"docs\开发档案.md",
    r"docs\贴图清单.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s（重跑会覆盖改前件，直接中止）" % BK)
        return 1
    lines, ok = [], 0
    for rel in FILES:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            fails.append(u"缺文件：%s" % rel)
            lines.append(u"MISSING  %s" % rel)
            continue
        dst = os.path.join(BK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        before = sha1(src)
        shutil.copy2(src, dst)
        after = sha1(dst)
        if before != after:
            fails.append(u"%s：拷贝后哈希不一致" % rel)
        else:
            ok += 1
            lines.append(u"%s  %10d  %s" % (after, os.path.getsize(dst), rel))
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
