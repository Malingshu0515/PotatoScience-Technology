# -*- coding: utf-8 -*-
u"""_zf81_docs.py —— ZF81 文档：档案 §5 ZF81 行 + §9 验收（含"缓冲只剩 20 tick"这条待拍板）

`__NEWSHA__` / `__NEWSIZE__` / `__NEWENTRIES__` 由 `_zf81_publish.py` 打包后填真值。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOCS = os.path.join(ROOT, "docs")
fails = []


def read(p):
    if not os.path.exists(p):
        fails.append(u"缺文件：%s" % p)
        return u""
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)


ROW = (u"| ZF81 | **新建 `zf81_pre`**（17 份改前件：`ElectrolyzerBlockEntity` / `MachineRecipes` / "
       u"4 份 lang / 6 个往轮校验脚本 / `_zf78_falsify.py` / 2 份文档 / 旧成品 jar 与 `.sha1`；"
       u"逐份核哈希、失败 0。⚠ **`PotatoST.java` 漏抄了**（探针挂钩改的就是它），"
       u"事后按 ZF33 先例补记并证明「与 `zf80_pre` 那份逐字节相同」，见 `zf81_pre\\_说明.txt`） | "
       u"0.11：**电解器能耗 100 → 1000 FE/t**（用户原话："
       u"「**电解器还是改成 1000Fe/t 吧**」）。① **两个常量一起抬**"
       u"（纯水制氧 `ENERGY_PER_TICK_OXYGEN`、盐水制氯 `ENERGY_PER_TICK_CHLORINE`，本来都是 100），"
       u"**水/产物速度、海盐消耗、三个罐容量、缓冲一个没动**。② 探针 `ElectrolyzerCheck` 在真服务端上 "
       u"**27 项全 [OK]**：999 FE 一点不动、凑够 1000 FE 才走一 tick（水 −10 / 氧 +3 / 氢 +6 / "
       u"电正好扣光）、连跑 10 tick（−100 水 / +30 氧 / +60 氢）、盐水模式同样 1000 FE 一 tick、"
       u"累计 500 mB 水吃 1 个海盐、海盐没了自动回纯水模式。③ **顺带核了 ZF38 那条坑**："
       u"缓冲 20000 FE ≥ 单 tick 电费 1000 FE ⇒ 不会像当年那台泵一样「永久待机」；"
       u"**但缓冲只够 20 tick**（100 FE/t 时代是 200 tick）——要不要跟着抬**等你拍板，本轮没动**。"
       u"④ **活体数字一次改全**（上一轮 ZF80 就是漏了这个、白跑一整遍门）：四份 lang tooltip、"
       u"英文公告、`_zf71_verify.py` 的两条期望、`MachineRecipes` 的 JEI 说明注释，"
       u"全部 100 FE → 1000 FE；JEI 显示的是**引用常量**所以自动跟。"
       u"⑤ 新增常驻校验 `_zf81_verify.py` + 两把反证刀（能耗常量、tooltip 字面量）。 |\n")

VERIFY = u"""
### ZF81（0.11）电解器 1000 FE/t —— 待你实测

- [ ] 电解器（**不**放海盐）接电 ⇒ JEI 与 tooltip 都写 **1000 FE/t**；电跟得上时每 tick 走一格
      （水 −10 mB、氧 +3、氢 +6）
- [ ] 只给得起几百 FE/t ⇒ 表现应是「一充一停、走得极慢」，**不是坏了**（这是新能耗的正常表现）
- [ ] 电解质槽放**海盐** ⇒ 同样是 1000 FE/t，产 3 氯 + 6 氢，每 500 mB 水吃 1 个海盐
- [ ] ⚠ **一个待你拍板的数**：缓冲现在还是 **20000 FE**，满载只顶 **20 tick**
      （100 FE/t 时代是 200 tick）。若想"照旧顶 200 tick"就是 **200000 FE**（改一行）。
      本轮**没动**它 —— 你说抬我就抬
- [ ] 参考：本模组**低级发电机 100 FE/t** ⇒ 电解器满载要 **10 台**（或用更高档电源）

**成品**：`release\\PotatoST-0.11.jar` = `__NEWSHA__`（__NEWSIZE__ B / __NEWENTRIES__ 条目），
**作废上一版 `c43c3468224b5b114a8943a76bf8adb5f89c9d35`**（ZF80）；0.10 成品 `84d09345…` 原样保留。
"""


def insert_after(text, anchor, block, label):
    u"""在 anchor 那一行之后插入 block；**锚点必须恰好命中 1 次**（§4.36 硬规矩）。"""
    if text.count(anchor) != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, text.count(anchor)))
        return text
    at = text.find(anchor)
    eol = text.find(u"\n", at)
    return text[:eol + 1] + block + text[eol + 1:]


def main():
    arch_p = os.path.join(DOCS, u"开发档案.md")
    arch = read(arch_p)
    if u"| ZF81 |" not in arch:
        arch = insert_after(arch, u"| ZF80 | **新建 `zf80_pre`**", ROW, u"档案 §5：ZF81 行")
    if u"### ZF81（0.11）电解器 1000 FE/t" not in arch:
        if arch.count(u"\n## 10. 备份策略") != 1:
            fails.append(u"档案 §9：锚点命中 %d 次（必须 1 次）" % arch.count(u"\n## 10. 备份策略"))
        else:
            arch = arch.replace(u"\n## 10. 备份策略", u"\n" + VERIFY + u"\n## 10. 备份策略", 1)
    write(arch_p, arch)
    print(u"档案改完，失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
