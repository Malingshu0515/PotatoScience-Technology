# -*- coding: utf-8 -*-
u"""_zf128_handfix.py —— 修 交接文档 §6 第 18/19/20 条的**错位**（我自己的锅，如实记）

**怎么坏的**：交接文档每一条都是**跨多行的整段**，而 `_zf127_docs.py` / `_zf128_docs.py` 用的
`insert_after_line(..., u"18. **ZF126 的账**", ...)` 只按**第一行**匹配 ⇒ 新条目被插到了
**上一条的正文中间**。现在盘上的顺序是：

```
17 → 18(第一行) → 19(第一行) → 20(整段) → 19(剩下) → 18(剩下)
```

**修法**：按行区间把三段重新拼回 `17 → 18 → 19 → 20`，并顺手给第 20 条补上素材线那一段（⑥）。
**教训**：多行条目的文档，"插在某条之后"必须按**整条的结束位置**算，不能按首行匹配
（§4.99/§4.104 那条"拼接式补丁"的家族）。

跑法：
    python build\\zftools\\_zf128_handfix.py
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = r"E:\PotatoST\docs\多会话协作交接.md"
notes, fails = [], []

ADD = (u"\n    ⑥ ⚠ **本轮期间素材线把银线那两张贴图画了**（13:02）⇒ 待画 **15 → 13**，"
       u"ZF127 立的「不许有自己的 png」那几条判据当场被顶红 ⇒ 已按「图到了就换成正向判据」跟平，"
       u"并把**待画数这条链改成现问 `TextureCheck.py`**（顺手钉了子进程编码 `PYTHONIOENCODING=utf-8`）；"
       u"另有两处「素材线改了、我这边跟平判据」：`_zf107_verify.py` 的 C1/C2/C5（根节点图标专属判据）、"
       u"`_zf125_verify.py` 的 E3（控制器模型加了顶面贴图）。见 §4.111 与 §9 第五节。")


def main():
    lines = io.open(P, encoding="utf-8", newline=u"").read().split(u"\n")
    idx = {}
    for i, l in enumerate(lines):
        for n in (18, 19, 20):
            if l.startswith(u"%d. **ZF" % n):
                idx[n] = i
    if len(idx) != 3:
        fails.append(u"三条的起点没找齐：%s" % idx)
        print(u"  !! " + fails[-1])
        return 1
    i18, i19, i20 = idx[18], idx[19], idx[20]
    head = lines[:i18]                 # 到第 17 条结束（含空行）
    b18_head, b19_head, b20 = lines[i18], lines[i19], lines[i20:i19 + 0]  # 占位，下面重算
    b20 = lines[i20:i19] if False else None
    # 实际区间：18 的正文 = i18 那一行 + 【i19-1 之后】；坏序是 18头,19头,20段,19尾,18尾
    # 用内容找边界：19 的尾巴从"     **16134 FE/t**"那行开始；18 的尾巴从"     18k的fe」）"那行开始
    t19 = next((i for i, l in enumerate(lines) if u"**16134 FE/t**，铜线仍 2048）" in l), -1)
    t18 = next((i for i, l in enumerate(lines) if u"18k的fe」）——" in l), -1)
    if t19 < 0 or t18 < 0 or not (i20 < t19 < t18):
        fails.append(u"区间没对上（19尾=%d 18尾=%d 20=%d）" % (t19, t18, i20))
        print(u"  !! " + fails[-1])
        return 1

    item18 = [lines[i18]] + lines[t18:]
    item19 = [lines[i19]] + lines[t19:t18]
    item20 = lines[i20:t19]
    if not any(u"⑥ ⚠ **本轮期间素材线" in l for l in item20):
        item20 = item20 + ADD.split(u"\n")

    out = head + item18 + [u""] + item19 + [u""] + item20
    io.open(P, "w", encoding="utf-8", newline=u"").write(u"\n".join(out))
    notes.append(u"§6 重排：18（%d 行）/ 19（%d 行）/ 20（%d 行）"
                 % (len(item18), len(item19), len(item20)))

    # 自检：三条各自连续、顺序正确、20 条里有素材线那一段
    t = io.open(P, encoding="utf-8", newline=u"").read()
    order = [t.find(u"18. **ZF126 的账**"), t.find(u"19. **ZF127 的账**"),
             t.find(u"20. **ZF128 的账")]
    check = [
        (u"三条都在", all(x >= 0 for x in order)),
        (u"顺序 18 < 19 < 20", order == sorted(order)),
        (u"第 20 条里有素材线那一段", u"⑥ ⚠ **本轮期间素材线" in t),
        (u"第 18 条正文里不再夹着 19/20（18 之后紧跟 19）",
         t.find(u"18k的fe」）——") < t.find(u"19. **ZF127 的账**")),
        (u"19 的正文完整（含 ⑦ 证据那一行）",
         0 < t.find(u"⑦ 证据：探针 **45 项全绿**") < t.find(u"20. **ZF128 的账")),
    ]
    for name, ok in check:
        if ok:
            notes.append(name)
        else:
            fails.append(name)

    print(u"\n".join(u"  [OK] " + x for x in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
