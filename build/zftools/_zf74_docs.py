# -*- coding: utf-8 -*-
u"""_zf74_docs.py —— ZF74（流体挂 c: 通用标签）的六处编辑，每处断言「正好命中 1 次」

① 档案 §5 追加 ZF74 行；② 档案 §6 新增 §6.19「加流体要挂哪些通用标签」；
③ 档案 §9 追加 ZF74 待办；④ 规划文档 §3.1 把「本轮不加标签」改写成已挂（含两路取证）；
⑤ 英文公告补一句流体标签；⑥ `_zf72_verify.py` 的 C10 标签改名（条件仍成立，避免误导）。
"""
import hashlib
import io
import sys

ARCH = r"E:\PotatoST\docs\开发档案.md"
PLAN = r"E:\PotatoST\docs\v0.11规划.md"
ANN = r"E:\PotatoST\docs\UpdateAnnouncement_EN.md"
Z72 = r"E:\PotatoST\build\zftools\_zf72_verify.py"

A_S6 = u"## 7. 权威情报来源（怎么查原版行为，别靠记忆）"
A_ROW = u"| 见 §4.44 / §4.45 / §6.18 / §9 / §10 |"
A_S9 = u"      并把 `_zf69_repro.py` 改成**响的**。"
A_PLAN = (u"* 跨 mod 标签：**本轮不加**。已核 NeoForge 21.1.235 的 `Tags.java`，**没有**原油类通用 `c:` 标签；\n"
          u"  以后真有别的 mod 要互通，再补 `data/c/tags/fluid/crude_oil.json`。")
A_ANN = u"Oil can also be **pumped** with the Fluid Pump"
A_C10 = u'check(u"C10 文档：明确说不加 c: 标签（因为上游没有）",'

NEW_PLAN = u"""* 跨 mod 标签（**2026-09-24 ZF74 更新：从"不加"改成"挂上"**）—— 两路取证推翻了原计划：
  ① 上游 NeoForge 21.1.235 的 `Tags.java` 里**没有**原油类通用 `c:` 标签，**但有** `Tags.Fluids.GASEOUS`
     （上游 `data/c/tags/fluid/gaseous.json` 现在只挂了个 legacy 别名 `#forge:gaseous`，
     等于"等各 mod 自己挂进来"）；
  ② 现实约定：机械动力·柴油动力（`createdieselgenerators`）自带 `data/c/tags/fluid/crude_oil.json`
     ⇒ "原油"的通用名就是 **`c:crude_oil`**。
  ⇒ 本模组现在挂 5 份：`c:gaseous`（氧/氢/氯，源+流动）、`c:crude_oil`（原油，源+流动），
  外加 `c:oxygen` / `c:hydrogen` / `c:chlorine`（上游没有，但按 `c:` 命名约定补上，
  别人写 `#c:oxygen` 就能对上）。**以后每加一种流体，一律先挂 `c:` 标签**（见档案 §6.19）。"""

NEW_ANN = u"""Crude oil and the three process gases carry the common `c:` fluid tags
(`c:crude_oil`, `c:gaseous`, plus `c:oxygen` / `c:hydrogen` / `c:chlorine`), so other mods'
recipes and machines can accept them — and this mod accepts anyone else's gas as a gas.

Oil can also be **pumped** with the Fluid Pump"""

ROW_ZF74 = u"""| ZF74 | **新建 `zf74_pre`**（8 个改前件：`ModFluids.java` + 3 份文档 + `_zf72_verify.py` + `_zf72_vanilla_evidence.py` + 旧成品 jar 与 `.sha1`；逐份核哈希、失败 0） | 0.11：**给流体挂通用标签**（用户问：「以前的流体（氧气 氯气 氢气）可以和别的mod配方通用吗 可以的话以后的流体也通用 不行的话看看能不能加个标签」）。① **先取证**（`_zf74_tagprobe.py`，只读）：本工程 `data/**/tags/fluid/` **一个都没有**（60 个标签文件里 0 个流体标签）⇒ 现状是**完全不通用**；上游 NeoForge 21.1.235 声明了 `Tags.Fluids.GASEOUS`（`c:gaseous`），其 json 目前只有 legacy 别名 `#forge:gaseous`；本机 mod 扫描抓到 **机械动力·柴油动力** 自带 `data/c/tags/fluid/crude_oil.json`（`createdieselgenerators:crude_oil`）⇒ 原油的通用名就是 `c:crude_oil`；② **挂上 5 份标签**（全部 `replace:false`，源+流动都挂，照上游 `c:water` 的写法）：`c:gaseous`（氧/氢/氯）、`c:crude_oil`（原油）、`c:oxygen`、`c:hydrogen`、`c:chlorine`；③ **判定也改成认标签**：`ModFluids.isGas` 先认自家 3 种（写死一遍 ⇒ 标签没加载时也认得出），再认 `#c:gaseous` ⇒ **别的 mod 的氧气也能灌进高压气罐、油桶也照样拒收它**（双向通用，不只是我们挂出去）；④ **同版本重打包**：`release\\PotatoST-0.11.jar` 重新发布 ⇒ **前一个 SHA1 `2a35a9eeda99…` 作废**（新 SHA1 见 §9）；⑤ 规划文档 §3.1 与公告同步更新" | 见 §6.19 / §9 |"""

SEC_619 = r"""### 6.19 加一种**流体**要挂哪些通用标签（0.11 ZF74 立的规矩）

用户口径：**流体要能和别的 mod 配方通用，以后的流体也通用**。落地规矩：

| 挂哪 | 文件 | 内容 |
|---|---|---|
| 气体通用名 | `data/c/tags/fluid/gaseous.json` | 源 + 流动都进（NeoForge 上游 `Tags.Fluids.GASEOUS`，默认无条目，等各 mod 自己挂） |
| 每种流体自己的名字 | `data/c/tags/fluid/<fluid>.json` | 例：`oxygen.json` / `hydrogen.json` / `chlorine.json` / `crude_oil.json`，同样源+流动 |
| 一律 | 全部 `"replace": false` | 否则会把别人挂的条目**整张覆盖掉**（这是跨 mod 兼容最常见的自伤） |

两条要点：
1. **只挂 `c:`（通用）命名空间**，不要发明 `potato_s_t:` 的对外标签 —— 别人不会去查我们的命名空间；
2. **判定也要认标签**：`ModFluids.isGas` 除了写死自家 3 种（保证数据包没加载时也能判），还要认 `#c:gaseous`。
   否则"我们把气体挂出去了、别人的气体却进不了我们的机器"，只通了半边。

取证脚本：`build\zftools\_zf74_tagprobe.py`（只读：本工程 / 上游 jar / 本机别的 mod 三路对照）。

"""

SEC_S9 = u"""- [ ] **ZF74：流体现在挂上通用标签了**（成品 `release\\PotatoST-0.11.jar`，**同版本重打包 ⇒ `2a35a9ee…` 作废**）。
      挂的是 `c:gaseous`（氧/氢/氯）、`c:crude_oil`（原油）、`c:oxygen`/`c:hydrogen`/`c:chlorine`（源+流动都挂，
      `replace:false`）。**效果**：别的 mod 配方里写 `#c:crude_oil` 或 `#c:oxygen` 就能用我们的流体；
      反过来，**别人挂进 `#c:gaseous` 的气体在我们这儿也算气体**（能灌进高压气罐、油桶拒收）。
      要验的话：跟柴油动力（`createdieselgenerators`）一起装，看它的 `#c:crude_oil` 配方认不认我们的原油。
"""


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def patch(path, pairs, label):
    text = io.open(path, "r", encoding="utf-8").read()
    for old, new, what in pairs:
        n = text.count(old)
        if n != 1:
            print(u"  !! %s / %s：命中 %d 次（必须 1）⇒ 该文件不写" % (label, what, n))
            return False
        text = text.replace(old, new, 1)
        print(u"  [OK] %s / %s" % (label, what))
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
    return True


def main():
    ok = True
    ok &= patch(ARCH, [
        (A_S6, SEC_619 + A_S6, u"§6.19"),
        (A_ROW, A_ROW + u"\n" + ROW_ZF74, u"§5 ZF74 行"),
        (A_S9, A_S9 + u"\n" + SEC_S9.rstrip(u"\n"), u"§9 ZF74 待办"),
    ], u"开发档案")
    ok &= patch(PLAN, [(A_PLAN, NEW_PLAN, u"§3.1 标签口径更新")], u"v0.11规划")
    ok &= patch(ANN, [(A_ANN, NEW_ANN, u"公告补标签一句")], u"公告")
    ok &= patch(Z72, [(A_C10, u'check(u"C10 文档：上游没有「原油类」c: 标签这条事实仍在（ZF74 起我们按 c:crude_oil 约定挂上了）",',
                       u"C10 标签改名")], u"_zf72_verify")
    print(u"\n六处编辑全部命中 1 次" if ok else u"\n有锚点没命中，见上")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
