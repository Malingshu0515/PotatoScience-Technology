# -*- coding: utf-8 -*-
u"""_zf160_docs2.py —— ZF160 文档第二笔（幂等，默认 dry-run）：

  ① 档案 §4.168 追加 ⑤：**§4 撞号**（本轮取 4.167，写到一半发现另一条线 ZF159 也占了 4.167 ⇒ 当场改 4.168）
     与**重打 jar 里带上别人的在途活**（3 份 generator_fuel 配方 + 1 个 class + 3 张 c:dusts 标签 ⇒
     class 360→365、配方 91→94，四处活体数字一起跟平）。
  ② 档案 §5 的 ZF160 行补 ⑥：成品与全门快照对照。

跑法：python build\\zftools\\_zf160_docs2.py [--write]
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
notes, fails = [], []

ADD4 = u"""
**⑤ 这一轮还撞了两件事（都不是代码问题，是并行开发的账）。**
  · **§4 撞号**：我按开工时的 max（4.166）取了 **4.167**，写到一半发现另一条线（ZF159）也立了 4.167
    ⇒ 当场把自己的改成 **4.168**（只改我自己的三处引用：小节标题 / §5 行里的 `§4.167` / 交接第 34 条），
    别人的一个字没碰。档案里现在 `4.166 ×2`、`4.167 ×2` 是并行留下的账（§4.147 同族，历史上 4.90/91/92、
    4.146~4.150 也是这么来的）。
  · **重打出来的 jar 里带上了别人的在途活**：逐条目比对上一版 jar，多出来的是
    3 份 `data/potato_s_t/recipe/generator_fuel/{gasoline,lpg,naphtha}.json`、
    `com/potatost/mod/DieselGeneratorBlockEntity$FuelClass.class`、以及 `data/c/tags/item/dusts{,/carbon,/iron,/titanium}.json`
    —— 另一条线（柴油发电机燃料那轮）**还没提交**的产物。jar 是从工作树打的，所以照样进去了。
    连带四处"活体数字"跟平：`_zf149_jar.py` 的配方份数 **91 → 94**、`_zf149_verify.py` 钉公告的那句
    与英文公告一起 **`360 classes / 91 recipes` → `365 classes / 94 recipes`**、`_zf156_jarcheck.py`
    的配方份数 **91 → 94**。判据没放宽（仍是逐字比"发布那一刻的实测值"），只是**跟到实际打出来的那份**。
"""

ADD5_OLD = (u"⑤ 本轮**不碰** `PotatoST.java`（别人的探针挂在里面）：探针自带 `@EventBusSubscriber` "
            u"自动注册，卸载只是删文件（§4.168②④） | 见 §9 ｜ 见 §4.168 |\n")
ADD5_NEW = (u"⑤ 本轮**不碰** `PotatoST.java`（别人的探针挂在里面）：探针自带 `@EventBusSubscriber` "
            u"自动注册，卸载只是删文件（§4.168②④）。"
            u"⑥ **重打成品**：`release\\PotatoST-0.13.jar` = **5,886,943 字节 / sha1 "
            u"`b3688162332a3e5e8a65000d40b09e53f0e578e1`**；`_zf149_jar.py` 26/0、`_zf149_verify.py` 28/0、"
            u"`_zf160_verify.py` 16/0、`_zf156_jarcheck.py` ALL OK、`_zf155_jarcheck.py` ALL OK。"
            u"⚠ 这一版**还带上了另一条线在途的 3 份发电机燃料配方 + 1 个 class + 3 张 c:dusts 标签**"
            u"（class 360→365、配方 91→94，四处活体数字已跟平）—— 见 §4.168⑤。"
            u"⑦ 全门快照对照见交接 §6 第 34 条（`_zf160_gatediff.py`） | 见 §9 ｜ 见 §4.168 |\n")


def main(argv):
    write = u"--write" in argv
    doc = io.open(DOC, encoding="utf-8", newline=u"").read()

    anchor = u"**④ \"基准选错\"的第四种形态（§4.161 同族）：我一个字没动，但那个文件被**别人**改了。**"
    if u"**⑤ 这一轮还撞了两件事" in doc:
        notes.append(u"  [跳过] §4.168 ⑤（已经在，幂等）")
    elif anchor in doc:
        j = doc.find(u"\n\n", doc.find(anchor))
        doc = doc[:j] + u"\n" + ADD4 + doc[j:]
        notes.append(u"  [改] §4.168 追加 ⑤")
    else:
        fails.append(u"§4.168 ④ 锚点没找到")

    if u"⑥ **重打成品**：`release\\PotatoST-0.13.jar` = **5,886,943" in doc:
        notes.append(u"  [跳过] §5 行的 ⑥⑦（已经在，幂等）")
    elif doc.count(ADD5_OLD) == 1:
        doc = doc.replace(ADD5_OLD, ADD5_NEW, 1)
        notes.append(u"  [改] §5 行补 ⑥⑦")
    else:
        fails.append(u"§5 行尾锚点命中 %d 次" % doc.count(ADD5_OLD))

    print(u"\n".join(notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    if fails or not write:
        if not write:
            print(u"（没加 --write，只算不写）")
        return 1 if fails else 0
    io.open(DOC, u"w", encoding="utf-8", newline=u"").write(doc)
    print(u"  已写 docs\\开发档案.md")
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
