# -*- coding: utf-8 -*-
u"""_zf140_docs2.py —— 补一条 §4.140：并发环境里「刚进门还没提交的素材」最容易被扫走

来历（本轮真实事故）：我 22:5x 把用户发的 `黑洞.jpg` 落进 `build\\用户素材\\`，
23:1x 发现它**连同另外 17 份原件一起不见了** —— 另一条线在跑素材区清理。
我的那份是**未跟踪文件**，`git status` 里根本不会提示，清理脚本也不认它。
好在 ① 哈希早就写进了 `_zf140_pre.py` 与 `_来源凭据.json`；② 原始附件还在 ⇒ 按 sha256 逐字节复原。

⚠ 号是抢来的：`4.139` 写之前一刻被 ZF141 那条线占了（`_zf140_docs.py` 的断言当场拦住），顺延 `4.140`。

跑法：python build\\zftools\\_zf140_docs2.py [--write]
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = os.path.join(r"E:\PotatoST", "docs", "开发档案.md")
R4_ANCHOR = u"## 6. 内容速查：加一样东西要动哪些文件\n"

NEW = u"""
### 4.%(n)d 【流程雷】并发环境里，**刚进门还没提交的素材**最容易被别的线扫走（0.11 ZF140）

本轮的素材 `build\\用户素材\\黑洞.jpg` 是 22:5x 落盘的，23:1x 就不见了 —— 连同
**另外 17 份原件**（`crude_oil.png` / `diesel.png` / `star_steel.png` / `星璨钢套装.png` /
`钛合金套装.png` …，`git status` 里全是 ` D`）。那是**另一条线在跑素材区清理**，不是我的脚本干的。

我这份特殊在**它是未跟踪文件**：`git status` 不会提醒、清理脚本也不认得它，
两边都"没做错"，东西就没了。**能复原靠的是两样东西**：

1. **哈希早就写下了** —— `_zf140_pre.py` 里钉着 `sha256 c3466747…`、`_来源凭据.json` 里也有一条；
2. **原始附件还在**（本机 `C:\\Users\\Administrator\\.dsh\\attachments\\…`）⇒ 按 sha256 复原，**逐字节对得上**。

对策（按力度排）：
- **进门就提交**：新素材落盘后立刻单独 commit 一次，比"等这轮做完一起提交"安全得多
  —— 未跟踪文件是并发环境里最脆弱的状态；
- **哈希先落纸**：即使文件被删，"它原本是什么"是可验证的，复原不等于伪造；
- ⚠ **别把"盘上有"当成"盘上还在"**：本轮 `_zf140_commit.py` 的清单体检第一个抓到的就是
  「缺 1：`build/用户素材/黑洞.jpg`」——**清单体检本身就是探测器**，别嫌它烦。

> 号是**抢**来的：这条我先后想用 `4.139`、`4.140`，两次都在落笔前一刻被 ZF141 那条线占掉
> （脚本的"号被占了"断言当场拦住，没写坏档案）。所以这条脚本改成**落笔时现算最大号 +1** ——
> 并发环境里**不许把编号写死在脚本里**（§4.132 的同款教训）。
"""


def main(argv):
    import re
    write = "--write" in argv
    doc = io.open(DOC, "r", encoding="utf-8", newline="").read()
    nums = [int(m.group(1)) for m in re.finditer(r"^### 4\.(\d+) ", doc, re.M)]
    n = (max(nums) + 1) if nums else 135
    body = NEW % {"n": n}
    assert (u"### 4.%d " % n) not in doc, u"§4.%d 已经被占了" % n
    assert doc.count(R4_ANCHOR) == 1, u"锚点不唯一"
    n0 = len(doc)
    doc = doc.replace(R4_ANCHOR, body + R4_ANCHOR, 1)
    print(u"现算最大号 = %d ⇒ 本轮占用 §4.%d" % (max(nums), n))
    print(u"开发档案 %d → %d 字符（+%d）" % (n0, len(doc), len(doc) - n0))
    if write:
        io.open(DOC, "w", encoding="utf-8", newline="").write(doc)
        print(u">>> 已写入")
    else:
        print(u"（只试算；加 --write 才落笔）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
