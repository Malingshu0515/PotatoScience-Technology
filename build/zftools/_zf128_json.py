# -*- coding: utf-8 -*-
u"""_zf128_json.py —— ZF128 的数据改动（**一行**）：根成就的图标换成毒马铃薯

用户原话：「成就栏换成毒马铃薯 但是成就还是粉碎机可以嘛」

改的是 `data\\potato_s_t\\advancement\\new_beginning.json` 的 **`display.icon.id`**：

| 字段 | 改前 | 改后 |
|---|---|---|
| `display.icon.id` | `potato_s_t:micro_crusher` | **`minecraft:poisonous_potato`** |
| `criteria…items` | `potato_s_t:micro_crusher` | **一个字不动**（"成就还是粉碎机"那一半） |
| `display.title` / `description` / `background` / `frame` / `hidden` | —— | **一个字节不动** |

⚠ 页签图标与根节点图标是**同一个字段**（`AdvancementTab.icon = display.getIcon()`，
树里的节点也画 `display.getIcon()`）⇒ 换了这个，页签与树里那个小方块**一起变**。

跑法：
    python build\\zftools\\_zf128_json.py
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
P = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\advancement\new_beginning.json")
BK = r"C:\PotatoST救援\zf128_pre\src\main\resources\data\potato_s_t\advancement\new_beginning.json"

OLD = u'"id": "potato_s_t:micro_crusher"'
NEW = u'"id": "minecraft:poisonous_potato"'
KEEP = u'"items": "potato_s_t:micro_crusher"'

notes, fails = [], []


def main():
    text = io.open(P, encoding="utf-8", newline=u"").read()
    before = json.loads(text)
    if before["display"]["icon"]["id"] == u"minecraft:poisonous_potato":
        notes.append(u"图标已经是毒马铃薯（幂等跳过）")
    else:
        n = text.count(OLD)
        if n != 1:
            fails.append(u"锚点 %s 命中 %d 次（要 1 次）—— 停手" % (OLD, n))
        elif KEEP not in text:
            fails.append(u"判据那行不在（%s）—— 停手" % KEEP)
        else:
            io.open(P, "w", encoding="utf-8", newline=u"").write(text.replace(OLD, NEW, 1))
            notes.append(u"display.icon.id：micro_crusher → minecraft:poisonous_potato（一行）")

    after = json.loads(io.open(P, encoding="utf-8", newline=u"").read())
    check = [
        (u"图标 = minecraft:poisonous_potato",
         after["display"]["icon"]["id"] == u"minecraft:poisonous_potato"),
        (u"判据**仍是** potato_s_t:micro_crusher（「成就还是粉碎机」那一半）",
         after["criteria"]["got"]["conditions"]["items"][0]["items"] == u"potato_s_t:micro_crusher"),
        (u"title / description 仍是 translate 键（没被写成字面量）",
         isinstance(after["display"]["title"], dict) and isinstance(after["display"]["description"], dict)),
        (u"background / frame / hidden / show_toast 没动",
         (after["display"]["background"], after["display"]["frame"], after["display"]["hidden"],
          after["display"]["show_toast"]) ==
         (before["display"]["background"], before["display"]["frame"], before["display"]["hidden"],
          before["display"]["show_toast"])),
        (u"requirements / sends_telemetry_event 没动",
         after["requirements"] == before["requirements"]
         and after["sends_telemetry_event"] == before["sends_telemetry_event"]),
        (u"除 icon.id 外，JSON 对象与改前件完全相同（逐字段比）",
         {k: v for k, v in before.items() if k != u"display"} ==
         {k: v for k, v in after.items() if k != u"display"}
         and {k: v for k, v in before["display"].items() if k != u"icon"} ==
         {k: v for k, v in after["display"].items() if k != u"icon"}
         and before["display"]["icon"] == {u"count": 1, u"id": u"potato_s_t:micro_crusher"}),
        (u"改前件在 zf128_pre 里（取证用）", os.path.exists(BK)),
    ]
    for name, ok in check:
        if ok:
            notes.append(name)
        else:
            fails.append(name)

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
