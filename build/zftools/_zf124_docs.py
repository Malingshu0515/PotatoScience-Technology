# -*- coding: utf-8 -*-
u"""_zf124_docs.py —— ZF124 的文档三件套（锚点替换）

① `docs\\开发档案.md` §5 表格追加 ZF124 行；
② 同文件 §9 追加 ZF124 小节（插在 `## 10. 备份策略` 之前）；
③ `docs\\多会话协作交接.md` §6 追加第 16 条。

跑法：
    python build\\zftools\\_zf124_docs.py            # 只校验
    python build\\zftools\\_zf124_docs.py --write    # 落盘
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, r"docs\开发档案.md")
HAND = os.path.join(ROOT, r"docs\多会话协作交接.md")

A5_TAIL = u'''| 见 §9 |



> ZF40~ZF44 全是**电力高炉的连续改动**'''

ROW = u'''| ZF124 | **新建 `zf124_pre`**（**105 份**改前件：`ModItems.java` + 四份 lang + 根成就 `new_beginning.json` + `_zf70_verify`/`_zf70_lang` + 全部常驻校验脚本 + 3 份文档 + 旧成品 jar 与 `.sha1`；逐份核哈希 + **回读证明**、失败 0） | 0.11：**成就页签改名 + 创造页图标换星轨坠**。用户原话（附成就界面截图：鼠标停在「新的开始！」那个页签上、页签图标是微型粉碎机）：「把成就的 新的开始！这一分类改成 PotatoS&T 创造模式标签页换成星轨追的物品贴图」（「星轨追」按「星轨坠」理解）。① **成就页签的名字 = 根成就 `new_beginning` 的标题**（成就界面一个模组一个页签，页签悬浮名就是它；JSON 里写的是 `translate` 键 ⇒ 数据包一个字不用动）⇒ 四语言的值 `新的开始！`/`A New Beginning!`/`新たな始まり！`/`Новое начало!` **统一改成 `PotatoS&T`**（**商标名不翻译** —— 与创造页标题 `itemGroup.potato_s_t` 四语言一直是 `PotatoS&T` 的口径一致，改完两边**同名**）；② **创造页图标**：`ModItems.POTATO_ST_TAB` 的 `.icon(...)` 从**铝锭**换成**星轨坠**（`STARFALL_PENDANT`；静态序核过：星轨坠声明在 483 行、创造页在 541 行，而且 `.icon(...)` 是 lambda、求值在造标签页时 ⇒ 不会踩 §4.1 那个"注册没完就取物品"的雷）；③ ⚠ **边界（如实记）**：用户那句「换成星轨坠的物品贴图」有两种读法（**创造页**的图标 / **成就页签**的图标），本轮**按字面**改创造页，**成就页签的图标（微型粉碎机）一个字没动**，并在汇报里请他一句话确认；④ **retarget 两处**：`_zf70_verify.py` 里根成就的 `title_zh`（那是"中文标题逐字等于用户原话"的判据，目标值跟着换成 `PotatoS&T`，判据本身没放宽；表里另外两条一个字没动）+ 英文公告的**成就树那一行**（当前状态）；**ZF107 那条 changelog 历史记录没动**（改了就是篡改当时发生的事）；⑤ 证据：`_zf124_verify.py`（**39 项**）、反证 **K183~K186 四把刀**（改回旧名 / 只改回 en_us / 图标改回铝锭 / 往轮门改回去）；⚠ 本轮**没有探针**（改的是 lang 的值 + 客户端标签页图标，无头服务端只能验到 lang 与源码）| 见 §9 |'''

A9_ANCHOR = u'''## 10. 备份策略'''

A9_NEW = u'''### ZF124（0.11）成就页签改名 PotatoS&T + 创造页图标换成星轨坠 —— **待你实测**

原话（附成就界面截图：鼠标正停在「新的开始！」那个页签上，页签图标是**微型粉碎机**）：
「把成就的 新的开始！这一分类改成 PotatoS&T 创造模式标签页换成星轨追的物品贴图」
（「星轨追」按**星轨坠**理解）。

#### 一、改了什么

| # | 改哪儿 | 改前 | 改后 |
|---|---|---|---|
| ① | **成就页签的名字** = 根成就 `new_beginning` 的标题（四语言） | 新的开始！/ A New Beginning! / 新たな始まり！/ Новое начало! | **PotatoS&T**（四语言统一） |
| ② | **创造模式标签页的图标** = `ModItems.POTATO_ST_TAB` 的 `.icon(...)` | **铝锭** | **星轨坠**（`STARFALL_PENDANT`） |

两条说明：

- 成就界面里**一个模组一个页签**，页签的悬浮名就是**根成就的标题**、页签图标就是**根成就的
  `display.icon`**；而 JSON 里写的是 `translate` 键 ⇒ **数据包一个字都不用动**，只改四份 lang 的**值**。
- 四语言**都**写成 `PotatoS&T`：这是**商标名**，跟创造页标题 `itemGroup.potato_s_t`
  （四语言历来都是 `PotatoS&T`、不翻译）同一条口径 —— 改完**成就页签与创造页同名**。

#### 二、⚠ 你那句话有两种读法，我按字面做了，请你一句话确认

「创造模式标签页换成星轨追的物品贴图」—— **换成星轨坠贴图的到底是哪一个**？

| 读法 | 我做了什么 |
|---|---|
| **创造页的图标**（字面） | ✅ 已改：创造页图标 = 星轨坠 |
| 成就页签的图标（截图里那个黑方块 = **微型粉碎机**） | ❌ **没动**（用户只说了改名，没说换图标；`_zf124_verify.py` 里专门有一条盯着它"仍是微型粉碎机"） |

如果你要的是**成就页签那个图标**也换成星轨坠，说一声 —— 改的是
`data\\potato_s_t\\advancement\\new_beginning.json` 的 `display.icon`（一行，改完再重跑校验）。

#### 三、连带改的两处（都是"被本轮的改动作废的判据/说明"，不是放宽）

1. **`_zf70_verify.py` 的 `title_zh`**：那是 ZF70 立的"中文标题逐字等于用户原话"判据，
   目标值跟着换成 `PotatoS&T`。**判据本身没放宽**（仍然是逐字相等）；表里另外两条
   （更强劲的电源 / 入门清洁能源）**一个字没动**（K186 专门咬这一条）。
2. **英文公告的成就树那一行**（`A New Beginning!        obtain a Micro Crusher`
   → `PotatoS&T                obtain a Micro Crusher`）：那是给玩家看的**当前状态**树。
   ⚠ 同一份文档下面第 269 行 `- **"A New Beginning!" moved earlier.**` 是 **ZF107 那轮的
   changelog 记录**，属于**历史**，**一个字没动**（改了就是篡改当时发生的事）。

#### 四、证据

| 项 | 值 |
|---|---|
| 探针 | **本轮没有探针**（如实说）：改的是 lang 的**值** + 客户端标签页图标；无头服务端只能验到 lang 与源码，验不到"页签上写着什么" |
| 常驻校验 | `_zf124_verify.py` **39 项**：四语言标题值 / 与创造页同名 / 相对改前件只动了这一个值 / 根成就 JSON 仍是 `translate` 键 / 根成就图标没被动 / 创造页 `.icon` 是星轨坠且铝锭不再当图标 / 静态序 / 往轮门 retarget / 英文公告树改了而那行历史没动 |
| 反证刀 | **K183~K186 四把**：zh_cn 改回旧名 / 只把 en_us 改回去 / 图标改回铝锭 / 往轮门目标值改回去 —— 每把都必须咬住**指定的那一条** |
| 要你实测 | **重启客户端**（或 `F3+T` 重载资源包）：① 成就界面那个页签应当叫 **PotatoS&T**（悬浮也是）；② 创造模式物品栏里 PotatoS&T 页签的图标应当是**星轨坠** |

**成品**：**本轮没有新成品** —— `release\\PotatoST-0.11.jar` 仍是 ZF114 打的 **`303c5d468b96826ef6836b0a4e54ccb8a539557c`**（432 键，**不含 ZF116~ZF124**）。

## 10. 备份策略'''

H16_OLD = u'''    ④ 本轮**没有探针**（改的是纯客户端代码），证据是客户端日志前后对照 + 源码逐一对应 + 5 把反证刀。'''
H16_NEW = u'''    ④ 本轮**没有探针**（改的是纯客户端代码），证据是客户端日志前后对照 + 源码逐一对应 + 5 把反证刀。
16. **ZF124 的账**：① **成就页签的名字 = 根成就 `new_beginning` 的标题**（四语言现在都是
    `PotatoS&T`，与创造页标题同名）；**创造页图标**从铝锭换成了**星轨坠**
    （`ModItems.POTATO_ST_TAB` 的 `.icon(...)`）；② ⚠ **待用户确认的一处**：他那句
    「换成星轨坠的物品贴图」我按字面理解成**创造页**的图标，**成就页签的图标（微型粉碎机）
    没动** —— 若他要的是页签图标，改 `new_beginning.json` 的 `display.icon` 一行即可；
    ③ `_zf70_verify.py` 的根成就 `title_zh` 已 retarget 到 `PotatoS&T`（判据没放宽），
    英文公告的**成就树**改了、**ZF107 那条 changelog 历史没动**；④ 本轮没有探针（改的是
    lang 的值 + 客户端图标），证据是 31 项常驻校验 + 4 把反证刀。'''

EDITS = [(DOC, A9_ANCHOR, A9_NEW, u"§9 ZF124 小节"),
         (HAND, H16_OLD, H16_NEW, u"交接 §6 第 16 条")]


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
            print(u"  [跳过] %-24s（幂等）" % label)
            done += 1
            continue
        n = txt.count(old)
        if n != 1:
            fails.append(u"%s 的锚点命中 %d 次（应为 1）" % (label, n))
            continue
        cache[path] = txt.replace(old, new, 1)
        print(u"  [改]   %-24s %s" % (label, os.path.basename(path)))
        done += 1
    doc = cache[DOC]
    if u"| ZF124 |" not in doc:
        n = doc.count(A5_TAIL)
        if n != 1:
            fails.append(u"§5 表格尾锚点命中 %d 次（应为 1）" % n)
        else:
            doc = doc.replace(A5_TAIL, u"| 见 §9 |\n" + ROW +
                              u"\n\n\n\n> ZF40~ZF44 全是**电力高炉的连续改动**", 1)
            print(u"  [改]   §5 表格追加 ZF124 行")
            done += 1
    else:
        print(u"  [跳过] §5 表格 ZF124 行（已加过，幂等）")
        done += 1
    cache[DOC] = doc
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
