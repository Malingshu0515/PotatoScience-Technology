# -*- coding: utf-8 -*-
r"""_zf96_supplement.py —— ZF96 的**补账**（§4.17 来源等级）：`mineable/pickaxe.json`

## 为什么会漏

`zf96_pre` 的清单是我"打算碰哪些文件"列的（§10 的规矩就是这个），当时**漏了这张标签文件**：
新机器虽然 `Block.getDrops` 自己实现了掉落，但本工程**每一台机器**都挂进了
`mineable/pickaxe`（micro_crusher / distillation_controller / distillation_operator / asphalt_block …），
`_zf78_verify.py` 与 `_zf79_verify.py` 里各有一条断言盯着这件事 ⇒ 本轮也该挂。

发现方式：写完机器之后我核"机器方块家族还差哪些联动"，翻到 `_zf78_verify.py:413` 那条断言。

## 来源等级

- **等级 ①（逐字节权威）**：改前那份就在**上一版已发布成品**里 ——
  `zf96_pre\release\PotatoST-0.11.jar`（sha1 必须是 `67d92be3…`，即 ZF95 那版）里的
  `data/minecraft/tags/block/mineable/pickaxe.json`。
- **等级 ③（减法重建）**：另一种独立算法 —— 拿**盘上现在的文件**把我加的那一行删掉、再补回逗号，
  两者必须**逐字节相同**。两条路对上了才算补账成立（§4.17：能失败的检查才算检查）。
"""
import hashlib
import io
import os
import shutil
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf96_pre"
PRE_JAR = os.path.join(BK, r"release\PotatoST-0.11.jar")
REL = u"data/minecraft/tags/block/mineable/pickaxe.json"
DISK = os.path.join(ROOT, r"src\main\resources\data\minecraft\tags\block\mineable\pickaxe.json")
DST = os.path.join(BK, r"src\main\resources\data\minecraft\tags\block\mineable\pickaxe.json")
PRE_JAR_SHA = "67d92be385540d2cd93c587f003e2a788dfab45d"
# 我加的那一行（与盘上写法逐字一致：**最后一行没有逗号**，逗号加在了上一行末尾）
ADDED = u'    "potato_s_t:hydrodesulfurization_chamber"\n'
PREV_WITH_COMMA = u'"potato_s_t:alloy_smelter_port",\n'
PREV_NO_COMMA = u'"potato_s_t:alloy_smelter_port"\n'
fails = []


def check(ok, msg):
    print((u"  [OK]   " if ok else u"  [FAIL] ") + msg)
    if not ok:
        fails.append(msg)
    return ok


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.exists(DST):
        print(u"  [STOP] 补账文件已存在（重跑会覆盖）：%s" % DST)
        return 1
    if not os.path.exists(PRE_JAR):
        print(u"  [STOP] 找不到改前成品：%s" % PRE_JAR)
        return 1
    check(sha1(PRE_JAR) == PRE_JAR_SHA,
          u"改前成品 jar 的 sha1 = %s…（必须是 ZF95 那版）" % PRE_JAR_SHA[:8])

    # ---- 等级 ①：从已发布成品里取改前件 ----
    with zipfile.ZipFile(PRE_JAR) as zf:
        check(REL in zf.namelist(), u"改前成品里有 %s" % REL)
        if REL not in zf.namelist():
            return 1
        official = zf.read(REL)

    # ---- 等级 ③：减法重建（拿盘上现在的文件删掉我加的那一行）----
    now = open(DISK, "rb").read().decode("utf-8")
    check(ADDED in now, u"盘上确实有那一行（%s）" % ADDED.strip())
    if ADDED not in now:
        return 1
    # 删行之后：上一行（alloy_smelter_port）末尾那个逗号要**去掉**（它原本是最后一行、没有逗号）
    rebuilt = now.replace(ADDED, u"")
    check(PREV_WITH_COMMA in rebuilt, u"删掉新行之后，上一行末尾还留着那个逗号（等着去掉）")
    rebuilt = rebuilt.replace(PREV_WITH_COMMA, PREV_NO_COMMA)
    check(rebuilt.encode("utf-8") == official,
          u"减法重建与成品里那份**逐字节相同**（%d B vs %d B）" % (len(rebuilt.encode("utf-8")), len(official)))

    if fails:
        print(u"\n  失败项 = %d ⇒ 不落盘" % len(fails))
        return 1

    os.makedirs(os.path.dirname(DST), exist_ok=True)
    with open(DST, "wb") as fh:
        fh.write(official)
    # 落盘后核"副本自己"
    check(sha1(DST) == hashlib.sha1(official).hexdigest(), u"补账副本落盘后哈希一致")
    io.open(os.path.join(BK, u"_补说明.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"ZF96 补账（1 份）\n"
        u"=================\n"
        u"文件：src\\main\\resources\\data\\minecraft\\tags\\block\\mineable\\pickaxe.json\n"
        u"为什么漏：zf96_pre 的清单是「打算碰哪些文件」列的，当时没想到新机器要挂 mineable/pickaxe；\n"
        u"          发现方式 = 核「机器方块家族还差哪些联动」时翻到 _zf78_verify.py:413 那条断言。\n"
        u"来源等级 ①：改前那份 = zf96_pre\\release\\PotatoST-0.11.jar（sha1 %s…）里的同名条目（逐字节权威）。\n"
        u"来源等级 ③（交叉自证）：拿盘上现在的文件删掉「我加的那一行」+ 补回上一行末尾的逗号，\n"
        u"          与等级 ① 那份**逐字节相同**。\n"
        u"改动内容：加一行 potato_s_t:hydrodesulfurization_chamber（并给上一行补逗号）。\n"
        u"回退办法：用本目录这一份覆盖回去即可（它就是改前件）。\n" % PRE_JAR_SHA[:8])
    print(u"\n  补账已落盘：%s" % DST)
    print(u"  说明：%s" % os.path.join(BK, u"_补说明.txt"))
    print(u"  失败项 = 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
