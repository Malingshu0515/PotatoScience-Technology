# -*- coding: utf-8 -*-
r"""_rzh_restore_preserved.py —— 把 ZF107 承诺"一个字节不改"的两条老成就文案按 HEAD 恢复。

背景：本轮（翻译润色）动了 clean_energy / stronger_power 的标题与说明，
      而 _zf107_verify.py 的 E7/E8 把"这两条不许改"写成了硬断言 ⇒ 554 项里 8 项失败。
口径（档案 §4.36）：**改锚点，不放宽断言** ⇒ 恢复原文，而不是去改校验器。

做法：**逐行替换**，只换那 4 行里冒号后那个字符串字面量。
      不用 json.dump 重写整个文件（会平掉原排版），也不用正则（跨行会失控）。
"""
import io
import json
import subprocess

GIT = r"C:\Program Files\Git\cmd\git.exe"
KEYS = [
    u"advancements.potato_s_t.clean_energy.title",
    u"advancements.potato_s_t.clean_energy.description",
    u"advancements.potato_s_t.stronger_power.title",
    u"advancements.potato_s_t.stronger_power.description",
]
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]


def head_json(path):
    raw = subprocess.run([GIT, u"show", u"HEAD:" + path],
                         capture_output=True, check=True).stdout
    return json.loads(raw.decode(u"utf-8"))


total = 0
for loc in LOCALES:
    rel = u"src/main/resources/assets/potato_s_t/lang/%s.json" % loc
    old = head_json(rel)
    raw = io.open(rel, encoding=u"utf-8", newline=u"").read()
    lines = raw.split(u"\n")
    touched = []

    for k in KEYS:
        want = json.dumps(old[k], ensure_ascii=False)
        indent = u" " * 4
        # 原文件里这两条都是 4 空格缩进的标准形态，先按它找
        needle = indent + json.dumps(k, ensure_ascii=False) + u":"
        hit = [i for i, ln in enumerate(lines) if ln.startswith(needle)]
        if len(hit) != 1:
            # 兜底：不限缩进
            hit = [i for i, ln in enumerate(lines)
                   if ln.strip().startswith(json.dumps(k, ensure_ascii=False) + u":")]
        if len(hit) != 1:
            raise SystemExit(u"定位不到唯一一行：%s / %s （命中 %d）" % (loc, k, len(hit)))

        i = hit[0]
        ln = lines[i]
        c = ln.index(u":", ln.index(json.dumps(k, ensure_ascii=False)))
        head, rest = ln[:c + 1], ln[c + 1:]
        # rest 形如 '  "旧值",' —— 保留冒号后的空白与前缀、行尾逗号
        j = rest.index(u'"')
        k2 = j + 1
        while True:
            if rest[k2] == u"\\":
                k2 += 2
                continue
            if rest[k2] == u'"':
                break
            k2 += 1
        cur_lit = rest[j:k2 + 1]
        if cur_lit != want:
            lines[i] = head + rest[:j] + want + rest[k2 + 1:]
            touched.append(k.replace(u"advancements.potato_s_t.", u""))

    if touched:
        io.open(rel, u"w", encoding=u"utf-8", newline=u"").write(u"\n".join(lines))
        total += len(touched)
        print(u"[OK] %-6s 恢复 %d 处：%s" % (loc, len(touched), u", ".join(touched)))
    else:
        print(u"[--] %-6s 本来就没动" % loc)

print(u"\n合计恢复 %d 处" % total)
