# -*- coding: utf-8 -*-
u"""_zf93_apply.py —— ZF93 动手：加第二张音乐唱片《茉莉花（管弦乐）》（§6.1 那 6 处联动）

用户给的：`Jasmine_Flower_Strings_mono.ogg`（1691739 字节 / sha256 `ca2493b0…`）
         + 贴图 `音乐唱片茉莉花.png`（ZF92 已留档）+ 一句「这是 茉莉花(管弦乐) 的音乐唱片 贴图在item里」。

实测（`_zf93_ogg.py`，两条独立算法：soundfile 与自解 Ogg 末页 granule，都是 **147.102132 s**）：
  **单声道 / 44100 Hz / Ogg Vorbis** —— 正好是本工程要的规格，**不需要转码**，原字节复制即可。

命名：物品 `music_disc_jasmine_flower` / 曲目 `jasmine_flower` / 声音事件 `music_disc_jasmine_flower`。
比较器输出取 **15**（与第一张唱片一致，原版最长的那批也是 15）。
`length_in_seconds` 取 **147.1**（与第一张唱片同样的"1 位小数"写法：103.53898 → 103.5）。

⚠ 不做合成配方：第一张唱片也没有（`data/potato_s_t/recipe` 里没有唱片配方），本轮保持一致、不发明。

用法：
    python _zf93_apply.py            # 预演
    python _zf93_apply.py --write    # 真做
"""
import hashlib
import io
import json
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
DATA = os.path.join(ROOT, r"src\main\resources\data\potato_s_t")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
TOOLS = os.path.join(ROOT, "build", "zftools")
DOCS = os.path.join(ROOT, "docs")
OGG_SRC = (r"C:\Users\Administrator\.dsh\attachments\v1\files\ca"
           r"\ca2493b0bb4cbaf6fd1784245eb0490042405bec922b6c0e4918de2a841939be"
           r"\Jasmine_Flower_Strings_mono.ogg")
OGG_SHA256 = "ca2493b0bb4cbaf6fd1784245eb0490042405bec922b6c0e4918de2a841939be"
PNG_SRC = os.path.join(ROOT, "build", u"用户素材", "music_disc_jasmine_flower.png")
PNG_SHA1 = "0b1bf5f444a2cd4f320831652c6067c097a0d54d"
ITEM = "music_disc_jasmine_flower"
SONG = "jasmine_flower"
LENGTH = 147.1
COMPARATOR = 15
LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]
LANG_NEW = {
    "zh_cn": (u"音乐唱片", u"茉莉花（管弦乐）"),
    "en_us": (u"Music Disc", u"Jasmine Flower (Orchestral)"),
    "ja_jp": (u"音楽ディスク", u"茉莉花（管弦楽）"),
    "ru_ru": (u"Пластинка", u"Жасмин (оркестр)"),
}
EXPECT_KEYS = 272          # 270 + 2
fails = []
patched = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def patch(path, old, new, label, expect=1):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != expect:
        fails.append(u"%s：锚点命中 %d 次（必须 %d 次）" % (label, hits, expect))
        return False
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    patched.append(label)
    print(u"  [OK]   %s" % label)
    return True


def main(argv):
    write = "--write" in argv
    print(u"== ① 落两个新资源（音频与贴图都**原字节复制**）==")
    print(u"  %s → sounds/%s.ogg" % (os.path.basename(OGG_SRC), ITEM))
    print(u"  %s → textures/item/%s.png" % (os.path.basename(PNG_SRC), ITEM))
    if not os.path.exists(OGG_SRC):
        fails.append(u"用户音频不在：%s" % OGG_SRC)
    elif sha256(OGG_SRC) != OGG_SHA256:
        fails.append(u"音频 sha256 与留档不符")
    elif os.path.exists(PNG_SRC) and sha1(PNG_SRC) != PNG_SHA1:
        fails.append(u"贴图 sha1 与凭据不符")
    if fails:
        print(u"[STOP] 入参不对 ⇒ 什么都不写")
        for f in fails:
            print(u"  !! " + f)
        return 1
    if not write:
        print(u"\n预演：没加 --write，什么都不写")
        return 0

    dst_ogg = os.path.join(ASSETS, "sounds", ITEM + ".ogg")
    dst_png = os.path.join(ASSETS, "textures", "item", ITEM + ".png")
    os.makedirs(os.path.dirname(dst_ogg), exist_ok=True)
    shutil.copy2(OGG_SRC, dst_ogg)
    shutil.copy2(PNG_SRC, dst_png)
    if sha256(dst_ogg) != OGG_SHA256:
        fails.append(u"复制后音频哈希不一致")
    else:
        print(u"  [OK]   %s（%d 字节，sha256 一致）" % (os.path.basename(dst_ogg), os.path.getsize(dst_ogg)))
    if sha1(dst_png) != PNG_SHA1:
        fails.append(u"复制后贴图哈希不一致")
    else:
        print(u"  [OK]   %s（%d 字节，sha1 一致）" % (os.path.basename(dst_png), os.path.getsize(dst_png)))

    print(u"\n== ② 两个新 JSON ==")
    model = os.path.join(ASSETS, "models", "item", ITEM + ".json")
    io.open(model, "w", encoding="utf-8", newline=u"\n").write(
        u'{ "parent": "minecraft:item/template_music_disc", "textures": '
        u'{ "layer0": "potato_s_t:item/%s" } }\n' % ITEM)
    print(u"  [OK]   models/item/%s.json" % ITEM)
    song = os.path.join(DATA, "jukebox_song", SONG + ".json")
    io.open(song, "w", encoding="utf-8", newline=u"\n").write(json.dumps({
        "comparator_output": COMPARATOR,
        "description": {"translate": "jukebox_song.potato_s_t." + SONG},
        "length_in_seconds": LENGTH,
        "sound_event": "potato_s_t:" + ITEM,
    }, ensure_ascii=False, indent=2) + u"\n")
    print(u"  [OK]   data/potato_s_t/jukebox_song/%s.json（%.1f s / 比较器 %d）" % (SONG, LENGTH, COMPARATOR))

    print(u"\n== ③ sounds.json（长音频必须 stream: true）==")
    sp = os.path.join(ASSETS, "sounds.json")
    old = (u'  "music_disc_anvil_of_the_republic": {\n'
           u'    "sounds": [ { "name": "potato_s_t:music_disc_anvil_of_the_republic", "stream": true } ]\n'
           u'  },\n')
    new = old + (u'  "%s": {\n'
                 u'    "sounds": [ { "name": "potato_s_t:%s", "stream": true } ]\n'
                 u'  },\n' % (ITEM, ITEM))
    patch(sp, old, new, u"sounds.json 加 %s 条目" % ITEM)
    json.loads(io.open(sp, encoding="utf-8").read())
    print(u"  [OK]   sounds.json 仍是合法 JSON（%d 个条目）"
          % len(json.loads(io.open(sp, encoding="utf-8").read())))

    print(u"\n== ④ ModSounds.java ==")
    ms = os.path.join(JAVA, "sound", "ModSounds.java")
    anchor = (u'                            ResourceLocation.fromNamespaceAndPath('
              u'"potato_s_t", "music_disc_anvil_of_the_republic")));\n')
    add = anchor + (u'\n    /** 音乐唱片《茉莉花（管弦乐）》（0.11 ZF93）。曲目数据见 '
                    u'data/potato_s_t/jukebox_song/%s.json；\n'
                    u'     *  音频实测 147.102132 s / 单声道 44100 Hz（build/zftools/_zf93_ogg.py 两条算法互核）。 */\n'
                    u'    public static final DeferredHolder<SoundEvent, SoundEvent> MUSIC_DISC_JASMINE_FLOWER =\n'
                    u'            SOUND_EVENTS.register("%s",\n'
                    u'                    () -> SoundEvent.createVariableRangeEvent(\n'
                    u'                            ResourceLocation.fromNamespaceAndPath("potato_s_t", "%s")));\n'
                    % (SONG, ITEM, ITEM))
    patch(ms, anchor, add, u"ModSounds.java 加 MUSIC_DISC_JASMINE_FLOWER")

    print(u"\n== ⑤ ModItems.java（曲目键 + 物品 + 创造页）==")
    mi = os.path.join(JAVA, "ModItems.java")
    anchor = u'                    .jukeboxPlayable(ANVIL_OF_THE_REPUBLIC_SONG)));\n'
    add = anchor + (u'\n    /**\n'
                    u'     * 曲目键：对应 {@code data/potato_s_t/jukebox_song/%s.json}（0.11 ZF93 第二张唱片）。\n'
                    u'     *\n'
                    u'     * <p>用户原话：「这是 茉莉花(管弦乐) 的音乐唱片 贴图在item里」。音频是用户给的\n'
                    u'     * {@code Jasmine_Flower_Strings_mono.ogg}（1691739 字节）：<b>单声道 44100 Hz Ogg Vorbis</b>，\n'
                    u'     * 实测 <b>%.6f s</b>（{@code _zf93_ogg.py} 用 soundfile 与自解 Ogg 末页 granule 两条算法互核），\n'
                    u'     * 所以 {@code length_in_seconds} 写 %.1f。</p>\n'
                    u'     */\n'
                    u'    public static final ResourceKey<JukeboxSong> JASMINE_FLOWER_SONG =\n'
                    u'            ResourceKey.create(Registries.JUKEBOX_SONG,\n'
                    u'                    ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "%s"));\n'
                    u'\n'
                    u'    /** 音乐唱片：《茉莉花（管弦乐）》。放进唱片机即可播放 */\n'
                    u'    public static final DeferredItem<Item> MUSIC_DISC_JASMINE_FLOWER =\n'
                    u'            ITEMS.register("%s", () -> new Item(new Item.Properties()\n'
                    u'                    .stacksTo(1)\n'
                    u'                    .rarity(Rarity.RARE)\n'
                    u'                    .jukeboxPlayable(JASMINE_FLOWER_SONG)));\n'
                    % (SONG, 147.102132, LENGTH, SONG, ITEM))
    patch(mi, anchor, add, u"ModItems.java 加曲目键与唱片物品")
    anchor2 = u'                        output.accept(MUSIC_DISC_ANVIL_OF_THE_REPUBLIC.get());// ← 新增（0.04 音乐唱片）\n'
    patch(mi, anchor2, anchor2 + u'                        output.accept(MUSIC_DISC_JASMINE_FLOWER.get());// ← 新增（0.11 ZF93 第二张唱片）\n',
          u"ModItems.java 创造页加一张")

    print(u"\n== ⑥ 四份 lang（各 +2 键，270 → %d）==" % EXPECT_KEYS)
    for lg in LANGS:
        p = os.path.join(ASSETS, "lang", lg + ".json")
        before = json.loads(io.open(p, encoding="utf-8").read())
        item_name, song_name = LANG_NEW[lg]
        t = io.open(p, encoding="utf-8").read()
        # ① 物品键：插在第一位唱片物品键那一行之后（行内定位，避免各语言取值不同导致锚点不唯一）
        key1 = u'"item.potato_s_t.music_disc_anvil_of_the_republic"'
        key2 = u'"jukebox_song.potato_s_t.anvil_of_the_republic"'
        lines = t.split(u"\n")
        out, n1, n2 = [], 0, 0
        for ln in lines:
            out.append(ln)
            if key1 in ln:
                n1 += 1
                out.append(u'    "item.potato_s_t.%s":  "%s",' % (ITEM, item_name))
            if key2 in ln:
                n2 += 1
                out.append(u'    "jukebox_song.potato_s_t.%s":  "%s",' % (SONG, song_name))
        if n1 != 1 or n2 != 1:
            fails.append(u"%s：物品键命中 %d 次 / 曲目键命中 %d 次（必须各 1 次）" % (lg, n1, n2))
            continue
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(out))
        after = json.loads(io.open(p, encoding="utf-8").read())
        if len(after) != len(before) + 2:
            fails.append(u"%s：键数 %d → %d（应 +2）" % (lg, len(before), len(after)))
        if len(after) != EXPECT_KEYS:
            fails.append(u"%s：键数 %d，期望 %d" % (lg, len(after), EXPECT_KEYS))
        patched.append(u"%s 语言 +2 键（%d）" % (lg, len(after)))
        print(u"  [OK]   %s：%d → %d 键" % (lg, len(before), len(after)))
    sets = {lg: set(json.loads(io.open(os.path.join(ASSETS, "lang", lg + ".json"),
                                       encoding="utf-8").read())) for lg in LANGS}
    base = sets[LANGS[0]]
    for lg in LANGS[1:]:
        if sets[lg] != base:
            fails.append(u"%s 键集合与 zh_cn 不一致：多 %s 少 %s"
                         % (lg, sorted(sets[lg] - base), sorted(base - sets[lg])))
    if not fails:
        print(u"  [OK]   四份键集合完全一致（各 %d 键）" % len(base))

    print(u"\n== ⑦ 活体数字：八个往轮校验 + 英文公告（270 → %d）==" % EXPECT_KEYS)
    patch(os.path.join(TOOLS, "_zf71_verify.py"),
          u'set(keys.values()) == {270} and u"270 keys each" in doc',
          u'set(keys.values()) == {%d} and u"%d keys each" in doc' % (EXPECT_KEYS, EXPECT_KEYS),
          u"_zf71_verify.py 键数 → %d" % EXPECT_KEYS)
    patch(os.path.join(TOOLS, "_zf73_verify.py"),
          u'check(u"B11 四语言各 270 键（ZF78 27 + ZF79 2 + ZF80 9 + ZF82 13）", all(v == 270 for v in counts.values()), str(counts))',
          u'check(u"B11 四语言各 %d 键（ZF78 27 + ZF79 2 + ZF80 9 + ZF82 13 + ZF93 2）", all(v == %d for v in counts.values()), str(counts))'
          % (EXPECT_KEYS, EXPECT_KEYS),
          u"_zf73_verify.py B11 键数 → %d" % EXPECT_KEYS)
    patch(os.path.join(TOOLS, "_zf75_verify.py"),
          u'check(u"C2 四语言各 270 键（ZF82 起）", all(v == 270 for v in counts.values()), str(counts))',
          u'check(u"C2 四语言各 %d 键（ZF93 起）", all(v == %d for v in counts.values()), str(counts))'
          % (EXPECT_KEYS, EXPECT_KEYS),
          u"_zf75_verify.py C2 键数 → %d" % EXPECT_KEYS)
    patch(os.path.join(TOOLS, "_zf78_verify.py"),
          u'check(u"四份语言键数一致且 = 270（ZF82 容器换流器 + 两个桶又 +13）",\n'
          u'          len(set(counts.values())) == 1 and list(counts.values())[0] == 270)',
          u'check(u"四份语言键数一致且 = %d（ZF93 第二张唱片又 +2）",\n'
          u'          len(set(counts.values())) == 1 and list(counts.values())[0] == %d)'
          % (EXPECT_KEYS, EXPECT_KEYS),
          u"_zf78_verify.py 键数 → %d" % EXPECT_KEYS)
    patch(os.path.join(TOOLS, "_zf79_verify.py"),
          u'check(u"四份语言键数一致且 = 270（ZF82 容器换流器 + 两个桶 +13）",\n'
          u'          len(set(counts.values())) == 1 and list(counts.values())[0] == 270)',
          u'check(u"四份语言键数一致且 = %d（ZF93 第二张唱片 +2）",\n'
          u'          len(set(counts.values())) == 1 and list(counts.values())[0] == %d)'
          % (EXPECT_KEYS, EXPECT_KEYS),
          u"_zf79_verify.py 键数 → %d" % EXPECT_KEYS)
    patch(os.path.join(TOOLS, "_zf80_verify.py"),
          u'EXPECT_KEYS = 270', u'EXPECT_KEYS = %d' % EXPECT_KEYS,
          u"_zf80_verify.py EXPECT_KEYS → %d" % EXPECT_KEYS)
    patch(os.path.join(TOOLS, "_zf81_verify.py"),
          u'eq(u"语言键数（ZF82 起 270：换流器 + 两个桶 +13）", 270, len(inside))',
          u'eq(u"语言键数（ZF93 起 %d：第二张唱片 +2）", %d, len(inside))' % (EXPECT_KEYS, EXPECT_KEYS),
          u"_zf81_verify.py jar 键数 → %d" % EXPECT_KEYS)
    patch(os.path.join(TOOLS, "_zf82_verify.py"),
          u'EXPECT_KEYS = 270', u'EXPECT_KEYS = %d' % EXPECT_KEYS,
          u"_zf82_verify.py EXPECT_KEYS → %d" % EXPECT_KEYS)
    patch(os.path.join(TOOLS, "_zf82_verify.py"),
          u'u"270 keys each" in ann', u'u"%d keys each" in ann' % EXPECT_KEYS,
          u"_zf82_verify.py 公告键数 → %d" % EXPECT_KEYS)
    patch(os.path.join(DOCS, "UpdateAnnouncement_EN.md"),
          u'(270 keys each)', u'(%d keys each)' % EXPECT_KEYS,
          u"英文公告键数 → %d" % EXPECT_KEYS)

    print(u"\n== ⑧ 收尾自检 ==")
    print(u"  改动/新增 %d 处" % len(patched))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
