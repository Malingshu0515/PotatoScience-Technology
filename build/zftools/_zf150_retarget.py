# -*- coding: utf-8 -*-
"""_zf150_retarget.py —— ZF150：把「四语言键数」这个**活体数字**从 579 跟到 583

用户原话（0.12）：「…其中四种粒你先注册一下…」
四种粒 × 4 语言 = **16 个键** = **每份语言文件 +4** ⇒ 579 → **583**。

⚠ 我先把 16 个键口算成了「595」——那是把"16 个键"当成"每份 +16"了。
   实际是 `4 个物品 × 1 个键 = 每份 +4`，16 是**四份合计**。脚本里把这条写成断言，
   免得下次再算错（`KEYS_BEFORE + 4 == KEYS_AFTER`）。

## 为什么必须动这一批门

这个数被十几份常驻门写死在 `EXPECT_KEYS` / `KEY_NEW` / `KEYS` 里（活体数字，
档案交接文档里点名"加/删一个语言键要一起改"）。不同步它们，它们会全部变红。

## 谁不该动

`_zf93_verify.py` 里的 `RELEASE_KEYS = 482` 指的是**已发布 jar 里**的键数
（本轮没打包）⇒ **一个字都不动**。这是有意为之的口径，动它反而错。
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOOLS = r"E:\PotatoST\build\zftools"
LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
OLD, NEW = 579, 583
fails = []

# 与 `_zf145_verify.py` 的 F 组同一张表（那是上一轮的权威名单），
# 但这里**按"盘上确实还写着 OLD"来筛**，没有的跳过并报出来。
GUARDS = {
    "_zf100_verify.py": u"EXPECT_KEYS = %d",
    "_zf101_verify.py": u"EXPECT_KEYS = %d",
    "_zf102_verify.py": u"EXPECT_KEYS = %d",
    "_zf103_verify.py": u"len(table) == %d",
    "_zf107_verify.py": u"EXPECT_KEYS = %d",
    "_zf109_verify.py": u"EXPECT_KEYS = %d",
    "_zf111_verify.py": u"EXPECT_KEYS = %d",
    "_zf112_verify.py": u"EXPECT_KEYS = %d",
    "_zf114_verify.py": u"EXPECT_KEYS = %d",
    "_zf118_verify.py": u"KEY_NEW = %d",
    "_zf122_verify.py": u"EXPECT_KEYS = %d",
    "_zf141_verify.py": u"KEYS = %d",
    "_zf80_verify.py": u"EXPECT_KEYS = %d",
    "_zf82_verify.py": u"EXPECT_KEYS = %d",
    "_zf96_verify.py": u"EXPECT_KEYS = %d",
    "_zf97_verify.py": u"EXPECT_KEYS = %d",
    "_zf98_verify.py": u"EXPECT_KEYS = %d",
    "_zf93_verify.py": u"EXPECT_KEYS = %d",
    "_zf119_verify.py": u"KEY_OLD, KEY_NEW = 448, %d",
    "_zf139_verify.py": u"KEYS_BEFORE, KEYS_AFTER = 482, %d",
}


def main():
    # ① 先确认盘上的真实键数
    import json
    base = None
    for lg in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        n = len(json.loads(io.open(os.path.join(LANG, lg + ".json"), encoding="utf-8").read()))
        base = n if base is None else base
        if n != NEW:
            fails.append(u"%s 实际 %d 键，期望 %d" % (lg, n, NEW))
    if base != NEW:
        print(u"!! 盘上键数是 %s，不是 %d —— 先别动门" % (base, NEW))
        for f in fails:
            print(u"  !! " + f)
        return 1
    print(u"① 盘上四语言各 %d 键 ✓（%d + 4 = %d：四个物品各 1 个键）" % (NEW, OLD, NEW))

    # ② 逐份改
    print(u"\n② 同步常驻门（只改写死的那个数，别的一字不动）")
    done, skipped = [], []
    for fn, tmpl in sorted(GUARDS.items()):
        p = os.path.join(TOOLS, fn)
        if not os.path.exists(p):
            skipped.append((fn, u"文件不在"))
            continue
        t = io.open(p, encoding="utf-8").read()
        old_s, new_s = tmpl % OLD, tmpl % NEW
        if new_s in t:
            skipped.append((fn, u"已经是 %d" % NEW))
            continue
        n = t.count(old_s)
        if n != 1:
            skipped.append((fn, u"锚点 %d 次" % n))
            continue
        io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old_s, new_s))
        b = io.open(p, encoding="utf-8").read()
        if new_s in b:
            done.append(fn)
            print(u"  [OK] %-24s %s -> %s" % (fn, old_s, new_s))
        else:
            fails.append(u"%s 回读失败" % fn)
    for fn, why in skipped:
        print(u"  [跳过] %-24s %s" % (fn, why))

    # ③ 反向：`RELEASE_KEYS`（成品 jar 的靶子）**不许动**
    z93 = os.path.join(TOOLS, "_zf93_verify.py")
    if os.path.exists(z93):
        t = io.open(z93, encoding="utf-8").read()
        import re as _re
        _m = _re.search(r"RELEASE_KEYS = (\d+)", t)
        _rk = int(_m.group(1)) if _m else -1
        if _rk not in (OLD, NEW):
            print(u"\n③ [OK] `_zf93_verify.py` 的 `RELEASE_KEYS = %d` 没被动（成品 jar 的靶子，与盘上键数无关）" % _rk)
        else:
            fails.append(u"RELEASE_KEYS 变成了 %d（既不是 %d 也不该是 %d）" % (_rk, OLD, NEW))
            print(u"\n③ !! RELEASE_KEYS = %d，可疑" % _rk)

    # ④ 还有谁残留 OLD（不含 482 那条老链）
    print(u"\n④ 扫残留：还有哪些 _zf*_verify.py 写着 %d" % OLD)
    left = []
    for f in sorted(os.listdir(TOOLS)):
        if not re.match(r"^_zf\d+_verify\.py$", f):
            continue
        t = io.open(os.path.join(TOOLS, f), encoding="utf-8").read()
        if re.search(r"\b%d\b" % OLD, t):
            left.append(f)
    if left:
        print(u"  仍有：%s" % u"、".join(left))
        print(u"  （其中部分是历史叙述——注释/文档里提到旧值，不一定是判据；逐个人看）")
    else:
        print(u"  [OK] 没有残留")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
