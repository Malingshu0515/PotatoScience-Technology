# -*- coding: utf-8 -*-
u"""_zf76_docs2.py —— 把 ZF76 重打包后的新成品哈希写进档案 §9（ZF75/ZF74 校验都要求）"""
import io
import sys

ARCH = r"E:\PotatoST\docs\开发档案.md"
OLD = u"      **验证**：清了端口残留后端起新世界，`Preparing spawn area` 正常推到 51%+ 并继续（修复前直接在生成阶段崩）。"
NEW = OLD + u"""
      **成品**：同版本重打包 ⇒ 新 `release\\PotatoST-0.11.jar` = **`850d4673075ee86df87305cd2c7aff16f5a2442f`**
      （2,231,564 B）；上一版 `4528ed53…` 作废（0.10 成品 `84d09345…` 仍原样保留）。
      **服务端实测**：新世界正常跑起来 —— `Done (8.183s)!`（修复前是崩在区块生成、客户端卡 0%）。"""


def main():
    t = io.open(ARCH, "r", encoding="utf-8").read()
    n = t.count(OLD)
    if n != 1:
        print(u"锚点命中 %d 次 ⇒ 不写" % n)
        return 1
    io.open(ARCH, "w", encoding="utf-8", newline=u"\n").write(t.replace(OLD, NEW, 1))
    print(u"档案 §9 已记入新成品哈希与实测结果")
    return 0


if __name__ == "__main__":
    sys.exit(main())
