# -*- coding: utf-8 -*-
r"""_zf119_verify.py —— ZF119 **常驻校验**：振金锭（动画贴图 + 物品 + 标签 + 没有配方）

用户原话：「加个振金锭（目前没配方）这是振金锭贴图 做成动态贴图 3t播放一帧」

它盯的是**这一轮说出口的每一句话**：
  A 贴图与动画：32×320（10 帧 × 32）、每帧内容 y=4..27（照 `titanium_ingot.png` 的摆位基准）、
    上下留白全透明、零半透明、**每帧逐像素等于源图里那个锭**、mcmeta 的 `frametime == 3`、
    帧与帧真的不同（不是复制同一帧充数）、源图哈希可追；
  B 物品：ModItems 注册 + 创造页（§4.82）+ 模型 layer0 + 三个 c: 标签 + **没有任何配方产出它**；
  C 活体数字：四语言 **449** 键、23 份往轮校验无残留 448、公告同步；
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
TEX_SHA = "98aa8894f14427e90075fdc43ca5231858e8ef16"
MC_SHA = "12e4a8093d2cf4d1edf99db861f1681f7e318427"
ARC_SHA = "9f02ab7c24119b607a90177b5813b411a5b16322"
MODITEMS_BK_SHA = "972450d25a333c7c"      # 补账那份（前 16 位）
KEY_OLD, KEY_NEW = 448, 449
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


def ingot_starts(w, h, buf):
    u"""**独立**再写一遍"找每个锭从哪一行开始"（不 import 出图那个脚本）"""
    r = rows(w, h, buf)
    counts = [sum(1 for px in row if px[3] > 0) for row in r]
    starts = []
    for y in range(h):
        prev = counts[y - 1] if y > 0 else 0
        if counts[y] > 0 and prev <= 8:
            if starts and y - starts[-1] < CONTENT:
                continue
            if any(counts[min(h - 1, y + k)] >= 28 for k in range(0, 20)):
                starts.append(y)
    return starts, counts, r


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
    # 每帧内容 + 留白（尺寸对才算）
    r = rows(w, h, buf) if size_ok else None
    bad_bbox, bad_pad, semi = [], [], 0
    if r is not None:
        for k in range(N_FRAMES):
            ys = [y for y in range(FRAME) if any(px[3] > 0 for px in r[k * FRAME + y])]
            if not ys or (min(ys), max(ys)) != (PAD_TOP, PAD_TOP + CONTENT - 1):
                bad_bbox.append((k, (min(ys), max(ys)) if ys else None))
            for y in list(range(0, PAD_TOP)) + list(range(PAD_TOP + CONTENT, FRAME)):
                if any(px[3] != 0 for px in r[k * FRAME + y]):
                    bad_pad.append((k, y))
        for row in r:
            for px in row:
                if 0 < px[3] < 255:
                    semi += 1
        eq(u"A8 每帧内容都在 y=%d..%d（照 titanium_ingot 的摆位）"
           % (PAD_TOP, PAD_TOP + CONTENT - 1), [], bad_bbox)
        eq(u"A9 每帧上下留白全透明", [], bad_pad)
        eq(u"A10 零半透明像素", 0, semi)
    # 摆位基准还在不在（依据不能悄悄变）
    rw, rh, rbuf = read_png(os.path.join(TEXI, u"titanium_ingot.png"))
    rys = [y for y in range(rh) if any(px[3] > 0 for px in rows(rw, rh, rbuf)[y])]
    eq(u"A11 摆位基准 titanium_ingot.png 仍是 %d×%d、内容 y=%d..%d"
       % (FRAME, FRAME, PAD_TOP, PAD_TOP + CONTENT - 1),
       (FRAME, FRAME, PAD_TOP, PAD_TOP + CONTENT - 1), (rw, rh, min(rys), max(rys)))
    # 与源图逐像素等价
    sw, sh, sbuf = read_png(srcart)
    starts, scounts, srows = ingot_starts(sw, sh, sbuf)
    eq(u"A12 源图里检出 %d 个锭（每帧一个）" % N_FRAMES, N_FRAMES, len(starts))
    if len(starts) == N_FRAMES and r is not None:
        diff = []
        for k, s in enumerate(starts):
            for rr in range(CONTENT):
                if r[k * FRAME + PAD_TOP + rr] != srows[s + rr]:
                    diff.append((k, rr))
                    break
        eq(u"A13 每帧内容**逐像素等于**源图里那个锭（零重采样）", [], diff)
    # 帧真的在动
    if r is not None:
        uniq = len(set(tuple(tuple(px) for px in r[k * FRAME + PAD_TOP + 1])
                       for k in range(N_FRAMES)))
        check(u"A14 至少 3 种不同的帧（真的在动，实际 %d 种）" % uniq, uniq >= 3)
        same_pairs = sum(1 for k in range(N_FRAMES - 1)
                         if all(r[k * FRAME + y] == r[(k + 1) * FRAME + y] for y in range(FRAME)))
        check(u"A15 相邻帧完全相同的对数 ≤ 2（实际 %d）" % same_pairs, same_pairs <= 2)
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
    eq(u"B6 **没有任何配方**产出它（用户明说「目前没配方」）", [], hits)
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
    check(u"D6 交接文档的键数已到 %d" % KEY_NEW, (u"%d 键" % KEY_NEW) in hand)
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
