# -*- coding: utf-8 -*-
"""_zf133_docs4.py —— §9 补记（锚点换成 ZF133 段里真实存在的那一行）

上一次锚点写的是「#### 五、本轮踩的坑」—— 那是我**计划里**的标题，实际没落进档案
（当时用的是「四、要你实测」）。⇒ 又一次"按记忆写锚点"（§4.90 的老坑），这次改成
**在 ZF133 段内部**按真实文本定位，并断言锚点唯一。

跑法：python build\\zftools\\_zf133_docs4.py [--write]
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DOC = r"E:\PotatoST\docs\开发档案.md"
WRITE = "--write" in sys.argv

# 用 ZF133 段里"只有我有"的一行当锚点（九道门那行在 §9 的 ZF133 表格里）
ANCHOR = "| 九道门 | **全绿**"

FEEDBACK = """
#### 四·补（2026-09-26 21:37 用户实测反馈）：**客户端一进去就崩**

用户报「Execution failed for task ':runClient' … non-zero exit value -1」。
从 `run/client/crash-reports/crash-2026-09-26_21.37.45-client.txt` 定位到**我自己的渲染代码**：

```
java.lang.IllegalStateException: BufferBuilder was empty
  at com.potatost.mod.client.ShockwaveRenderer.drawWall(ShockwaveRenderer.java:147)
```

根因与修法见 **§4.123**；为什么会漏（只跑了 `runServer`）见 **§4.124**。
已补：`_zf133_verify.py` 新增 **C13/C13b** 两条判据（`begin` 次数 == `drawWithShader` 次数、
不许有单独成句的 `buildOrThrow()`），并写了对应反证 `_zf133_falsify_client.py`（2 把刀都咬住）。
常驻校验 **89 项 0 失败**；成品重打。

"""


def main():
    s = io.open(DOC, encoding="utf-8").read()
    n = s.count(ANCHOR)
    print("锚点出现 %d 次" % n)
    assert n == 1, "锚点不唯一"

    # 找锚点所在行尾 + 该行是否已经是表格最后一行（后面紧跟空行或 "#### "）
    i = s.index(ANCHOR)
    line_end = s.index("\n", i) + 1

    if not WRITE:
        print("（只看；要落笔加 --write）")
        print("插入位置（前后各 3 行）：")
        ls = s[:line_end].split("\n")
        print("\n".join(ls[-3:]))
        return

    s = s[:line_end] + FEEDBACK + s[line_end:]
    io.open(DOC, "w", encoding="utf-8", newline="\n").write(s)
    print("已落笔")
    body = io.open(DOC, encoding="utf-8").read()
    for key in ("四·补", "4.123", "4.124", "BufferBuilder was empty"):
        print("  复核 %-24s 出现 %d 次" % (key, body.count(key)))


main()
