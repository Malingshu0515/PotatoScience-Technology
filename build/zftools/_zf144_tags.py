# -*- coding: utf-8 -*-
"""_zf144_tags.py —— ZF144：四种粒的 `c:` 标签（兼容别的 mod）

用户原话：「…记得加标签兼容别的mod」

## 结构照 NeoForge 现抠（不是记忆）

NeoForge 21.1.235 自带 `data/c/tags/item/nuggets.json`：

    { "values": [ "#c:nuggets/gold", "#c:nuggets/iron",
                  { "id": "#forge:nuggets", "required": false } ] }

⇒ `c:nuggets` 是**聚合标签**，引用 `#c:nuggets/<材料>`。
本工程沿用它那套（`c:ingots` 也是这个形状：聚合 + 单件）。

## 建哪几个

单件（4 个）：`c:nuggets/{aluminum,cobalt,nickel,silver}` —— 各放本模组那一颗粒。
聚合（1 个）：`c:nuggets` —— 引用上面 4 个 `#c:...`，**外加** `#forge:nuggets`
        与 `#forge:nuggets/<材料>` 的 `required:false` 回退（NeoForge 自己就是这么写的，
        这样老 Forge 系别的 mod 也能互通）。

⚠ 聚合 `c:nuggets` 是 **NeoForge 已经提供**的标签文件（在 neoforge jar 里）。
本工程要在**自己的 `data/c/`** 下复写它 —— 数据包合并时同 id 的标签会**合并**（不是覆盖），
所以这样写是安全的，而且这正是 `c:ingots` 的做法（本工程也自己写了一份）。
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

C = r"E:\PotatoST\src\main\resources\data\c\tags\item"
MATS = ["aluminum", "cobalt", "nickel", "silver"]
fails = []


def w(path, obj):
    io.open(path, "w", encoding="utf-8", newline="\n").write(
        json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def main():
    print(u"① 单件标签 c:nuggets/<材料>")
    os.makedirs(os.path.join(C, "nuggets"), exist_ok=True)
    for m in MATS:
        p = os.path.join(C, "nuggets", m + ".json")
        w(p, {"values": ["potato_s_t:%s_nugget" % m]})
        back = json.loads(io.open(p, encoding="utf-8").read())
        ok = back["values"] == ["potato_s_t:%s_nugget" % m]
        print(u"  %s c:nuggets/%-9s -> %s"
              % (u"[OK]" if ok else u"[!!]", m, back["values"]))
        if not ok:
            fails.append(u"c:nuggets/%s 内容不对" % m)

    print(u"\n② 聚合标签 c:nuggets")
    p = os.path.join(C, "nuggets.json")
    if os.path.exists(p):
        print(u"  ⚠ 已存在，先看它原来是什么：")
        print(u"    " + io.open(p, encoding="utf-8").read().replace(u"\n", u" "))
    obj = {"values": ["#c:nuggets/" + m for m in MATS]
                     + [{"id": "#forge:nuggets", "required": False}]
                     + [{"id": "#forge:nuggets/" + m, "required": False} for m in MATS]}
    w(p, obj)
    back = json.loads(io.open(p, encoding="utf-8").read())
    ok = (len(back["values"]) == len(obj["values"])
          and all("#c:nuggets/" + m in back["values"] for m in MATS))
    print(u"  %s c:nuggets -> %s" % (u"[OK]" if ok else u"[!!]", json.dumps(back["values"], ensure_ascii=False)))
    if not ok:
        fails.append(u"c:nuggets 聚合内容不对")

    print(u"\n③ 自检：JSON 能真解析 + 四语言无关")
    import glob
    n = 0
    for f in glob.glob(os.path.join(C, "nuggets*.json")) + \
             [os.path.join(C, "nuggets", m + ".json") for m in MATS]:
        json.loads(io.open(f, encoding="utf-8").read())
        n += 1
    print(u"  [OK] %d 个标签文件都能被真解析器读回" % n)

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
