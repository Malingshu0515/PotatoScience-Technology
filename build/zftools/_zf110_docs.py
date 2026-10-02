# -*- coding: utf-8 -*-
u"""_zf110_docs.py —— 把 ZF110 的小节接到 `docs/贴图清单.md` 末尾（只加行，不整份覆盖）

⚠ 规矩（§4.7）：汇合点文件只准加行 ⇒ 本脚本读全文、在**末尾追加**、按原换行风格写回，
   写完立刻回读断言「前面的内容逐字节没变」。
"""
import hashlib
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DOC = r"E:\PotatoST\docs\贴图清单.md"

SECTION = u"""

## ZF110（0.11）：用户新放的 5 件素材上线（**星璨钢头盔 + 碳酸锂 / 氯化钠 / 硫 顶掉占位 + 油桶**）

用户原话「现在放了」—— 这轮收的是**图片**（没有音频）。5 件全是 16×16：
其中 4 件是**真 PNG / 8 位 RGBA / 背景透明 / 半透明像素 0** ⇒ **原字节复制，一个像素没重编码**；
只有油桶那件是**真 JPEG**（无 alpha）⇒ 要转档。

| 你的文件名 | 字节 | 落到哪 | 状态 |
|---|---|---|---|
| `星璨钢头盔.png` | 2979 | `textures/item/star_steel_helmet.png` | ✅ **新建**（模型原先借 `minecraft:item/iron_helmet`） |
| `碳酸锂.png` | 2891 | `textures/item/lithium_carbonate.png` | ✅ **换新**（顶掉 ZF86 生成的占位 373 B） |
| `氯化钠.png` | 3166 | `textures/item/sodium_chloride.png` | ✅ **换新**（顶掉 ZF86 生成的占位 477 B） |
| `E:\\硫_001.png` | 2978 | `textures/item/sulfur.png` | ✅ **换新**（顶掉 ZF96 生成的占位 136 B） |
| `油桶.jpg` | 779 | `textures/item/oil_bucket.png` | ✅ **换新**（顶掉 ZF87 那版 824 B） |

- **活体数字：还在借原版贴图的模型 13 → 12**（只有星璨钢头盔这一件能减；其余四件本来就是
  我们自己的图，不在"借原版"那一档）。已同步三处：英文公告那句、`_zf71_verify.py`、`_zf90_verify.py`。
- `models/item/star_steel_helmet.json` 的 `layer0` 从 `minecraft:item/iron_helmet` 改成
  `potato_s_t:item/star_steel_helmet`。**其余四件模型一个字没动**（文件名就是注册名）。
- ⚠ **`TextureCheck.py --plan` 报的"待画"是 12，而 `docs/UpdateAnnouncement_EN.md` 之前写 13** ——
  那 1 个差不是本轮造成的：ZF106 只改了公告，没重跑 `--plan`，清单表头一直停在"5 个"
  （表体其实早就是 12 行）。本轮**重跑并收口**：表头 12、与门一致。手写段（`## ZF78` 起）
  重跑前后 **18864 字符 / sha1 逐字符不变**。

### ⚠ 油桶这一件：**不能**照「四边泛洪去背景」做（本轮踩到，见档案 §4.81）

ZF83/ZF86/ZF87 那套去背景的前提是「**亮底 + 主体在中间**」。用户这张**不是**：
实测（`build/zftools/_zf110_oil_look.py`）**最外圈 60 个像素全是暗色**（亮 0 / 暗 60），
四角 ≈ RGB(5,3,0)，而**桶身的暗部与"背景"同色系** ⇒ 泛洪顺着暗部把桶一起吃掉。

第一版照抄泛洪，只剩 **137 个实心像素**（桶没了），而脚本里"40..230"那条断言**照样放行** ——
又一个「检查能过 ≠ 结果对」。改成**只掏掉最外圈一圈**（桶身一个像素不动）后留下 **196 个**，
肉眼复核（`_zf110_show.png` 放大 26 倍）是一只完整的桶。

- 生成脚本：`build\\zftools\\_zf110_convert.py`（**幂等**：⓪ 段先从 `zf110_pre` 恢复成品、
  ① 段的前置断言接受"改造前 / 本轮成品"两态，**第三态 = 盘被别人动过 ⇒ 停手**）；
  JPEG 像素由 `_zf110_jpeg_dump.ps1` 用 **.NET System.Drawing** 解出（沿用 `_zf83` 立的口径：
  "和资源管理器看到的一样"）。
- ⚠ **记一笔我自己的失误**：第一次跑时把旧的 `油桶.jpg` 留档**直接覆盖**了（779 B 顶掉 824 B）。
  成品 `oil_bucket.png`（824 B / sha1 `750c80745a14`）已从 `zf110_pre` 完整恢复并回写，
  但**那个旧 jpg 留档的原字节已丢**，`_来源凭据.json` 里只留了名称与哈希。教训见档案 §4.81。

### 要换手绘的

四张 PNG 直接覆盖同名文件即可（16×16 / RGBA），**模型不用改**；油桶同上。
星璨钢那套**还差 3 件**背包图标（胸甲 / 护腿 / 靴子）与钛合金整套 4 件 —— 都还在待画表里。
"""


def main():
    before = io.open(DOC, "rb").read()
    newline = u"\r\n" if b"\r\n" in before else u"\n"
    text = before.decode("utf-8")
    if u"## ZF110（0.11）" in text:
        print(u"  [幂等] ZF110 小节已存在，不重复追加")
        return 0
    if not text.endswith(newline):
        text += newline
    body = SECTION.replace(u"\r\n", u"\n").replace(u"\n", newline)
    out = (text + body).encode("utf-8")
    io.open(DOC, "wb").write(out)

    # 回读断言：前面那段必须逐字节没变，且新内容确实在末尾
    after = io.open(DOC, "rb").read()
    if not after.startswith(before):
        print(u"  !! 前面的内容被改动了（不是纯追加）")
        return 1
    if u"## ZF110（0.11）" not in after.decode("utf-8"):
        print(u"  !! 追加失败")
        return 1
    print(u"  [OK] 纯追加 %d -> %d 字节（换行风格 %s）"
          % (len(before), len(after), "CRLF" if newline == u"\r\n" else "LF"))
    print(u"  [OK] 前缀逐字节未变；sha1(前段) %s"
          % hashlib.sha1(before).hexdigest()[:12])
    return 0


if __name__ == "__main__":
    sys.exit(main())
