# -*- coding: utf-8 -*-
r"""_zf120_retarget.py —— 活体数字重定目标：四语言键数 **449 → 454**（+5 = 振金套四件名字 + 一条套装说明）

加物品名 = 四份语言各多 **5** 个键 ⇒ 所有把键数写死的门都要跟着走（老规矩，§4.64/§4.80）。
ZF119（+1 键，448 → 449）刚做过同一件事，本轮照它的脚本改成 +5。

范围：
  改：`build\zftools\_zf*_verify.py`（除本轮自己的 `_zf120_*`）——
      每一处 `449` **都必须**是键数断言（逐行核对「这行里同时有 449 和 键/keys/KEYS/KEY_」才动手）；
      `_zf119_falsify.py` 的那条 `expect=u"C1 四语言各 449 键"`（它是**断言标签**，
      `_zf119_verify.py` 的 C1 一改，标签不跟着改那一刀就会假失败）；
      `docs\UpdateAnnouncement_EN.md` 的 `(449 keys each)`。
  不改：`_zf120_*`（本轮自己的）、`docs\开发档案.md`（历史行）、任何 sha1 里的 449。

⚠ 与 ZF119 那份的一处差别：**必须绕开 sha1**。`_zf117_verify.py` 里有一行
  `"clean_energy": "ee7467159e453c71f4f9b4bef91449e9e748b68c",` —— 里面就有 `449`。
  所以替换用的正则要求前后都**不是十六进制字符**（`(?<![0-9a-fA-F])449(?![0-9a-fA-F])`），
  sha1 里的那串天然被排除；而真正的键数断言（前面是空格/等号、后面是空格/逗号/引号）照样命中。

改完立刻：① 逐份 `compile()`；② 断言这些文件里一个"独立 449"都不剩；③ 四语言真的各 454 键。

⚠ **本脚本第一次真跑时结果是 0 份 / 0 处** —— 因为**并行那条线（ZF121）在我之前已经把
  449 → 454 的重定目标做完了**（`_zf121_retarget.py`，26 份脚本 / 39 处；他们的
  `_zf121_verify.py` 里甚至留了一句"本轮的活体数字（键数）故意不钉死"）。
  所以这个脚本现在的价值是**当断言用**：跑出来必须是 `0 份 / 0 处 / 失败项 = 0`，
  即"盘上再没有任何一份校验器还停在 449"。**它不该被删掉。**
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

OLD, NEW = u"449", u"454"
# 允许命令行覆盖（0.11 ZF120 当天就用了第二次：修完"25 份被清零"的事故之后，
# 并行线的 ZF121/ZF122 又把键数推到 464 ⇒ 再跑一次 454 → 464）。
if u"--old" in sys.argv:
    OLD = sys.argv[sys.argv.index(u"--old") + 1]
if u"--new" in sys.argv:
    NEW = sys.argv[sys.argv.index(u"--new") + 1]
# 前后不是十六进制字符才算"独立的 449"（sha1 里的不算）—— 见文件头 ⚠
RX = re.compile(r"(?<![0-9a-fA-F])%s(?![0-9a-fA-F])" % OLD)
RXNEW = re.compile(r"(?<![0-9a-fA-F])%s(?![0-9a-fA-F])" % NEW)

fails, notes = [], []


def read(p):
    return io.open(p, encoding="utf-8").read()


def main():
    targets = sorted(p for p in glob.glob(os.path.join(TOOLS, "_zf*_verify.py"))
                     if u"_zf120_" not in os.path.basename(p))
    # 断言标签也要跟着走（见文件头）
    targets.append(os.path.join(TOOLS, u"_zf119_falsify.py"))

    for p in targets:
        name = os.path.basename(p)
        raw = read(p)
        if not RX.search(raw):
            continue
        lines = raw.split(u"\n")
        touched = 0
        suspicious = False
        for i, l in enumerate(lines):
            if not RX.search(l):
                continue
            marker = ((u"键" in l) or (u"keys each" in l) or (u"KEYS" in l) or (u"KEY_" in l)
                      or (u"counts.values()" in l))
            if not marker:
                fails.append(u"%s:%d 有独立的 449 但不是键数断言 —— 停手：%s"
                             % (name, i + 1, l.strip()[:100]))
                suspicious = True
                continue
            lines[i] = RX.sub(NEW, l)
            touched += 1
            notes.append(u"%s:%d  %s" % (name, i + 1, lines[i].strip()[:96]))
        if suspicious:
            continue          # 有可疑行：整份不写
        text = u"\n".join(lines)
        try:
            compile(text, p, "exec")
        except SyntaxError as e:
            fails.append(u"%s：改完语法错 %s" % (name, e))
            continue
        if RX.search(text):
            fails.append(u"%s：还剩独立的 %s" % (name, OLD))
            continue
        io.open(p, "w", encoding="utf-8", newline=u"").write(text)

    raw = read(ANN)
    if u"(%s keys each)" % OLD in raw:
        io.open(ANN, "w", encoding="utf-8", newline=u"").write(
            raw.replace(u"(%s keys each)" % OLD, u"(%s keys each)" % NEW, 1))
        notes.append(u"公告：(449 keys each) → (454 keys each)")
    elif u"(%s keys each)" % NEW not in raw:
        fails.append(u"公告里既没有 449 也没有 454 的键数句")

    counts = {}
    for n in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"):
        counts[n] = len(json.loads(read(os.path.join(LANG, n + u".json"))))
    if set(counts.values()) != {int(NEW)}:
        fails.append(u"四语言键数不是各 454：%s" % counts)
    else:
        notes.append(u"四语言各 %s 键" % NEW)

    per = {}
    for n in notes:
        if u":" in n and n.split(u":")[0].endswith(u".py"):
            k = n.split(u":")[0]
            per[k] = per.get(k, 0) + 1
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
