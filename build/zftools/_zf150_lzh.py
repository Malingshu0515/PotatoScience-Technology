# -*- coding: utf-8 -*-
"""_zf150_lzh.py —— ZF150：把四种粒的 4 个键**补进第五语言 `lzh`（文言）**

⚠ 这是本轮自己抓到的一个**漏**：`_zf150_lang.py` 只处理了 `zh_cn/en_us/ja_jp/ru_ru`
四份（那是 I18n 的"四语言"口径），而工程在 ZF148 之后已经是**五语言**
（多了 `lzh`，文言，比四份多 `language.name` / `language.region` 两个元数据键）。

后果：`lzh` 里没有这 4 个键 ⇒ 切到文言时游戏会把
`item.potato_s_t.aluminum_nugget` 原样显示出来。

数：`lzh` 581 → **585**（仍是"四语言的 583 + 2 个元数据键"）。

用词照 `lzh` 既有风格（`鋁錠 / 鐵粉 / 粗銀` ⇒ 粒用「粒」，文言本就有"粒米"之说）。
繁体、与 `錠/板/礦/粉` 同一套。
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang\lzh.json"
NEW = {
    "aluminum": u"鋁粒",
    "cobalt": u"鈷粒",
    "nickel": u"鎳粒",
    "silver": u"銀粒",
}
ANCHOR = {"aluminum": "item.potato_s_t.aluminum_ingot",
          "cobalt": "item.potato_s_t.cobalt_ingot",
          "nickel": "item.potato_s_t.nickel_ingot",
          "silver": "item.potato_s_t.silver_ingot"}

raw = io.open(P, "rb").read()
if raw[:3] == b"\xef\xbb\xbf":
    print(u"  !! lzh.json 有 BOM")
data = json.loads(raw.decode("utf-8"))
before = len(data)

out, inserted = {}, []
for k, v in data.items():
    out[k] = v
    for mat, anchor in ANCHOR.items():
        if k == anchor:
            nk = "item.potato_s_t.%s_nugget" % mat
            if nk in data:
                continue
            out[nk] = NEW[mat]
            inserted.append(nk)

io.open(P, "w", encoding="utf-8", newline="\n").write(
    json.dumps(out, indent=2, ensure_ascii=False) + "\n")
back = json.loads(io.open(P, encoding="utf-8").read())
vals_kept = all(back[k] == v for k, v in data.items())
ok = (len(back) == before + 4 and len(inserted) == 4 and vals_kept
      and all("item.potato_s_t.%s_nugget" % m in back for m in NEW))
print(u"  %s lzh %d -> %d 键（+%d）  旧键值全未动=%s"
      % (u"[OK]" if ok else u"[!!]", before, len(back), len(inserted), vals_kept))
for m in ("aluminum", "cobalt", "nickel", "silver"):
    print(u"      item.potato_s_t.%-16s %s" % (m + "_nugget", NEW[m]))

# 与四语言对齐（lzh 应 = 四语言 + 2 个元数据键）
L = os.path.dirname(P)
zh = set(json.loads(io.open(os.path.join(L, "zh_cn.json"), encoding="utf-8").read()))
lz = set(back)
diff = lz ^ zh
ok2 = diff == {"language.name", "language.region"}
print(u"\n  %s lzh 与 zh_cn 的键差 = %s（应为 language.name / language.region 两个）"
      % (u"[OK]" if ok2 else u"[!!]", sorted(diff)))
sys.exit(0 if (ok and ok2) else 1)
