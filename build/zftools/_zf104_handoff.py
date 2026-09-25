# -*- coding: utf-8 -*-
r"""_zf104_handoff.py —— 往 ZF104 条目追加「并发改动处置 + 交付状态」一节

为什么要有这一节：本轮跑门的**后半段**发现另一条并行任务正在同一棵源码树上
加东西（硬质钛合金 + 稳定金属块配方 + 1 个语言键），把往轮脚本里写死的
"活体数字"锚点全撞歪了。这些失败**不是本轮盔甲的缺陷**，但必须写清楚，
否则下一个人会以为是盔甲写坏了。
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"

ANCHOR = u"**作废上一版 `90510e1890af79242cb41e0cda0a2f6472b12cdf`**（ZF103，中文润色那版）；0.10 成品 `84d09345…` 原样保留。\n"

NEW = r"""**作废上一版 `90510e1890af79242cb41e0cda0a2f6472b12cdf`**（ZF103，中文润色那版）；0.10 成品 `84d09345…` 原样保留。

**⚠ 本轮后半段：另一条并行任务在同一棵源码树上改东西 —— 三个事故与处置（如实记录）**

跑门跑到一半，发现文件在我眼皮底下变。取证到的**并行**改动（时间戳 18:50~18:56）：

| 并行改动 | 撞到我的什么 | 处置 |
|---|---|---|
| `ModArmorItems.java` 里星璨钢胸甲的护甲值被改成 **`9.0`** | 与用户原话「胸甲 护甲值**+9.5**」、与我写在同文件上一行的 javadoc `+9.5`、与四语言的 tooltip 全部矛盾 | 本轮探针**当场抓到**（`star_steel_chestplate 护甲值 9.5 编进了 class` + javap 指令流两条）。已改回 **9.5** 并重编、重验（168 条断言全过） |
| 四语言各 +1 键（`item.potato_s_t.hard_titanium_alloy`）⇒ 335 → **350** | 往轮 17 份 `_zf*_verify.py` 里写死的 `335` / `349` 锚点全部挂掉 | 三次 retarget 跟到位（`_zf104_retarget{,3,4}.py`），**只改数字不放宽断言**（§4.36） |
| 新增 `data/potato_s_t/recipe/stable_metal_block.json` ⇒ 定形配方 42 → **43** | 6 份 `EXPECT_SHAPED = 42` + `_zf71` / `_zf100_recipe_guard` 的内联断言 | 已跟到 43（`_zf104_retarget4.py`） |

⇒ **一件真事故**：`_zf103_falsify.py` 跑到 K2 还原时抛
`FileNotFoundError: [WinError 3]`（它那份 `_zf103_falsify_bak` 备份目录被并行的流程清掉/挪走），
整个脚本带 traceback 退出、后面 6 刀**全没跑**。**加固**：备份目录名带**进程号**
（两条线各用各的）、还原前先确认副本还在、缺了就大声报 FAIL（不许静默）。加固后 8 刀连跑两次全过。

**交付状态（截至本轮结束）**

- ✅ **本轮盔甲这条线本身是绿且自洽的**：`compileJava` 成功；
  `_zf103_verify.py` **168 条断言全过**；`_zf103_falsify.py` **8 刀全被抓到**；
  `Audit.ps1` / `ToolLint.py` / `LangCheck` / `RecipeCheck` / `ModelCheck` /
  `TextureCheck` / `print(JsonCheck)` 全部**失败项 0**；`runClient` 到主菜单无 ERROR。
- ⏸ **本轮没有打包发布** —— 理由不是盔甲有问题，而是：
  ① 并行的另一条任务还在往这棵树上加东西（它的探针自己都写着"源码树里有并行任务的在途改动，
     门会被它的键数改动挂掉、等两边都停下来再一次性对账"）；
  ② 全门里剩下的 FAIL **全是"往轮脚本锚在旧状态"**这一类（例如 `_zf70/_zf71/_zf72/_zf73`
  的公告文案与成品 jar 对照：它们要求"英文公告已改成 5 models still do this"，
  而本轮盔甲把那个数从 5 提到 13；还有 `c:ingots` 之外的多处清单要补
  `stable_metal_block.json`），**没有一条是本轮盔甲的缺陷**；
  ③ 带着一堆"我知道为什么红"的门硬发布，等于把"门绿"这件事贬值。
- 🔜 **下一步（等并行任务停下来做一次总对账）**：把所有"活体数字"锚点一次跟到位
  （键数 350 / 定形配方 43 / 借原版贴图 13 → 公告同步），再跑一次全门 → **打包发布**。
  发布脚本 `_zf104_publish.py` 已经写好（先查后拷 + 12 条断言），VOID 仍指着 ZF103 那版。
"""


def main():
    text = io.open(DOC, encoding="utf-8").read()
    hits = text.count(ANCHOR)
    if hits != 1:
        print(u"!! 锚点命中 %d 次（应为 1）" % hits)
        return 1
    io.open(DOC, "w", encoding="utf-8", newline=u"\n").write(text.replace(ANCHOR, NEW, 1))
    print(u"已追加「并发改动处置 + 交付状态」一节（%d → %d 字节）" % (len(text), len(text) + len(NEW) - len(ANCHOR)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
