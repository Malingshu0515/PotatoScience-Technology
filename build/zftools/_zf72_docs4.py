# -*- coding: utf-8 -*-
u"""_zf72_docs4.py —— ZF72 第四处档案编辑（一处）：把用户 09-24 的两条拍板记进 §9

用户原话：「5.配方吃两个 嗯 没提到0.12任务的话都是0.11」
  ⇒ ⑤ 油桶配方**吃 2 个铁桶**（产出按默认 1 个）；
  ⇒ ⑩ **没提到 0.12 任务的话，后面所有任务都是 v0.11** ⇒ ZF73 起 `mod_version = 0.11`。
第 ⑩ 条是**长期口径**（不只是这一轮的事），所以同时写进 §9 与规划文档头部。锚点不中就不写。
"""
import hashlib
import io
import sys

ARCH = r"E:\PotatoST\docs\开发档案.md"

ANCHOR = u"      （你说「原油**只能**通过油桶舀取」，而泵天生认液体方块 ⇒ 这条必须你定）。"

ADD = u"""
- [x] **ZF72 已拍板两条（用户 2026-09-24 原话：「5.配方吃两个 嗯 没提到0.12任务的话都是0.11」）**：
      ⑤ 油桶配方**吃 2 个铁桶**、产出按默认 **1 个**（要改成产出 2 就说一声，只改 `count` 一个数字）；
      ⑩ **长期口径：没提到 0.12 任务的话，后面所有任务都算 v0.11**
      ⇒ 石油线全部后续部分（分馏塔、石油产品…）都在 v0.11 里；
      **ZF73 打包时把 `mod_version` 提到 `0.11`**，产出 `PotatoST-0.11.jar`，
      `PotatoST-0.10.jar`（`84d09345…`）原样并存 —— 两个版本不是「作废」关系。
      其余 9 条（舀取量 1000 mB / 不做倒出 / 含水与岩浆 / 灌装机水箱开放 / 海洋油田不加油苗 /
      不算 `is_ocean` / 群系源加可选字段 / 原油不烧不爆 / **泵允许抽原油**）**仍按规划文档 §5 的默认值走**。"""

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    with io.open(ARCH, "r", encoding="utf-8") as fh:
        text = fh.read()
    n = text.count(ANCHOR)
    if n != 1:
        print(u"锚点命中 %d 次（必须正好 1 次）⇒ 整篇不写" % n)
        return 1
    before = sha1(ARCH)
    new_text = text.replace(ANCHOR, ANCHOR + ADD, 1)
    with io.open(ARCH, "w", encoding="utf-8", newline=u"\n") as fh:
        fh.write(new_text)
    print(u"改前 %d 字符 %s" % (len(text), before[:12]))
    print(u"改后 %d 字符 %s" % (len(new_text), sha1(ARCH)[:12]))
    print(u"§9 已记：⑤ 配方吃 2 个铁桶 / ⑩ 长期口径 = 后面全是 0.11")
    for f in fails:
        print(u"  !! " + f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
