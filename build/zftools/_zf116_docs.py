# -*- coding: utf-8 -*-
u"""_zf116_docs.py —— ZF116 文档：贴图清单加一节 + 档案加变更行与 §4.84

并发环境（ZF111~ZF115 三条线同时在跑）⇒ 一律「定位 → 插入 → 立刻回读断言」，
绝不整份覆盖；插入点用**行首前缀**定位，避免与别人的改动打架。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
LIST = ROOT + r"\docs\贴图清单.md"
ARCH = ROOT + r"\docs\开发档案.md"

SECTION = u"""

## ZF116（0.11）：星璨钢胸甲 / 护腿 / 靴子（**星璨钢套装齐了**）

用户第二次说「又放了」—— 又是**图片**，没有音频。三件都在 `build/用户素材/`：

| 你的文件名 | 字节 | sha1(前12) | 落到哪 | 不透明像素 |
|---|---|---|---|---|
| `星璨钢胸甲.png` | 3260 | `87d52aa95f70` | `textures/item/star_steel_chestplate.png` | 138 |
| `星璨钢护腿.png` | 3072 | `98b513d2734e` | `textures/item/star_steel_leggings.png` | 103 |
| `星璨钢靴子.png` | 3195 | `db88fae1670d` | `textures/item/star_steel_boots.png` | 90 |

三件实测都是 **16×16 / 8 位 RGBA / 背景透明 / 半透明像素 0** ⇒ **原字节复制**，一个像素没重编码
（与 ZF110 头盔同一套做法）。字符画肉眼核过：胸甲是护肩+躯干、护腿是两条腿管+腰带、靴子是两只靴，
和头盔那张同一套紫蓝配色。

- 三个模型 `layer0` 从 `minecraft:item/iron_{chestplate,leggings,boots}` 改成
  `potato_s_t:item/star_steel_*`。
- **活体数字：还在借原版贴图的模型 12 → 9**。三处一起改（与 ZF110 同一套口径）：
  英文公告那句、`_zf71_verify.py` 的 `n_draw`、`_zf90_verify.py` 的三条断言；
  `docs/贴图清单.md` 重跑 `--plan` ⇒ 表头 **12 → 9**（手写段 21005 字符逐字符未变）。
- **星璨钢套装 4 件齐了**；钛合金那套 4 件仍在待画表里（还是借原版铁套）。

### ⚠ 本轮踩到的并发坑（见档案 §4.84）

同一棵树上 ZF111~ZF115 三条线在跑，`_zf71_verify.py` / `_zf90_verify.py` 这类**共用门**
随时可能被人改动。本轮给 `_zf90_verify.py` 打补丁时，有一条锚点**只差一个缩进空格**就没匹配上——
脚本按设计**报了"锚点 0 次"并停手**（没有瞎改），换成正则按「代码实质」替换才打上。
**结论：跨会话改共用文件，别用带缩进的整段字面量当锚点。**
"""

ROW = (
    u"| ZF116 | **新建 `zf116_pre`**（8 个改前件：`models/item/` 的 "
    u"`star_steel_{chestplate,leggings,boots}.json` + 英文公告 + `_zf71_verify.py` + "
    u"`_zf90_verify.py` + `docs/贴图清单.md` + `docs/开发档案.md`；逐份核哈希、失败 0） | "
    u"0.11：**星璨钢胸甲 / 护腿 / 靴子三件上线，星璨钢套装齐了**（用户原话「又放了宝~」）。"
    u"三件都是 **16×16 / 8 位 RGBA / 零半透明** ⇒ **原字节复制**（3260 / 3072 / 3195 B），"
    u"字符画核过形状（护肩+躯干 / 两条腿管+腰带 / 两只靴）；三个模型 `layer0` 从 "
    u"`minecraft:item/iron_*` 改成 `potato_s_t:item/star_steel_*`；**活体数字 12 → 9**（三处一起改："
    u"公告 / `_zf71_verify.py` / `_zf90_verify.py`），`docs/贴图清单.md` 重跑 `--plan` 表头 12 → 9 "
    u"（手写段 21005 字符逐字符未变）。⚠ 本轮是**并发环境**（ZF111~ZF115 三条线同时在跑）："
    u"给 `_zf90_verify.py` 打补丁时有一条锚点**只差一个缩进空格**就没匹配上，脚本按设计报"
    u"「锚点 0 次」并**停手**（没有瞎改），换成正则按「代码实质」替换才打上 —— 立为 §4.84 |\n"
)

PITFALL = u"""
### 4.84 【方法论】跨会话改**共用文件**：别拿"带缩进的整段字面量"当锚点（0.11 ZF116）

同一棵工作树上 ZF111~ZF115 三条线在跑，`_zf71_verify.py` / `_zf90_verify.py` / 四份 lang
这类**共用门**随时会被人动。ZF116 给 `_zf90_verify.py` 打三处补丁，前两处打上了，
第三处报「锚点出现 0 次（期望 1）」—— 脚本按设计**停手没改**（这一步是对的，值得表扬的那种失败），
但原因很气人：锚点里 `for n in (5, 6, 7, 13)` 的**续行缩进我数错了一个空格**。

**规矩**：

1. 改共用文件一律 **读 → 替换 → 立刻回读断言**，且**只替换唯一出现的那一处**；
   出现次数不等于 1 就**报错停手**，绝不"看着差不多就写回去"。ZF116 靠这条挡住了半成品。
2. **锚点要按「代码实质」取，不要按排版取**：能匹配
   `for n in \\(5, 6, 7, 13\\)` 就不要匹配整段带换行与缩进的字面量。
   同理，断言里那句中文标签只认 `u"英文公告里不再写 5/6/7/13 models"` 这一段就够。
3. 这条和 §4.6「编辑前必须做锚点唯一性 + 作用域双检」是同一族，但**多会话场景下更狠**：
   单会话里锚点不匹配通常是我抄错了；**多会话里锚点不匹配还可能是别人刚改过** ——
   所以"停手 + 报出来"比"猜一个更宽松的匹配改下去"安全得多（后者会静默改错别人的东西）。
4. 本轮真发生过"别人插在我前面"：变更表里 ZF111/112/113/115 四行**插在了我的 ZF110 行之前**
   （表尾顺序乱了但不影响功能）。**追加自己那行时按「行首前缀」定位，别按行号。**
"""


def insert_after_line_prefix(path, prefix, payload, label, eol):
    raw = io.open(path, encoding="utf-8").read()
    idx = raw.find(prefix)
    if idx < 0:
        print(u"  !! %s：找不到行首前缀「%s」，停手" % (label, prefix[:40]))
        return None
    if raw.count(prefix) != 1:
        print(u"  !! %s：前缀出现 %d 次，不唯一，停手" % (label, raw.count(prefix)))
        return None
    eolpos = raw.index(u"\n", idx) + 1
    return raw[:eolpos] + payload + raw[eolpos:]


def main():
    # ---------- 贴图清单：末尾追加一节 ----------
    raw = io.open(LIST, encoding="utf-8").read()
    if u"## ZF116（0.11）" in raw:
        print(u"  [幂等] 贴图清单已有 ZF116 小节")
    else:
        body = SECTION.replace(u"\r\n", u"\n")
        out = raw + body
        io.open(LIST, "w", encoding="utf-8", newline="\n").write(out)
        back = io.open(LIST, encoding="utf-8").read()
        ok = back.startswith(raw) and u"## ZF116（0.11）" in back
        print(u"  %s 贴图清单追加 ZF116 小节（%d -> %d 字节，纯追加）"
              % (u"[OK]" if ok else u"[!!]", len(raw.encode()), len(back.encode())))

    # ---------- 档案：变更行 ----------
    raw = io.open(ARCH, encoding="utf-8").read()
    if u"| ZF116 |" in raw:
        print(u"  [幂等] 档案已有 ZF116 变更行")
    else:
        got = insert_after_line_prefix(ARCH, u"| ZF110 |", ROW, u"变更行", u"\n")
        if got is None:
            return 1
        io.open(ARCH, "w", encoding="utf-8", newline="\n").write(got)
        print(u"  [OK] 档案变更表已插入 ZF116 行（追在 ZF110 行之后）")

    # ---------- 档案：§4.84 ----------
    raw = io.open(ARCH, encoding="utf-8").read()
    if u"### 4.84 " in raw:
        print(u"  [幂等] 档案已有 §4.84")
    else:
        anchor = u"### 4.83 "
        if raw.count(anchor) != 1:
            print(u"  !! §4.83 锚点出现 %d 次，停手" % raw.count(anchor))
            return 1
        # 插在 §4.83 小节**之前**（紧挨着它），保持 4.8x 连续
        idx = raw.index(anchor)
        out = raw[:idx] + PITFALL.strip(u"\n") + u"\n\n" + raw[idx:]
        io.open(ARCH, "w", encoding="utf-8", newline="\n").write(out)
        back = io.open(ARCH, encoding="utf-8").read()
        ok = u"### 4.84 " in back and u"### 4.83 " in back and u"| ZF116 |" in back
        print(u"  %s 档案插入 §4.84 并在回读里确认 4.83 / ZF116 行都在" % (u"[OK]" if ok else u"[!!]"))
        if not ok:
            return 1
    print(u"\n  done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
