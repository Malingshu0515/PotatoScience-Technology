# -*- coding: utf-8 -*-
"""_zf64_verify.py —— ZF64 盘面复核（JEI 说明行删除 / 合金炉进度箭头 / 运行时循环音效）

ZF64 干了三件事，每件都有"坏了也不报错"的坏法，所以逐条量：

  ① <b>删掉 JEI 里那条标签判定说明</b>（用户：「所有的这种文字可以删掉 给玩家看没必要列出来 还占空间 不美观」）
     —— 坏法：只删了 Java 那一行、4 个语言文件里留了孤儿键（或反过来，把别的机器的说明行误删）。
  ② <b>进度箭头</b>（用户：「正在熔炼什么的箭头（同时也是进度条）」）
     —— 坏法：箭头画到槽位/能量条上、偏离中线、菜单没把进度暴露出来 ⇒ 全是"能编译、进游戏才发现"的错。
        这里把常量从源码里读出来，按像素算 bbox 有没有压到东西。
  ③ <b>运行中循环电机声</b>（用户给的素材，要求"不是单声道就转单声道"）
     —— 坏法：ogg 还是立体声（MC 里不吃距离衰减）、sounds.json 键名错一个字母 ⇒ 静默无声。

⚠ 本脚本只做**静态**复核：声音"响不响"要人在游戏里听，界面好不好看要人眼看（同目录另出一张复刻预览图）。
⚠ 期望值一律是**用户给的字面量 / 从源码读出的常量**，不从被测常量抄（§4.27）。

用法:
    python _zf64_verify.py                 # 正常复核
    python _zf64_verify.py --ogg <path>    # 反证用：换一个 ogg 去撞格式断言（应报 单声道/规格 FAIL）
"""
import io
import json
import os
import re
import struct
import sys
import zlib

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
SOUNDS = os.path.join(ASSETS, "sounds")
OUT_PNG = os.path.join(ROOT, r"build\zftools\zf64_arrow_preview.png")

OSS = [os.path.join(JAVA, n) for n in (
    "MachineRecipes.java", "AlloySmelterBlockEntity.java", "AlloySmelterMenu.java",
    "sound\\ModSounds.java", "client\\AlloySmelterScreen.java",
    "client\\gui\\parts\\ProgressArrowPart.java",
)]

fails = []
warns = []


def check(ok, msg):
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fails.append(msg)
    return ok


def warn(msg):
    print("  [WARN] " + msg)
    warns.append(msg)


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def num(src, name):
    m = re.search(r"\b%s\s*=\s*(\d+)\s*;" % re.escape(name), src)
    return int(m.group(1)) if m else None


def body_of(src, method):
    """截出 `private static void <method>(...) {` 到同缩进的收尾 `}` 之间的正文。"""
    m = re.search(r"\n    (?:private|public|protected)[^\n]*\b%s\s*\([^)]*\)\s*\{" % re.escape(method), src)
    if not m:
        return ""
    start = m.end()
    end = src.find("\n    }", start)
    return src[start:end if end > 0 else len(src)]


# ============================================================ ① JEI 文字
print("== ① JEI 说明行：标签判定那条删干净了，别的机器没被误伤 ==")
rec = read(os.path.join(JAVA, "MachineRecipes.java"))
langs = {n: json.loads(read(os.path.join(LANG, n + ".json"))) for n in ("zh_cn", "en_us", "ja_jp", "ru_ru")}

hits = []
for path in OSS + [os.path.join(LANG, n + ".json") for n in ("zh_cn", "en_us", "ja_jp", "ru_ru")]:
    if "tag_inputs" in read(path):
        hits.append(os.path.basename(path))
check(not hits, "src 里再也没有 tag_inputs 的引用（命中: %s）" % (hits or "无"))

for name, data in langs.items():
    check("gui.potato_s_t.jei.tag_inputs" not in data, "%s.json 里的孤儿键也删了" % name)

alloy_info = len(re.findall(r'Component\.translatable\("gui\.potato_s_t\.jei\.',
                            body_of(rec, "buildAlloySmelter")))
check(alloy_info == 2, "合金炉那条配方只剩 耗时/耗电 两行说明（读到 %d 行）" % alloy_info)

for method in ("buildBlastFurnace", "buildSaltDecomposer", "buildHydraulicPress", "buildAlloySmelter"):
    n = len(re.findall(r'Component\.translatable\("gui\.potato_s_t\.jei\.', body_of(rec, method)))
    check(n >= 1, "%s 的说明行还在（%d 行）—— 没被连坐删掉" % (method, n))

keysets = {n: set(d.keys()) for n, d in langs.items()}
base = keysets["zh_cn"]
for name, ks in keysets.items():
    check(ks == base, "%s.json 键集合与 zh_cn 完全一致（%d 键）" % (name, len(ks)))
check(len(base) > 150, "语言键没被整片删空（%d 键）" % len(base))

# ============================================================ ② 音效链路
print()
print("== ② 音效链路：注册名 / sounds.json / ogg 文件 ==")
snd = read(os.path.join(JAVA, r"sound\ModSounds.java"))
registered = re.findall(r'SOUND_EVENTS\.register\(\s*"([^"]+)"', snd)
check("alloy_smelter_running" in registered,
      "ModSounds 注册了 alloy_smelter_running（现有 %d 个音效）" % len(registered))
check(re.search(r'ALLOY_SMELTER_RUNNING\s*=\s*\n?\s*SOUND_EVENTS\.register\(\s*"alloy_smelter_running"', snd) is not None,
      "常量名 ALLOY_SMELTER_RUNNING 绑的就是这个名字")

sounds_json = json.loads(read(os.path.join(ASSETS, "sounds.json")))
entry = sounds_json.get("alloy_smelter_running")
check(entry is not None, "sounds.json 有键 alloy_smelter_running")
names = []
if entry:
    for s in entry.get("sounds", []):
        names.append(s["name"] if isinstance(s, dict) else s)
check(names == ["potato_s_t:alloy_smelter_running"],
      "sounds.json 指向 potato_s_t:alloy_smelter_running（读到 %s）" % names)

ogg_arg = None
for i, a in enumerate(sys.argv):
    if a == "--ogg":
        ogg_arg = sys.argv[i + 1]
ogg = ogg_arg or os.path.join(SOUNDS, "alloy_smelter_running.ogg")
print("  检查的 ogg: %s" % ogg)
check(os.path.isfile(ogg), "ogg 文件存在")

try:
    import numpy as np
    import soundfile as sf
    info = sf.info(ogg)
    check(info.format == "OGG" and info.subtype == "VORBIS",
          "格式是 OGG/VORBIS（读到 %s/%s）" % (info.format, info.subtype))
    check(info.channels == 1, "**单声道**（读到 %d 声道 —— 用户要求：不是单声道就转）" % info.channels)
    check(info.samplerate == 44100, "采样率 44100 Hz（读到 %d）" % info.samplerate)
    data, sr = sf.read(ogg, dtype="float32", always_2d=True)
    mono = data[:, 0]
    dur = len(mono) / float(sr)
    rms = float(np.sqrt((mono ** 2).mean()))
    peak = float(np.max(np.abs(mono)))
    seam = abs(float(mono[-1]) - float(mono[0]))
    print("  规格: %.2fs  %d Hz  %d 声道  峰值 %.3f  RMS %.4f  接缝首尾差 %.4f"
          % (dur, info.samplerate, info.channels, peak, rms, seam))
    check(7.0 <= dur <= 9.0, "时长在 7~9 秒（读到 %.2fs；原素材 8.75s 切接缝后约 8.3s）" % dur)
    check(abs(rms - 0.10) <= 0.01, "响度对齐到本项目机器循环的 0.10 RMS（读到 %.4f）" % rms)
    check(peak <= 0.9, "不削波（峰值 %.3f ≤ 0.9）" % peak)
    check(seam <= 0.02, "循环接缝首尾差 ≤ 0.02（%.4f，越接近 0 越不会咔）" % seam)
except ImportError:
    warn("没装 soundfile / numpy，跳过 ogg 规格检查")

be = read(os.path.join(JAVA, "AlloySmelterBlockEntity.java"))
check(re.search(r"if \(level\.isClientSide\) \{\s*be\.clientTick\(\);", be) is not None,
      "tick() 分客户端/服务端（客户端那一支才有循环音）")
check(re.search(r"clientTick\(\)\s*\{\s*MachineRunningSound\.update\(this, this\.running,"
                r"\s*ModSounds\.ALLOY_SMELTER_RUNNING\.get\(\)\);", be) is not None,
      "clientTick() 用 running 标记驱动 MachineRunningSound（文本级证据，见报告口径）")
check(re.search(r"tag\.putBoolean\(\"running\"", be) is not None
      and re.search(r'tag\.getBoolean\("running"\)', be) is not None,
      "running 进了 NBT（否则 getUpdateTag 带不出去，客户端永远不知道）")
check(re.search(r"if \(before != this\.running\) \{\s*sync\(\);", be) is not None,
      "serverTick 只在 running 翻转时发包（不刷网络）")

# ============================================================ ③ 进度箭头几何
print()
print("== ③ 进度箭头：常量从源码读出来，按像素算有没有压到东西 ==")
menu = read(os.path.join(JAVA, "AlloySmelterMenu.java"))
screen = read(os.path.join(JAVA, r"client\AlloySmelterScreen.java"))
arrow = read(os.path.join(JAVA, r"client\gui\parts\ProgressArrowPart.java"))

c = {}
for name in ("INPUT_X", "INPUT_Y", "OUTPUT_X", "OUTPUT_Y", "CONSUME_X", "CONSUME_Y"):
    c[name] = num(menu, name)
for name in ("INPUT_COUNT", "OUTPUT_COUNT", "CONSUME_COUNT"):
    c[name] = num(be, name)
for name in ("ARROW_X", "ARROW_Y", "ARROW_W", "ARROW_H", "ENERGY_X", "ENERGY_Y", "ENERGY_W", "ENERGY_H"):
    c[name] = num(screen, name)
missing = [k for k, v in c.items() if v is None]
check(not missing, "所有几何常量都读到了（缺: %s）" % (missing or "无"))
if missing:
    print("  常量: %s" % c)
    print()
    print("失败项 = %d" % len(fails))
    sys.exit(1)
print("  常量: " + ", ".join("%s=%d" % (k, c[k]) for k in sorted(c)))

# 外框：箭头自身 [x, x+w) × [y, y+h)，描边再外扩 1px，箭尾封口在 y-1
ax0, ax1 = c["ARROW_X"] - 1, c["ARROW_X"] + c["ARROW_W"] + 1
ay0, ay1 = c["ARROW_Y"] - 1, c["ARROW_Y"] + c["ARROW_H"] + 1
# 槽位背景是 18×18，画在 (slot-1, slot-1)
slots = []
for k in range(c["INPUT_COUNT"]):
    slots.append(("in%d" % k, c["INPUT_X"] + k * 18, c["INPUT_Y"]))
for k in range(c["OUTPUT_COUNT"]):
    slots.append(("out%d" % k, c["OUTPUT_X"] + k * 18, c["OUTPUT_Y"]))
for k in range(c["CONSUME_COUNT"]):
    slots.append(("con%d" % k, c["CONSUME_X"] + k * 18, c["CONSUME_Y"]))
slots = [(n, x - 1, y - 1, x + 17, y + 17) for n, x, y in slots]

def overlap(a0, a1, b0, b1):
    return a0 < b1 and b0 < a1

bad = [n for n, sx0, sy0, sx1, sy1 in slots if overlap(ax0, ax1, sx0, sx1) and overlap(ay0, ay1, sy0, sy1)]
check(not bad, "箭头外框 (%d..%d, %d..%d) 不压任何槽位（压到: %s）" % (ax0, ax1, ay0, ay1, bad or "无"))

ex0, ex1 = c["ENERGY_X"], c["ENERGY_X"] + c["ENERGY_W"]
ey0, ey1 = c["ENERGY_Y"], c["ENERGY_Y"] + c["ENERGY_H"]
check(not (overlap(ax0, ax1, ex0, ex1) and overlap(ay0, ay1, ey0, ey1)),
      "箭头不压能量条（能量条 %d..%d, %d..%d）" % (ex0, ex1, ey0, ey1))

check(ax0 >= 0 and ay0 >= 0, "箭头没画出面板左上（x0=%d y0=%d）" % (ax0, ay0))
check(ax1 <= 176 and ay1 <= 186, "箭头没画出面板右下（x1=%d y1=%d，面板 176x186）" % (ax1, ay1))

in_center = ((c["INPUT_X"] - 1) + (c["INPUT_X"] + (c["INPUT_COUNT"] - 1) * 18 + 17)) / 2.0
out_center = ((c["OUTPUT_X"] - 1) + (c["OUTPUT_X"] + (c["OUTPUT_COUNT"] - 1) * 18 + 17)) / 2.0
arrow_center = c["ARROW_X"] + c["ARROW_W"] / 2.0
check(arrow_center == in_center == out_center,
      "箭头中线 %.1f 与输入排中线 %.1f / 输出排中线 %.1f 重合" % (arrow_center, in_center, out_center))

in_bottom = c["INPUT_Y"] - 1 + 18
out_top = c["OUTPUT_Y"] - 1
check(ay0 >= in_bottom, "箭头顶(y=%d) 在输入排底(y=%d) 之下 —— 不叠字" % (ay0, in_bottom))
check(ay1 <= out_top, "箭头底(y=%d) 在输出排顶(y=%d) 之上" % (ay1, out_top))
print("  空档 %d..%d 共 %dpx，箭头外框占了 %d..%d（%dpx）"
      % (in_bottom, out_top, out_top - in_bottom, ay0, ay1, ay1 - ay0))

check(re.search(r"public int getProgress\(\)", menu) is not None
      and re.search(r"public int getProgressMax\(\)", menu) is not None,
      "菜单把 进度/满值 暴露出来了（界面才读得到）")
check("menu::getProgress" in screen and "menu::getProgressMax" in screen,
      "界面把 menu::getProgress / menu::getProgressMax 喂给了箭头部件")
check("implements GuiPart" in arrow and "gg.fill(" in arrow and "texture" not in arrow.lower(),
      "箭头部件是零贴图 GuiPart（全 gg.fill）")
check("ProgressArrowPart.Direction.DOWN" in screen,
      "箭头当前朝下（输入排在上、输出排在下；要改朝向只动这一处）")

# ============================================================ ④ 复刻预览
print()
print("== ④ 箭头形状（Python 按同一套算式复刻，只为出图给人看）==")


def span(step, ln, cross):
    head = max(1, min(cross // 2, ln - 1))
    shaft = max(2, cross // 2)
    if shaft > 2 and ((cross - shaft) % 2):
        shaft -= 1
    center = cross // 2
    if step < ln - head:
        lo = (cross - shaft) // 2
        return lo, lo + shaft
    k = step - (ln - head)
    half = max(1, center * (head - k) // head)
    return center - half, center + half


W, H = c["ARROW_W"], c["ARROW_H"]
spans = [span(s, H, W) for s in range(H)]
symmetric = all(lo + hi == W for lo, hi in spans)
widths = [hi - lo for lo, hi in spans]
head = max(1, min(W // 2, H - 1))
taper = widths[H - head:]
monotone = all(taper[i] >= taper[i + 1] for i in range(len(taper) - 1))
check(symmetric, "箭头左右对称（每格 lo+hi == 宽 %d）" % W)
check(monotone, "箭头段单调收窄（%s）" % taper)
check(taper[-1] <= 2, "箭尖收成 %dpx（≤2 才算尖）" % taper[-1])
want_shaft = max(2, W // 2)
if want_shaft > 2 and ((W - want_shaft) % 2):
    want_shaft -= 1
check(widths[0] == want_shaft,
      "箭杆宽 %d = 横截面 %d 的一半且两侧留白相等（%d / %d）"
      % (widths[0], W, spans[0][0], W - spans[0][1]))
print("  逐格宽度: %s" % widths)

COL_PANEL = (198, 198, 198)
COL_SLOT = (139, 139, 139)
COL_BORDER = (55, 55, 55)
COL_TROUGH = (30, 30, 30)
COL_FILL = (74, 158, 210)
COL_ENERGY = (74, 158, 210)


def draw_preview(fill_frac, path):
    Wp, Hp = 176, 186
    S = 3
    img = [[COL_PANEL for _ in range(Wp)] for _ in range(Hp)]
    for _, sx0, sy0, sx1, sy1 in slots:
        for yy in range(sy0, sy1):
            for xx in range(sx0, sx1):
                if 0 <= xx < Wp and 0 <= yy < Hp:
                    img[yy][xx] = COL_SLOT
    for yy in range(ey0, ey1):
        for xx in range(ex0, ex1):
            if 0 <= xx < Wp and 0 <= yy < Hp:
                img[yy][xx] = COL_ENERGY
    filled = int(H * fill_frac)
    for step in range(H):
        lo, hi = spans[step]
        col = COL_FILL if step < filled else COL_TROUGH
        yy = c["ARROW_Y"] + step
        for xx in range(c["ARROW_X"] + lo - 1, c["ARROW_X"] + hi + 1):
            if 0 <= xx < Wp and 0 <= yy < Hp:
                img[yy][xx] = COL_BORDER if (xx < c["ARROW_X"] + lo or xx >= c["ARROW_X"] + hi) else col
    for xx in range(c["ARROW_X"] + spans[0][0] - 1, c["ARROW_X"] + spans[0][1] + 1):
        if 0 <= xx < Wp and c["ARROW_Y"] - 1 >= 0:
            img[c["ARROW_Y"] - 1][xx] = COL_BORDER

    big = []
    for row in img:
        line = bytearray()
        for px in row:
            line += bytes(px) * S
        for _ in range(S):
            big.append(bytes(line))
    write_png(path, Wp * S, Hp * S, big)


def write_png(path, w, h, rows):
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))
    raw = b"".join(b"\x00" + r for r in rows)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


draw_preview(0.40, OUT_PNG)
check(os.path.isfile(OUT_PNG) and os.path.getsize(OUT_PNG) > 200,
      "复刻预览图写出来了: %s（%d 字节，40%% 进度）" % (OUT_PNG, os.path.getsize(OUT_PNG) if os.path.isfile(OUT_PNG) else 0))

print()
print("失败项 = %d   警告项 = %d" % (len(fails), len(warns)))
for m in fails:
    print("   - " + m)
sys.exit(1 if fails else 0)
