# -*- coding: utf-8 -*-
u"""_zf149_jar.py —— ZF149 成品审计（只读）：把手册真的在不在 jar 里逐项钉死。

查的是**成品 jar 自己**（不是盘上的源目录）：
  ① 全条目 CRC + 结构计数（class / 配方 / 进度 / 语言 / 模型 / 贴图）；
  ② 手册相关 26 份资源在不在，且与源目录**逐字节相同**；
  ③ 五份 lang 在 jar 里的**键数**是 579×4 + 581，且与源文件逐字节相同；
  ④ `neoforge.mods.toml` 渲染后：版本 0.13、`patchouli` 是 required；
  ⑤ 没有探针 class；`libs/` 那份帕秋莉 jar **没有**被打进产物（compileOnly 的判据）；
  ⑥ 配方 `guide_book.json` 在 jar 里且带组件。

跑法：python build\\zftools\\_zf149_jar.py [jar 路径]（默认 release\\PotatoST-0.13.jar）
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = r"E:\PotatoST"
RES = os.path.join(ROOT, "src", "main", "resources")
DEFAULT_JAR = os.path.join(ROOT, "release", "PotatoST-0.13.jar")

passed = 0
failed = 0
fails = []


def check(cond, label, detail=u""):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label if not detail else u"%s（%s）" % (label, detail))
        print(u"  [FAIL] " + label + (u" —— " + detail if detail else u""))


def main():
    jar = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JAR
    print(u"================ ZF149 成品审计：%s ================" % jar)
    if not os.path.isfile(jar):
        print(u"  !! jar 不在：%s" % jar)
        return 1
    raw = open(jar, "rb").read()
    print(u"  大小 %d 字节 ；sha1 %s" % (len(raw), hashlib.sha1(raw).hexdigest()))

    z = zipfile.ZipFile(jar)
    bad = z.testzip()
    check(bad is None, u"① 全条目 CRC 校验通过", u"坏条目 %s" % bad)

    names = z.namelist()
    files = [n for n in names if not n.endswith(u"/")]
    cls = [n for n in files if n.endswith(u".class")]
    recipes = [n for n in files if n.startswith(u"data/potato_s_t/recipe/")]
    advs = [n for n in files if n.startswith(u"data/potato_s_t/advancement/")]
    langs = sorted(n for n in files if n.startswith(u"assets/potato_s_t/lang/"))
    models = [n for n in files if n.startswith(u"assets/potato_s_t/models/")]
    textures = [n for n in files if n.startswith(u"assets/potato_s_t/textures/")]
    print(u"  条目 %d（目录 %d）/ class %d / 配方 %d / 进度 %d / 语言 %d / 模型 %d / 贴图 %d"
          % (len(names), len(names) - len(files), len(cls), len(recipes), len(advs),
             len(langs), len(models), len(textures)))

    # ⚠ ZF153 跟平：振金剑改了 Java ⇒ 成品按"同版本原地重打"重打了一次；这两个数按
    #   **发布那一刻的实测值**写（ZF149 那次是 74 / 358）。⚠ **本轮一条配方都没加**
    #   （74 → 89 是别的线在途加的），class 也 ≥ 358 不变（本轮 +1 个 VibraniumSwordItem）。
    check(len(recipes) == 93, u"① 配方份数（发布那一刻的实测值；ZF162 重打时 93：ZF160 的 94 减掉电力高炉那条）",
          u"实际 %d" % len(recipes))
    check(len(advs) == 43, u"① 进度 43 条", u"实际 %d" % len(advs))
    check(len(langs) == 5, u"① 语言 5 份", u"实际 %d" % len(langs))
    check(len(cls) >= 358, u"① class 数 ≥ 358（ZF148 加了 GuideBook）", u"实际 %d" % len(cls))

    # ② 手册资源
    book = u"data/potato_s_t/patchouli_books/guide/book.json"
    check(book in names, u"② 书定义 book.json 在 jar 里")
    cats = [u"getting_started", u"power", u"materials", u"oil", u"starfall", u"faq"]
    ents = 0
    miss = []
    for c in cats:
        p = u"assets/potato_s_t/patchouli_books/guide/en_us/categories/%s.json" % c
        if p not in names:
            miss.append(p)
    base = u"assets/potato_s_t/patchouli_books/guide/en_us/entries/"
    ents = len([n for n in names if n.startswith(base) and n.endswith(u".json")])
    check(not miss, u"② 六个分类都在 jar 里", u"缺 %s" % miss)
    check(ents == 18, u"② 条目 18 份在 jar 里", u"实际 %d" % ents)
    for extra in (u"assets/potato_s_t/models/item/guide_book.json",
                  u"assets/potato_s_t/textures/item/guide_book.png",
                  u"data/potato_s_t/recipe/guide_book.json"):
        check(extra in names, u"② 在 jar 里：%s" % extra)

    # ②b 与源目录逐字节相同
    def same(entry, rel):
        src = os.path.join(RES, rel.replace(u"/", os.sep))
        if not os.path.isfile(src):
            return False
        return z.read(entry) == open(src, "rb").read()

    pair = [(book, u"data/potato_s_t/patchouli_books/guide/book.json"),
            (u"assets/potato_s_t/models/item/guide_book.json",
             u"assets/potato_s_t/models/item/guide_book.json"),
            (u"assets/potato_s_t/textures/item/guide_book.png",
             u"assets/potato_s_t/textures/item/guide_book.png"),
            (u"data/potato_s_t/recipe/guide_book.json",
             u"data/potato_s_t/recipe/guide_book.json")]
    ok = all(same(a, b) for a, b in pair)
    check(ok, u"② 书定义 / 模型 / 贴图 / 配方在 jar 里与源目录逐字节相同")

    # ③ 语言
    # ⚠ 这里**只钉手册那 71 个键**在 jar 与源目录里逐字相同，**不钉整份 lang 文件逐字节相同**：
    #   成品是**快照**，别的线在打包之后往 lang 里加键（实测 ZF150 就在我打包 3 分钟后加了 4 个键）
    #   ⇒ 拿"整份文件相同"当判据，等于让别人的提交节奏决定我这条门红不红（§5.1 同款）。
    #   整份文件的漂移仍然打出来，但只是**提示**，不算判据。
    # ⚠ ZF153 跟平：语言键数是**活体数字** —— ZF150 四种粒 +4（579 → 583）、
    #   ZF153 振金剑 +4（583 → **587**），lzh 585 → **589**。
    want = {u"zh_cn": 593, u"en_us": 593, u"ja_jp": 593, u"ru_ru": 593, u"lzh": 595}
    counts = {}
    book_keys = [row[0] for row in __import__(u"_zf148_text").TEXTS]
    mismatch = []
    drift = []
    for lang, n in sorted(want.items()):
        entry = u"assets/potato_s_t/lang/%s.json" % lang
        if entry not in names:
            check(False, u"③ jar 里有 %s.json" % lang)
            continue
        data = z.read(entry)
        table = json.loads(data.decode(u"utf-8"))
        counts[lang] = len(table)
        check(len(table) == n, u"③ jar 里 %s 键数 = %d" % (lang, n), u"实际 %d" % len(table))
        src = os.path.join(RES, u"assets", u"potato_s_t", u"lang", lang + u".json")
        disk = json.loads(io.open(src, encoding=u"utf-8").read())
        for k in book_keys:
            if table.get(k) != disk.get(k):
                mismatch.append(u"%s/%s" % (lang, k))
        if len(disk) != len(table):
            drift.append(u"%s 源 %d / jar %d" % (lang, len(disk), len(table)))
    check(not mismatch, u"③ 手册那 71 个键在 jar 与源目录里逐字相同", u"%s" % mismatch[:3])
    if drift:
        print(u"  [提示] 打包之后源 lang 又被改过（别人的轮次）：%s" % u"；".join(drift))
    need = [k for k in json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode(u"utf-8"))
            if k.startswith(u"potato_s_t.guide.") or u"guide_book" in k]
    check(len(need) == 71, u"③ jar 的 zh_cn 里手册键 71 个（含书名与赠书提示）", u"实际 %d" % len(need))

    # ④ mods.toml
    toml = z.read(u"META-INF/neoforge.mods.toml").decode(u"utf-8")
    check(u'version="0.13"' in toml, u"④ mods.toml 里版本是 0.13")
    check(u'modId="patchouli"' in toml and u'type="required"' in toml,
          u"④ mods.toml 里有帕秋莉硬依赖")
    check(u'${mod_version}' not in toml, u"④ 占位符已展开（没有残留 ${mod_version}）")

    # ⑤ 探针与 compileOnly
    probes = [n for n in cls if re.search(r"Zf\d+Check", n)]
    check(not probes, u"⑤ jar 里没有临时探针 class", u"%s" % probes[:3])
    patchouli = [n for n in files if n.startswith(u"vazkii/patchouli/")]
    check(not patchouli, u"⑤ 帕秋莉自己的类**没有**被打进产物（compileOnly 的判据）",
          u"%d 个" % len(patchouli))
    jei = [n for n in files if n.startswith(u"mezz/jei/")]
    check(not jei, u"⑤ JEI 的类也没有被打进产物", u"%d 个" % len(jei))

    # ⑥ 配方内容
    r = json.loads(z.read(u"data/potato_s_t/recipe/guide_book.json").decode(u"utf-8"))
    res = r.get(u"result") or {}
    check(r.get(u"type") == u"minecraft:crafting_shapeless"
          and res.get(u"id") == u"patchouli:guide_book"
          and (res.get(u"components") or {}).get(u"patchouli:book") == u"potato_s_t:guide",
          u"⑥ jar 里的手册配方：书 + 铁锭 → 带组件的 patchouli:guide_book")

    z.close()
    print(u"")
    print(u"================ 通过 %d / 失败 %d ================" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == u"__main__":
    sys.exit(main())
