# -*- coding: utf-8 -*-
r"""_zf170_finish.py —— ZF170 收尾：文档三处 + §4.165 记"第 2 次" + 门 + 产物 + 复核图"""
import io, os, re, sys, hashlib, subprocess
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png

ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
DOCS = os.path.join(ROOT, 'docs')
PRE = os.path.join(TOOLS, 'zf170_pre')
LIST = os.path.join(DOCS, u'贴图清单.md')
ARCH = os.path.join(DOCS, u'开发档案.md')
ANN_PATH = os.path.join(DOCS, 'UpdateAnnouncement_EN.md')
TEXB = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'textures', 'block')
BTEXB = os.path.join(ROOT, 'build', 'resources', 'main', 'assets', 'potato_s_t', 'textures', 'block')
BMODEL = os.path.join(ROOT, 'build', 'resources', 'main', 'assets', 'potato_s_t', 'models', 'block', 'filling_machine.json')
fails = []
def check(ok, msg):
    print(('  [OK]   ' if ok else u'  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)
def read(p):
    return io.open(p, encoding='utf-8').read()
def write(p, t):
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t)

SEC = u"""
---

## ZF170（0.13）饮料灌装机三面新材质（侧面 / 顶部 / 底部）

**用户原话**：「饮料灌装机新材质在用户素材」（素材名把三个槽点得很清楚）

| 素材 | 字节 | sha1 | 落位 | 用在 |
|---|---|---|---|---|
| `饮料灌装机侧面_001.png` | 2833 | `1cb30de97346` | `textures/block/filling_machine_side.png` | 南 / 东 / 西 三个侧面 |
| `饮料灌装机顶部_001.png` | 2954 | `e0852840e843` | `textures/block/filling_machine_top.png` | 顶面 |
| `饮料灌装机底部_001.png` | 2851 | `9db3ca07bdc5` | `textures/block/filling_machine_bottom.png` | 底面（**本轮新开的槽**） |

- 三张都是 **16×16 / 8 位 RGBA / 整张不透明**（256/256 像素）⇒ **原字节复制**。
- `models/block/filling_machine.json`：**新增 `bottom` 槽**，并把 `down` 面从 `#top` 改成 `#bottom`
  —— 原来**顶面和底面共用同一张顶面图**；改法与 ZF154 采油机同一套。
- ⚠ **正面没动**：用户这轮给的是「侧面 / 顶部 / 底部」，**没有给正面**。`north` 面仍用
  `filling_machine_front`（ZF-era 的程序生成占位，180 B / 7 色）。要不要把正面也换成新侧面那张，
  等他一句话。
- ⚠ **补账**：备份循环又把**资源相对路径**当仓库相对路径（§4.165 **第 2 次**），四份改前件没抄进
  `zf170_pre`、其中三张贴图当场被覆盖 ⇒ 从 **git HEAD** 取回，sha1 与 dry 实测逐位核对，
  并与 `build/resources/main` 里的旧副本**交叉印证**（三张都对上）。
"""
ROW = (u"| ZF170 | **新建 `zf170_pre`**（4 份改前件 = 三张在用贴图 + 方块模型，**从 git HEAD 取回**"
       u"—— 见下方补账；另 4 份备份 = 凭据 + 三份文档）；⚠ **同一个坑第二次踩**（§4.165：备份循环把资源相对路径当仓库相对路径）"
       u"⇒ 四份改前件一份都没抄、三张贴图当场被覆盖；这次是**逐份断言**拦下来的 | "
       u"0.13：**饮料灌装机三面新材质**（用户原话「饮料灌装机新材质在用户素材」）。"
       u"① 三张素材 `16x16 / 8 位 RGBA / 整张不透明 / 2·8·2 色` ⇒ **原字节复制**："
       u"侧面 → `filling_machine_side.png`、顶部 → `filling_machine_top.png`、底部 → **新建** `filling_machine_bottom.png`；"
       u"② 模型**新开 `bottom` 槽**、`down` 面由 `#top` 改指 `#bottom`（原来**顶/底共用顶面那张**），"
       u"与 ZF154 采油机同一套做法；`up`／`north` 与 `front` 槽**一个字节没动**；"
       u"③ ⚠ **正面仍是 ZF-era 程序生成占位**（`filling_machine_front.png` 180 B / 7 色）—— 用户这轮**没给正面图**，"
       u"按「给什么放什么、不猜」处理，并在汇报里请他拍板；"
       u"④ 凭据 55 → 58 条（三条纯追加，先证明「读进来再原样写回」与盘上逐字节相同才动笔） | 见 §4.165 / §9 |\n")

ANN_TEXT = u"""
## New in 0.13 ZF170 - the Filling Machine gets its own textures

- **The Filling Machine is no longer a placeholder.** Three new 16x16 textures were supplied and are
  copied in byte-for-byte: the **side** (used on the south/east/west faces), the **top**, and - new -
  a separate **bottom**.
- **Top and bottom used to share one texture.** The model gained a `bottom` slot and the `down` face
  now points at it, the same way the Oil Pump was fixed earlier.
- **The front face is deliberately untouched**: no front artwork was supplied this round, so the
  north face still uses the old placeholder. Say the word if it should reuse the new side texture.
- Note for the record: the backup loop in this round's apply script repeated a mistake first
  documented earlier - it resolved asset-relative paths against the repository root, so four
  pre-change files were not copied (and three textures were overwritten). They were recovered from
  git HEAD and verified against the values measured before the change, plus cross-checked against the
  stale copies still sitting in the build output.
"""

print(u'===== ① 文档 =====')
raw = read(LIST)
if u'## ZF170' in raw:
    print(u'  [幂等] 清单已有 ZF170 小节')
else:
    if not raw.endswith(u'\n'):
        raw += u'\n'
    write(LIST, raw + SEC)
    check(u'## ZF170' in read(LIST), u'贴图清单加了一节')

raw = read(ARCH)
if u'| ZF170 |' in raw:
    print(u'  [幂等] 档案已有 ZF170 行')
else:
    lines = raw.split(u'\n')
    idx = max(i for i, l in enumerate(lines) if l.startswith(u'| ZF'))
    lines.insert(idx + 1, ROW.rstrip(u'\n'))
    write(ARCH, u'\n'.join(lines))
    check(u'| ZF170 |' in read(ARCH), u'档案变更表插入 ZF170 行（追在 %s 之后）' % lines[idx][:10])

raw = read(ARCH)
NOTE = (u"\n**第 2 次（0.13 ZF170）**：同一个循环我**又照抄了一遍** —— 四份改前件（三张在用贴图 + 一个方块模型）"
        u"没抄进 `zf170_pre`，三张贴图**当场被覆盖**。这次是**逐份断言**把它拦下来的（每条 `check` 都红了，"
        u"不像 ZF157 那次被 `check(True, …)` 蒙过去 —— 那一课记在这一节上面）。补法同前：git HEAD 取回 + "
        u"sha1 与 dry 实测逐位核对 + `build/resources/main` 里的旧副本交叉印证。\n\n"
        u"**规矩（加一条）**：写备份循环时，**先问「这份 rel 是相对谁的」**，再写 `os.path.join`；"
        u"清单里混着两套口径时，宁可用**两个列表**分开写，也别用一条 `if` 猜。")
ANCH = u"不许来自我手写的那张清单。"
if u'第 2 次（0.13 ZF170）' in raw:
    print(u'  [幂等] §4.165 已记过第 2 次')
else:
    n = raw.count(ANCH)
    check(n == 1, u'§4.165 收尾锚点命中 1 次（实测 %d）' % n)
    if n == 1:
        i = raw.index(ANCH) + len(ANCH)
        write(ARCH, raw[:i] + NOTE + raw[i:])
        check(u'第 2 次（0.13 ZF170）' in read(ARCH), u'§4.165 已补记「第 2 次」')

raw = read(ANN_PATH)
if u'ZF170' in raw:
    print(u'  [幂等] 英文公告已有 ZF170 条')
else:
    if not raw.endswith(u'\n'):
        raw += u'\n'
    write(ANN_PATH, raw + ANN_TEXT)
    check(u'ZF170' in read(ANN_PATH), u'英文公告加了一条')

print()
print(u'===== ② 复核图 =====')
S, GAP, M = 8, 10, 10
CELL = 16 * S
ROWS = [
    (u'改前 side/top/front（占位）', [os.path.join(PRE, 'src__main__resources__assets__potato_s_t__textures__block__filling_machine_%s.png' % k)
                                 for k in ('side', 'top', 'front')]),
    (u'改后 side/top/bottom（新）', [os.path.join(TEXB, 'filling_machine_%s.png' % k) for k in ('side', 'top', 'bottom')]),
]
W = M * 2 + CELL * 3 + GAP * 2
H = M * 2 + CELL * 2 + GAP * 3
cv = bytearray(W * H * 4)
for y in range(H):
    for x in range(W):
        v = 62 if ((x // 8 + y // 8) % 2 == 0) else 74
        i = (y * W + x) * 4
        cv[i] = cv[i + 1] = cv[i + 2] = v
        cv[i + 3] = 255
for r, (label, ps) in enumerate(ROWS):
    oy = M + r * (CELL + GAP + GAP)
    for c, p in enumerate(ps):
        w, h, px = read_png(p)
        ox = M + c * (CELL + GAP)
        for y in range(16):
            for x in range(16):
                i = (y * 16 + x) * 4
                if not px[i + 3]:
                    continue
                for dy in range(S):
                    for dx in range(S):
                        di = ((oy + y * S + dy) * W + (ox + x * S + dx)) * 4
                        cv[di:di + 4] = px[i:i + 4]


def write_png2(path, w, h, rgba):
    import zlib, struct
    raw2 = bytearray()
    for y in range(h):
        raw2.append(0)
        raw2 += rgba[y * w * 4:(y + 1) * w * 4]

    def ch(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    png += ch(b'IDAT', zlib.compress(bytes(raw2), 9)) + ch(b'IEND', b'')
    open(path, 'wb').write(png)


PV = os.path.join(TOOLS, '_zf170_preview.png')
write_png2(PV, W, H, cv)
print(u'  上排 = 改前（side / top / front 占位）、下排 = 改后（side / top / bottom），已写出 %s' % PV)

print()
print(u'===== ③ 产物与门 =====')
n_ok = 0
for k in ('side', 'top', 'bottom', 'front'):
    a = os.path.join(TEXB, 'filling_machine_%s.png' % k)
    b = os.path.join(BTEXB, 'filling_machine_%s.png' % k)
    ha = hashlib.sha1(open(a, 'rb').read()).hexdigest()
    hb = hashlib.sha1(open(b, 'rb').read()).hexdigest() if os.path.exists(b) else 'MISSING'
    print(u'  %-26s 源=%s 产物=%s' % (k, ha[:12], hb[:12]))
    if ha == hb:
        n_ok += 1
check(n_ok == 4, u'build 产物四张与源逐字节一致（%d/4）' % n_ok)
if os.path.exists(BMODEL):
    bt = read(BMODEL)
    check(u'"bottom"' in bt and u'"#bottom"' in bt, u'build 产物里的模型也带了 bottom 槽（processResources 已跟平）')
else:
    check(False, u'build 产物里没有模型（要先跑 processResources）')
for g in ['TextureCheck.py', 'ModelCheck.py', 'JsonCheck.py']:
    r = subprocess.run([sys.executable, os.path.join(TOOLS, g)], cwd=ROOT,
                       env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode('utf-8', 'replace')
    tail = [l.strip() for l in out.splitlines() if (u'失败' in l or u'结论' in l or u'非法' in l or u'孤儿' in l)]
    print(u'  %-20s rc=%d  %s' % (g, r.returncode, u' | '.join(tail[-2:])))
    check(r.returncode == 0, u'%s rc=0' % g)
print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
