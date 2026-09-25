# -*- coding: utf-8 -*-
u"""_zf78_manifest.py —— 给 `C:\\PotatoST救援\\zf78_pre` 写 MANIFEST.md + _sha1.txt（含实测哈希）"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BK = r"C:\PotatoST救援\zf78_pre"

MOD = ["ModFluids.java", "ModItems.java", "ModBlocks.java", "ModMenus.java", "PotatoST.java",
       "PotatoSTClient.java", os.path.join("client", "gui", "parts", "EnergyBarPart.java"),
       os.path.join("client", "gui", "parts", "FluidTankPart.java")]
NEWJ = ["DistillationTowerStructure.java", "DistillationControllerBlock.java",
        "DistillationControllerBlockEntity.java", "DistillationOperatorBlock.java",
        "DistillationOperatorBlockEntity.java", "DistillationOperatorMenu.java",
        os.path.join("client", "DistillationOperatorScreen.java")]

TEXT = u"""# zf78_pre —— ZF78（0.11 分馏塔三件套）改前件

## ⚠ 先说清楚：本轮的改前件**不是动手前抄的**（我的失误，如实记录）

§10 的规矩是「动第一个字节之前先抄一份并核哈希」。ZF78 我**漏做了这一步**：
改完 8 个 java 之后才发现没有 `zf78_pre`。补救办法照 **ZF65 那条先例**（那轮也是忘抄）：

1. 把这轮的每一次编辑**反向套用**回当前文件（`build/zftools/_zf78_prebackup.py`，
   每条反向替换都断言**正好命中 1 次**，不中就不写）；
2. **证明"重建"不是"猜"**：把这 8 份重建件换回源码树、删掉本轮新增的 8 个 java，
   编译通过后与 **ZF77 成品 jar**（`release\\PotatoST-0.11.jar` = `27787d5e…`，
   本轮尚未重打包）里的同名 class **逐字节比对** ——
   `build/zftools/_zf78_precheck.py` 实测：**8 个类 / 31 个 class 全部相同、0 不同、0 缺失**；
3. 反证：重建件第一版把 `ModBlocks` 的整段 ZF78 只删了标题行 ⇒ **编译当场报
   「找不到符号 DistillationControllerBlockEntity」** —— 说明"错的重建活不过编译"，
   这条证明不是走过场。

## 诚实边界（这几条别当没发生）

- **注释不参与字节码**：逐字节相同只能证明「逻辑与当时一致」，
  改前件里的注释措辞可能与我当时的原文有差异（正文代码、常量、结构完全一致）。
- `新增文件\\` 里是本轮**改后**的 16 份 java（**事后**抄的，用于防丢），
  不是"改前"；改前件在**根目录**的 `src\\main\\java\\com\\potatost\\mod\\` 下。
- **文档的改前件 = 当前 `docs/开发档案.md`**：本轮在补建备份之前**一个字节都没动文档**
  （所有文档改动都发生在备份建好之后）⇒ 不需要重建。
- 旧成品 jar（ZF77 = `27787d5e…`）另存一份在 `新增文件\\release\\`，作为逐字节比对的参照物留档。

## 目录

| 位置 | 内容 |
|---|---|
| `src\\main\\java\\com\\potatost\\mod\\…` | **8 份重建的改前件**（重组后与 ZF77 jar 逐字节同） |
| `新增文件\\src\\…` | 本轮**改后**的 16 份 java（8 改 + 8 新，防丢） |
| `新增文件\\release\\` | 参照用的 ZF77 成品 jar 与 `.sha1` |
| `MANIFEST.md` / `_sha1.txt` | 本文件与全量哈希清单 |

## 本轮改了哪 8 个 java（即这 8 份改前件对应的文件）

| 文件 | 本轮改动 |
|---|---|
| `ModFluids.java` | +4 种分馏产物流体（柴油/石脑油/汽油/液化石油气）+ 共用的 `liquidType` 工厂 |
| `ModItems.java` | +沥青物品 `bitumen`（火药占位贴图）+ 创造页 3 行 |
| `ModBlocks.java` | +分馏塔控制器 / 操作器两个方块 + 两个方块实体类型 |
| `ModMenus.java` | +分馏塔操作器菜单 |
| `PotatoST.java` | +操作器 3 条能力（能量/流体/物品）；控制器**故意不给能力** |
| `PotatoSTClient.java` | +操作器界面登记 |
| `client/gui/parts/EnergyBarPart.java` | 上限改成 `IntSupplier`（容量随塔数变）+ 重载 |
| `client/gui/parts/FluidTankPart.java` | 容量改成 `IntSupplier` + 重载 |
"""


def sha1(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


def walk():
    rows = []
    for base, _dirs, files in os.walk(BK):
        for f in sorted(files):
            p = os.path.join(base, f)
            rel = os.path.relpath(p, BK)
            rows.append((rel.replace("\\", "/"), os.path.getsize(p), sha1(p)))
    return sorted(rows)


def main():
    io.open(os.path.join(BK, "MANIFEST.md"), "w", encoding="utf-8", newline=u"\n").write(TEXT)
    rows = walk()
    out = [u"# zf78_pre 全量哈希（SHA1）—— 实测生成，%d 个文件" % len(rows), u""]
    for rel, size, h in rows:
        out.append(u"%s  %10d  %s" % (h, size, rel))
    io.open(os.path.join(BK, "_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(out) + u"\n")
    print(u"MANIFEST.md 与 _sha1.txt 已写：%d 个文件" % len(rows))
    # 顺带把"改前件 8 份"逐个点名（防止 MANIFEST 里说的和磁盘上的不一致）
    for name in MOD:
        p = os.path.join(BK, "src", "main", "java", "com", "potatost", "mod", name)
        print(u"  %-46s %s" % (name, u"在" if os.path.exists(p) else u"**缺**"))
    for name in NEWJ:
        p = os.path.join(BK, u"新增文件", "src", "main", "java", "com", "potatost", "mod", name)
        print(u"  [改后] %-39s %s" % (name, u"在" if os.path.exists(p) else u"**缺**"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
