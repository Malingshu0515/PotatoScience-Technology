# -*- coding: utf-8 -*-
r"""_zf134_keys.py —— 把 ZF133 漏掉的「语言键数」跟平：**478 → 482**（四语言各 +4 = 星璨钢斧那 4 个键）

## 为什么这一轮要管它不是自己欠的账

ZF133（星璨钢斧）给四语言各加了 **4** 个键 ⇒ 键数 478 → **482**；
但那条线**没跑活体数字重定目标**（交接文档 §4 那张表写着：加/删一个语言键要一起改十几份校验器）。
于是盘上 482、而 29 份 `_zf*_verify.py` 还写着 478 ⇒ 它们全红。

它挡住的正好是本轮的交付：`ZF104 falsify` 的第一步是"基线必须绿"，
而基线 `_zf103_verify.py` 就是这 29 份之一 ⇒ 13 把刀全部报成"还原失败"（**假失败**）。
所以本轮顺带把这条链跟平 —— 机械替换，改完逐份 `compile()` + 逐份跑一遍。

## 范围（与 `_zf122_live.py` 同一套口径，不更宽）

  改：`build\zftools\_zf*_verify.py` 里**每一处"独立 478"**，但要求该行同时带键数标记
      （`键` / `keys each` / `KEYS` / `KEY_` / `counts.values()`）—— 不带标记就**停手不写那份**；
      以及英文公告的 `(478 keys each)`。
  不改：`_zf*_docs.py` / `_zf*_lang.py` / `_zf127_*.py` 这类**历史记录**（那里的 478 是"当时是多少"，
      改了就把历史改成假的了）；任何 sha1 里的 478（用前后非十六进制的规则排除）。

跑法：
    python build/zftools/_zf134_keys.py            # 只体检
    python build/zftools/_zf134_keys.py --write
"""
import glob
import io
import json
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
ZT = os.path.join(PROJ, "build", "zftools")
LANG = os.path.join(PROJ, r"src\main\resources\assets\potato_s_t\lang")
ANN = os.path.join(PROJ, "docs", "UpdateAnnouncement_EN.md")

OLD, NEW = u"478", u"482"
RX = re.compile(r"(?<![0-9a-fA-F])%s(?![0-9a-fA-F])" % OLD)
fails, notes = [], []


def read(p):
    return io.open(p, encoding="utf-8").read()


def keys_now():
    out = {}
    for n in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"):
        out[n] = len(json.loads(read(os.path.join(LANG, n + u".json"))))
    return out


def main(argv):
    write = u"--write" in argv
    now = keys_now()
    if set(now.values()) != {int(NEW)}:
        print(u"  [FAIL] 四语言键数不是各 %s：%s —— 先确认盘上的真相再改脚本" % (NEW, now))
        return 1
    print(u"四语言各 %s 键 ✔（本次要跟平的目标）" % NEW)

    targets = sorted(glob.glob(os.path.join(ZT, u"_zf*_verify.py")))
    touched = {}
    for p in targets:
        name = os.path.basename(p)
        raw = read(p)
        if not RX.search(raw):
            continue
        lines = raw.split(u"\n")

        def marked(l, prev):
            u"""这一行算不算"键数断言"。

            两处放宽，都是**先看到它拦住了真断言**才加的：
              · `活体数字` —— 有些门把这条写进 docstring（`F 活体数字：往轮门都跟到 478`），
                它说的是"别的脚本现在是几"，也是活体数字；
              · **上一行带标记** —— 断言常常折成两行：
                `check(u"四份都是 478 键（...）",` 换行 `      all(len(tables[l]) == 478 ...))`，
                数字在两行里都出现，第二行自己不带"键"字。
            """
            m = ((u"键" in l) or (u"keys each" in l) or (u"KEYS" in l) or (u"KEY_" in l)
                 or (u"counts.values()" in l) or (u"活体数字" in l) or l.strip().startswith(u"#"))
            if m:
                return True
            return ((u"键" in prev) or (u"keys each" in prev) or (u"KEYS" in prev)
                    or (u"KEY_" in prev) or (u"活体数字" in prev))

        n_ok, suspicious = 0, []
        for i, l in enumerate(lines):
            if not RX.search(l):
                continue
            if not marked(l, lines[i - 1] if i else u""):
                suspicious.append(i + 1)
                continue
            lines[i] = RX.sub(NEW, l)
            n_ok += 1
        if suspicious:
            fails.append(u"%s:%s 有独立的 478 但不是键数断言 —— 停手不写这份" % (name, suspicious))
            continue
        text = u"\n".join(lines)
        try:
            compile(text, p, "exec")
        except SyntaxError as e:
            fails.append(u"%s：改完语法错 %s" % (name, e))
            continue
        if RX.search(text):
            fails.append(u"%s：还剩独立的 %s" % (name, OLD))
            continue
        if write:
            io.open(p, "w", encoding="utf-8", newline=u"").write(text)
        touched[name] = n_ok
        notes.append(u"%s：%d 处" % (name, n_ok))

    raw = read(ANN)
    if u"(%s keys each)" % OLD in raw:
        if write:
            io.open(ANN, "w", encoding="utf-8", newline=u"").write(
                raw.replace(u"(%s keys each)" % OLD, u"(%s keys each)" % NEW, 1))
        notes.append(u"英文公告：(478 keys each) → (482 keys each)")
    elif u"(%s keys each)" % NEW not in raw:
        fails.append(u"英文公告里既没有 478 也没有 482 的键数句")

    print(u"\n%s %d 份脚本、%d 处："
          % (u"已改" if write else u"将改", len(touched), sum(touched.values())))
    for n in notes:
        print(u"   " + n)

    if write:
        print(u"\n回跑一遍（红的当场看见）：")
        for name in sorted(touched):
            r = subprocess.run([sys.executable, os.path.join(ZT, name)],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            tail = [l.strip() for l in r.stdout.decode("utf-8", "replace").split(u"\n")
                    if u"失败项" in l or u"失败 = " in l]
            print(u"   [%s] %-22s %s" % (u"OK" if r.returncode == 0 else u"FAIL", name,
                                         u" / ".join(tail[-1:]) or u"（没有汇总行）"))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
