# -*- coding: utf-8 -*-
"""_zf134_fixtails.py —— 修两处"注释尾巴"（终点标记只匹配了注释行的前半截）

现象：编译报 `非法字符: '\\u3002'`（中文句号）在第 202/507 行 —— 那两行是
```
 {@code PotatoST} 挂在 {@code ServerTickEvent.Post} 上。 */
（探针/验证用，不参与玩法）。 */
```
即：我切 [起点, 终点) 时只吃到注释行的**前半截**，后半截留在原地成了裸文本。
⇒ 又一条规矩：**终点标记要吃到整行**（含该行的其余内容），否则会留下"半行"。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
M = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

FIXES = [
    (" {@code PotatoST} 挂在 {@code ServerTickEvent.Post} 上。 */",
     "    /** 推进所有冲击波；由 {@code PotatoST} 挂在 {@code ServerTickEvent.Post} 上。 */"),
    ("（探针/验证用，不参与玩法）。 */",
     "    /** 当前还有几道波（探针/验证用，不参与玩法）。 */"),
]


def main():
    lines = io.open(M, encoding="utf-8").read().split("\n")
    for k, l in enumerate(lines):
        for bad, good in FIXES:
            if l == bad:
                print("行 %d: %s  ->  %s" % (k + 1, bad[:40], good.strip()[:50]))
                lines[k] = good
    body = "\n".join(lines)
    for bad, _ in FIXES:
        assert bad not in body.split("\n"), "还有残留：%s" % bad[:30]
    io.open(M, "w", encoding="utf-8", newline="\n").write(body)
    print("[OK] 两处注释尾巴已修好")


main()
