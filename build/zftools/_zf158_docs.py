# -*- coding: utf-8 -*-
u"""_zf158_docs.py —— ZF158 文档落地（幂等，默认 dry-run）：

  ① 档案 **§4.166**：生成器表是那 35 份 JSON 的**唯一来源** —— 只改盘上的 JSON、不改表，
     下一次 `--write` 就把改动 revert 掉（本轮实测两笔：ZF156 的板→标签、ZF155 的模板）；
  ② 档案 **§5** 加 ZF158 行（接在 ZF156 之后）；
  ③ 档案 **§9** 加 ZF158 小段（**待用户实测**）；
  ④ 交接 **§6** 加第 33 条；
  ⑤ 英文公告末尾加一条（§4.150 日志纪律）。

跑法：python build\\zftools\\_zf158_docs.py [--write]
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

notes, fails = [], []


D4_TITLE = u"### 4.166 【工具雷】配方生成器表是那 35 份 JSON 的**唯一来源** —— 只改盘上的 JSON，下一跑就白改（0.13 ZF158）"
D4 = D4_TITLE + u"""

用户这轮的话很短：「**热力金属改成铜板夹银锭（铜板银锭互相调换一下位置）**」。
照规矩改配方要动 `build\\zftools\\_zf45_recipes.py`（那支脚本自称是这 35 份 JSON 的**唯一来源**：
改图纸改表，再 `--write` 让它重出 JSON），顺手把两笔**旧账**一起跟平 —— 结果发现它们都是同一个病：

**① ZF156 的账：表里 13 行 15 处还写着「自家板当物品」。**
上一轮把盘上 29 处原料换成 `#c:plates/<金属>`（为了跨 mod），**表没动**。
于是表与盘不一致；谁哪天跑一次 `--write`，那 29 处就被悄悄换回物品。

**② ZF155 的账：表的 `SMITHING_TEMPLATE` 还写着下界合金升级模板。**
上一轮把 4 件振金护甲的模板换成了通用升级模板，同样**只改了盘**。
本轮实测出血：`--write` 一跑，**4 份文件当场被改回下界合金**（因为表说该那样）。
（发现方式就是本轮设计的那一步"重出之后看哪些文件变了"——不是靠人眼比对。）

**③ 跟平之后，"重出"必须一份不动。**
本轮的做法：先把表改成与盘一致，再跑 `--write`，然后拿整份改动与改前备份对账 ——
**只该有 `thermal_metal.json` 一份不同**（那正是用户点名要改的）。
跑出来就是 1 份，这条同时是"表 == 盘"的机器证明。
常驻门 `_zf158_verify.py` 的 B5 把它固化了：把生成器复制一份、只把输出目录改到临时夹再跑一遍，
产物必须与盘上**逐字节相同**（跑完删临时夹）。

**④ 附带发现（不是本轮的账，记在这儿给后面的人）**：
  · 表里管着的 8 份"粒/锭"配方（`*_nugget.json` / `*_ingot_from_nuggets.json`）在盘上但**没进 git**
    （ZF150 那条线的在途产物）；本轮 `--write` 重出后与盘上逐字节相同，等于顺带证明它们没漂。
  · 生成器的文档写着 `--check`，但 argparse 里**没有**这个开关 —— 只校验就是**不带参数**跑。
    （本轮的常驻门第一版照着文档写了 `--check`，rc=2 当场被自己的门抓住。）
"""

D5_ROW = (u"| ZF158 | **新建 `zf158_pre`**（**105 份**：`_zf45_recipes.py`（生成器表）/ **整个 "
          u"`data\\potato_s_t\\recipe\\` 目录**（因为要用生成器 `--write` 重出，必须能证明「除了热力金属谁都没动」）/ "
          u"三份文档 / 常驻门与打包脚本 / 成品 0.13 + `.sha1` + `build\\libs` 那份；逐份核 sha1 + 回读，失败 0。"
          u"⚠ 开工前查过轮号：**ZF157 已被另一条线占用**（`_zf157_*` 十几个文件）⇒ 本轮用 **ZF158**；"
          u"救援目录里没有 `zf158_pre`（§4.147））"
          u" | **0.13：热力金属换成「铜板夹银锭」**（用户原话「热力金属改成铜板夹银锭（铜板银锭互相调换一下位置）」）。"
          u"① 图纸由 `SSS/CCC/SSS`（银在外）换成 `CCC/SSS/CCC`（**铜在外**）= 铜板 ×6 + 银锭 ×3 → 热力金属 ×1；"
          u"两个 key **一个字没改**（`C` 仍是 `#c:plates/copper`、`S` 仍是 `#c:ingots/silver`）⇒ 上一轮的跨 mod 兼容不倒退。"
          u"② 照规矩**改表再 `--write`**（`_zf45_recipes.py` 是那 35 份 JSON 的唯一来源），"
          u"顺手跟平两笔旧账：表里 **13 行 15 处「自家板当物品」→ `#c:plates/<金属>`**（ZF156 只改了盘）、"
          u"`SMITHING_TEMPLATE` **下界合金模板 → 通用升级模板**（ZF155 只改了盘）。"
          u"⚠ 跟平前先实测到出血：跑一次 `--write` 把 ZF155 的 4 份振金护甲模板**当场 revert** 了（已还原）。"
          u"③ 验收：跟平后 `--write` 重出，**除 `thermal_metal.json` 一份不动**（= 表与盘的机器证明）；"
          u"`_zf45_recipes.py` 校验模式 47 条 0 失败；常驻 `_zf158_verify.py`（A 图纸 7 项 / B 表 5 项 / C 旁证 2 项 / "
          u"D 文档与成品）**全绿**，其中 B5 是「把生成器复制到临时夹重出一遍、与盘逐字节相同」。（详见 §4.166）"
          u" | 见 §9 ｜ 见 §4.166 |\n")

D9_ANCHOR = u"## 10. 备份策略"
D9 = u"""### ZF158（0.13）热力金属换成**铜板夹银锭** —— **待你实测**

用户原话：「**热力金属改成铜板夹银锭（铜板银锭互相调换一下位置）**」。

| 改前 | 改后（现在） |
|---|---|
| 银锭 ×3 / 铜板 ×3 / 银锭 ×3 | **铜板 ×3 / 银锭 ×3 / 铜板 ×3** |

也就是 3×3 里：**上下两行各 3 块铜板（共 6 块）、中间一行 3 个银锭** → 出 1 个热力金属。
铜板那格认的是 `#c:plates/copper` 标签 ⇒ **沉浸工程/机械动力的铜板一样能用**（上一轮的跨 mod 兼容照旧）。
配方份数不变（仍 91 份），语言键数不变。

⚠ 顺带说明：这一轮把**配方生成器表**（那 35 份 JSON 的唯一来源）跟平了两笔旧账 ——
上一轮（ZF156）改的板子标签、和上上轮（ZF155）改的振金护甲模板，都**只改了盘上的 JSON**；
不跟平的话，谁哪天跑一次生成器 `--write` 就会把它们悄悄改回去。跟平后重出一遍：**除热力金属一份不动**。

---

"""

H6_ANCHOR = u"    ④ 谁要拿 ZF155 的探针源码复核那轮结论，**以报告 `_zf155_probe_utf8.txt` 为准**（28 项全绿那份）。"
H6_NEW = H6_ANCHOR + u"""

33. **ZF158 的账（0.13：热力金属换图纸 + 生成器表跟平）**：① 用户原话与形状见档案 §9；
    `thermal_metal.json` 由 `SSS/CCC/SSS` 换成 `CCC/SSS/CCC`（铜在外），两个 key 一字未改。② ⚠ **本轮真正的坑**：
    `build\\zftools\\_zf45_recipes.py`（那 35 份 JSON 的唯一来源）与盘**早就漂了**两笔 ——
    ZF156 的 29 处 `#c:plates/*`、ZF155 的 `SMITHING_TEMPLATE` 都只改了盘。跟平前实测到出血：
    跑一次 `--write` 把 4 份振金护甲模板当场 revert（已还原）。③ 跟平后的验收口径：
    `--write` 重出**只该动 `thermal_metal.json` 一份**（拿改前备份整目录对账），
    常驻门 `_zf158_verify.py` B5 把这条固化（复制生成器 → 改输出目录到临时夹 → 重出 → 逐字节比）。
    ④ 附带发现：表里管的 8 份"粒/锭"配方在盘上但**没进 git**（ZF150 那条线的在途产物，本轮没动它们，
    只是重出后与盘逐字节相同）；生成器的文档写 `--check` 但 argparse 里没有这个开关，"只校验"= 不带参数跑。
    ⑤ 重打成品：`release\\PotatoST-0.13.jar` 哈希/体积随重打走（§4.159 三处联动）。"""

ANN_ADD = u"""
## New in 0.13 ZF158 - Thermal Metal recipe flipped

- **Thermal Metal is now "copper plates around a silver core".** The 3x3 recipe used to be
  Silver / Copper / Silver; it is now **Copper Plates / Silver Ingots / Copper Plates** -
  six copper plates on the top and bottom rows, three silver ingots in the middle, still
  producing one Thermal Metal.
- Both slots still use the common tags (`c:plates/copper` and `c:ingots/silver`), so Immersive
  Engineering plates or Create sheets keep working in the recipe.
- Under the hood the recipe generator table was brought back in sync with the shipped JSON files
  (an earlier round had changed the files without updating the table, so re-running the generator
  would have silently reverted those changes). Re-running the generator now changes nothing but
  this one recipe.
"""


def main(argv):
    write = u"--write" in argv
    doc = io.open(DOC, encoding="utf-8", newline=u"").read()
    nums = [int(m.group(1)) for m in re.finditer(u"(?m)^#{3,4} 4\\.([0-9]+) ", doc)]
    mx = max(nums)
    already = D4_TITLE in doc
    print(u"档案 §4 最大编号 = %d（目标 §4.166；已写入 = %s）" % (mx, already))
    if not already and mx != 165:
        fails.append(u"§4 编号不是 166（实测 max=%d）—— 停手先看清" % mx)

    # ① §4.166：插在 §5 表头那一行之前
    anchor4 = u"| ZF147 | \u26a0 **没有备份根也要有账**"
    if D4_TITLE in doc:
        notes.append(u"  [跳过] §4.166（已经在，幂等）")
    elif doc.count(anchor4) == 1:
        doc = doc.replace(anchor4, D4 + u"\n\n" + anchor4, 1)
        notes.append(u"  [改] §4.166")
    else:
        fails.append(u"§4.166 插入锚点命中 %d 次" % doc.count(anchor4))

    # ② §9 小节
    if u"### ZF158（0.13）" in doc:
        notes.append(u"  [跳过] §9 ZF158 小节（已经在，幂等）")
    elif doc.count(D9_ANCHOR) == 1:
        doc = doc.replace(D9_ANCHOR, D9 + D9_ANCHOR, 1)
        notes.append(u"  [改] §9 ZF158 小节")
    else:
        fails.append(u"§9 锚点命中 %d 次" % doc.count(D9_ANCHOR))

    # ③ §5 行（接在 ZF156 之后）
    if u"| ZF158 |" in doc:
        notes.append(u"  [跳过] §5 ZF158 行（已经在，幂等）")
    else:
        anchor5 = u"| 见 §9 ｜ 见 §4.164 |\n"
        if doc.count(anchor5) != 1:
            fails.append(u"§5 的 ZF156 行尾锚点命中 %d 次" % doc.count(anchor5))
        else:
            doc = doc.replace(anchor5, anchor5 + D5_ROW, 1)
            notes.append(u"  [改] §5 ZF158 行")
    if write:
        io.open(DOC, u"w", encoding="utf-8", newline=u"").write(doc)
    else:
        notes.append(u"  （没加 --write：档案只算不写）")

    # ④ 交接 §6
    hand = io.open(HAND, encoding="utf-8", newline=u"").read()
    if u"33. **ZF158 的账" in hand:
        notes.append(u"  [跳过] 交接 §6 第 33 条（已经在，幂等）")
    elif hand.count(H6_ANCHOR) == 1:
        if write:
            io.open(HAND, u"w", encoding="utf-8", newline=u"").write(hand.replace(H6_ANCHOR, H6_NEW, 1))
        notes.append(u"  [改] 交接 §6 第 33 条")
    else:
        fails.append(u"交接 §6 锚点命中 %d 次" % hand.count(H6_ANCHOR))

    # ⑤ 公告
    ann = io.open(ANN, encoding="utf-8", newline=u"").read()
    if u"## New in 0.13 ZF158" in ann:
        notes.append(u"  [跳过] 公告 ZF158（已经在，幂等）")
    else:
        if write:
            io.open(ANN, u"w", encoding="utf-8", newline=u"").write(ann.rstrip(u"\n") + u"\n" + ANN_ADD)
        notes.append(u"  [改] 公告 ZF158")

    print(u"\n".join(notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    if not write:
        print(u"（没加 --write 时：档案已经写了，交接/公告只在上面报告里 —— 直接带 --write 跑）")
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
