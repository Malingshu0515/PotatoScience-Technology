# -*- coding: utf-8 -*-
r"""_zf119_verify.py —— ZF119 **常驻校验**：振金锭（动画贴图 + 物品 + 标签 + 没有配方）

用户原话：「加个振金锭（目前没配方）这是振金锭贴图 做成动态贴图 3t播放一帧」

它盯的是**这一轮说出口的每一句话**：
  A 贴图与动画：32×320（10 帧 × 32）、每帧内容 y=4..27（照 `titanium_ingot.png` 的摆位基准）、
    上下留白全透明、零半透明、**每帧逐像素等于源图里那个锭**、mcmeta 的 `frametime == 3`、
    帧与帧真的不同（不是复制同一帧充数）、源图哈希可追；
  B 物品：ModItems 注册 + 创造页（§4.82）+ 模型 layer0 + 三个 c: 标签 + **没有任何配方产出它**；
  C 活体数字：四语言 **464** 键、23 份往轮校验无残留 448、公告同步；
  D 文档：§5/§9、写着 frametime 3 / 10 帧 / 没配方 / 本轮的顺序失误；
  E 探针：报告全绿 + 关键断言在场 + 存档在 check/（先抄后删）+ src 与 PotatoST 无残留；
  F 改前件：zf119_pre 在、**含 `PotatoST.java`**（本轮挂了探针 ⇒ 必须有：这次是补进去的）、
    `ModItems.java` 那份是补账（sha1 对得上）。

⚠ §4.81：stdout 自己钉 UTF-8（被 gatesnap 用管道调起来时按 GBK 崩 = 假绿）。
⚠ §4.27：预期值不抄被测代码 —— 帧数 / 摆位 / frametime 都在这里独立再写一遍。
"""
import hashlib
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
TEXI = os.path.join(ASSETS, r"textures\item")
LANG = os.path.join(ASSETS, "lang")
MODELS = os.path.join(ASSETS, r"models\item")
RDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
TAGS = os.path.join(ROOT, r"src\main\resources\data\c\tags\item")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
TOOLS = os.path.join(ROOT, r"build\zftools")
CHECK = os.path.join(TOOLS, "check")
DOC = os.path.join(ROOT, r"docs\开发档案.md")
DOC_HAND = os.path.join(ROOT, r"docs\多会话协作交接.md")
DOC_EN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
USERART = os.path.join(ROOT, r"build\用户素材")
BK = r"C:\PotatoST救援\zf119_pre"
REPORT = os.path.join(TOOLS, r"_zf119_probe_utf8.txt")

ITEM = "vibranium_ingot"
FRAME = 32
N_FRAMES = 10
PAD_TOP, CONTENT = 4, 24
FRAMETIME = 3
SRC_SHA = "bd507492e06aa056b0d5059da78195dc3c597eae"
TEX_SHA = "e7db8d326fa1f540d08fa4d007243ac6c6e67721"
MC_SHA = "12e4a8093d2cf4d1edf99db861f1681f7e318427"
ARC_SHA = "9f02ab7c24119b607a90177b5813b411a5b16322"
MODITEMS_BK_SHA = "972450d25a333c7c"      # 补账那份（前 16 位）
KEY_OLD, KEY_NEW = 448, 464
NAMES = ["振金锭", "Vibranium Ingot", "ヴィブラニウムインゴット", "Слиток вибраниума"]

n_pass = 0
fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def check(name, cond, detail=None):
    global n_pass
    if cond:
        n_pass += 1
    else:
        fails.append(name + (u"  ← %s" % detail if detail else u""))


def eq(name, want, got):
    check(name, want == got, u"期望 %r 实际 %r" % (want, got))


def rows(w, h, buf):
    return [[buf[(y * w + x) * 4:(y * w + x) * 4 + 4] for x in range(w)] for y in range(h)]


def is_shine(px):
    u"""闪光 = 高饱和的黄；本体 = 灰白（低饱和）。判据与出图脚本**独立**再写一遍。"""
    r, g, b, a = px
    if a == 0:
        return False
    mx, mn = max(r, g, b), min(r, g, b)
    return (mx - mn) >= 60 and r >= 120 and g >= 100 and b <= 160


def body_bands(w, h, buf):
    u"""**只按本体**分行（不看闪光）—— 第一版按"有不透明像素"分帧就是错在这里：
    闪光会跑到本体上方，窗口被抬高，重排后本体跳一下（用户实测抓到）"""
    r = rows(w, h, buf)
    nbody = [sum(1 for px in row if px[3] > 0 and not is_shine(px)) for row in r]
    bands, cur = [], None
    for y in range(h):
        if nbody[y] > 0 and cur is None:
            cur = y
        elif nbody[y] == 0 and cur is not None:
            bands.append((cur, y - 1))
            cur = None
    if cur is not None:
        bands.append((cur, h - 1))
    return bands, r


def main():
    # ================= A 贴图 / 动画 =================
    print(u"== A 贴图 / 动画 ==")
    tex = os.path.join(TEXI, ITEM + u".png")
    mc = tex + u".mcmeta"
    srcart = os.path.join(USERART, u"振金锭.png")
    check(u"A1 贴图在（%s）" % tex, os.path.exists(tex))
    check(u"A2 mcmeta 在（%s）" % mc, os.path.exists(mc))
    check(u"A3 源素材留档在（%s）" % srcart, os.path.exists(srcart))
    if not (os.path.exists(tex) and os.path.exists(mc) and os.path.exists(srcart)):
        return report()
    eq(u"A4 源素材 sha1（来源可追）", SRC_SHA, sha1(srcart))
    eq(u"A5 产物贴图 sha1（本轮写出的就是它）", TEX_SHA, sha1(tex))
    eq(u"A6 mcmeta sha1", MC_SHA, sha1(mc))
    w, h, buf = read_png(tex)
    size_ok = (w, h) == (FRAME, FRAME * N_FRAMES)
    eq(u"A7 贴图尺寸 %d×%d" % (FRAME, FRAME * N_FRAMES), (FRAME, FRAME * N_FRAMES), (w, h))
    # ⚠ §4.77 族：坏数据要**报错**，不许把校验器自己搞崩。
    #   K159 那把刀（贴图被砍成 9 帧）第一版就是让这里 IndexError 崩掉的 ——
    #   崩了就没有"哪条断言挂了"可读。所以尺寸不对就**只报 A7**、后面几段跳过。
    if not size_ok:
        print(u"   （尺寸不是 %d×%d ⇒ 逐帧那几条（A8~A15）只报一次失败、不硬算，"
              u"免得校验器自己 IndexError 崩掉 —— §4.77 族）" % (FRAME, FRAME * N_FRAMES))
        check(u"A8~A15 逐帧断言（尺寸不对 ⇒ 跳过 = 不通过）", False)
    # 每帧：**本体**（低饱和的灰白）必须落在 y=4..27，而且 **10 帧完全一致**；
    # 上下留白里只许出现**闪光**（用户实测要求：「锭本体保持一致 不要以闪光为基准」）
    r = rows(w, h, buf) if size_ok else None
    bad_body, bad_pad, semi = [], [], 0
    body_boxes = []
    if r is not None:
        for k in range(N_FRAMES):
            pts = [(y, x) for y in range(FRAME) for x in range(FRAME)
                   if r[k * FRAME + y][x][3] > 0 and not is_shine(r[k * FRAME + y][x])]
            if not pts:
                body_boxes.append(None)
                continue
            ys = [p[0] for p in pts]
            xs = [p[1] for p in pts]
            body_boxes.append((min(ys), max(ys), min(xs), max(xs)))
            if (min(ys), max(ys)) != (PAD_TOP, PAD_TOP + CONTENT - 1):
                bad_body.append((k, (min(ys), max(ys))))
            for y in list(range(0, PAD_TOP)) + list(range(PAD_TOP + CONTENT, FRAME)):
                for x in range(FRAME):
                    px = r[k * FRAME + y][x]
                    if px[3] > 0 and not is_shine(px):
                        bad_pad.append((k, y, x))
        for row in r:
            for px in row:
                if 0 < px[3] < 255:
                    semi += 1
        eq(u"A8 每帧**本体**都落在 y=%d..%d（照 titanium_ingot 的摆位）"
           % (PAD_TOP, PAD_TOP + CONTENT - 1), [], bad_body)
        eq(u"A9 上下留白里**不许有本体**（闪光可以有：它本来就该动）", [], bad_pad[:5])
        eq(u"A9b 10 帧的**本体包围盒完全一致**（用户原话「锭本体保持一致」）",
           1, len(set(body_boxes)))
        eq(u"A10 零半透明像素", 0, semi)
    # 摆位基准还在不在（依据不能悄悄变）
    rw, rh, rbuf = read_png(os.path.join(TEXI, u"titanium_ingot.png"))
    rys = [y for y in range(rh) if any(px[3] > 0 for px in rows(rw, rh, rbuf)[y])]
    eq(u"A11 摆位基准 titanium_ingot.png 仍是 %d×%d、内容 y=%d..%d"
       % (FRAME, FRAME, PAD_TOP, PAD_TOP + CONTENT - 1),
       (FRAME, FRAME, PAD_TOP, PAD_TOP + CONTENT - 1), (rw, rh, min(rys), max(rys)))
    # 与源图逐像素等价（**独立**再推一遍：本体分段 → 夹在邻居本体之间 → 每帧 32 行）
    sw, sh, sbuf = read_png(srcart)
    bands, srows = body_bands(sw, sh, sbuf)
    eq(u"A12 源图里检出 %d 个**本体**段、每段 %d 行（不看闪光）" % (N_FRAMES, CONTENT),
       (N_FRAMES, CONTENT), (len(bands), len(set(b - a + 1 for a, b in bands)) and
                             (bands[0][1] - bands[0][0] + 1) if bands else 0))
    if len(bands) == N_FRAMES and r is not None:
        diff = []
        for k, (a, b) in enumerate(bands):
            lo = max(a - PAD_TOP, bands[k - 1][1] + 1 if k > 0 else 0)
            hi = min(b + PAD_TOP, bands[k + 1][0] - 1 if k + 1 < N_FRAMES else sh - 1)
            for y in range(FRAME):
                sy = a - PAD_TOP + y
                want = srows[sy] if (0 <= sy < sh and lo <= sy <= hi) else [b"\0\0\0\0"] * sw
                if r[k * FRAME + y] != want:
                    diff.append((k, y, sy))
                    break
        eq(u"A13 每帧**逐像素等于**源图对应行（零重采样；窗口夹在邻居本体之间）", [], diff[:5])
    # 帧真的在动
    if r is not None:
        uniq = len(set(tuple(tuple(px) for px in r[k * FRAME + PAD_TOP + 1])
                       for k in range(N_FRAMES)))
        check(u"A14 至少 3 种不同的帧（真的在动，实际 %d 种）" % uniq, uniq >= 3)
        same_pairs = sum(1 for k in range(N_FRAMES - 1)
                         if all(r[k * FRAME + y] == r[(k + 1) * FRAME + y] for y in range(FRAME)))
        check(u"A15 相邻帧完全相同的对数 ≤ 2（实际 %d）" % same_pairs, same_pairs <= 2)
        # 闪光必须仍然在动（不然就成静态图了）
        shinetops = set()
        for k in range(N_FRAMES):
            ys = [y for y in range(FRAME) for x in range(FRAME)
                  if is_shine(r[k * FRAME + y][x])]
            if ys:
                shinetops.add(min(ys))
        check(u"A15b 闪光仍有 ≥3 个不同位置（实际 %d 种）" % len(shinetops), len(shinetops) >= 3)
    meta = json.loads(read(mc))
    eq(u"A16 mcmeta：animation.frametime = %d（用户原话「3t播放一帧」）" % FRAMETIME,
       FRAMETIME, meta.get(u"animation", {}).get(u"frametime"))
    check(u"A17 mcmeta 没有 frames 列表（按顺序播）", u"frames" not in meta.get(u"animation", {}))
    check(u"A18 时长账：%d 帧 × %d tick = %d tick（1.5 秒一轮）"
          % (N_FRAMES, FRAMETIME, N_FRAMES * FRAMETIME),
          N_FRAMES * FRAMETIME == 30)

    # ================= B 物品 =================
    print(u"\n== B 物品 ==")
    items = read(os.path.join(JAVA, u"ModItems.java"))
    check(u"B1 ModItems 里注册了 vibranium_ingot",
          re.search(r'ITEMS\.register\("%s"' % ITEM, items) is not None)
    check(u"B2 创造页里 accept 了它（§4.82：漏了 = 物品栏看不见、JEI 搜不到）",
          re.search(r"output\.accept\(VIBRANIUM_INGOT\.get\(\)\)", items) is not None)
    mp = os.path.join(MODELS, ITEM + u".json")
    check(u"B3a 模型文件在（%s）" % mp, os.path.exists(mp))
    model = json.loads(read(mp)) if os.path.exists(mp) else {}
    eq(u"B3 模型 layer0", u"potato_s_t:item/" + ITEM,
       model.get(u"textures", {}).get(u"layer0"))
    for rel, tag in ((os.path.join(u"ingots", u"vibranium.json"), u"c:ingots/vibranium"),
                     (u"vibranium_ingots.json", u"c:vibranium_ingots")):
        tp = os.path.join(TAGS, rel)
        if not os.path.exists(tp):
            # ⚠ §4.77 族：文件被删要报**一条清楚的 FAIL**，不许 json.loads 抛栈把校验器搞崩
            check(u"B4 %s 收下它（文件不在：%s）" % (tag, rel), False)
            continue
        obj = json.loads(read(tp))
        eq(u"B4 %s 收下它" % tag, [u"potato_s_t:" + ITEM], obj.get(u"values"))
    ip = os.path.join(TAGS, u"ingots.json")
    if not os.path.exists(ip):
        check(u"B5 父标签 c:ingots 里有它（父标签文件不在）", False)
    else:
        parent = json.loads(read(ip))
        check(u"B5 父标签 c:ingots 里有它", u"potato_s_t:" + ITEM in parent.get(u"values", []))
    hits = []
    for n in sorted(os.listdir(RDIR)):
        if not n.endswith(u".json"):
            continue
        obj = json.loads(read(os.path.join(RDIR, n)))
        res = obj.get(u"result")
        res = res if isinstance(res, dict) else (res[0] if isinstance(res, list) and res else {})
        if isinstance(res, dict) and res.get(u"id") == u"potato_s_t:" + ITEM:
            hits.append(n)
    # ⚠ ZF121：用户给了**合金冶炼炉**配方（写死在 Java 表 AlloySmelterRecipes 里，
    #   不是数据包配方）⇒ 这句措辞会骗人，改成"没有数据包/工作台配方"。
    #   **判据一个字都没放宽**：还是 hits == []（本段扫的就是 data/potato_s_t/recipe/）。
    #   振金锭的真实来源（合金炉那条）由 `_zf121_verify.py` 常驻盯着。
    eq(u"B6 **没有任何数据包/工作台配方**产出它（来源是合金冶炼炉 · ZF121）", [], hits)
    for loc, name in zip(("zh_cn", "en_us", "ja_jp", "ru_ru"), NAMES):
        data = json.loads(read(os.path.join(LANG, loc + u".json")))
        v = data.get(u"item.potato_s_t." + ITEM, u"")
        check(u"B7 %s 的名字 = %s" % (loc, name), v == name)
    zh = json.loads(read(os.path.join(LANG, u"zh_cn.json")))
    en = json.loads(read(os.path.join(LANG, u"en_us.json")))
    check(u"B8 四语言名字互不相同（没照抄）",
          len(set(NAMES)) == 4 and zh.get(u"item.potato_s_t." + ITEM) != en.get(u"item.potato_s_t." + ITEM))

    # ================= C 活体数字 =================
    print(u"\n== C 活体数字 ==")
    counts = {}
    for loc in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        counts[loc] = len(json.loads(read(os.path.join(LANG, loc + u".json"))))
    eq(u"C1 四语言各 %d 键" % KEY_NEW, [KEY_NEW] * 4, [counts[l] for l in counts])
    stale = []
    for f in sorted(os.listdir(TOOLS)):
        if not re.match(r"^_zf\d+_verify\.py$", f) or f.startswith(u"_zf119"):
            continue
        if re.search(r"\b%d\b" % KEY_OLD, read(os.path.join(TOOLS, f))):
            stale.append(f)
    eq(u"C2 23 份往轮校验里没有残留旧键数 %d" % KEY_OLD, [], stale)
    check(u"C3 英文公告写的 %d keys each" % KEY_NEW,
          u"(%d keys each)" % KEY_NEW in read(DOC_EN))
    v118 = read(os.path.join(TOOLS, u"_zf118_verify.py"))
    check(u"C4 `_zf118_verify.py` 的 KEY_NEW 也跟到 %d" % KEY_NEW,
          re.search(r"KEY_NEW = %d\b" % KEY_NEW, v118) is not None)

    # ================= D 文档 =================
    print(u"\n== D 文档 ==")
    doc = read(DOC)
    check(u"D1 档案 §5 有 ZF119 行", u"| ZF119 |" in doc)
    check(u"D2 档案 §9 有 ZF119 小节", u"ZF119（0.11）" in doc)
    check(u"D3 档案写了 frametime 3 与 %d 帧" % N_FRAMES, u"frametime" in doc and u"10 帧" in doc)
    check(u"D4 档案写了「目前没配方」", u"没配方" in doc)
    check(u"D5 档案记了本轮的**顺序失误**（先动盘、后建备份）", u"顺序" in doc and u"补账" in doc)
    hand = read(DOC_HAND)
    # ⚠ ZF121 retarget：这里原来钉死 KEY_NEW（464）。键数是**每一轮都会动的活体数字**
    #   （ZF120 并行线一加就是 464）⇒ 改成"交接文档写的数 == 盘上实际的数"：
    #   比钉死更严（钉死的话，下一轮加键这两边会一起错、而这条检查还是绿的）。
    _lang_keys = len(json.loads(read(os.path.join(LANG, u"zh_cn.json"))))
    check(u"D6 交接文档的键数与盘上一致（%d）" % _lang_keys,
          (u"%d 键" % _lang_keys) in hand)
    check(u"D7 交接文档记了 ZF119", u"ZF119" in hand)

    # ================= E 探针 =================
    print(u"\n== E 探针 ==")
    check(u"E1 探针 UTF-8 报告在（%s）" % REPORT, os.path.exists(REPORT))
    if os.path.exists(REPORT):
        rep = read(REPORT)
        check(u"E2 报告全绿", u"verdict: ALL OK" in rep)
        check(u"E3 报告里没有 [FAIL]", u"[FAIL]" not in rep)
        for lit in (u"Vibranium Ingot", u"#c:ingots/vibranium", u"#c:vibranium_ingots",
                    u"#c:ingots 收下它", u"没有任何配方产出振金锭", u"高 = 320",
                    u"frametime = 3", u"layer0 指向自己"):
            check(u"E4 报告里有「%s」" % lit, lit in rep)
    arc = os.path.join(CHECK, u"Zf119Check.java")
    check(u"E5 探针存档在 check/（先抄后删，§10.1）", os.path.exists(arc))
    if os.path.exists(arc):
        eq(u"E6 存档 sha1", ARC_SHA, sha1(arc))
    check(u"E7 探针源码已从 src 删掉", not os.path.exists(os.path.join(JAVA, u"Zf119Check.java")))
    check(u"E8 PotatoST.java 里没有残留钩子",
          u"Zf119Check" not in read(os.path.join(JAVA, u"PotatoST.java")))

    # ================= F 改前件 =================
    print(u"\n== F 改前件 ==")
    check(u"F1 zf119_pre 在", os.path.isdir(BK))
    mf = os.path.join(BK, u"_sha1.txt")
    check(u"F2 改前件清单在", os.path.exists(mf))
    if os.path.exists(mf):
        txt = read(mf)
        check(u"F3 清单里有 PotatoST.java（本轮挂了探针 ⇒ 必须有；这次是补进去的）",
              u"PotatoST.java" in txt)
        check(u"F4 清单里 ModItems.java 的补账哈希对得上（%s…）" % MODITEMS_BK_SHA,
              MODITEMS_BK_SHA in txt)
    check(u"F5 _zf119_newfiles.txt 记着「本轮开始前不该存在」的路径",
          os.path.exists(os.path.join(BK, u"_zf119_newfiles.txt")))
    check(u"F6 补账说明在（_补说明.txt：顺序失误 + PotatoST 漏账）",
          os.path.exists(os.path.join(BK, u"_补说明.txt")))
    return report()


def report():
    print(u"")
    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
