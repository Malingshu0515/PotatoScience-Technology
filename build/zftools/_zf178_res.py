# -*- coding: utf-8 -*-
u"""_zf178_res.py —— ZF178 的资源三件套：**7 份 loot table** + **2 个方块 tag** + **7 个语言键 ×5**。

（贴图与 blockstate/模型由另一个写手在做；这里只碰 loot_table / tags / lang。）

跑法：python build\\zftools\\_zf178_res.py [--write]
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
LOOT = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\loot_table\blocks")
TEMPLATE = os.path.join(LOOT, u"advanced_metal_block.json")
TAGS = os.path.join(ROOT, r"src\main\resources\data\minecraft\tags\block")
LANGDIR = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]

IDS = [u"magnet_block", u"raw_aluminum_block", u"raw_cobalt_block", u"raw_nickel_block",
       u"raw_silver_block", u"raw_tungsten_block", u"raw_uranium_block"]

NAMES = {
    u"zh_cn": [u"磁铁块", u"粗铝块", u"粗钴块", u"粗镍块", u"粗银块", u"粗钨块", u"粗铀块"],
    u"en_us": [u"Magnet Block", u"Block of Raw Aluminum", u"Block of Raw Cobalt",
               u"Block of Raw Nickel", u"Block of Raw Silver", u"Block of Raw Tungsten",
               u"Block of Raw Uranium"],
    u"ja_jp": [u"磁石ブロック", u"粗アルミニウムのブロック", u"粗コバルトのブロック",
               u"粗ニッケルのブロック", u"粗銀のブロック", u"粗タングステンのブロック",
               u"粗ウランのブロック"],
    u"ru_ru": [u"Блок магнита", u"Блок необработанного алюминия", u"Блок необработанного кобальта",
               u"Блок необработанного никеля", u"Блок необработанного серебра",
               u"Блок необработанного вольфрама", u"Блок необработанного урана"],
    u"lzh": [u"磁石塊", u"粗鋁塊", u"粗鈷塊", u"粗鎳塊", u"粗銀塊", u"粗鎢塊", u"粗鈾塊"],
}


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def main(argv):
    write = u"--write" in argv
    fails, notes = [], []

    # ① loot table：照 advanced_metal_block.json 的样子换 id（两处：name 与 random_sequence）
    tpl = read(TEMPLATE)
    if u"potato_s_t:advanced_metal_block" not in tpl:
        fails.append(u"模板 loot table 里找不到 advanced_metal_block")
    for i in IDS:
        p = os.path.join(LOOT, i + u".json")
        if os.path.isfile(p):
            notes.append(u"loot_table/%s.json：（已存在，跳过）" % i)
            continue
        text = tpl.replace(u"potato_s_t:advanced_metal_block", u"potato_s_t:" + i)
        obj = json.loads(text)
        if obj[u"pools"][0][u"entries"][0][u"name"] != u"potato_s_t:" + i:
            fails.append(u"%s：loot table 内容不对" % i)
            continue
        notes.append(u"loot_table/%s.json" % i)
        if write:
            io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)

    # ② 两个方块 tag：在最后一个 ] 前插 7 行（保留原有排版与顺序）
    for tag in (os.path.join(TAGS, u"mineable", u"pickaxe.json"),
                os.path.join(TAGS, u"needs_stone_tool.json")):
        text = read(tag)
        if not text:
            fails.append(u"tag 不在：%s" % tag)
            continue
        already = [i for i in IDS if u"potato_s_t:" + i in text]
        if len(already) == len(IDS):
            notes.append(u"%s：（已加过）" % os.path.basename(tag))
            continue
        eol = u"\r\n" if u"\r\n" in text else u"\n"
        lines = text.split(eol)
        idx = max(i for i, ln in enumerate(lines) if ln.strip().startswith(u"]"))
        ind = lines[idx - 1][:len(lines[idx - 1]) - len(lines[idx - 1].lstrip())]
        add = [ind + u'"potato_s_t:%s",' % i for i in IDS if u"potato_s_t:" + i not in text]
        # 最后一行原本没有逗号（它在 ] 之前）——补一个，保证 JSON 合法
        if lines[idx - 1].strip() and not lines[idx - 1].rstrip().endswith(u","):
            lines[idx - 1] = lines[idx - 1].rstrip() + u","
        if add:
            add[-1] = add[-1][:-1]      # 最后一条不加逗号
        lines = lines[:idx] + add + lines[idx:]
        new_text = eol.join(lines)
        try:
            parsed = json.loads(new_text)
        except Exception as exc:      # noqa: BLE001
            fails.append(u"%s：改完解析失败 %s" % (tag, exc))
            continue
        if len(parsed[u"values"]) != len(json.loads(text)[u"values"]) + len(add):
            fails.append(u"%s：values 数量对不上" % tag)
            continue
        notes.append(u"%s：+%d 项（共 %d 项）" % (os.path.basename(tag), len(add),
                                             len(parsed[u"values"])))
        if write:
            io.open(tag, "w", encoding="utf-8", newline=u"").write(new_text)

    # ③ 语言：7 个 block.<id> 键 ×5
    for loc in LOCALES:
        p = os.path.join(LANGDIR, loc + u".json")
        text = read(p)
        before = json.loads(text)
        keys = [u"block.potato_s_t." + i for i in IDS]
        if all(k in before for k in keys):
            notes.append(u"%s：（7 个键都在）%d 键" % (loc, len(before)))
            continue
        eol = u"\r\n" if u"\r\n" in text else u"\n"
        lines = text.split(eol)
        anchor = None
        for i, ln in enumerate(lines):
            if ln.strip().startswith(u'"block.potato_s_t.'):
                anchor, ind = i, ln[:len(ln) - len(ln.lstrip())]
                break
        if anchor is None:
            fails.append(u"%s：找不到 block.* 锚点" % loc)
            continue
        add = [ind + u'"%s": %s,' % (k, json.dumps(v, ensure_ascii=False))
               for k, v in zip(keys, NAMES[loc]) if k not in before]
        lines = lines[:anchor] + add + lines[anchor:]
        new_text = eol.join(lines)
        parsed = json.loads(new_text)
        if len(parsed) != len(before) + len(add):
            fails.append(u"%s：键数对不上" % loc)
            continue
        notes.append(u"%s：+%d 键（%d → %d）" % (loc, len(add), len(before), len(parsed)))
        if write:
            io.open(p, "w", encoding="utf-8", newline=u"").write(new_text)

    print(u"模式：%s" % (u"落盘" if write else u"干跑（不写）"))
    for n in notes:
        print(u"  " + n)
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
