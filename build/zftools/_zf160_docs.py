# -*- coding: utf-8 -*-
u"""_zf160_docs.py —— ZF160 文档落地（幂等，默认 dry-run）：

  ① 档案 **§4.167**：本轮三条工具/判据雷（探针别等 tick / 汇合点被占时改用注解注册 /
     读 private 字段走官方编解码器 / 卸载自检的"基准选错"变体）；
  ② 档案 **§5** 加 ZF160 行（接在 ZF158 之后）；
  ③ 档案 **§9** 加 ZF160 小段（**待用户实测**）；
  ④ 交接 **§6** 加第 34 条；
  ⑤ 英文公告末尾加一条（§4.150 日志纪律）。

跑法：python build\\zftools\\_zf160_docs.py [--write]
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

D4_TITLE = u"### 4.167 【工具雷】探针别等 tick（别人的探针会先把服务器 halt）；汇合点被占就改用注解注册（0.13 ZF160）"
D4 = D4_TITLE + u"""

用户原话：「**银矿矿脉可以稍微调大一点 大概和铜差不多（或者生成权重大一点也可以）然后铝的权重调小1~2**」。
本轮改的是两条 `placed_feature` / 一条 `configured_feature` 的三个数，活很小，**坑全在证据链上**：

**① 探针"等 20 tick 再验"会一个字都写不出来 —— 别人的探针在启动期就 halt 了。**
第一版探针沿用 ZF156 那套（`ServerStartedEvent` 记下 server、到第 20 tick 再验）。
跑完发现报告文件**根本不存在**：另一条线的 `Zf159Check` 在启动期就 `halt` ⇒
日志里 "Done (1.467s)!" 后面**紧跟着** "Stopping server"，服务器**一个 tick 都没跑**。
（不是红，是"报告不存在"——这种失败最容易被误读成"探针没挂上"。）
改法：`ServerStartedEvent` 那一刻 configure/placed feature 两个注册表**已经装好**
（本工程的 `UniversalUpgradeTemplate` 就是在那儿读配方的）⇒ 立即验、立即写、立即 halt，不等 tick。

**② 汇合点被占时，别去挤 `PotatoST.java`（§4.7），用注解注册。**
那一刻盘上正挂着别人的 `Zf159Check`，"挂载/卸载"那套结构性锚点就没法用（会叠罗汉）。
本探针改成自带 `@EventBusSubscriber(modid = PotatoST.MODID)`（默认就是 game 总线，与 `GuideBook` 同款写法）
⇒ **挂载 = 拷一个类文件，卸载 = 删掉它**，`PotatoST.java` 一个字节都不用动。
代价是"卸载自检"要换个基准（见 ④）。

**③ 读 `CountPlacement.count`（private）不用反射 —— 用官方编解码器把它编回 NBT。**
`PlacedFeature.placement()` 是 public，但 `CountPlacement` 的 `count` 字段是 private。
本工程对反射零容忍（ZF155 立的口径）⇒ 走 `PlacementModifier.CODEC.encodeStart(NbtOps.INSTANCE, mod)`，
拿回来就是 `{"type":"minecraft:count","count":12}` 这样的 NBT，直接读字段。
高度区间同理（`height_range` 编回来读 `min_inclusive/max_inclusive`）。

**④ "基准选错"的第四种形态（§4.161 同族）：我一个字没动，但那个文件被**别人**改了。**
本轮 `PotatoST.java` 只承载别人的探针 —— 拿"改前件"当卸载自检的基准，会显示"不一致"（假红）。
改法：**挂载那一刻把 sha1 存一份快照**，卸载时跟快照比；真正的硬判据只有一条
（"源码里不再出现 `Zf160Check`"）。
"""

D5_ROW = (u"| ZF160 | **新建 `zf160_pre`**（**17 份**：3 份世界生成 JSON + 铝的 configured / biome modifier / "
          u"`PotatoST.java`（⚠ 本轮**没动它**，只是备份留底）/ 三份文档 / 常驻门与打包脚本 / "
          u"成品 0.13 + `.sha1` + `build\\libs` 那份；逐份核 sha1 + 回读，失败 0。"
          u"⚠ 开工前查过轮号：**ZF159 已被另一条线占用**（`_zf159_lang*.py` 十来个文件）⇒ 本轮用 **ZF160**；"
          u"`zf160_pre` 不在（§4.147））"
          u" | **0.13：银矿调大、铝的权重调小**（用户原话见 §9）。"
          u"① 取证（`_zf160_recon.txt`）：本模组 9 种矿里**银是最小的**（size 3；铝 11、锰 12、铀 10…），"
          u"原版铜是**小脉 size 10 / 每区块 16 次**（另有 size 20 的大脉）。"
          u"② 改动只有三个数：银 `size` **3 → 10**（直接对齐原版铜小脉）、银 `count` **9 → 12**"
          u"（用户说「或者生成权重大一点也可以」，顺手提一档；仍低于铜的 16）、"
          u"铝 `count` **12 → 10**（「调小 1~2」取了 2）。高度区间 / 步数 / targets / 其余 7 种矿**一个没动**。"
          u"③ 探针 `Zf160Check`（真开服，**注册表现查**）**7 项 ALL OK**：银 size=10 / 银 count=12 / "
          u"银 targets 没动 / 铝 count=10 且 size 仍 11 / 九种矿逐条对上改后表 / 九条高度区间逐条没动 / "
          u"负对照（读到的不是旧值）。⚠ 报告是在 `ServerStartedEvent` 里**立即**写的 —— "
          u"那一刻另一条线的探针会先把服务器 halt（一个 tick 都不跑），见 §4.167①。"
          u"④ 常驻 `_zf160_verify.py`（A 盘上 JSON 7 项 / B 探针 3 项 / C 文档成品 6 项）**全绿**，"
          u"其中 A5 是「把新旧两份 JSON 里那三个数都换成占位符之后逐字相同」（= 只动了该动的数）。"
          u"⑤ 本轮**不碰** `PotatoST.java`（别人的探针挂在里面）：探针自带 `@EventBusSubscriber` "
          u"自动注册，卸载只是删文件（§4.167②④） | 见 §9 ｜ 见 §4.167 |\n")

D9_ANCHOR = u"## 10. 备份策略"
D9 = u"""### ZF160（0.13）银矿调大 / 铝的权重调小 —— **待你实测**

用户原话：「**银矿矿脉可以稍微调大一点 大概和铜差不多（或者生成权重大一点也可以）然后铝的权重调小1~2**」。

| 矿 | 矿脉大小（size） | 每区块次数（count） | 说明 |
|---|---|---|---|
| **银** | 3 → **10** | 9 → **12** | size 直接对齐**原版铜的小脉**（铜还有一条 size 20 的大脉）；权重也提了一档 |
| **铝** | 11（没动） | 12 → **10** | 你说"调小 1~2"，我取了 **2** |

其余 7 种矿（钴 / 镍 / 铀 / 锰 / 锂 / 钨 / 钛）**一个数都没动**；九条矿脉的高度区间也原样。

**进世界怎么看**：同一片地下，银矿应该明显比 0.13 之前多、而且**成团更大**（以前只有 3 格一小撮）；
铝会略微稀一点。矿脉大小与次数都是**建新世界/新区块**才生效的 —— **已经生成过的区块不会变**，
想立刻看效果建议**开新世界**，或者跑远一点去看没生成过的区块。

⚠ 一个口径说明：你说"大概和铜差不多"——铜是 `size 10 × 16 次` **外加**一条 `size 20 × 16 次`的大脉，
我这次只对齐了**小脉**那一半（银 10 × 12）。要是你觉得还该更多，一句话我就把 count 提到 16
或者再加一条大脉。

---

"""

H6_ANCHOR = u"    ④ 谁要拿 ZF155 的探针源码复核那轮结论，**以报告 `_zf155_probe_utf8.txt` 为准**（28 项全绿那份）。"
H6_NEW = H6_ANCHOR + u"""

34. **ZF160 的账（0.13：银矿调大 / 铝权重调小）**：① 改动只有三个数（银 size 3→10、银 count 9→12、
    铝 count 12→10），取证与口径见档案 §9、工具雷见 §4.167。② ⚠ **本轮探针不等 tick**：
    第一版沿用"等 20 tick"的写法，而另一条线的 `Zf159Check` 在启动期就 halt ⇒ 服务器一个 tick 都没跑、
    报告文件根本没生成（最容易误读成"探针没挂上"）。③ ⚠ **本轮没有动 `PotatoST.java`**：
    那一刻汇合点被别人的探针占着，改用 `@EventBusSubscriber` 自动注册（拷一个文件/删一个文件），
    卸载自检的基准因此换成"挂载那一刻的 sha1 快照"。④ 读 private 字段（`CountPlacement.count`）
    走 `PlacementModifier.CODEC` 编回 NBT，零反射。⑤ 重打成品：`release\\PotatoST-0.13.jar`
    哈希/体积随重打走（§4.159 三处联动）。"""

ANN_ADD = u"""
## New in 0.13 ZF160 - Silver ore is more common

- **Silver veins are bigger and more frequent.** The vein size went from 3 to **10** (the same size as
  vanilla's small copper vein) and the number of veins per chunk from 9 to **12**.
- **Aluminium is a bit rarer**: 12 veins per chunk went down to **10**. Its vein size is unchanged.
- Nothing else changed: the other seven ores, all height ranges and every other placement step are
  exactly as before.
- These numbers only affect **newly generated chunks** - an existing world keeps the ore it already has.
"""


def main(argv):
    write = u"--write" in argv
    doc = io.open(DOC, encoding="utf-8", newline=u"").read()
    nums = [int(m.group(1)) for m in re.finditer(u"(?m)^#{3,4} 4\\.([0-9]+) ", doc)]
    mx = max(nums)
    print(u"档案 §4 最大编号 = %d（目标 §4.167；已写入 = %s）" % (mx, D4_TITLE in doc))
    if D4_TITLE not in doc and mx != 166:
        fails.append(u"§4 编号不是 167（实测 max=%d）" % mx)

    if D4_TITLE in doc:
        notes.append(u"  [跳过] §4.167（已经在，幂等）")
    else:
        anchor4 = u"| ZF147 | \u26a0 **没有备份根也要有账**"
        if doc.count(anchor4) == 1:
            doc = doc.replace(anchor4, D4 + u"\n\n" + anchor4, 1)
            notes.append(u"  [改] §4.167")
        else:
            fails.append(u"§4 插入锚点命中 %d 次" % doc.count(anchor4))

    if u"### ZF160（0.13）" in doc:
        notes.append(u"  [跳过] §9 ZF160 小节（已经在，幂等）")
    elif doc.count(D9_ANCHOR) == 1:
        doc = doc.replace(D9_ANCHOR, D9 + D9_ANCHOR, 1)
        notes.append(u"  [改] §9 ZF160 小节")
    else:
        fails.append(u"§9 锚点命中 %d 次" % doc.count(D9_ANCHOR))

    if u"| ZF160 |" in doc:
        notes.append(u"  [跳过] §5 ZF160 行（已经在，幂等）")
    else:
        anchor5 = u" | 见 §9 ｜ 见 §4.166 |\n"
        if doc.count(anchor5) != 1:
            # ZF158 行尾（ZF160 要接在它后面）
            anchor5 = u"| 见 §9 ｜ 见 §4.166 |\n"
        if doc.count(anchor5) != 1:
            fails.append(u"§5 的 ZF158 行尾锚点命中 %d 次" % doc.count(anchor5))
        else:
            doc = doc.replace(anchor5, anchor5 + D5_ROW, 1)
            notes.append(u"  [改] §5 ZF160 行")

    if write:
        io.open(DOC, u"w", encoding="utf-8", newline=u"").write(doc)
    else:
        notes.append(u"  （没加 --write：档案只算不写）")

    hand = io.open(HAND, encoding="utf-8", newline=u"").read()
    if u"34. **ZF160 的账" in hand:
        notes.append(u"  [跳过] 交接 §6 第 34 条（已经在，幂等）")
    elif hand.count(H6_ANCHOR) == 1:
        if write:
            io.open(HAND, u"w", encoding="utf-8", newline=u"").write(hand.replace(H6_ANCHOR, H6_NEW, 1))
        notes.append(u"  [改] 交接 §6 第 34 条")
    else:
        fails.append(u"交接 §6 锚点命中 %d 次" % hand.count(H6_ANCHOR))

    ann = io.open(ANN, encoding="utf-8", newline=u"").read()
    if u"## New in 0.13 ZF160" in ann:
        notes.append(u"  [跳过] 公告 ZF160（已经在，幂等）")
    else:
        if write:
            io.open(ANN, u"w", encoding="utf-8", newline=u"").write(ann.rstrip(u"\n") + u"\n" + ANN_ADD)
        notes.append(u"  [改] 公告 ZF160")

    print(u"\n".join(notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
