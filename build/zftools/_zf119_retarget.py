# -*- coding: utf-8 -*-
r"""_zf119_retarget.py —— 活体数字重定目标：四语言键数 **448 → 449**（+1 = 振金锭的名字）

加一个物品名 = 四份语言各多 **1** 个键 ⇒ 所有把键数写死的门都要跟着走（本工程的老规矩，§4.64/§4.80）。

范围（与 ZF114/ZF117 同口径，且更窄）：
  改：`build\zftools\_zf*_verify.py` —— 每一处 `448` **都必须**是键数断言（脚本会逐行打印并核对
      「这行里同时有 448 和 键/keys」才动手；对不上就报错停手）；
      `docs\UpdateAnnouncement_EN.md` 的 `(448 keys each)`。
  不改：`_zf119_*`（本轮自己的）、`docs\开发档案.md`（历史行）、任何 sha1 里的 448。

改完立刻：① 逐份 `compile()`；② 断言这些文件里一个 `448` 都不剩；③ 四语言真的各 449 键。
"""
import glob
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, r"build\zftools")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
ANN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")

OLD, NEW = u"448", u"449"
fails, notes = [], []


def read(p):
    return io.open(p, encoding="utf-8").read()


def main():
    targets = sorted(p for p in glob.glob(os.path.join(TOOLS, "_zf*_verify.py"))
                     if u"_zf119_" not in os.path.basename(p))
    for p in targets:
        name = os.path.basename(p)
        raw = read(p)
        if OLD not in raw:
            continue
        lines = raw.split(u"\n")
        hits, ok_lines = 0, 0
        for i, l in enumerate(lines):
            if OLD not in l:
                continue
            hits += l.count(OLD)
            marker = ((u"键" in l) or (u"keys each" in l) or (u"KEYS" in l) or (u"KEY_" in l)
                      or (u"counts.values()" in l))
            if not marker:
                fails.append(u"%s:%d 有 448 但不是键数断言 —— 停手：%s" % (name, i + 1, l.strip()[:100]))
                continue
            lines[i] = l.replace(OLD, NEW)
            ok_lines += 1
            notes.append(u"%s:%d  %s" % (name, i + 1, lines[i].strip()[:96]))
        if ok_lines != len([1 for l in raw.split(u"\n") if OLD in l]):
            continue          # 有可疑行：整份不写
        text = u"\n".join(lines)
        try:
            compile(text, p, "exec")
        except SyntaxError as e:
            fails.append(u"%s：改完语法错 %s" % (name, e))
            continue
        if OLD in text:
            fails.append(u"%s：还剩 %s" % (name, OLD))
            continue
        io.open(p, "w", encoding="utf-8", newline=u"").write(text)

    raw = read(ANN)
    if u"(%s keys each)" % OLD in raw:
        write_ok = raw.replace(u"(%s keys each)" % OLD, u"(%s keys each)" % NEW, 1)
        io.open(ANN, "w", encoding="utf-8", newline=u"").write(write_ok)
        notes.append(u"公告：(448 keys each) → (449 keys each)")
    elif u"(%s keys each)" % NEW not in raw:
        fails.append(u"公告里既没有 448 也没有 449 的键数句")

    counts = {}
    for n in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        counts[n] = len(json.loads(read(os.path.join(LANG, n + u".json"))))
    if set(counts.values()) != {int(NEW)}:
        fails.append(u"四语言键数不是各 449：%s" % counts)
    else:
        notes.append(u"四语言各 %s 键" % NEW)

    # 打印：只留每个文件的"改了哪几行"，别把 23 份全刷一遍
    per = {}
    for n in notes:
        if u":" in n and n.split(u":")[0].endswith(u".py"):
            per.setdefault(n.split(u":")[0], 0)
            per[n.split(u":")[0]] += 1
    print(u"改到的文件（处数）：")
    for k in sorted(per):
        print(u"  %-26s %d 处" % (k, per[k]))
    print(u"")
    for n in notes:
        if not (u":" in n and n.split(u":")[0].endswith(u".py")):
            print(u"  [OK] " + n)
    print(u"\n共 %d 份脚本、%d 处替换" % (len(per), sum(per.values())))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
