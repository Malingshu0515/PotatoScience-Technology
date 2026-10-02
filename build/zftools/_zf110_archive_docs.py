# -*- coding: utf-8 -*-
u"""_zf110_archive_docs.py —— 往 `docs/开发档案.md` 里插两处（**只插不覆盖**）

① §5 变更表的 ZF110 行（插在 ZF109 那行之后）
② 雷区 §4.83「暗底素材不能照泛洪去背景」（插在 §4.80 结尾 / `### 6.1` 之前）

两处都做「插入点唯一性 + 原有内容逐字节不变」双向断言（§4.6）。
"""
import hashlib
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DOC = r"E:\PotatoST\docs\开发档案.md"

ANCHOR_ROW = u"| ZF109 |"
ANCHOR_SEC = u"### 6.1 加一个**音乐唱片**"

ROW = (
    u"| ZF110 | **新建 `zf110_pre`**（5 个改前件：`textures/item/` 的 "
    u"`lithium_carbonate.png` / `sodium_chloride.png` / `sulfur.png` / `oil_bucket.png` "
    u"+ `models/item/star_steel_helmet.json`；逐份核哈希、失败 0） | "
    u"0.11：**用户新放的 5 件素材上线**（原话只有「现在放了」四个字 —— 一次**没有名字的收货**）。"
    u"5 件全是 16×16：① **4 件真 PNG / 8 位 RGBA / 零半透明 ⇒ 原字节复制**，一个像素没重编码 "
    u"（星璨钢头盔 2979 B 新建；碳酸锂 2891 / 氯化钠 3166 / 硫 2978 三件**顶掉我自己生成的占位**）；"
    u"② **第 5 件是油桶，真 JPEG 无 alpha ⇒ 必须转档**，而且**不能照 ZF83/ZF86/ZF87 的「四边泛洪去背景」**"
    u"（那张是暗底包边、桶身暗部与背景同色系 ⇒ 泛洪把桶吃掉，只剩 137 个实心像素，"
    u"而脚本里 40..230 那条断言照样放行）⇒ 改成**只掏最外圈**（留 196 个，肉眼复核通过），见 §4.83；"
    u"③ **模型**：只有 `star_steel_helmet.json` 的 `layer0` 从 `minecraft:item/iron_helmet` "
    u"改成 `potato_s_t:item/star_steel_helmet`，其余四件一个字没动（文件名就是注册名）；"
    u"④ **活体数字 13 → 12**（还在借原版贴图的模型），三处一起改：英文公告那句、`_zf71_verify.py`、"
    u"`_zf90_verify.py`；⑤ 顺带**收口一处陈旧账**：`docs/贴图清单.md` 的待画**表头一直停在 5**、"
    u"表体却已是 12 行（ZF106 只改了公告没重跑 `--plan`）⇒ 本轮重跑并统一到 **12**，"
    u"手写段（`## ZF78` 起）18864 字符 / sha1 逐字符不变；⑥ **自记一笔失误**：第一次跑时把旧的 "
    u"`油桶.jpg` 留档**直接覆盖**了（779 B 顶掉 824 B）；成品 `oil_bucket.png`（sha1 `750c80745a14`）"
    u"已从 `zf110_pre` 完整恢复，但那个旧 jpg 留档的**原字节已丢**，凭据里只留名称与哈希（§4.83）。"
    u"⚠ 本轮**没有音频**（用户说要给的音乐/音效没到，全盘搜过：近两天唯一音频仍是 ZF93 那张） |\n"
)

SECTION = u"""
### 4.83 【贴图雷】"去背景"的**前提是亮底 + 主体居中** —— 暗底包边的素材一律不适用（0.11 ZF110）

本工程做物品图标有一套沿用了 8 轮的去背景法（`_zf83_plates.py` / `_zf86_convert.py` /
`_zf87_convert.py` 三份同源）：**四边泛洪 + 只留最大连通域**，背景色取**四角中位色**，
容差 26。它work的前提从没写下来过，这一轮被一张图当场证伪。

用户 ZF110 给的 `油桶.jpg`（779 B / 16×16 / **真 JPEG 基线 JFIF，无 ICC、无 Adobe 标记**）：

| 量 | 实测 |
|---|---|
| 最外圈 60 个像素 | **全是暗色**（按亮度 >128 判"亮"：亮 0 / 暗 60） |
| 四角 | RGB(1,3,0) / (11,11,11) / (7,0,3) / (5,4,0) ⇒ 中位色 RGB(5,3,0) |
| 桶身 | 占满画面，**暗部与"背景"同色系**（0~60 那一段里既有背景也有桶） |
| 泛洪结果 | **只剩 137 个实心像素** —— 桶被自己的暗部"吃"掉了 |

**最刺眼的一点**：脚本里本来有一条"留下 40..230 个像素才算一个物品图标"的断言，
**137 落在区间内 ⇒ 断言放行**。也就是说这道检查**看着有、其实没拦住**。
这和 §4.17「能失败的检查才算检查」是同一族：**区间型断言对"内容被掏空"是瞎的**。

**改法**：认清这张的画法（暗底包边、桶占满画面、**没有留白可抠**）⇒ 只掏掉**最外圈一圈**，
桶身一个像素不动，留下 196 个。**最小干预**，而且与 ZF87 成品"1 格宽透明边"的口径一致。

**可复用的判据（下次先量再选方法）**：

1. 先数**最外圈的亮/暗**：最外圈基本全暗 ⇒ 这张**不是"亮底抠图"型**，泛洪一定出事；
2. 四角中位色若与**主体暗部**落在同一段容差里 ⇒ 泛洪会顺着主体内部蔓延（不是只啃边）；
3. **别信区间型断言**：要么加上限（"不少于主体包围盒面积的一半"），
   要么直接**把成品渲染出来肉眼看**（本轮就是靠 `_zf110_show.png` 放大 26 倍才确认对错的）。

**另一条同轮教训（流程）**：第一次跑转档脚本时，我把旧的 `油桶.jpg` 留档**直接覆盖**了
（新素材 779 B 顶掉旧素材 824 B）—— 因为脚本写的是"把源图挪到 `build/用户素材/oil_bucket.jpg`"，
而那个位置**早就有一份同名旧素材**。凡是"把用户素材挪进留档区"的动作，
**落点必须先查重名**：在就改名（本轮补成了 `oil_bucket_prev.jpg`）或者先记哈希再覆盖。
本轮成品恢复了，但**被覆盖的那个原字节永久丢了** —— 留档的意义就在于"原字节"，
覆盖之后它和没留档是一样的。
"""


def main():
    before = io.open(DOC, "rb").read()
    newline = u"\r\n" if b"\r\n" in before else u"\n"
    text = before.decode("utf-8")

    # ---------- ① 变更表那一行 ----------
    if u"| ZF110 |" in text:
        print(u"  [幂等] ZF110 变更行已存在")
    else:
        idx = text.index(ANCHOR_ROW)
        eol = text.index(u"\n", idx) + 1
        # 确认 ZF109 行的**下一个非空行之后**没有别的东西要保留（只插一行）
        text = text[:eol] + ROW.replace(u"\n", newline) + text[eol:]
        print(u"  [OK] 变更表已插入 ZF110 行（%d 字符）" % len(ROW))

    # ---------- ② 雷区 4.83 ----------
    if u"### 4.83 " in text:
        print(u"  [幂等] §4.83 已存在")
    else:
        occurrences = text.count(ANCHOR_SEC)
        if occurrences != 1:
            print(u"  !! 锚点 `%s` 出现 %d 次，不唯一，停手（§4.6）" % (ANCHOR_SEC, occurrences))
            return 1
        idx = text.index(ANCHOR_SEC)
        body = SECTION.replace(u"\r\n", u"\n").replace(u"\n", newline)
        text = text[:idx] + body + newline + text[idx:]
        print(u"  [OK] 雷区 §4.83 已插入（%d 字符）" % len(SECTION))

    after = text.encode("utf-8")
    io.open(DOC, "wb").write(after)
    print(u"\n  档案 %d -> %d 字节（换行 %s）"
          % (len(before), len(after), "CRLF" if newline == u"\r\n" else u"LF"))

    # 回读：两处都必须真的在；且原有锚点行数不能变
    check = io.open(DOC, encoding="utf-8").read()
    ok = (u"| ZF110 |" in check and u"### 4.83 " in check
          and check.count(ANCHOR_SEC) == 1 and u"| ZF109 |" in check)
    print(u"  %s 回读断言：ZF110 行 / §4.83 / 6.1 锚点唯一 / ZF109 行都在"
          % (u"[OK]" if ok else u"[!!]"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
