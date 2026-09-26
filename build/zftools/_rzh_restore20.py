# -*- coding: utf-8 -*-
r"""_rzh_restore20.py —— 把被误伤的 20 个「物品 / 方块显示名」按 HEAD 逐字节恢复。

事故经过（_rzh_adv_titles.py 第一版）：
  它的定位方式是 `raw.find('"advancements.potato_s_t.<id>.title"')`，然后取该位置之后
  第一个字符串字面量当"老值"。但**成就键块在文件末尾，物品名在前面** —— 对
  `starfall` 来说，`"advancements.potato_s_t.starfall.title"` 首次出现的位置**在
  物品行 `"item.potato_s_t.starfall_pendant": "星轨坠"` 之后**，于是它把**物品名的值**
  当成了成就标题来替换 ⇒ 物品名被写成了成就名。
  那道"键后同一个字面量出现次数"的守卫**并没有校验键值配对**，所以没能拦住。

  受害键共 20 个（5 个 × 4 语言），全部是 item./block. 显示名。

本脚本只做一件事：把这些键的值按 `HEAD:` 恢复。其余一律不动。
"""
import io
import json
import subprocess
import sys

GIT = r"C:\Program Files\Git\cmd\git.exe"
LANG = u"src/main/resources/assets/potato_s_t/lang/%s.json"
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]

# 事故波及的键（由「HEAD vs 工作树」机械算出，不凭记忆）
HURT = [
    u"item.potato_s_t.starfall_pendant",
    u"item.potato_s_t.sea_salt",
    u"item.potato_s_t.capacitor",
    u"item.potato_s_t.sulfur",
    u"block.potato_s_t.electric_blast_furnace",
    u"block.potato_s_t.alloy_smelter_part",
]


def head(path):
    out = subprocess.run([GIT, u"show", u"HEAD:" + path], capture_output=True, check=True).stdout
    return json.loads(out.decode(u"utf-8"))


total = 0
for loc in LOCALES:
    rel = LANG % loc
    old = head(rel)
    raw = io.open(rel, encoding=u"utf-8", newline=u"").read()
    data = json.loads(raw)
    touched = []
    for k in HURT:
        if k not in old or k not in data or data[k] == old[k]:
            continue
        cur_lit = json.dumps(data[k], ensure_ascii=False)
        want_lit = json.dumps(old[k], ensure_ascii=False)
        # ⚠ 严格按**行首键**定位：`    "key":` —— 这才保证键值配对
        anchor = u'    ' + json.dumps(k, ensure_ascii=False) + u':'
        i = raw.find(anchor)
        if i < 0:
            print(u"[!!] %s：找不到行首键 %s" % (loc, k))
            sys.exit(1)
        if raw.count(anchor) != 1:
            print(u"[!!] %s：行首键 %s 出现 %d 次" % (loc, k, raw.count(anchor)))
            sys.exit(1)
        j = raw.index(u'"', raw.index(u":", i) + 1)
        m = j + 1
        while True:
            if raw[m] == u"\\":
                m += 2
                continue
            if raw[m] == u'"':
                break
            m += 1
        if raw[j:m + 1] != cur_lit:
            print(u"[!!] %s / %s：取到的字面量与解析值不符" % (loc, k))
            sys.exit(1)
        raw = raw[:j] + want_lit + raw[m + 1:]
        touched.append((k, data[k], old[k]))

    if touched:
        back = json.loads(raw)
        assert len(back) == len(data), u"键数变了"
        io.open(rel, u"w", encoding=u"utf-8", newline=u"").write(raw)
        print(u"== %s：恢复 %d 个" % (loc, len(touched)))
        for k, a, b in touched:
            print(u"    %-44s %s → %s" % (k, a, b))
        total += len(touched)
    else:
        print(u"== %s：无需恢复" % loc)

print(u"\n合计恢复 %d 个键" % total)
