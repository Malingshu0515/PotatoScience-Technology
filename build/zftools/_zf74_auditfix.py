# -*- coding: utf-8 -*-
u"""_zf74_auditfix.py —— 给第 1 道门（Audit.ps1）补流体知识

问题（ZF74 门跑出来的 13 条 FAIL）：J 项的"已注册 id 清单"是从 lang 键里抄的，只认
`item.potato_s_t.*` / `block.potato_s_t.*` ⇒ **流体 id 一律被判"不存在"**
（`potato_s_t:oxygen`、`potato_s_t:flowing_crude_oil` …）。

两处改动：
  ① id 清单补上 `ModFluids.java` 里 `FLUIDS.register("…")` 注册的流体（源头而不是 lang）；
  ② **新增一条硬检查**：每种流体都必须挂进某个 `c:` 标签 —— 把用户 2026-09-24 的规矩
     （「以后的流体也通用」）变成机器守的规矩，将来加流体忘了挂标签，门会直接红。

改前先按 §10 抄一份到 `zf74_pre`（Audit.ps1 不在本轮一开始的清单里，属于"改到才发现要动"的文件）。
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
AUDIT = os.path.join(PROJ, u"build", u"zftools", u"Audit.ps1")
PRE = r"C:\PotatoST救援\zf74_pre\build\zftools"

OLD = u"""    $ids = @($ids | Sort-Object -Unique)"""
NEW = u"""    # 【ZF74 补】流体也是 id：从 ModFluids.java 的注册里抄（原来只认 lang 的 item/block 键，
    #            于是所有 potato_s_t:<fluid> 都被误判成"不存在"）
    $fluidIds = @()
    $fluidsFile = 'E:\\PotatoST\\src\\main\\java\\com\\potatost\\mod\\ModFluids.java'
    if (Test-Path $fluidsFile) {
        $ft = [IO.File]::ReadAllText($fluidsFile, [Text.Encoding]::UTF8)
        foreach ($fm in [regex]::Matches($ft, 'FLUIDS\\.register\\("([a-z0-9_]+)"')) {
            $fluidIds += $fm.Groups[1].Value
        }
    }
    $fluidIds = @($fluidIds | Sort-Object -Unique)
    $ids = @($ids + $fluidIds | Sort-Object -Unique)
    # ①b 每种流体都必须挂进某个 c: 标签（ZF74 规矩：以后的流体也要和别的 mod 通用，见档案 §6.19）
    foreach ($fid in $fluidIds) {
        if ($tagText -notmatch ('potato_s_t:' + [regex]::Escape($fid) + '\\b')) {
            Write-Output ("  [FAIL] 流体 {0} 没挂进任何 c: 标签 —— 见档案 §6.19" -f $fid); $j++; $fail++
        }
    }"""


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    # §10：改前先抄一份（这次要动的文件没在一开始的清单里）
    if not os.path.isdir(PRE):
        os.makedirs(PRE)
    dst = os.path.join(PRE, u"Audit.ps1")
    if not os.path.isfile(dst):
        shutil.copy2(AUDIT, dst)
        print(u"  [OK] 改前件补抄 Audit.ps1  %s" % sha1(dst)[:12])
    else:
        print(u"  [SKIP] Audit.ps1 改前件已在")

    text = io.open(AUDIT, "r", encoding="utf-8").read()
    n = text.count(OLD)
    if n != 1:
        print(u"  !! 锚点命中 %d 次（必须 1）⇒ 不写" % n)
        return 1
    io.open(AUDIT, "w", encoding="utf-8", newline=u"\n").write(text.replace(OLD, NEW, 1))
    print(u"  [OK] Audit.ps1 补上「流体 id 清单 + 每种流体必须挂 c: 标签」")
    return 0


if __name__ == "__main__":
    sys.exit(main())
