# -*- coding: utf-8 -*-
"""音效一致性自检（ZF36 新写，本项目第 7 个可脱离游戏跑的检查）。

为什么需要它：音效链路的坏法**全是静默的** ——
  · `ModSounds` 里注册了，`sounds.json` 里键名打错一个字母 ⇒ 游戏里**不报错、就是没声音**；
  · `sounds.json` 指的 `sounds/<x>.ogg` 文件不存在 ⇒ 同上；
  · ogg 不是 **44100 Hz 单声道** ⇒ 立体声不吃距离衰减、采样率不对会变速变调（§8）。
`ModelCheck` 管模型、`JsonCheck` 管 JSON 合法性，都覆盖不到这三条。

本脚本查四件事：
  ① `ModSounds.java` 里 `SOUND_EVENTS.register("<名>"` 的每个名字，`sounds.json` 里必须有同名键
  ② `sounds.json` 里每个音效名 `potato_s_t:<x>`，`sounds/<x>.ogg` 必须存在
  ③ 每个 ogg 必须是 44100 Hz 单声道 Vorbis
  ④ 反向找孤儿：sounds.json 里有键但没注册 / on-disk 有 ogg 但没人引用

退出码 0 = 全过。
"""
import io
import json
import os
import re
import sys

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
SOUNDS_JSON = os.path.join(ASSETS, "sounds.json")
SOUNDS_DIR = os.path.join(ASSETS, "sounds")
MODSOUNDS = os.path.join(ROOT, r"src\main\java\com\potatost\mod\sound\ModSounds.java")

fail = []


def check(ok, msg):
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fail.append(msg)


def warn(msg):
    print("  [WARN] " + msg)


# ---- 读注册名 ----
src = io.open(MODSOUNDS, encoding="utf-8").read()
registered = re.findall(r'SOUND_EVENTS\.register\(\s*"([^"]+)"', src)
print("ModSounds 注册了 %d 个音效：%s" % (len(registered), ", ".join(registered)))

# ---- 读 sounds.json ----
with io.open(SOUNDS_JSON, encoding="utf-8") as f:
    sounds = json.load(f)
print("sounds.json 有 %d 个键：%s" % (len(sounds), ", ".join(sorted(sounds))))

print()
print("== ① 注册名 -> sounds.json 键 ==")
for name in registered:
    check(name in sounds, "sounds.json 有键 \"%s\"" % name)

print()
print("== ② sounds.json -> 文件存在 ==")
referenced = set()
for key, entry in sorted(sounds.items()):
    for s in entry.get("sounds", []):
        nm = s["name"] if isinstance(s, dict) else s
        if not nm.startswith("potato_s_t:"):
            warn("%s 引用了非本模组音效 %s（跳过文件检查）" % (key, nm))
            continue
        stem = nm.split(":", 1)[1]
        referenced.add(stem)
        path = os.path.join(SOUNDS_DIR, stem + ".ogg")
        check(os.path.exists(path), "%s -> sounds/%s.ogg 存在" % (key, stem))

print()
print("== ③ 每个 ogg 必须是 44100 Hz 单声道 Vorbis ==")
try:
    import soundfile as sf
    have_sf = True
except ImportError:
    have_sf = False
    warn("没装 soundfile，跳过格式检查（pip install soundfile）")

on_disk = sorted(f[:-4] for f in os.listdir(SOUNDS_DIR) if f.endswith(".ogg"))
print("  sounds/ 下 %d 个 ogg：%s" % (len(on_disk), ", ".join(on_disk)))
if have_sf:
    for stem in on_disk:
        info = sf.info(os.path.join(SOUNDS_DIR, stem + ".ogg"))
        ok = (info.samplerate == 44100 and info.channels == 1 and info.format == "OGG"
              and info.subtype == "VORBIS")
        check(ok, "%-34s %5.2fs  %d Hz  %d 声道  %s/%s"
              % (stem + ".ogg", info.duration, info.samplerate, info.channels,
                 info.format, info.subtype))

print()
print("== ④ 孤儿 ==")
for name in registered:
    if name not in sounds:
        warn("注册了但 sounds.json 没键：%s" % name)
for key in sorted(sounds):
    if key not in registered:
        warn("sounds.json 有键但 ModSounds 没注册：%s" % key)
for stem in on_disk:
    if stem not in referenced:
        warn("sounds/%s.ogg 没有任何 sounds.json 条目引用" % stem)

print()
print("失败项 = %d" % len(fail))
if fail:
    for m in fail:
        print("   - " + m)
    sys.exit(1)
print("结论: 全部通过")
