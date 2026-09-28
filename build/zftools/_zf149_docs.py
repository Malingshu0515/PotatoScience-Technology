# -*- coding: utf-8 -*-
u"""_zf149_docs.py —— ZF149 打包轮文档落地（幂等，默认 dry-run）。

  ① 档案 **§4.159**：成品哈希/键数在**三处**写死（文档 / 公告 / 门），重打必须一起改；
  ② 档案 **§5** 加 ZF149 行；
  ③ 档案 **§9** 加 ZF149 小节；
  ④ 交接 **§1** 成品行跟到新哈希；**§6** 第 29 条标注 (a) 已做；
  ⑤ 英文公告 **Download** 段三个数（508/73/357）跟到 **579/74/358** + 换新哈希，末尾加一条。

跑法：python build\\zftools\\_zf149_docs.py [--write]
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", "开发档案.md")
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

NEW_SHA = u"59894a9efb7ba45cc811a558f1fea4a8dac56863"
NEW_SIZE = u"5,812,286"
OLD_SHA = u"45c061dfc9c171aeea783b64c05ca0e3d884871b"
OLD_SIZE = u"5,769,926"

notes, fails, plan = [], [], []


def want(text, old, new, label):
    if new in text:
        notes.append(u"  [跳过] %s（已经在，幂等）" % label)
        return text
    if text.count(old) != 1:
        fails.append(u"%s：锚点命中 %d 次（应为 1）" % (label, text.count(old)))
        return text
    notes.append(u"  [改] %s" % label)
    return text.replace(old, new, 1)


D4_TITLE = u"### 4.159 【流程雷】成品换哈希是**三处联动**：文档 / 英文公告 / 门各写死一次（0.12 ZF149）"
D4 = u"""
""" + D4_TITLE + u"""

重打一次成品，要跟着改的地方**至少三处**（本轮实测）：
1. `release\\PotatoST-0.12.jar.sha1`（纯哈希一行，§4.92）；
2. **文档**：`开发档案.md` 与 `多会话交接.md` 里那条"已发布成品"行的哈希 + 字节数；
3. **英文公告**：`UpdateAnnouncement_EN.md` 的 `## Download` 段 —— 那里还写死了
   **class 数 / 配方数 / 键数**（本轮 357 / 73 / 508 → **358 / 74 / 579**）。
漏一处的表现是"门红一条、文档与现实不符"，而且**没人会立刻发现**（`_zf91_verify.py`
就是专门盯"文档里最新成品行的哈希 == `release\\*.sha1`"的那条，它已经因为两条线各打各的而红了很久）。

⚠ 附带口径：重打**之前**先看清"门指的是哪个版本的 jar"——
本工程里 `_zf70/_zf72/_zf73/_zf74/_zf75/_zf78/_zf79/_zf80/_zf81/_zf82/_zf91/_zf93/_zf100/
_zf101/_zf102/_zf114/_zf117_verify.py` 里有十几处写死 `release\\PotatoST-0.11.jar`
（它们的改前件也在 `zf***_pre\\release\\` 里躺着那一份）——**那是它们那条线的参照物，不要顺手改**，
本轮只动 0.12 这一个文件。
"""

D5_ROW = (u"| ZF149 | **新建 `zf149_pre`**（**86 份**：`release\\PotatoST-0.12.jar` + `.sha1` + "
          u"`build\\libs\\potato_s_t-0.12.jar` + `gradle.properties` + 三份文档 + **全部常驻门**；"
          u"逐份核 sha1 + 回读，失败 0）"
          u" | 0.12：**重打成品，把教程手册装进去**（用户原话「现在是0.12版本！jar貌似没有教程书」）。"
          u"旧的 `release\\PotatoST-0.12.jar`（12:56 那份 `45c061df…`）**早于 ZF148**，里面没有手册、"
          u"还是 508 键 / 73 配方 / 357 类。重打后（`59894a9e…`，" + NEW_SIZE + u" B）："
          u"**358 class / 74 配方 / 43 进度 / 五语言 579×4 + lzh 581**；手册那 26 份资源（书定义 / 6 分类 / "
          u"18 条目 / 模型 / 贴图 / 配方）全在，且与源目录**逐字节相同**；`mods.toml` 里 `patchouli` 是 "
          u"`required`；探针 class 不在产物里；`libs/` 那份帕秋莉**没被打进包**（compileOnly 判据）。"
          u"审计脚本 `_zf149_jar.py` **26 项 0 失败**（CRC 全过）| 见 §9 ｜ 见 §4.159 |\n")

D9_ANCHOR = u"### ZF148（0.12）联动帕秋莉：一本教程手册 —— **待你实测**"
D9 = (u"### ZF149（0.12）重打成品：把手册装进 `PotatoST-0.12.jar`\n\n"
      u"用户原话：「**现在是0.12版本！jar貌似没有教程书**」。\n\n"
      u"- **根因**：`release\\PotatoST-0.12.jar` 是 **12:56** 打的（`45c061df…`），"
      u"而 ZF148 的手册是 **13:00 之后**才做进源目录的 ⇒ 成品比源目录旧一轮（ZF148 §9 的"
      u"「边界」那条已经写明了）。\n"
      u"- **做法**：`gradlew build --offline` → `build\\libs\\potato_s_t-0.12.jar`（`59894a9e…`，"
      + NEW_SIZE + u" B）→ 覆盖 `release\\PotatoST-0.12.jar` + 写 `.sha1`（纯哈希一行）。"
      u"⚠ `PotatoST-0.11.jar` / 0.10 **一个字没动**（它们是别轮门的参照物，见 §4.159）。\n"
      u"- **成品里现在有什么**：358 class（ZF148 的 `GuideBook` 在内）/ **74 配方** / 43 进度 / "
      u"五语言 **579×4 + 581** / 手册 26 份资源 / `patchouli` 硬依赖（`mods.toml` 里 `type=\"required\"`）。\n"
      u"- **证据**：`_zf149_jar.py` 审计 **26 项 0 失败** —— 全条目 CRC、jar 内 lang 键数、"
      u"手册资源与源目录**逐字节相同**、`mods.toml` 渲染后版本 0.12 且依赖是 required、"
      u"产物里没有探针 class、也没有帕秋莉/JEI 的类（compileOnly 没漏进去）。\n"
      u"- **要你实测**：① 把**新**的 `release\\PotatoST-0.12.jar` 丢进 `mods/`（连同帕秋莉 `1.21.1-93+`）；"
      u"② 进世界应当收到一本手册、右键能开；③ 创造模式物品栏里应当有这本书。\n"
      u"- **还剩的账**（交接 §6 第 29 条）：公告 `Download` 段与本轮已同步；"
      u"十几处写死 `PotatoST-0.11.jar` 的门**按 §4.159 不动**（那是那些线自己的参照物）。\n\n"
      + D9_ANCHOR)

H_JAR_OLD = (u"| **已发布成品** | `release\\PotatoST-0.12.jar` = `45c061dfc9c171aeea783b64c05ca0e3d884871b`"
             u"（5,769,926 B，**12:56 打的**：508 键 / 73 配方 / 357 类，五语言齐全）")
H_JAR_NEW = (u"| **已发布成品** | `release\\PotatoST-0.12.jar` = `" + NEW_SHA + u"`（" + NEW_SIZE +
             u" B，**ZF149 重打**：**579 键 / 74 配方 / 358 类**，含 ZF148 的教程手册与 `patchouli` 硬依赖）")

H6_OLD = u"③ ⚠ **打包轮要做的三件事**："
H6_NEW = (u"③ ✅ **打包轮已做（ZF149）**：`release\\PotatoST-0.12.jar` 已重打为 `" + NEW_SHA[:12] +
          u"…`（" + NEW_SIZE + u" B，579 键 / 74 配方 / 358 类，手册在内）；"
          u"公告 `Download` 段的三个数已同步。剩下的：那十几处写死 `PotatoST-0.11.jar` 的门"
          u"**按 §4.159 不动**（是那些线自己的参照物）。原计划三件事：")

ANN_DL_OLD = (u"**`release/PotatoST-0.12.jar`** — " + OLD_SIZE + u" bytes, sha1 `" + OLD_SHA + u"`.\n\n"
              u"This is the first **0.12** build, and the first jar to contain the rewritten text in all five\n"
              u"languages. It carries 357 classes, 43 advancements, 73 recipes, and five complete language files\n"
              u"(English 508 keys, Japanese 508, Russian 508, Simplified Chinese 508, Literary Chinese 510).")
ANN_DL_NEW = (u"**`release/PotatoST-0.12.jar`** — " + NEW_SIZE + u" bytes, sha1 `" + NEW_SHA + u"`.\n\n"
              u"Rebuilt for ZF149: this jar now contains the **in-game guide book** as well as the rewritten\n"
              u"text. It carries **358 classes, 43 advancements, 74 recipes**, and five complete language files\n"
              u"(English **579** keys, Japanese 579, Russian 579, Simplified Chinese 579, Literary Chinese 581).\n"
              u"⚠ It **requires Patchouli** `1.21.1-93` or newer.")

ANN_ADD = u"""

## Rebuilt for 0.12 — the guide book is now inside the jar (ZF149)

The previous `PotatoST-0.12.jar` was built a few minutes **before** the guide book landed in the
source tree, so it shipped without it. The jar in `release/` has been rebuilt:

- **358 classes / 74 recipes / 43 advancements**, five language files (579 keys each, Literary
  Chinese 581) — and the guide book's 26 resources (book definition, 6 categories, 18 entries,
  item model, texture, crafting recipe) are all inside.
- sha1 `""" + NEW_SHA + u"""` — `""" + NEW_SIZE + u""" bytes.
- Reminder: **Patchouli `1.21.1-93`+ is required**; the mod will not start without it. Install both
  jars, then open the book you receive on your first login (or craft one from a book + an iron ingot).
"""


def main(argv):
    write = u"--write" in argv

    doc = io.open(DOC, encoding=u"utf-8", newline=u"").read()
    nums = [int(m.group(1)) for m in re.finditer(u"(?m)^#{3,4} 4\\.([0-9]+)", doc)]
    mx = max(nums)
    # ⚠ 幂等：写完之后 max 就是 159（我自己那节）⇒ 判据要分「还没写」和「已经写过」两种
    already = D4_TITLE in doc
    print(u"档案 §4 最大编号 = %d（目标 §4.159；已写入 = %s）" % (mx, already))
    if not already and mx + 1 != 159:
        fails.append(u"§4 编号不是 159（实测 max=%d）—— 停手先看清" % mx)
    doc2 = want(doc, D9_ANCHOR, D9, u"档案 §9 加 ZF149 小节")
    if D4_TITLE not in doc2:
        i = doc2.find(D9_ANCHOR)
        if i < 0:
            fails.append(u"档案：找不到 §9 的 ZF148 锚点，没处插 §4.159")
        else:
            # §4 那一节插在 **§4.158 之后**（即 §5 表格之前）
            j = doc2.find(u"\n| ZF148 |")
            if j < 0:
                fails.append(u"档案：找不到 §5 的 ZF148 行")
            else:
                k = doc2.rfind(u"\n", 0, j)
                doc2 = doc2[:k] + D4 + doc2[k:]
                notes.append(u"  [改] 档案 §4.159（插在 §5 之前）")
    i = doc2.find(u"| ZF147 |")
    if u"| ZF149 |" in doc2:
        notes.append(u"  [跳过] 档案 §5 的 ZF149 行（已经在，幂等）")
    elif i < 0:
        fails.append(u"档案：找不到 §5 的 ZF147 行")
    else:
        j = doc2.find(u"\n", i)
        doc2 = doc2[:j + 1] + D5_ROW + doc2[j + 1:]
        notes.append(u"  [改] 档案 §5 加 ZF149 行")
    # 顺手把 ZF148 §9 里"成品早于本轮"那句标注成已解决
    doc2 = want(doc2,
                u"- `release\\PotatoST-0.12.jar`（12:56 打的，`45c061df…`）**早于本轮** ⇒ 里面没有手册、",
                u"- ~~`release\\PotatoST-0.12.jar`（12:56 打的，`45c061df…`）早于本轮~~ ⇒ **ZF149 已重打**"
                u"（`59894a9e…`，手册已进成品）；重打前那一份没有手册、",
                u"档案 §9 ZF148 边界标注「已由 ZF149 重打」")
    if doc2 != doc:
        plan.append((DOC, doc, doc2))

    hand = io.open(HAND, encoding=u"utf-8", newline=u"").read()
    h2 = want(hand, H_JAR_OLD, H_JAR_NEW, u"交接 §1 成品行 → 新哈希")
    h2 = want(h2, H6_OLD, H6_NEW, u"交接 §6 第 29 条标注打包已完成")
    if h2 != hand:
        plan.append((HAND, hand, h2))

    ann = io.open(ANN, encoding=u"utf-8", newline=u"").read()
    a2 = want(ann, ANN_DL_OLD, ANN_DL_NEW, u"公告 Download 段三个数 + 新哈希")
    if u"## Rebuilt for 0.12" in a2:
        notes.append(u"  [跳过] 公告末尾 ZF149 那一条（已经在，幂等）")
    else:
        a2 = a2.rstrip(u"\n") + u"\n" + ANN_ADD
        notes.append(u"  [改] 公告末尾加 ZF149 那一条")
    if a2 != ann:
        plan.append((ANN, ann, a2))

    print(u"\n".join(notes))
    print(u"")
    print(u"计划写盘 %d 份" % len(plan))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    if fails or not write:
        if not write:
            print(u"（没加 --write，只算不写）")
        return 1 if fails else 0
    for p, old, new in plan:
        io.open(p, u"w", encoding=u"utf-8", newline=u"").write(new)
        assert io.open(p, encoding=u"utf-8", newline=u"").read() == new, p
    print(u"已写盘 %d 份" % len(plan))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
