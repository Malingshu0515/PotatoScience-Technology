# -*- coding: utf-8 -*-
u"""_zf121_retarget2.py —— ZF121 第二轮 retarget：**本轮自己把 4 道门顶红了**（第一轮快照抓出来的）

第一轮全门快照（`_zf121_gatesnap.txt`：绿 12 / 红 29）里，逐条分过账：
**29 红里有 25 道是并行那条线（ZF120 振金套：键数 449 → 454 / 配方 60 → 64 / 成品 jar 还是 ZF114 版）
的账**，剩下的 **4 道是本轮造成的**，在这里收口：

1. `_zf111_verify.py`：「这条配方用 MAX_ENERGY_PER_TICK（不是 800）」
   —— 本轮把星璨钢那条从 `MAX_ENERGY_PER_TICK` 拆成了 `STAR_STEEL_ENERGY_PER_TICK`（§4.100）
   ⇒ 判据改成新的那个常量。**没放宽**（仍然是"必须引用某个具体常量"）。

2. `_zf112_verify.py`：「除了新加的 9 个键，别的键与改前件逐字相同」
   —— 本轮改了 `tooltip.potato_s_t.alloy_smelter` 的**值**（脚注：2 消耗槽 → 四条配方）
   ⇒ 像 ZF117 的 `DESC_TOUCHED` 那样，把"别人动过的键"单列一张名单。

3. `_zf119_verify.py` D6：「交接文档的键数已到 449」
   —— 本轮更新交接文档时把那个数写成了**当时的实际值 454**（并行线加的 5 个键）
   ⇒ 不再钉死一个会漂的数字，改成**与盘上实际键数一致**（更严：钉死会被下一轮打红）。

4. `docs\\开发档案.md` §9 的成品行：我把哈希**折到了下一行**，而 `_zf90/_zf91` 是逐行正则
   （`l.startswith(u"**成品**：")` 那一行里找 40 位哈希）⇒ 它们读到"(没读到哈希)"。
   把那一句收成一行。**这是我自己写文档时踩的格式坑**（不是门的问题）。

跑法：
    python build\\zftools\\_zf121_retarget2.py            # 只校验
    python build\\zftools\\_zf121_retarget2.py --write    # 落盘
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
DOC = os.path.join(ROOT, r"docs\开发档案.md")


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)


RAW = []

RAW.append((
    os.path.join(ZT, u"_zf111_verify.py"),
    u'''    check(u"这条配方用 MAX_ENERGY_PER_TICK（不是 800）",
          "DURATION_TICKS, MAX_ENERGY_PER_TICK));" in recipes)''',
    u'''    # ⚠ ZF121 retarget：这条配方原来借的是 MAX_ENERGY_PER_TICK（"全表最贵那条"那个活体数字），
    #   本轮的振金那条把它抬高 ⇒ 星璨钢会跟着从 12000 变成 14500（§4.100）⇒ 已拆成自己的常量。
    #   判据没放宽：仍然要求它引用**一个具体的每 tick 耗电常量**。
    check(u"这条配方用自己的 STAR_STEEL_ENERGY_PER_TICK（12000，不是 800、也不借 MAX）",
          "DURATION_TICKS, STAR_STEEL_ENERGY_PER_TICK));" in recipes)'''))

RAW.append((
    os.path.join(ZT, u"_zf112_verify.py"),
    u'''        eq(u"%s 除了新加的 9 个键，别的键与改前件逐字相同" % name, [],
           [k for k in before if k not in NEW_KEYS and before[k] != now.get(k)])''',
    u'''        # ⚠ ZF121 追加名单：`tooltip.potato_s_t.alloy_smelter` 的**值**是本轮改的
        #   （脚注从"2 消耗槽 / 配方三条"改成"四条配方 + 振金锭那条"；键没加没删）。
        #   口径照 ZF117 的 `DESC_TOUCHED`：别人动过的键单列名单，别的一个字都不许动。
        eq(u"%s 除了新加的 9 个键 + ZF121 动过的合金炉脚注，别的键与改前件逐字相同" % name, [],
           [k for k in before
            if k not in NEW_KEYS and k not in TOUCHED_BY_ZF121 and before[k] != now.get(k)])'''))

RAW.append((
    os.path.join(ZT, u"_zf112_verify.py"),
    u'''EXPECT_KEYS = 454''',
    u'''EXPECT_KEYS = 454

# ⚠ ZF121：本轮改了这一个键的**值**（合金炉 tooltip 的脚注），键数一个没动。
TOUCHED_BY_ZF121 = [u"tooltip.potato_s_t.alloy_smelter"]'''))

RAW.append((
    os.path.join(ZT, u"_zf119_verify.py"),
    u'''    check(u"D6 交接文档的键数已到 %d" % KEY_NEW, (u"%d 键" % KEY_NEW) in hand)''',
    u'''    # ⚠ ZF121 retarget：这里原来钉死 KEY_NEW（449）。键数是**每一轮都会动的活体数字**
    #   （ZF120 并行线一加就是 454）⇒ 改成"交接文档写的数 == 盘上实际的数"：
    #   比钉死更严（钉死的话，下一轮加键这两边会一起错、而这条检查还是绿的）。
    _lang_keys = len(json.loads(read(os.path.join(LANG, u"zh_cn.json"))))
    check(u"D6 交接文档的键数与盘上一致（%d）" % _lang_keys,
          (u"%d 键" % _lang_keys) in hand)'''))

RAW.append((
    DOC,
    u'''**成品**：**本轮没有新成品** —— `release\\PotatoST-0.11.jar` 仍是 ZF114 打的
**`303c5d468b96826ef6836b0a4e54ccb8a539557c`**（432 键，**不含 ZF116~ZF121**）。''',
    u'''**成品**：**本轮没有新成品** —— `release\\PotatoST-0.11.jar` 仍是 ZF114 打的 **`303c5d468b96826ef6836b0a4e54ccb8a539557c`**（432 键，**不含 ZF116~ZF121**）。'''))


def main(argv):
    do_write = "--write" in argv
    fails, done, cache = [], 0, {}
    for path, old, new in RAW:
        if path not in cache:
            cache[path] = read(path)
        txt = cache[path]
        if new.strip()[:50] in txt and old not in txt:
            print(u"  [跳过] %-24s %s" % (os.path.basename(path), new.strip().split(u"\n")[0][:50]))
            done += 1
            continue
        n = txt.count(old)
        if n != 1:
            fails.append(u"%s 的锚点匹配到 %d 次（应为 1）：%s"
                         % (os.path.basename(path), n, old.strip().split(u"\n")[0][:60]))
            continue
        cache[path] = txt.replace(old, new, 1)
        print(u"  [改]   %-24s %s" % (os.path.basename(path), new.strip().split(u"\n")[0][:60]))
        done += 1
    if fails:
        print(u"")
        print(u"锚点对不上，**一个字节都没写**：")
        for f in fails:
            print(u"  !! " + f)
        return 1
    if do_write:
        for p, txt in cache.items():
            write(p, txt)
        print(u"\n落盘：%d 个文件" % len(cache))
    else:
        print(u"\n（只校验，没落盘；加 --write 才写）")
    print(u"通过 = %d   失败 = 0" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
