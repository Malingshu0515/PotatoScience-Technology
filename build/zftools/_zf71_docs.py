# -*- coding: utf-8 -*-
"""_zf71_docs.py —— 把 ZF71（英文公告）写进《开发档案》

⚠ 本轮**不动 jar**：只新增 `docs/UpdateAnnouncement_EN.md` + 改档案 ⇒
   成品仍是 ZF70 的 `84d09345…`，**不作废**（同 ZF61 的口径）。
"""
import io
import sys

DOCS = r"E:\PotatoST\docs\开发档案.md"

fails = []
applied = []


def rep(text, old, new, why):
    n = text.count(old)
    if n != 1:
        fails.append(u"%s：命中 %d 次（要求恰好 1 次）" % (why, n))
        return text
    applied.append(why)
    return text.replace(old, new, 1)


def main():
    with io.open(DOCS, encoding="utf-8") as fh:
        text = fh.read()
    before = text.count("\n") + 1

    # ---------- ① §5 加 ZF71 行 ----------
    old = u"\n\n> ZF40~ZF44 全是**电力高炉的连续改动**"
    row = (
        u"| ZF71 | **新建 `zf71_pre`**（1 个改前件：`docs/开发档案.md`。公告文档本身是**新增**，没有改前件） "
        u"| 0.10：**给玩家一份英文公告**（用户：「给个 mod 目前能干什么 或者说更新公告 英文」）⇒ 新增 "
        u"`docs/UpdateAnnouncement_EN.md`（**纯文档，不动 jar** —— 成品仍是 ZF70 的 `84d09345…`，**不作废**，"
        u"同 ZF61 口径）。① 内容**不是我凭记忆写的**：先写 `_zf71_overview_dump.py` 把「这个 mod 现在有什么」"
        u"从项目里挖出来（46 物品 / 44 方块 / 3 流体 / 9 矿石 + 7 深层 / 28 合成 + 6 烧炼配方 / 3 进度 / "
        u"8 个 JEI 机器分类 / 7 个音效 / 4 语言各 210 键），机器数值从 java 常量抓、玩家看到的英文名从 "
        u"`en_us.json` 抓；② 新写常驻 `_zf71_verify.py`（**83 项**）做**事实核对**：公告里的每个数必须等于"
        u"代码常量算出来的值、每个英文名必须等于 lang 里的正式名、并且与**已发布的 tooltip** 不打架；"
        u"③ 「尚未完成」那一节写成**可证伪的断言**（「这 4 个方块还没有配方」、「粗钨没有任何用处」、"
        u"「3 个进度都没有 rewards」）—— 哪天补齐了，校验会自己挂，逼着公告跟着改；"
        u"④ **反证**：改两个数字（液压机 24,000→34,000、高炉 10 s→12 s）⇒ CHECKER **2 项 FAIL**，"
        u"其中高炉那条**第一次没抓到**（我原来只查了常量、没查公告正文），补完断言后再反证才挂 —— "
        u"反证的价值就在这儿；⑤ 核对过程**抓到我自己数错**：公告第一版写「8 个深层变体」，"
        u"实际是 **7**（我把 `textures/block/deepslate_aluminiu_ore.png` 这张**拼错名的孤儿贴图**当成了第 8 个）"
        u" | 见 §9 |"
    )
    text = rep(text, old, u"\n" + row + old, u"§5 ZF71 行")

    # ---------- ② §9 加 ZF71 待办 + 核出来的 5 个真问题 ----------
    old = u"- [ ] **ZF66 我替你定的三个数**"
    new = (u"- [ ] **ZF71：英文公告在 `docs\\UpdateAnnouncement_EN.md`**（可直接贴到 Discord / Modrinth）。\n"
           u"      它覆盖：电力网络（端子/线缆轴/模式）、发电（低级发电机/太阳能板/动力能源捕获器+发电机/锂电池）、\n"
           u"      6 台单方块机器、3 台多方块、9 种矿与材料链、钛合金工具、3 个成就、JEI/Jade/四语言/音效，\n"
           u"      外加一节 **Known gaps**（如实写「哪些还不能做」）。\n"
           u"      要改语气/长度/加截图位，说一声即可；**它不在 jar 里**（`docs/` 不是资源目录）⇒ 不影响成品。\n"
           u"- [ ] **ZF71 顺手核出来的 5 个真问题（都要你拍板，我一行都没改）**：\n"
           u"      ① **微型粉碎机的 tooltip 少了一条配方**：ZF48 加的「粗钛 → 钛粉（6s，300 FE/t）」\n"
           u"         **四种语言都没写进去**（JEI 里有，因为 JEI 读的是 java 配方表）——我看了一眼，\n"
           u"         同一段里 `铜锭 → 4 铜线` 那行还少了个「·」前缀。要不要补？（也可以按你 ZF64 的口径\n"
           u"         「给玩家看的没必要列」**反着删**掉整段配方列表，只留缓冲/关机那两句。）\n"
           u"      ② **两个方块连配方都没有**（不是「配方没写进 tooltip」，是**生存里根本做不出来**）：\n"
           u"         **合金炉主控** `alloy_smelter` 与 **三元聚合物锂电池** `lithium_battery`。\n"
           u"         加上早已记着的 `advanced_metal_block` / `stable_metal_block`，一共 **4 个方块只能创造取**。\n"
           u"         （电力高炉不用配方：空手 Shift 右键原版高炉就能装出来。）要配方的话给我图纸/思路。\n"
           u"      ③ **锂电池的英文名**是 `Ternary polymer lithium battery` —— 和其它方块的名字风格不一致\n"
           u"         （首字母小写、像个描述句）。要不要改成 `Lithium Battery`？中文「三元聚合物锂电池」保持不变？\n"
           u"      ④ **`aluminium` 拼法不统一**：物品叫 `Aluminum Ingot`（美式），液压机 tooltip 里写的是\n"
           u"         `aluminium`（英式）。以哪个为准？\n"
           u"      ⑤ **一张拼错名的孤儿贴图**：`textures/block/deepslate_aluminiu_ore.png`（少了个 m），\n"
           u"         没有任何模型引用（ModelCheck 早已按 WARN 报出来，和 `lv_001.png` 一起是那 2 条提示项）。\n"
           u"         铝**没有**深层变体 ⇒ 这张图要么删掉，要么你本来想要「深层铝矿」？后者的话我补方块+世界生成。\n"
           u"- [ ] **ZF66 我替你定的三个数**")
    text = rep(text, old, new, u"§9 ZF71 待办与 5 个问题")

    if fails:
        print(u"**有失败项，未写盘**：")
        for f in fails:
            print(u"  !! " + f)
        return 1
    with io.open(DOCS, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(u"已改 %d 处：" % len(applied))
    for a in applied:
        print(u"  [OK] " + a)
    print(u"行数 %d -> %d" % (before, text.count("\n") + 1))
    print(u"失败项 = 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
