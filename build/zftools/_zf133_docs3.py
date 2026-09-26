# -*- coding: utf-8 -*-
"""_zf133_docs3.py —— 补记：客户端崩溃两条（§4.123/§4.124）+ §9 里加一段实测反馈

锚点：
  · §4 那条插在 "### 4.118 【陷阱】假玩家探针" 之前（我的五条之前，编号接 4.122 之后 → 4.123/4.124）
  · §9 的补充插在 "### ZF133（0.11）星璨钢斧 + 冲击波" 那一段的 "#### 五、本轮踩的坑" 之前

跑法：python build\\zftools\\_zf133_docs3.py            # 只看
      python build\\zftools\\_zf133_docs3.py --write
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DOC = r"E:\PotatoST\docs\开发档案.md"
T = r"E:\PotatoST\build\zftools"
WRITE = "--write" in sys.argv

PIT_FILE = os.path.join(T, "_zf133_pitfall2.md")
R4_ANCHOR = "### 4.118 【陷阱】假玩家探针"

FEEDBACK = """#### 四·补（2026-09-26 21:37 用户实测反馈）：**客户端一进去就崩**

用户报「Execution failed for task ':runClient' … non-zero exit value -1」。
从 `run/client/crash-reports/crash-2026-09-26_21.37.45-client.txt` 定位到**我自己的渲染代码**：

```
java.lang.IllegalStateException: BufferBuilder was empty
  at com.potatost.mod.client.ShockwaveRenderer.drawWall(ShockwaveRenderer.java:147)
```

根因与修法见 **§4.123**；为什么会漏（只跑了 `runServer`）见 **§4.124**。
已补：`_zf133_verify.py` 新增 **C13/C13b** 两条判据（`begin` 次数 == `drawWithShader` 次数、
不许有单独成句的 `buildOrThrow()`），并写了对应的反证 `_zf133_falsify_client.py`（2 把刀都咬住）。
常驻校验 **89 项 0 失败**；成品重打（SHA1 见文末）。

"""


def main():
    s = io.open(DOC, encoding="utf-8").read()
    before = len(s)
    pit = io.open(PIT_FILE, encoding="utf-8").read()

    n = s.count(R4_ANCHOR)
    print("§4 锚点出现 %d 次" % n)
    assert n == 1, "§4 锚点不唯一"

    fb_anchor = "#### 五、本轮踩的坑（每条都已立成 §4 的规矩）"
    if fb_anchor in s:
        print("§9 补充锚点出现 1 次")
    else:
        print("⚠ §9 补充锚点没找到（可能被我改过）—— 只落 §4")

    if not WRITE:
        print("（只看；要落笔加 --write）")
        return

    # ① §4.123/4.124 插在 4.118 之前
    i = s.index(R4_ANCHOR)
    s = s[:i] + pit.strip("\n") + "\n\n" + s[i:]

    # ② §9 补一段实测反馈
    if fb_anchor in s:
        j = s.index(fb_anchor)
        s = s[:j] + FEEDBACK + s[j:]

    io.open(DOC, "w", encoding="utf-8", newline="\n").write(s)
    print("已落笔：%d -> %d 字符（+%d）" % (before, len(s), len(s) - before))

    body = io.open(DOC, encoding="utf-8").read()
    for key in ("4.123", "4.124", "BufferBuilder was empty", "C13"):
        print("  复核 %-22s 出现 %d 次" % (key, body.count(key)))


main()
