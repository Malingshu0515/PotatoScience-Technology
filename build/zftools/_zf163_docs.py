# -*- coding: utf-8 -*-
r"""_zf163_docs.py —— ZF163 文档（贴图清单节 / 档案 §5 行 + §4.168 / 英文公告）+ 终检"""
import io, os, re, sys, json, hashlib, subprocess
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\PotatoST'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
DOCS = os.path.join(ROOT, 'docs')
LIST = os.path.join(DOCS, u'贴图清单.md')
ARCH = os.path.join(DOCS, u'开发档案.md')
ANN = os.path.join(DOCS, 'UpdateAnnouncement_EN.md')
TEXB = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'textures', 'block')
BTEXB = os.path.join(ROOT, 'build', 'resources', 'main', 'assets', 'potato_s_t', 'textures', 'block')
fails = []
def check(ok, msg):
    print(('  [OK]   ' if ok else '  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)
def read(p):
    return io.open(p, encoding='utf-8').read()
def write(p, t):
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t)

SEC = u"""
---

## ZF163（0.13）流体动画改成「原版水那样」：不再行军，改成液面涌动

**用户原话**：「这个流体动画有点怪 你看看能不能改成原版水那样子的」

**先把原版水量了一遍**（`_zf163_extract.py`，从真 `client.jar` 现抠；原版 `water_still.png` 是
**4 位调色板**，本工程的 `PngRecolor` 只吃 8 位，所以那一步用带 Pillow 的运行时跑）：

| | 原版 `water_still` | 我们原来的做法（ZF132/ZF135） |
|---|---|---|
| 帧数 / frametime | **32 帧 / 2** | 16 帧 / 3 |
| 尺寸 | 16×512 | 16×256 |
| 相邻帧最佳竖向位移 | **恒 0 行（它根本不滚动，是原地亮暗）** | 每帧整体下滚 **1 行** |
| 逐帧变化像素比 | **11.0%** | **49% ~ 98%** |
| 平均 \\|ΔRGB\\|（改动的像素） | 16.2 | —— |

结论：**"怪"不是参数问题，是做法问题** —— 横条纹底图上"整张往下滚"，逐帧变化量是原版水的
5~9 倍，看起来就是一面墙在走。原版 `water_flow` 则是 **32×1024 / 32 帧 / 内容每帧上移 1 行**
（32 宽上量到 31 行）。

**改了 30 张**（15 种流体 × `_still` / `_flow`）：

- **`_still`**：**32 帧 / frametime 2 / 16×512**，内容改成**亚像素驻波** ——
  每一列整体升降 `w(x,t) = 2·cos(2πx/16)·sin(2πt/32)` 行，行间线性插值。
  ⇒ **t=0 位移处处为 0**（静止时就是你给的**原始贴图**，逐字节相同）、
  幅度 ≤ 2 行、相邻列差 ≤ 0.8 行（相干）、**32 帧两两不同**、32 帧精确闭环。
- **`_flow`**：**16 帧 / frametime 缺省（与原版一致）**，内容**每帧上移 1 行**
  （原来是下滚 2 行）⇒ 与原版水**同方向、同速度**（1 像素/刻；原版靠 32 高的底图铺 32 帧，
  我们底图只有 16 高 ⇒ 帧数取 16，速度一样、周期减半）。

**试了四版，账都留着**（`_zf163_*.py` / `_zf163_preview*.png`）：

| 版本 | 做法 | 为什么否掉 |
|---|---|---|
| A | 直接搬原版水的逐像素亮暗掩码 | 那掩码是**为水自己那张图案设计的**，落在横条纹底图上变成**互不相关的雪花噪点** |
| B | 行波 `round(2 sin(2π(x/16 − t/32)))` | 好看，但 **t=0 位移不为 0** ⇒ 静止时原始贴图是变形的 |
| C | 驻波 `round(2 cos·sin)`（整数行） | t=0 归零了，但整数位移**只有 5 档** ⇒ **32 帧里 19 对相邻帧逐字节相同**，一顿一顿 |
| **D（现行）** | 同样的驻波，位移取**实数** + 行间线性插值 | 全过 |

**常驻门 `_zf135_fluidcheck.py` 换成更严的一套**（是换严，不是放宽）：

- 老「**首末帧**必须不同」⇒ 新「**逐对相邻帧**都必须有变化」（C 版就是这么被抓出来的）；
- 新增「still **每个像素**必须等于底图按亚极点公式位移后的插值」；
- 新增「still **第 0 帧**必须与底图逐像素相同（t=0 位移为 0）」；
- 新增「flow 第 t 帧必须**精确**等于底图第 (y+t) 行」；
- 接缝四条（比值 + 绝对差）照旧。
"""
ROW = (u"| ZF163 | **新建 `zf163_pre`**（60 份改前件 = 30 张贴图 + 30 份 mcmeta，逐份核 sha1 + 回读；"
       u"另存 `_zf135_fluidcheck.py` 与三份文档）；⚠ **同一轮里我自己误删过 `_zf163_apply.py`**"
       u"（一条写错的 `Remove-Item` 打到了它自己）⇒ 重建为 `_zf163_apply2.py` 并就地记账 | "
       u"**0.13：流体动画改成「原版水那样」**（用户原话「这个流体动画有点怪 你看看能不能改成原版水那样子的」）。"
       u"① **先量原版，再动手**（`_zf163_extract.py`，真 `client.jar`；原版 `water_still.png` 是 **4 位调色板** ⇒ 用带 Pillow 的运行时跑）："
       u"原版 still = **32 帧 / frametime 2 / 16×512**，而且**它不滚动** —— 相邻帧最佳竖向位移**恒 0 行**、"
       u"逐帧变化像素 **11.0%**、平均 |ΔRGB| 16.2；原版 flow = 32×1024 / 32 帧 / **每帧上移 1 行**（32 宽量到 31 行）。"
       u"而我们的老做法（ZF132/ZF135）是**整张下滚 1 行/帧、16 帧、frametime 3** ⇒ 逐帧变化像素 **49%~98%**，"
       u"是原版的 5~9 倍 —— **「怪」不是参数问题，是做法问题**；"
       u"② **四版试错**：A 搬原版亮暗掩码（在横条纹上=雪花噪点）/ B 行波（**t=0 位移不为 0** ⇒ 静止时原始贴图是变形的）/ "
       u"C 整数驻波（t=0 归零，但整数位移只有 5 档 ⇒ **32 帧里 19 对相邻帧逐字节相同**，一顿一顿）/ **D 亚像素驻波（现行）**；"
       u"③ D 的做法：still = 32 帧 / frametime 2 / 16×512，每列整体升降 `w(x,t)=2·cos(2πx/16)·sin(2πt/32)` 行、**行间线性插值** "
       u"⇒ **t=0 位移处处为 0**（第 0 帧与原始贴图**逐字节相同**）、幅度 ≤2 行、相邻列差 ≤0.8 行、**32 帧两两不同**、精确闭环；"
       u"flow = 16 帧 / frametime 缺省、**每帧上移 1 行**（与原版同方向同速度：1 像素/刻）；"
       u"④ **常驻门换成更严的一套**：老「首末帧必须不同」⇒ 新「**逐对相邻帧**都必须有变化」（C 版就是这么被抓出来的）、"
       u"新增「still 每个像素 == 亚像素公式插值」「still 第 0 帧 == 底图」「flow 第 t 帧 == 底图第 (y+t) 行」，接缝四条照旧；"
       u"⑤ 顺手修了 v2 门里 `sample()` 的入参类型（把「行列表」当扁平缓冲传进去 ⇒ TypeError），模板与盘上的门一起改；"
       u"⑥ 立 **§4.168** | 见 §9 |\n")

PIT = u"""
### 4.168 【做法雷】"动画有点怪"先别调参数 —— 先量**原版的同类东西**在做什么；以及**量化**只有量出来才看得见（0.13 ZF163）

用户一句"流体动画有点怪"，我原来的做法是**整张往下滚 1 行/帧**（16 帧 / frametime 3）。
把原版 `water_still` 从真 jar 里量完才看清：**原版 still 根本不滚动** ——
相邻帧最佳竖向位移**恒 0 行**（它是原地亮暗），逐帧只改 **11%** 的像素；
我们那一版改 **49%~98%**，是它的 5~9 倍。**参数（帧数 / frametime / 步长）怎么调都救不了**，
因为"行军"和"原地涌"是两种做法。

**试错账**（四版，全是量出来才否掉的，不是看出来的）：
  · **A** 搬原版水的逐像素亮暗掩码 ⇒ 那掩码是**为水自己那张图案设计的**，落在横条纹底图上
    就是**互不相关的雪花噪点**。判据得再准也没用，**相干**才是"像水"的关键；
  · **B** 行波 `round(2 sin(2π(x/16 − t/32)))` ⇒ 好看，但 **t=0 位移不为 0**：
    等于"静止时玩家看到的不是你给的原始贴图，而是已经起了浪的样子"——
    这一条是**判据（第 t 帧 == 底图位移公式量）逼出来的**，肉眼在预览图上看不出来；
  · **C** 驻波 `round(2 cos·sin)`（整数行）⇒ t=0 归零了，但 `round()` 只有 **5 档取值**
    ⇒ **32 帧里 19 对相邻帧逐字节相同**（"逐对相邻帧都必须有变化"这条判据抓的）；
  · **D** 同样的驻波、位移取**实数** + 行间线性插值 ⇒ 全过。

**规矩**：
  ① 用户说"某样东西怪"，先**把原版同类东西量出来**（帧数 / frametime / 相邻帧位移 / 逐帧变化密度），
     再改自己的做法 —— 别在旧做法上调参数；
  ② **量化**是隐形的杀手：整数位移在 16 高的图上一共就那么几档，
     "32 帧"里可能只有 5 个**真正不同**的状态。所以判据必须是"**逐对相邻帧都要有变化**"，
     而不是"首末帧不同"（后者对 C 版完全无感）；
  ③ 位移类动画要**两个方向都钉住**：幅度（≤ 某个上界）与**相干性**（相邻列差 ≤ 某个上界），
     否则"每列随机跳"也能满足"每帧都不一样"。
"""

ANN_TEXT = u"""
## New in 0.13 ZF163 - Fluid animations now move like vanilla water

- **The still textures no longer march.** Every fluid used to scroll its whole 16x16 tile downwards
  one row per frame. Measured against vanilla, that was **5-9x more change per frame than water**
  (49-98% of pixels per frame, against water's 11%) - a stripe pattern walking down a wall, which is
  exactly what looked wrong.
- **What vanilla actually does** (measured out of the real client jar): `water_still` is **32 frames,
  `frametime` 2**, and it **does not scroll at all** - the best vertical shift between neighbouring
  frames is 0 rows; it shimmers in place. `water_flow` is 32 frames of a 32x32 tile scrolling **up**
  one row per frame.
- **Still fluid is now a sub-pixel standing wave**: each column rises and falls by
  `2*cos(2*pi*x/16)*sin(2*pi*t/32)` rows, interpolated between rows, over **32 frames at
  `frametime` 2**. The displacement is **exactly zero at frame 0**, so the art you supplied is shown
  untouched at rest; the surface heaves in place with no net drift, and all 32 frames differ.
- **Flowing fluid now scrolls up one row per frame** (16 frames, default frametime) - the same
  direction and the same speed as vanilla water's flow, instead of scrolling down at half speed.
- Three earlier approaches were tried and thrown away, with the measurements kept in the notes:
  transplanting vanilla water's pixel mask (uncorrelated noise on our stripe art), a travelling wave
  (non-zero displacement at frame 0, so the art was distorted at rest), and an integer standing wave
  (**19 of 31 neighbouring frames were byte-identical** - it stuttered).
"""

print(u'===== ① 文档 =====')
raw = read(LIST)
if u'## ZF163' in raw:
    print(u'  [幂等] 清单已有 ZF163 小节')
else:
    if not raw.endswith(u'\n'):
        raw += u'\n'
    write(LIST, raw + SEC)
    check(u'## ZF163' in read(LIST), u'贴图清单加了一节')
raw = read(ARCH)
if u'| ZF163 |' in raw:
    print(u'  [幂等] 档案已有 ZF163 行')
else:
    lines = raw.split(u'\n')
    idx = max(i for i, l in enumerate(lines) if l.startswith(u'| ZF'))
    lines.insert(idx + 1, ROW.rstrip(u'\n'))
    write(ARCH, u'\n'.join(lines))
    check(u'| ZF163 |' in read(ARCH), u'档案变更表插入 ZF163 行（追在 %s 之后）' % lines[idx][:10])
raw = read(ARCH)
nums = [int(m.group(1)) for m in re.finditer(u'^### 4\\.(\\d+)', raw, re.M)]
nxt = max(nums) + 1
check(u'### 4.%d ' % nxt not in raw, u'§4.%d 这个号没被占（现最大 4.%d）' % (nxt, max(nums)))
lines = raw.split(u'\n')
i = next(k for k, l in enumerate(lines) if l.startswith(u'### 4.%d ' % (nxt - 2)))
j = next(k for k in range(i + 1, len(lines)) if lines[k].startswith(u'## '))
write(ARCH, u'\n'.join(lines[:j]) + PIT + u'\n' + u'\n'.join(lines[j:]))
check(u'### 4.%d ' % nxt in read(ARCH), u'§4.%d 已插入' % nxt)
raw = read(ANN_PATH)
if u'ZF163' in raw:
    print(u'  [幂等] 英文公告已有 ZF163 条')
else:
    if not raw.endswith(u'\n'):
        raw += u'\n'
    write(ANN_PATH, raw + ANN_TEXT)
    check(u'ZF163' in read(ANN_PATH), u'英文公告加了一条')

print()
print(u'===== ② 终检：产物 / 四门 =====')
n_ok = 0
for f in sorted(os.listdir(TEXB)):
    if not (f.endswith('_still.png') or f.endswith('_flow.png')):
        continue
    a = os.path.join(TEXB, f)
    b = os.path.join(BTEXB, f)
    ha = hashlib.sha1(open(a, 'rb').read()).hexdigest()
    hb = hashlib.sha1(open(b, 'rb').read()).hexdigest() if os.path.exists(b) else 'MISSING'
    if ha == hb:
        n_ok += 1
check(n_ok == 30, u'build 产物里 30 张流体贴图与源逐字节一致（实测 %d）' % n_ok)
for g in ['TextureCheck.py', 'ModelCheck.py', 'JsonCheck.py', '_zf135_fluidcheck.py']:
    r = subprocess.run([sys.executable, os.path.join(TOOLS, g)], cwd=ROOT,
                       env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode('utf-8', 'replace')
    tail = [l for l in out.splitlines() if u'失败' in l or u'结论' in l or u'非法' in l or u'最大比值' in l]
    print(u'  %-24s rc=%d  %s' % (g, r.returncode, u' | '.join(tail[-2:])))
    check(r.returncode == 0, u'%s rc=0' % g)

print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
