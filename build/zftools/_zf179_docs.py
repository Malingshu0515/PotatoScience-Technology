# -*- coding: utf-8 -*-
r"""_zf179_docs.py —— ZF179 文档：贴图清单重跑 --plan + 新节 + 档案行 + §4.165 第三次 + 英文公告"""
import io, os, re, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
DOCS = os.path.join(ROOT, 'docs')
LIST = os.path.join(DOCS, u'贴图清单.md')
ARCH = os.path.join(DOCS, u'开发档案.md')
ANN = os.path.join(DOCS, 'UpdateAnnouncement_EN.md')
fails = []
def check(ok, msg):
    print((u'  [OK]   ' if ok else u'  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)
def read(p):
    return io.open(p, encoding='utf-8').read()
def write(p, t):
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t)

print(u'===== ① 重跑 TextureCheck --plan（让"已有"表把这两件收进去）=====')
r = subprocess.run([sys.executable, os.path.join(TOOLS, 'TextureCheck.py'), '--plan'], cwd=ROOT,
                   env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
o = r.stdout.decode('utf-8', 'replace')
io.open(os.path.join(TOOLS, '_zf179_plan.txt'), 'w', encoding='utf-8', newline='\n').write(o)
check(r.returncode == 0, u'TextureCheck --plan rc=0')
check(u'手写部分原样接回' in o, u'手写段原样接回（我的 ZF157/163/170/172 节不会被冲掉）')
t = read(LIST)
check(u'## 待画（9 个' in t, u'清单待画表头 = 9')
check(u'`gravity_device.png`' in t and u'`ore_detector.png`' in t, u'"已有"表里出现这两件')

NOTE = (u"\n> ⚠ **本轮的补账**：`_zf179_apply.py` 的备份清单里，资源路径写成了相对 ASSET 的写法，"
        u"而拼接是按仓库根走的（**§4.165 第三次**）⇒ 两个物品模型没抄进 `zf179_pre`；"
        u"已从 **git HEAD 逐字节取回**（那两件是别的线 16:51 刚加的、已在 HEAD 里）并核 sha1。\n")
SEC = u"""
---

## ZF179（0.13）引力装置 + 矿物探测器：两件物品不再借原版了

**用户原话**：「我把引力装置和矿物探测的材质放素材了」，随后「引力装置高清点行不行 要不然看不出来是黑洞了」

| 素材 | 字节 | sha1 | 落位 | 说明 |
|---|---|---|---|---|
| `矿物探测器_001.png` | 3221 | `68439f658c8e` | `textures/item/ore_detector.png` | ✅ **新建**（模型原先借 `minecraft:item/compass`）—— 16x16 **原字节复制** |
| `引力装置_001.png` | 17455 | `8c283a8272b7` | `textures/item/gravity_device.png` | ✅ **新建**（原先借 `minecraft:item/ender_eye`）—— 128x128 **定尺成 64x64** |

- **待画 11 → 9**（这两件出列；11 是别的线 16:51 加这两件时涨上去的，本轮落回 9）。
- **尺寸试了三档，都留了档可以复看**：

| 定尺 | 结果 | 留档 |
|---|---|---|
| 128→**16**（8:1） | ❌ 造型被压坏：左尖角只剩**孤立 1 个像素**、白环变疙瘩 | `_zf179_reject16.png` |
| 128→**32**（4:1） | ⭕ 造型完整，但用户说「看不出来是黑洞」 | `_zf179_keep32.png` |
| 128→**64**（2:1） | ✅ **采用**（879 个实体像素、零半透明） | 在用 |
| 128 原样 | 备着（要最极致的说一声） | `_zf179_alt128.png` |

- **为什么"高清"真的有用**：物品贴图固定画在 **16 逻辑像素**的四边形上 ——
  界面缩放 2 时 32x32 才 1:1、**64x64 会被放大 2 倍**；缩放 4 时 64x64 才 1:1
  ⇒ 贴图分辨率越高，**高缩放 / 拿在手里越清楚**（低缩放时靠 mipmap 平滑）。
  `TextureCheck` 的规则是「16~256 的 2 的幂正方形」都放行 ⇒ **64 不产生警告**。
- **定尺算法两个讲究**：**只对不透明像素求平均**（覆盖率加权 ⇒ 不把透明区的黑边混进来）
  ＋ **alpha 二值化**（块覆盖率 >= 50% 才算实体）⇒ 成品仍是**零半透明**，与工程其余贴图一致。
- 两个模型 `layer0` 改成指向自己（`ender_eye` → `potato_s_t:item/gravity_device`、
  `compass` → `potato_s_t:item/ore_detector`），`parent` 一个字节没动。
- 凭据 59 → **61** 条。
"""
t = read(LIST)
if u'## ZF179（0.13）' in t:
    print(u'  [幂等] 清单已有 ZF179 节')
else:
    if not t.endswith(u'\n'):
        t += u'\n'
    write(LIST, t + NOTE + SEC)
    check(u'## ZF179（0.13）' in read(LIST), u'贴图清单加了 ZF179 节')

print()
print(u'===== ② 档案：ZF179 行 + §4.165 第三次 =====')
ROW = (u"| ZF179 | **新建 `zf179_pre`**（8 份备份 + 2 份「改前不存在」；⚠ **两个物品模型没抄到** —— "
       u"备份清单又把资源路径写成相对 ASSET（**§4.165 第三次**）⇒ 已从 **git HEAD 逐字节取回**并核 sha1） | "
       u"0.13：**引力装置 + 矿物探测器两件物品的贴图**（用户原话「我把引力装置和矿物探测的材质放素材了」，"
       u"随后「引力装置高清点行不行 要不然看不出来是黑洞了」）。"
       u"① 两件都是**物品**（`ModItems.java:849 ore_detector` / `:854 gravity_device`），"
       u"原先分别借 `minecraft:item/compass` 与 `minecraft:item/ender_eye`；"
       u"② `矿物探测器_001.png` = 16x16 / 零半透明 ⇒ **原字节复制**；"
       u"`引力装置_001.png` = **128x128 / 3309 色** ⇒ 要定尺；"
       u"③ **尺寸试了三档**：128→16（8:1）造型被压坏（左尖角只剩孤立 1 像素，留档 `_zf179_reject16.png`）、"
       u"128→32（4:1）完整但用户说看不出来是黑洞（留档 `_zf179_keep32.png`）、**采用 128→64（2:1）**"
       u"（879 个实体像素、零半透明）；另备 128 原样一份；"
       u"④ **为什么 64 不违规**：`TextureCheck` 放行「16~256 的 2 的幂正方形」；而且物品贴图固定画在 16 逻辑像素的"
       u"四边形上 ⇒ 界面缩放 4 时 64x64 才 1:1、缩放 2 时它被放大 2 倍 ⇒ **分辨率越高越清楚**；"
       u"⑤ 定尺算法：只对不透明像素求平均（覆盖率加权）＋ alpha 二值化（覆盖率 >= 50%%）⇒ 成品零半透明；"
       u"⑥ 两个模型 `layer0` 改指自己、`parent` 未动；凭据 59 → **61** 条；待画 **11 → 9**（落回原值） | 见 §4.165 / §9 |\n")
t = read(ARCH)
if u'| ZF179 |' in t:
    print(u'  [幂等] 档案已有 ZF179 行')
else:
    lines = t.split(u'\n')
    idx = max(i for i, l in enumerate(lines) if l.startswith(u'| ZF'))
    lines.insert(idx + 1, ROW.rstrip(u'\n'))
    write(ARCH, u'\n'.join(lines))
    check(u'| ZF179 |' in read(ARCH), u'档案变更表插入 ZF179 行（追在 %s 之后）' % lines[idx][:10])

t = read(ARCH)
THIRD = (u"\n**第 3 次（0.13 ZF179）**：`_zf179_apply.py` 的备份清单里我又把资源路径写成相对 ASSET 的写法 —— "
         u"两个物品模型没抄到（其中一个是别的线当天下午刚加的，**差点就没有改前件**）。"
         u"这一次是那句 `check(len([l for l in lines if u'MISSING' not in l]) == 10)` 报的红，"
         u"取回仍走 git HEAD + sha1 逐位核对。\n\n"
         u"⇒ **规矩收紧（第三次了，写成硬规矩）**：**备份清单里的每条路径一律写成「仓库相对」的完整路径**"
         u"（`src/main/resources/…` 从头写起），**不许在清单里出现相对资源根/相对模块根的写法**，"
         u"这样拼接永远只有一种口径（`os.path.join(ROOT, rel)`），也就没有「这份 rel 是相对谁的」这个问题。\n")
if u'第 3 次（0.13 ZF179）' in t:
    print(u'  [幂等] §4.165 已记过第 3 次')
else:
    lines = t.split(u'\n')
    i = next((k for k, l in enumerate(lines) if l.startswith(u'### 4.165 ')), None)
    check(i is not None, u'找到 §4.165')
    if i is not None:
        j = next((k for k in range(i + 1, len(lines)) if lines[k].startswith(u'### ') or lines[k].startswith(u'## ')), None)
        check(j is not None, u'找到这一节的结束边界')
        if j is not None:
            while j - 1 > i and lines[j - 1].strip() == u'':
                j -= 1
            write(ARCH, u'\n'.join(lines[:j]) + THIRD + u'\n'.join(lines[j:]))
            check(u'第 3 次（0.13 ZF179）' in read(ARCH), u'§4.165 已补记第 3 次')

print()
print(u'===== ③ 英文公告 =====')
t = read(ANN)
EN = u"""
## New in 0.13 ZF179 - the Gravity Device and the Ore Detector get real textures

- **The Ore Detector** no longer borrows vanilla's compass: its own 16x16 texture is copied in
  byte-for-byte. **The Gravity Device** no longer borrows the Eye of Ender, and its texture was
  supplied at **128x128** - an item is drawn on a 16-pixel quad, so it had to be rescaled.
- **Sizes were tried and measured, not guessed.** Rescaling to 16x16 (8:1) wrecked the silhouette -
  the left jet came out as a single stray pixel, so the black hole was unrecognisable. 32x32 (4:1)
  held the shape but was still not obvious. The shipped version is **64x64 (2:1)**, which keeps the
  accretion disk and both jets legible.
- **Why higher resolution helps here**: an item texture is always drawn on a 16-pixel quad, so at GUI
  scale 4 a 64x64 texture is 1:1 while a 32x32 one is stretched 2x. `TextureCheck` accepts any power
  of two from 16 to 256, so 64 is fine and produces no warning.
- The rescale averages **only opaque pixels** (coverage-weighted) and thresholds alpha at 50%
  coverage, so the result stays **fully hard-edged** (no semi-transparent pixels), like the rest of
  the mod. A 128x128 copy of the original is kept in the tools folder if you want it even sharper.
- The "still borrowing vanilla textures" list is back to **9** (it had briefly risen to 11 when these
  two items were added).
"""
if u'ZF179 - the Gravity Device' in t:
    print(u'  [幂等] 公告已有 ZF179 条')
else:
    if not t.endswith(u'\n'):
        t += u'\n'
    write(ANN, t + EN)
    check(u'ZF179 - the Gravity Device' in read(ANN), u'英文公告已加 ZF179 条')

print()
print(u'===== ④ 终检 =====')
t = read(ARCH)
nums = [int(m.group(1)) for m in re.finditer(u'^### 4\\.(\\d+)', t, re.M)]
print(u'  §4 共 %d 个小节，最大 4.%d' % (len(nums), max(nums)))
for label, cond in ((u'清单 ZF179 节', u'## ZF179（0.13）' in read(LIST)),
                    (u'清单待画 = 9', u'## 待画（9 个' in read(LIST)),
                    (u'档案 ZF179 行', u'| ZF179 |' in t),
                    (u'§4.165 第 3 次', u'第 3 次（0.13 ZF179）' in t),
                    (u'英文公告 ZF179', u'ZF179 - the Gravity Device' in read(ANN))):
    check(cond, label)
print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
