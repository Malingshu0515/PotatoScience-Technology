# -*- coding: utf-8 -*-
u"""_zf95_backup.py —— ZF95 **动手前**的改前件（§10）

本轮：用户给了 **5 条合成配方**（原话一条到底，我按"**名字在前、九宫格在后**"切开 ——
切开后每条都是**完整 3×3、不多不少正好 9 格**，这本身就是切法正确的证据）：

  茉莉花唱片   ← 四角灵魂灯笼 + 中心火把花 + 紧挨中心的四格粗金块
  共和国之砧   ← 最左最右两列红石粉（6）+ 中心铁砧 + 上下各一个钛锭
  合金炉主控   ← 铝板/铁板/铝板 · 镍板/电容/镍板 · 加热装置/一般金属块/散热装置
  分馏塔控制器 ← 钢板×3 · 耐热金属块/铜块/耐热金属块 · 高碳钢/黑曜石/高碳钢
  分馏塔操作器 ← 钴锭/钢板/钴锭 · 流体泵/钻石块/灌装机 · 油罐/分馏塔控制器/油罐

会动到的：**新建 5 份配方 JSON** + `_zf71_verify.py`（活体数字：crafting_shaped 30 → 35）
+ 两份文档 + `_zf78_falsify.py` + 旧成品 jar 与 `.sha1`。
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
BK = r"C:\PotatoST救援\zf95_pre"
FILES = [
    r"build\zftools\_zf71_verify.py",
    r"build\zftools\_zf78_falsify.py",
    r"docs\开发档案.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"docs\贴图清单.md",
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
    # 顺手记下"改前配方目录"的清单（本轮只会**新增**，不会改旧的 —— 新增前先留一份名字表）
    rdir = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
    names = sorted(n for n in os.listdir(rdir) if n.endswith(".json"))
    dst = os.path.join(BK, "recipe_before.txt")
    io.open(dst, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(names) + u"\n")
    ok += 1
    lines.append(u"%s  %10d  %s" % (sha1(dst), os.path.getsize(dst), u"recipe_before.txt（%d 份）" % len(names)))
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s（配方目录改前 %d 份）" % (ok, BK, len(names)))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
