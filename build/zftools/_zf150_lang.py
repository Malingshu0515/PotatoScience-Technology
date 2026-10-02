# -*- coding: utf-8 -*-
"""_zf150_lang.py —— ZF150：四种粒的四语言键（16 个）

用户原话：「嗯嗯放素材了几张图 其中四种粒你先注册一下 配方就是原版的
（对应锭合成9个粒 9个粒合成1个锭 记得加标签兼容别的mod）重复一遍！现在是0.12版本」

不加键的话游戏里会直接把 `item.potato_s_t.aluminum_nugget` 原样显示出来。

命名口径**照原版**（本轮从 client-extra.jar 的 en_us 现抠）：
  `item.minecraft.iron_nugget` = **Iron Nugget**、`item.minecraft.gold_nugget` = **Gold Nugget**
⇒ 本模组 `<材料> Nugget`；中文照原版「铁粒 / 金粒」⇒「铝粒 / 钴粒 / 镍粒 / 银粒」；
日文照原版「鉄の塊」那一族用 `塊`；俄文照原版 `<材料>овый самородок`。

只**加键**、不动任何旧键的值（脚本自带断言：旧键值逐条比对）。

四语言键数 579 → **595**（+16）。⚠ 这是全工程的**活体数字**：
一批常驻门把 579 写死在 `EXPECT_KEYS` / `KEY_NEW` / `KEYS` 里 ⇒
加完键必须同步那一批门（`_zf150_retarget.py` 负责），否则它们会全红。
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]

NEW = {
    "aluminum": {"zh_cn": u"铝粒", "en_us": u"Aluminum Nugget",
                 "ja_jp": u"アルミニウム塊", "ru_ru": u"Алюминиевый самородок"},
    "cobalt":   {"zh_cn": u"钴粒", "en_us": u"Cobalt Nugget",
                 "ja_jp": u"コバルト塊", "ru_ru": u"Кобальтовый самородок"},
    "nickel":   {"zh_cn": u"镍粒", "en_us": u"Nickel Nugget",
                 "ja_jp": u"ニッケル塊", "ru_ru": u"Никелевый самородок"},
    "silver":   {"zh_cn": u"银粒", "en_us": u"Silver Nugget",
                 "ja_jp": u"銀塊", "ru_ru": u"Серебряный самородок"},
}
ANCHOR = {"aluminum": "item.potato_s_t.aluminum_ingot",
          "cobalt": "item.potato_s_t.cobalt_ingot",
          "nickel": "item.potato_s_t.nickel_ingot",
          "silver": "item.potato_s_t.silver_ingot"}

fails = []


def main():
    for lg in LANGS:
        p = os.path.join(LANG, lg + ".json")
        raw = io.open(p, "rb").read()
        if raw[:3] == b"\xef\xbb\xbf":
            fails.append(u"%s 有 BOM" % lg)
        if b"\r\n" in raw:
            fails.append(u"%s 是 CRLF（既有是 LF）" % lg)
        data = json.loads(raw.decode("utf-8"))
        before = len(data)

        out = {}
        inserted = []
        for k, v in data.items():
            out[k] = v
            for mat, anchor in ANCHOR.items():
                if k == anchor:
                    nk = "item.potato_s_t.%s_nugget" % mat
                    if nk in data:
                        continue
                    out[nk] = NEW[mat][lg]
                    inserted.append(nk)
        io.open(p, "w", encoding="utf-8", newline="\n").write(
            json.dumps(out, indent=2, ensure_ascii=False) + "\n")
        back = json.loads(io.open(p, encoding="utf-8").read())
        vals_kept = all(back[k] == v for k, v in data.items())
        ok = (len(back) == before + len(inserted) and len(inserted) == 4
              and all("item.potato_s_t.%s_nugget" % m in back for m in NEW)
              and vals_kept)
        print(u"  %s %-7s %d -> %d 键（+%d）  旧键值全未动=%s"
              % (u"[OK]" if ok else u"[!!]", lg, before, len(back), len(inserted), vals_kept))
        if not ok:
            fails.append(u"%s 写回校验失败" % lg)
        for m in ("aluminum", "cobalt", "nickel", "silver"):
            print(u"        item.potato_s_t.%-16s %s" % (m + "_nugget", NEW[m][lg]))

    sets = {lg: set(json.loads(io.open(os.path.join(LANG, lg + ".json"),
                                       encoding="utf-8").read())) for lg in LANGS}
    base = sets["zh_cn"]
    same = all(sets[l] == base for l in LANGS)
    if not same:
        for l in LANGS:
            if sets[l] != base:
                fails.append(u"%s 键集合不一致（差 %s）" % (l, sorted(sets[l] ^ base)[:5]))
    print(u"\n  四语言键集合一致：%s（各 %d 键）" % (u"是" if same else u"否", len(base)))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
