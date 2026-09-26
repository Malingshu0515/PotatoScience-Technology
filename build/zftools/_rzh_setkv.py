# -*- coding: utf-8 -*-
r"""_rzh_setkv.py —— 语言文件"按键改值"的规范工具（带完整自检）。

为什么有这个东西：本轮我连着栽了两次，根因都是**用"找字符串字面量"来定位**：
  ① `_rzh_adv_titles.py` 第一版用裸 `find('"advancements...title"')` —— 成就标题**与物品名同名**，
     而成就键块在文件末尾、物品名在前面，于是取到的是**物品名的值**，把物品名改成了成就名；
  ② 之后的恢复脚本又和改名脚本互相覆盖。
⇒ 这里改成**按行处理**：只认 `    "完整键":` 这一种行；值的位置以**解析出来的键值**为准；
   每次替换后立刻 `json.loads` 回读，确认"该键 = 目标值"且"键数不变"，否则整体不写盘。

用法（本文件自带一张表；CLI 只是顺手）：
    python _rzh_setkv.py            # 按下面 TABLE 执行
"""
import io
import json
import subprocess
import sys

GIT = r"C:\Program Files\Git\cmd\git.exe"
LANG = u"src/main/resources/assets/potato_s_t/lang/%s.json"
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]

# ---- 1) 先把被误伤的物品/方块名按 HEAD 恢复 ----
RESTORE_PREFIX = (u"item.", u"block.", u"fluid")

# ---- 2) 这 10 条成就标题要改成"看得出是成就"的说法 ----
TITLES = {
    u"electrolyzer": {u"zh_cn": u"把水拆开", u"en_us": u"Split the Water",
                      u"ja_jp": u"水を分解しよう", u"ru_ru": u"Разложите воду"},
    u"distillation": {u"zh_cn": u"把原油拆成五份", u"en_us": u"Five From One",
                      u"ja_jp": u"原油を五つに分けよう", u"ru_ru": u"Пять из одного"},
    u"alloy_smelter": {u"zh_cn": u"配出一炉合金", u"en_us": u"Stoke the Alloy Line",
                       u"ja_jp": u"合金を一炉どうぞ", u"ru_ru": u"Сплавы в одной печи"},
    u"blast_furnace": {u"zh_cn": u"砌一座高炉", u"en_us": u"Raise a Blast Furnace",
                       u"ja_jp": u"高炉を建てよう", u"ru_ru": u"Постройте домну"},
    u"starfall": {u"zh_cn": u"召唤一颗星星", u"en_us": u"Call Down a Star",
                  u"ja_jp": u"星を呼び下ろす", u"ru_ru": u"Позовите звезду"},
    u"salt": {u"zh_cn": u"向大海要盐", u"en_us": u"Salt From the Sea",
              u"ja_jp": u"海から塩を", u"ru_ru": u"Соль из моря"},
    u"star_steel": {u"zh_cn": u"炼出星璨钢", u"en_us": u"Forge the Star Steel",
                    u"ja_jp": u"星燦鋼を鍛えよう", u"ru_ru": u"Выкуйте звёздную сталь"},
    u"oil_pump": {u"zh_cn": u"向海要油", u"en_us": u"Oil From Beneath the Sea",
                  u"ja_jp": u"海の底から油を", u"ru_ru": u"Нефть из-под моря"},
    u"capacitor": {u"zh_cn": u"攒出一颗电容", u"en_us": u"Build a Capacitor",
                   u"ja_jp": u"コンデンサを作ろう", u"ru_ru": u"Соберите конденсатор"},
    u"sulfur": {u"zh_cn": u"从沥青里掏出硫", u"en_us": u"Sulfur Out of Bitumen",
                u"ja_jp": u"瀝青から硫黄を", u"ru_ru": u"Сера из битума"},
}


def head(path):
    out = subprocess.run([GIT, u"show", u"HEAD:" + path], capture_output=True, check=True).stdout
    return json.loads(out.decode(u"utf-8"))


def set_values(rel, mapping, label):
    """mapping: {key: 目标值}。按行定位、逐个替换、回读自检，失败即整体不写。"""
    raw = io.open(rel, encoding=u"utf-8", newline=u"").read()
    before = json.loads(raw)
    lines = raw.split(u"\n")
    # 建索引：行首键 → 行号（要求唯一）
    idx = {}
    for n, line in enumerate(lines):
        s = line.strip()
        if not s.startswith(u'"'):
            continue
        k = s.split(u'"')[1] if s.count(u'"') >= 2 else None
        if k is None:
            continue
        idx.setdefault(k, []).append(n)

    changed = []
    for key, want in sorted(mapping.items()):
        if before.get(key) == want:
            continue
        rows = idx.get(key, [])
        if len(rows) != 1:
            return None, u"%s / %s：行首键命中 %d 次（应为 1）" % (rel, key, len(rows))
        n = rows[0]
        line = lines[n]
        q1 = line.index(u'"', line.index(u':'))
        q2 = q1 + 1
        while True:
            if line[q2] == u"\\":
                q2 += 2
                continue
            if line[q2] == u'"':
                break
            q2 += 1
        got = json.loads(line[q1:q2 + 1])
        if got != before.get(key):
            return None, u"%s / %s：行内字面量(%r) ≠ 解析值(%r)" % (rel, key, got, before.get(key))
        lines[n] = line[:q1] + json.dumps(want, ensure_ascii=False) + line[q2 + 1:]
        changed.append((key, got, want))

    if not changed:
        return u"", []
    out = u"\n".join(lines)
    after = json.loads(out)
    if len(after) != len(before):
        return None, u"%s：回读键数 %d ≠ %d" % (rel, len(after), len(before))
    for key, _, want in changed:
        if after.get(key) != want:
            return None, u"%s / %s：回读不是目标值" % (rel, key)
    io.open(rel, u"w", encoding=u"utf-8", newline=u"").write(out)
    return label, changed


fails = []
for loc in LOCALES:
    rel = LANG % loc
    old = head(rel)
    # ---- 第 1 步：恢复被误伤的物品/方块名（取 HEAD 的值）----
    rmap = {}
    cur = json.load(io.open(rel, encoding=u"utf-8"))
    for k in cur:
        if k.startswith(RESTORE_PREFIX) and k in old and cur[k] != old[k]:
            rmap[k] = old[k]
    if rmap:
        lab, ch = set_values(rel, rmap, u"恢复")
        if lab is None:
            fails.append(ch)
        else:
            print(u"== %s：恢复 %d 个物品/方块名" % (loc, len(ch)))
            for k, a, b in ch:
                print(u"     %-44s %s → %s" % (k, a, b))
    # ---- 第 2 步：成就标题改名 ----
    tmap = dict((u"advancements.potato_s_t.%s.title" % n, t[loc]) for n, t in TITLES.items())
    lab, ch = set_values(rel, tmap, u"改名")
    if lab is None:
        fails.append(ch)
    elif ch:
        print(u"== %s：改标题 %d 个" % (loc, len(ch)))
        for k, a, b in ch:
            print(u"     %-46s %s → %s" % (k.split(u".")[-2], a, b))

if fails:
    print(u"\n[!!] 有失败，相关文件未写：")
    for f in fails:
        print(u"   " + f)
    sys.exit(1)
print(u"\n完成。")
