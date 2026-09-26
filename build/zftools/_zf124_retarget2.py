# -*- coding: utf-8 -*-
u"""_zf124_retarget2.py —— ZF124 第二轮 retarget：**改一个值，会打到三道往轮门**（逐条说清）

改的只是 `advancements.potato_s_t.new_beginning.title` 这**一个值**（四语言），
可它落在三道"老键只许动这几条"的名单里 —— 名字得补进去。**三条判据本身都没放宽**
（仍然是"变动集合逐项相等"，只是名单里多了本轮这一条）：

1. `_zf123_langaudit.py` 的 `SAME_OK`（白名单：允许中文值 == 英文值的键）
   —— `PotatoS&T` 是**商标名**、四语言故意一样（与 `itemGroup.potato_s_t` 同一条口径）
   ⇒ 把新键加进白名单，并写清为什么它是合法的"中英相同"。

2. `_zf107_verify.py` 的 **E7/E8**（"advancements.* 里只有根节点说明这一处被改值"）
   —— 那是 ZF107 那轮立的账；ZF124 又改了根节点**标题**这一个值 ⇒ 两处名单都补上。

3. `_zf117_verify.py` 的 **D7**（"老键里只有状态文案 + 本轮润色的那几条成就说明被改值"）
   —— 名单是 `[ACID_FIX_KEY] + DESC_TOUCHED[l]`。里面缺的不止 ZF124 这一条：
   **ZF121 改的 `tooltip.potato_s_t.alloy_smelter`（合金炉脚注）也一直没补进来**
   （ZF121 那轮的快照里 `_zf117` 就红着，我当时把它整条记到了"润色线的账"上 ——
   **如实更正：其中两条是本项目线自己造成的**）⇒ 本轮一起补，并单列一个常量说明各自是谁改的。

跑法：
    python build\\zftools\\_zf124_retarget2.py            # 只校验
    python build\\zftools\\_zf124_retarget2.py --write    # 落盘
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

AUDIT_OLD = u'''# 允许"中文与英文一样"的键（商标 / 缩写）
SAME_OK = (u"itemGroup.potato_s_t",)'''
AUDIT_NEW = u'''# 允许"中文与英文一样"的键（商标 / 缩写）
# ⚠ ZF124 追加根成就标题：用户把「新的开始！」改成了 `PotatoS&T` —— **商标名不翻译**，
#   与 `itemGroup.potato_s_t`（创造页标题，四语言历来都是 PotatoS&T）同一条口径
#   ⇒ 成就页签与创造页从此**同名**。
SAME_OK = (u"itemGroup.potato_s_t", u"advancements.potato_s_t.new_beginning.title")'''

E7_OLD = u'''        eq(u"E7 %s：advancements.* 里只有根节点说明这 1 处被改值" % l,
           [u"advancements.potato_s_t.new_beginning.description"],
           [k for k in changed if k.startswith(u"advancements.")])
        eq(u"E8 %s：本轮新加的键没被别的东西改过（根节点说明是本轮自己要改的那一条）" % l, [],
           [k for k in changed + other_add if k in MY_KEYS
            and k != u"advancements.potato_s_t.new_beginning.description"])'''
E7_NEW = u'''        # ⚠ ZF124 retarget：根节点的**说明**是 ZF107 那轮自己改的；**标题**是 ZF124 用户点名改的
        #   （「新的开始！」→ PotatoS&T）⇒ 两处名单都补上。判据没放宽，仍是"逐项相等"。
        eq(u"E7 %s：advancements.* 里只有根节点的说明 + ZF124 改的标题这 2 处被改值" % l,
           [u"advancements.potato_s_t.new_beginning.description",
            u"advancements.potato_s_t.new_beginning.title"],
           [k for k in changed if k.startswith(u"advancements.")])
        eq(u"E8 %s：本轮新加的键没被别的东西改过（说明是 ZF107 自己要改的、标题是 ZF124 改的）" % l, [],
           [k for k in changed + other_add if k in MY_KEYS
            and k not in (u"advancements.potato_s_t.new_beginning.description",
                          u"advancements.potato_s_t.new_beginning.title")])'''

D7_OLD = u'''        eq(u"D7 %s：老键里只有状态文案 + 本轮润色的那几条成就说明被改值" % l,
           sorted([ACID_FIX_KEY] + DESC_TOUCHED[l]), changed)'''
D7_NEW = u'''        # ⚠ ZF124 补名单：下面两条**不是**润色线改的，是本项目线自己改的（判据没放宽）：
        #   · `tooltip.potato_s_t.alloy_smelter`  —— ZF121（脚注：2 消耗槽 / 配方三条 → 四条）
        #   · `advancements.potato_s_t.new_beginning.title` —— ZF124（页签改名 PotatoS&T）
        eq(u"D7 %s：老键里只有状态文案 + 润色的成就说明 + 本项目线 ZF121/ZF124 改的那两条被改值" % l,
           sorted([ACID_FIX_KEY] + DESC_TOUCHED[l] + TOUCHED_BY_MAIN_LINE), changed)'''

D7_ANCHOR_OLD = u'''    # 每个新节点的文案里那些"事实"必须还在'''
D7_ANCHOR_NEW = u'''    # ⚠ ZF124 新增：本项目线自己改过的老键（与润色线的 `DESC_TOUCHED` 分开列，便于追责）
    TOUCHED_BY_MAIN_LINE = [u"tooltip.potato_s_t.alloy_smelter",              # ZF121 合金炉脚注
                            u"advancements.potato_s_t.new_beginning.title"]   # ZF124 页签改名
    # 每个新节点的文案里那些"事实"必须还在'''

EDITS = [(os.path.join(ZT, u"_zf123_langaudit.py"), AUDIT_OLD, AUDIT_NEW, u"体检白名单"),
         (os.path.join(ZT, u"_zf107_verify.py"), E7_OLD, E7_NEW, u"E7/E8 名单"),
         (os.path.join(ZT, u"_zf117_verify.py"), D7_OLD, D7_NEW, u"D7 名单"),
         (os.path.join(ZT, u"_zf117_verify.py"), D7_ANCHOR_OLD, D7_ANCHOR_NEW, u"D7 新常量")]


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, text):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)


def main(argv):
    do_write = "--write" in argv
    fails, done, cache = [], 0, {}
    for path, old, new, label in EDITS:
        if path not in cache:
            cache[path] = read(path)
        txt = cache[path]
        if new.strip()[:40] in txt and old not in txt:
            print(u"  [跳过] %-20s %s（幂等）" % (label, os.path.basename(path)))
            done += 1
            continue
        n = txt.count(old)
        if n != 1:
            fails.append(u"%s 的锚点命中 %d 次（应为 1）" % (label, n))
            continue
        cache[path] = txt.replace(old, new, 1)
        print(u"  [改]   %-20s %s" % (label, os.path.basename(path)))
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
