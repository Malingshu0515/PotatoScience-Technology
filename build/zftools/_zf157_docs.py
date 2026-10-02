# -*- coding: utf-8 -*-
r"""_zf157_docs.py —— ZF157 文档：贴图清单加一节 + 档案加变更行 + 英文公告加一条"""
import io, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r'E:\PotatoST'
LIST = os.path.join(ROOT, 'docs', '贴图清单.md')
ARCH = os.path.join(ROOT, 'docs', '开发档案.md')
ANN = os.path.join(ROOT, 'docs', 'UpdateAnnouncement_EN.md')

SEC = u"""
---

## ZF157（0.13）钛合金套四件背包图标 + 热力金属新贴图

**用户原话**：「材质加一下喂 宝宝 你上回把钛合金装备和热力金属新材质都遗漏了」

| 素材 | 字节 | sha1 | 落位 | 说明 |
|---|---|---|---|---|
| `钛合金头盔_001.png` | 2901 | `207c9d45eae3` | `textures/item/titanium_alloy_helmet.png` | ✅ **新建**（模型原先借 `minecraft:item/iron_helmet`） |
| `钛合金胸甲_001.png` | 3106 | `4626b3ad5ad9` | `textures/item/titanium_alloy_chestplate.png` | ✅ **新建**（原先借 `minecraft:item/iron_chestplate`） |
| `钛合金护腿_001.png` | 3039 | `0afa47a216e6` | `textures/item/titanium_alloy_leggings.png` | ✅ **新建**（原先借 `minecraft:item/iron_leggings`） |
| `钛合金靴子_001.png` | 2878 | `b21e9b5b6a27` | `textures/item/titanium_alloy_boots.png` | ✅ **新建**（原先借 `minecraft:item/iron_boots`） |
| `热力金属_001.png` | 3080 | `b01520311042` | `textures/item/thermal_metal.png` | ✅ **替换**（顶掉一张 160×160 程序生成占位色块） |

- **五份素材都是 16×16 / 8 位 RGBA / 零半透明** ⇒ 原字节复制。
- **凭什么断定是「背包图标」而不是「盔甲层」**（`_zf157_probe.py` 真解码）：四件的 alpha 掩码不透明像素
  78 / 138 / 104 / 88，**头盔对 ZF116 那张星璨钢头盔图标的 IoU = 0.9744**（同一族盔甲图标），
  而盔甲层贴图是 **64×32**、四件之间尺寸根本对不上。热力金属 135 像素对**银锭**的 IoU = **1.0000** ⇒ 锭形。
- ⚠ **穿在身上那两张没动**：`textures/models/armor/titanium_alloy_layer_1.png` / `_layer_2.png`
  （ZF106 那轮由用户给的 `钛合金套装.png` 定尺写出，1077 B ×2）**一个字节没改** ——
  这轮用户给的是**物品栏图标**，两者是两回事。
- 结果：待画 **13 → 9**（四件钛合金出列）、`TextureCheck` 警告 **24 → 23**（那张 160×160 占位自带的尺寸警告消失）。
"""
ROW = (u"| ZF157 | **新建 `zf157_pre`**（10 份改前件：`textures/item/thermal_metal.png` + 四个钛合金物品模型 "
       u"+ 三份文档 + `_zf90_verify.py` + `_来源凭据.json`；⚠ **备份循环写错了基目录**（`os.path.join(ROOT, rel)` 只对 `docs/` 与 `build/` 成立，"
       u"资源类的 rel 是**相对 ASSET** 的）⇒ 五份改前件当场被判 MISSING、**一份都没抄**（脚本打了 `[MISS]`，没吞）；"
       u"补法**可验证**：用 **git HEAD** 取回，取回的 `thermal_metal.png` sha1 = `e827c8325d64…` / 728 B，"
       u"**与改前实测逐位一致**，四个模型里仍是 `minecraft:item/iron_*`（见 `_zf157_finish.py`）） | "
       u"0.13：**钛合金套四件背包图标 + 热力金属新贴图**（用户原话「材质加一下喂 宝宝 你上回把钛合金装备和热力金属新材质都遗漏了」）。"
       u"① 五份素材**真解码**全是 16×16 / 8 位 RGBA / **零半透明**；**身份靠掩码判**：四件盔甲不透明像素 78/138/104/88、"
       u"头盔对 ZF116 那张星璨钢头盔**图标**的 IoU **0.9744** ⇒ 是**背包图标**（盔甲层是 64×32，对不上）；"
       u"热力金属 135 像素对**银锭**的 IoU **1.0000** ⇒ 锭形物品图；"
       u"② 四件图标**原字节复制**上线 + 四个模型 `layer0` 从 `minecraft:item/iron_*` 改成 `potato_s_t:item/titanium_alloy_*`"
       u"（每处旧值**恰好命中 1 次**、`parent` 一个字节没动）⇒ **待画 13 → 9**；"
       u"③ `thermal_metal.png` 顶掉一张 **160×160 程序生成占位色块**（模型本来就指向自己 ⇒ 一个字节没动）⇒ "
       u"`TextureCheck` 警告 **24 → 23**；④ ⚠ **穿在身上那两张**（`models/armor/titanium_alloy_layer_1/2.png`，ZF106 由 `钛合金套装.png` 定尺写出、"
       u"两张逐字节相同）**本轮一个字节没动** —— 用户给的是图标，不是盔甲层；"
       u"⑤ ⚠ 立 **§4.166**：备份循环的**基目录**与那条 `check(True, …)`（**永远为真的断言**，§4.17）两处已修；"
       u"⑥ 凭据 48 → **53** 条（五条纯追加，先证明「读进来再原样写回」与盘上逐字节相同才动笔） | 见 §9 |\n")

ANN_ENTRY = u"""
## New in 0.13 ZF157 - Titanium armour icons and a new Thermal Metal texture

- **The four titanium armour pieces have their own inventory icons at last.** They used to borrow
  vanilla's iron armour textures (`minecraft:item/iron_helmet` and friends), so a full titanium set
  looked exactly like iron in the inventory and in item frames. All four models now point at their
  own 16x16 textures, copied byte-for-byte from the art you supplied.
- **Thermal Metal has a redrawn texture.** The old one was a 160x160 program-generated colour block
  that the game squashed into a 16x16 square; the new one is drawn at 16x16 and matches the shape of
  our other ingots exactly (alpha-mask overlap 1.0000).
- **The worn-armour art is untouched** - `models/armor/titanium_alloy_layer_1.png` and `_layer_2.png`
  are exactly as they were. What arrived this round were inventory icons, which are a different file.
- The "still borrowing vanilla textures" list is down to **9** entries (from 13), and TextureCheck
  warnings down to 23 (from 24).
"""


def read(p):
    return io.open(p, encoding='utf-8').read()


def write(p, t):
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t)


def main():
    fails = []
    # ① 贴图清单：纯追加一节 + 给尾部那条已经过时的手写行加一个指针
    raw = read(LIST)
    if u'## ZF157（0.13）' in raw:
        print(u'  [幂等] 清单已有 ZF157 小节')
    else:
        if not raw.endswith(u'\n'):
            raw += u'\n'
        write(LIST, raw + SEC)
        back = read(LIST)
        ok = back.startswith(raw) and u'## ZF157（0.13）' in back
        print(u'  %s 贴图清单纯追加（%d -> %d 字节）' % (u'[OK]' if ok else u'[!!]',
                                                     len(raw.encode()), len(back.encode())))
        if not ok:
            fails.append(u'清单追加失败')
    # 尾部那条"钛合金套的背包图标 —— 没有这张文件"现在是假话了，原地补一个指针（判据：锚点 1 次）
    raw = read(LIST)
    old = u'| **没有这张文件** —— 8 个模型直接写 `minecraft:item/iron_*`（借原版铁套），游戏里显示的就是铁套图标 |'
    new = u'| ~~没有这张文件~~ ⇒ **ZF157 已上线**（见文末 ZF157 节；那条历史备注写在当年，留档不改字，只加这个指针） |'
    if new in raw:
        print(u'  [幂等] 那条历史备注已有 ZF157 指针')
    else:
        n = raw.count(old)
        print(u'  %s 历史备注锚点命中 %d 次' % (u'[OK]' if n == 1 else u'[!!]', n))
        if n == 1:
            write(LIST, raw.replace(old, new))
        else:
            fails.append(u'历史备注锚点命中 %d 次' % n)

    # ② 档案：变更表插一行
    raw = read(ARCH)
    if u'| ZF157 |' in raw:
        print(u'  [幂等] 档案已有 ZF157 变更行')
    else:
        lines = raw.split(u'\n')
        idx = None
        for i, ln in enumerate(lines):
            if ln.startswith(u'| ZF'):
                idx = i
        if idx is None:
            fails.append(u'找不到变更表')
            print(u'  [!!] 找不到变更表，停手')
        else:
            lines.insert(idx + 1, ROW.rstrip(u'\n'))
            write(ARCH, u'\n'.join(lines))
            print(u'  [OK] 变更表已插入 ZF157 行（追在 %s 之后）' % lines[idx][:12])

    # ③ 英文公告：纯追加
    raw = read(ANN)
    if u'ZF157' in raw:
        print(u'  [幂等] 英文公告已有 ZF157 条目')
    else:
        if not raw.endswith(u'\n'):
            raw += u'\n'
        write(ANN, raw + ANN_ENTRY)
        back = read(ANN)
        ok = back.startswith(raw) and u'ZF157' in back
        print(u'  %s 英文公告纯追加（%d -> %d 字节）' % (u'[OK]' if ok else u'[!!]',
                                                    len(raw.encode()), len(back.encode())))
        if not ok:
            fails.append(u'英文公告追加失败')

    print(u'  ---- 回读 ----')
    L = read(LIST); A = read(ARCH); N = read(ANN)
    for label, cond in ((u'清单 ZF157 小节', u'## ZF157（0.13）' in L),
                        (u'清单 待画表头 = 9', u'## 待画（9 个' in L),
                        (u'清单 历史备注指针', u'ZF157 已上线' in L),
                        (u'档案 ZF157 行', u'| ZF157 |' in A),
                        (u'英文公告 ZF157 条', u'ZF157' in N)):
        print(u'  %s %s' % (u'[OK]' if cond else u'[!!]', label))
        if not cond:
            fails.append(label)
    print(u'失败项 = %d' % len(fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
