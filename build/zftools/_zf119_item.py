# -*- coding: utf-8 -*-
r"""_zf119_item.py —— ZF119：振金锭的**资源与标签**（模型 / c: 标签 / 四语言）

用户原话：「加个振金锭（目前没配方）这是振金锭贴图 做成动态贴图 3t播放一帧」

本脚本只做"文件层"的四件事（Java 那两处插入在 `ModItems.java` 里已经做完）：
  ① 模型 `models/item/vibranium_ingot.json`（照 `raw_vibranium.json` 的格式）；
  ② c: 标签三处（照 star_steel 先例：`ingots/<name>.json` + `<name>_ingots.json` + 父 `ingots.json`）；
  ③ 四语言各加 **1 个键** `item.potato_s_t.vibranium_ingot`（键数 448 → **449**）；
  ④ 回读断言：键数、老键值一个不动、模型/标签内容逐字节。

⚠ 本轮**没有配方**（用户明说）⇒ 本脚本一个配方文件都不写。
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
LANG = os.path.join(ASSETS, "lang")
MODELS = os.path.join(ASSETS, r"models\item")
TAGS = os.path.join(ROOT, r"src\main\resources\data\c\tags\item")

KEY_OLD, KEY_NEW = 448, 449
NAME = u"item.potato_s_t.vibranium_ingot"
NAMES = {
    "zh_cn": u"振金锭",
    "en_us": u"Vibranium Ingot",
    "ja_jp": u"ヴィブラニウムインゴット",
    "ru_ru": u"Слиток вибраниума",
}

fails, notes = [], []


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def main():
    # ---------- ① 模型 ----------
    mp = os.path.join(MODELS, u"vibranium_ingot.json")
    model = {u"parent": u"minecraft:item/generated",
             u"textures": {u"layer0": u"potato_s_t:item/vibranium_ingot"}}
    want = json.dumps(model, ensure_ascii=False, indent=2) + u"\n"
    if os.path.exists(mp) and read(mp) == want:
        notes.append(u"模型已在（同值，跳过）")
    else:
        write(mp, want)
        back = json.loads(read(mp))
        if back != model:
            fails.append(u"模型回读不一致")
        else:
            notes.append(u"模型 models/item/vibranium_ingot.json → %s" % back["textures"]["layer0"])

    # ---------- ② c: 标签三处 ----------
    vals = [u"potato_s_t:vibranium_ingot"]
    for rel in (os.path.join(u"ingots", u"vibranium.json"), u"vibranium_ingots.json"):
        tp = os.path.join(TAGS, rel)
        body = {u"values": vals}
        text = json.dumps(body, ensure_ascii=False, indent=2) + u"\n"
        if os.path.exists(tp) and read(tp) == text:
            notes.append(u"标签 %s 已在（同值，跳过）" % rel)
            continue
        write(tp, text)
        if json.loads(read(tp)).get(u"values") != vals:
            fails.append(u"标签 %s 回读不一致" % rel)
        else:
            notes.append(u"标签 c:%s ← vibranium_ingot"
                         % rel.replace(u"\\", u"/").replace(u".json", u"").replace(u"ingots/", u"ingots/"))
    # 父标签 ingots.json：**只加一行**
    ip = os.path.join(TAGS, u"ingots.json")
    raw = read(ip)
    if u'"potato_s_t:vibranium_ingot"' in raw:
        notes.append(u"父标签 c:ingots 已含它（跳过）")
    else:
        obj = json.loads(raw)
        obj[u"values"].append(u"potato_s_t:vibranium_ingot")
        text = json.dumps(obj, ensure_ascii=False, indent=2) + u"\n"
        before = obj[u"values"][:-1]
        write(ip, text)
        back = json.loads(read(ip))
        if back[u"values"] != before + vals:
            fails.append(u"父标签 c:ingots 回读不一致")
        else:
            notes.append(u"父标签 c:ingots 追加一行（%d → %d 项，旧的一行没动）"
                         % (len(before), len(back[u"values"])))

    # ---------- ③ 四语言 ----------
    for loc, name in sorted(NAMES.items()):
        lp = os.path.join(LANG, loc + u".json")
        raw = read(lp)
        data = json.loads(raw)
        if KEY_NEW not in (len(data),) and data.get(NAME) == name:
            notes.append(u"%s 已经有这个键（同值，跳过）" % loc)
            continue
        if len(data) != KEY_OLD:
            fails.append(u"%s 键数 %d ≠ %d（改动前先看清）" % (loc, len(data), KEY_OLD))
            continue
        anchor = u'    "item.potato_s_t.raw_vibranium":'
        lines = raw.split(u"\n")
        hits = [i for i, l in enumerate(lines) if l.startswith(anchor)]
        if len(hits) != 1:
            fails.append(u"%s：锚点行出现 %d 次" % (loc, len(hits)))
            continue
        lines.insert(hits[0] + 1,
                     u'    %s:  %s,' % (json.dumps(NAME, ensure_ascii=False),
                                        json.dumps(name, ensure_ascii=False)))
        text = u"\n".join(lines)
        back = json.loads(text)
        if len(back) != KEY_NEW:
            fails.append(u"%s：回读键数 %d ≠ %d" % (loc, len(back), KEY_NEW))
            continue
        dropped = [k for k in data if k not in back]
        changed = [k for k in data if k in back and back[k] != data[k]]
        if dropped or changed:
            fails.append(u"%s：动到了老键（丢 %s / 改 %s）" % (loc, dropped[:3], changed[:3]))
            continue
        write(lp, text)
        if json.loads(read(lp)).get(NAME) != name:
            fails.append(u"%s：回读后新键不对" % loc)
            continue
        notes.append(u"%s：%d → %d 键（+1：%s = %s）" % (loc, len(data), len(back), NAME, name))

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
