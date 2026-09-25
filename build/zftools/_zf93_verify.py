# -*- coding: utf-8 -*-
r"""_zf93_verify.py —— ZF93 常驻校验：第二张音乐唱片《茉莉花（管弦乐）》

加一张唱片要动 §6.1 那 6 处，任何一处漏了都会**静默出问题**（不报错、只是不响或显示英文键名）：
  · 少 `sounds.json` ⇒ 播放时静默（日志里才有 "Unable to play unknown soundEvent"）；
  · 少 `sound_event` 注册 ⇒ 同上；
  · `length_in_seconds` 写错 ⇒ 唱片机**提前停播或永不停止**、比较器输出不对；
  · 少 `jukebox_song/*.json` ⇒ 放进唱片机直接**不播**（曲目键解析不出来）；
  · 少贴图 ⇒ 紫黑块；少 lang 键 ⇒ 显示 `item.potato_s_t.…` 原文。

所以这里**逐条对着实物核**（音频时长是**现场量**的，不是抄注释里的数）。
"""
import hashlib
import io
import json
import os
import re
import struct
import sys
import zipfile

TRY_SF = True
try:
    import soundfile as sf
except Exception:                                     # pragma: no cover
    TRY_SF = False

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
DATA = os.path.join(ROOT, r"src\main\resources\data\potato_s_t")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
DOCS = os.path.join(ROOT, "docs")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
USERART = os.path.join(ROOT, "build", u"用户素材")
ITEM = "music_disc_jasmine_flower"
SONG = "jasmine_flower"
OGG = os.path.join(ASSETS, "sounds", ITEM + ".ogg")
OGG_SHA256 = "ca2493b0bb4cbaf6fd1784245eb0490042405bec922b6c0e4918de2a841939be"
PNG = os.path.join(ASSETS, "textures", "item", ITEM + ".png")
PNG_SHA1 = "0b1bf5f444a2cd4f320831652c6067c097a0d54d"
EXPECT_LENGTH = 147.1
EXPECT_KEYS = 398           # … + ZF107 成就 48 键
LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]
passed = 0
failed = 0
fails = []


def check(label, cond):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label)
        print(u"  [FAIL] " + label)


def eq(label, want, got):
    check(u"%s（期望 %r，实际 %r）" % (label, want, got), want == got)


def read(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else None


def sha1f(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def sha256f(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def ogg_duration(path):
    u"""两条独立算法：soundfile（若可用）与自解 Ogg 末页 granule。"""
    durs = []
    if TRY_SF:
        durs.append(sf.info(path).duration)
    data = io.open(path, "rb").read()
    pos, last, rate = 0, 0, None
    while pos < len(data) and data[pos:pos + 4] == b"OggS":
        seg = data[pos + 26]
        body = pos + 27 + seg
        n = sum(data[pos + 27:body])
        g = struct.unpack("<q", data[pos + 6:pos + 14])[0]
        if g > 0:
            last = g
        if rate is None and data[body:body + 7] == b"\x01vorbis":
            rate = struct.unpack("<I", data[body + 12:body + 16])[0]
        pos = body + n
    if last and rate:
        durs.append(last / float(rate))
    return durs


def main():
    print(u"=========== ZF93 校验：第二张音乐唱片《茉莉花（管弦乐）》===========")

    print(u"\n== A 音频实物（时长现场量，不抄注释）==")
    check(u"声音文件在（sounds/%s.ogg）" % ITEM, os.path.exists(OGG))
    if os.path.exists(OGG):
        eq(u"音频 sha256 = 用户给的那份", OGG_SHA256, sha256f(OGG))
        print(u"         字节 %d" % os.path.getsize(OGG))
        durs = ogg_duration(OGG)
        print(u"         实测时长（%d 条算法）：%s" % (len(durs), u" / ".join(u"%.6f" % d for d in durs)))
        if len(durs) >= 2:
            check(u"两条算法量出的时长一致（差 < 1 ms）", abs(durs[0] - durs[1]) < 1e-3)
        if durs:
            check(u"实测时长与 jukebox_song 的 length_in_seconds 对得上（差 < 0.5 s）",
                  abs(durs[0] - EXPECT_LENGTH) < 0.5)
        if TRY_SF:
            info = sf.info(OGG)
            eq(u"声道数（MC 要单声道）", 1, info.channels)
            eq(u"采样率", 44100, info.samplerate)

    print(u"\n== B 贴图与模型 ==")
    check(u"贴图在（textures/item/%s.png）" % ITEM, os.path.exists(PNG))
    if os.path.exists(PNG):
        eq(u"贴图 sha1 = 用户那张（留档在 build/用户素材）", PNG_SHA1, sha1f(PNG))
        check(u"留档件与在用件逐字节相同",
              os.path.exists(os.path.join(USERART, ITEM + ".png"))
              and sha1f(os.path.join(USERART, ITEM + ".png")) == PNG_SHA1)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import _zf66_png
        w, h, ct, px = _zf66_png.read_png(PNG)
        eq(u"贴图规格 16×16 / RGBA", (16, 16, 6), (w, h, ct))
        check(u"贴图有透明底（不是整张不透明）", any(p[3] == 0 for p in px))
    mj = read(os.path.join(ASSETS, "models", "item", ITEM + ".json")) or u""
    check(u"物品模型指 template_music_disc 且用自己那张贴图",
          u"minecraft:item/template_music_disc" in mj and u"potato_s_t:item/" + ITEM in mj)

    print(u"\n== C 曲目数据（1.21.1 schema）==")
    sp = os.path.join(DATA, "jukebox_song", SONG + ".json")
    check(u"曲目文件在（jukebox_song/%s.json）" % SONG, os.path.exists(sp))
    if os.path.exists(sp):
        d = json.loads(read(sp))
        eq(u"sound_event 是**纯字符串**（不是 1.21.2+ 的对象形式）",
           u"potato_s_t:" + ITEM, d.get("sound_event"))
        eq(u"description.translate", u"jukebox_song.potato_s_t." + SONG,
           (d.get("description") or {}).get("translate"))
        eq(u"length_in_seconds", EXPECT_LENGTH, float(d.get("length_in_seconds", -1)))
        co = d.get("comparator_output")
        check(u"comparator_output 是 1..15 的整数（实际 %r）" % (co,),
              isinstance(co, int) and 1 <= co <= 15)
        eq(u"曲目文件里的 JSON 键集合", {"comparator_output", "description",
                                        "length_in_seconds", "sound_event"}, set(d))
    # 声音事件必须在 sounds.json 里，且长音频要 stream
    sj = json.loads(read(os.path.join(ASSETS, "sounds.json")) or u"{}")
    check(u"sounds.json 里有 %s 条目" % ITEM, ITEM in sj)
    if ITEM in sj:
        snds = sj[ITEM].get("sounds") or []
        check(u"该条目 stream = true（长音频不能整段解码进内存）",
              len(snds) == 1 and snds[0].get("stream") is True)
        eq(u"该条目指向的声音名", "potato_s_t:" + ITEM, snds[0].get("name"))

    print(u"\n== D Java 注册 ==")
    ms = read(os.path.join(JAVA, "sound", "ModSounds.java")) or u""
    check(u"ModSounds：注册了 %s 声音事件" % ITEM,
          u'MUSIC_DISC_JASMINE_FLOWER' in ms and u'SOUND_EVENTS.register("%s"' % ITEM in ms)
    mi = read(os.path.join(JAVA, "ModItems.java")) or u""
    check(u"ModItems：曲目键指向 potato_s_t:%s" % SONG,
          u'JASMINE_FLOWER_SONG' in mi
          and re.search(r'ResourceKey\.create\(Registries\.JUKEBOX_SONG,\s*\n\s*'
                        r'ResourceLocation\.fromNamespaceAndPath\(PotatoST\.MODID, "%s"\)\)' % SONG, mi))
    check(u"ModItems：物品注册 id = %s" % ITEM, u'ITEMS.register("%s"' % ITEM in mi)
    # ⚠ 正则第一版写成 `\}\)\);`（以为物品块以 `}));` 收尾）—— 实际是 `() -> new Item(...))` 收尾，
    #   结尾只有 `)));`，没有花括号 ⇒ 断言恒假、假 FAIL。改成"从 register 到本语句分号"。
    blk = re.search(r'ITEMS\.register\("%s"[^;]*;' % ITEM, mi, re.S)
    check(u"ModItems：物品带 stacksTo(1) / Rarity.RARE / jukeboxPlayable(JASMINE_FLOWER_SONG)",
          bool(blk) and u".stacksTo(1)" in blk.group(0)
          and u"Rarity.RARE" in blk.group(0)
          and u".jukeboxPlayable(JASMINE_FLOWER_SONG)" in blk.group(0))
    check(u"ModItems：创造页里能拿到", u"output.accept(MUSIC_DISC_JASMINE_FLOWER.get())" in mi)

    print(u"\n== E 语言（四份各 %d 键，两张唱片的键都在）==" % EXPECT_KEYS)
    keysets = {}
    for lg in LANGS:
        d = json.loads(read(os.path.join(ASSETS, "lang", lg + ".json")) or u"{}")
        keysets[lg] = set(d)
        eq(u"%s 键数" % lg, EXPECT_KEYS, len(d))
        check(u"%s 有物品键与曲目键" % lg,
              u"item.potato_s_t." + ITEM in d and u"jukebox_song.potato_s_t." + SONG in d)
        check(u"%s 第一张唱片的键仍在" % lg,
              u"item.potato_s_t.music_disc_anvil_of_the_republic" in d
              and u"jukebox_song.potato_s_t.anvil_of_the_republic" in d)
    base = keysets[LANGS[0]]
    check(u"四份键集合完全一致", all(keysets[lg] == base for lg in LANGS))

    print(u"\n== F 第一张唱片没被带坏 ==")
    check(u"第一张的音频/贴图/模型/曲目都在",
          all(os.path.exists(p) for p in [
              os.path.join(ASSETS, "sounds", "music_disc_anvil_of_the_republic.ogg"),
              os.path.join(ASSETS, "textures", "item", "music_disc_anvil_of_the_republic.png"),
              os.path.join(ASSETS, "models", "item", "music_disc_anvil_of_the_republic.json"),
              os.path.join(DATA, "jukebox_song", "anvil_of_the_republic.json")]))
    old = json.loads(read(os.path.join(DATA, "jukebox_song", "anvil_of_the_republic.json")) or u"{}")
    eq(u"老曲目的 length_in_seconds 没动", 103.5, float(old.get("length_in_seconds", -1)))

    print(u"\n== G 成品 jar ==")
    if not os.path.exists(JAR):
        check(u"成品 jar 在", False)
    else:
        sha = sha1f(JAR)
        check(u".sha1 与 jar 一致（%s…）" % sha[:8], (read(JAR + u".sha1") or u"").strip() == sha)
        with zipfile.ZipFile(JAR) as zf:
            names = zf.namelist()
            check(u"成品里没有探针 class",
                  not [n for n in names if "Check" in n.split("/")[-1] and n.endswith(".class")])
            check(u"成品里 assets/ 与 data/ 的条目名全合法（无非 ASCII）",
                  not [n for n in names if (n.startswith(u"assets/") or n.startswith(u"data/"))
                       and not re.fullmatch(u"[a-z0-9/._-]+", n)])
            for rel, disk, what in [
                    (u"assets/potato_s_t/sounds/%s.ogg" % ITEM, OGG, u"音频"),
                    (u"assets/potato_s_t/textures/item/%s.png" % ITEM, PNG, u"贴图"),
                    (u"assets/potato_s_t/models/item/%s.json" % ITEM,
                     os.path.join(ASSETS, "models", "item", ITEM + ".json"), u"物品模型"),
                    (u"data/potato_s_t/jukebox_song/%s.json" % SONG, sp, u"曲目数据")]:
                inside = zf.read(rel) if rel in names else None
                check(u"成品里的%s与盘上一致（%s）" % (what, rel.split("/")[-1]),
                      inside is not None and inside == open(disk, "rb").read())
            inside = zf.read(u"assets/potato_s_t/lang/zh_cn.json")
            eq(u"成品里 zh_cn 键数", EXPECT_KEYS, len(json.loads(inside.decode("utf-8"))))

    print(u"\n== H 文档 ==")
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    listing = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    ann = read(os.path.join(DOCS, "UpdateAnnouncement_EN.md")) or u""
    check(u"档案里有 ZF93 那一行", u"| ZF93 |" in arch)
    check(u"档案里写清了两条算法互核的时长", u"147.102132" in arch)
    check(u"贴图清单里有 ZF93 一节", u"## ZF93" in listing)
    check(u"英文公告键数已跟到 %d" % EXPECT_KEYS, u"(%d keys each)" % EXPECT_KEYS in ann)

    print(u"\n通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
