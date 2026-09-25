# -*- coding: utf-8 -*-
u"""_zf98_backup.py —— ZF98 **动手前**的改前件（§10）

用户原话（一条）：

  「流体泵改一下 本身不能储存流体 只做传输 且优先传输目标容器需要/能被接受 的流体」

⇒ 两件事：
  ① **拆掉流体泵的内部缓冲罐**（`FluidTank tank` + `TANK_CAPACITY = 8000`）——
     泵从此**只做传输**：一 tick 内"从源网络抽出来、直接灌进目标网络"，
     中间不再落进自己的罐子；
  ② **优先送目标能收的流体**：按"目标罐里已经有那种流体" → "目标 SIMULATE 能收" 的顺序挑，
     收不下的流体**不抽**（以前是抽进内部罐、送不出去就攒着）。

会动到的：
  · 2 个 Java：`FluidPumpBlockEntity`（主体）与 `PotatoST`（撤掉泵的流体能力登记）
  · 四份 lang 的 `tooltip.potato_s_t.fluid_pump`（补一句"泵不存液体"，**值改动、不增减键**）
  · 3 份文档 + `_zf78_falsify.py` + `_zf97_gates.ps1`（下一轮门的模板）
  · 旧成品 jar 与 `.sha1`
  · ⚠ 本轮**不动**任何活体数字（键数 / 配方数 / JEI 分类 / 流体数都不变）⇒ 不用改往轮校验的锚点
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
BK = r"C:\PotatoST救援\zf98_pre"
JAVA = r"src\main\java\com\potatost\mod"
FILES = [
    JAVA + r"\FluidPumpBlockEntity.java",
    JAVA + r"\FluidPumpBlock.java",
    JAVA + r"\PotatoST.java",
    JAVA + r"\ModBlocks.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"build\zftools\_zf72_verify.py",
    r"build\zftools\_zf78_falsify.py",
    r"build\zftools\_zf97_gates.ps1",
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
    # 顺手留一份"改前泵的全文"，方便事后逐行 diff（本轮的改动集中在一个文件里）
    pump = os.path.join(BK, JAVA, u"FluidPumpBlockEntity.java")
    if os.path.exists(pump):
        io.open(os.path.join(BK, u"_泵改前全文副本.txt"), "w", encoding="utf-8",
                newline=u"\n").write(io.open(pump, encoding="utf-8").read())
        ok += 1
        lines.append(u"%s  %10d  %s" % (sha1(os.path.join(BK, u"_泵改前全文副本.txt")),
                                        os.path.getsize(os.path.join(BK, u"_泵改前全文副本.txt")),
                                        u"_泵改前全文副本.txt"))
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
