# -*- coding: utf-8 -*-
"""_zf134_apply2.py —— 补一刀：把残留的 `mainCoord` 方法体与旧类结尾的 `}` 一起吃掉

## 真因（终于看清了）
`Wave` 那一刀切的是 [类注释, "主轴坐标"注释行]，新文本自带 `}` 与结尾空行；
但**旧版的 `mainCoord` 方法体（3 行）与类结尾的 `}` 在终点之后** ⇒ 它们留了下来：

```
/*CUT*/        /** 主轴坐标（当前采样位置）。 */      ← 我的新文本接在这里（自带 }）
        private int mainCoord(int origin) {          ← 残留 1
            return origin + sign * travelled * ...;  ← 残留 2
        }                                            ← 残留 3
    }                                                ← 旧类的收尾 }（残留 4）
```

所以第 6 刀：把 [新文本结尾, `    /**\\n     * 右键出手：起一道波。` ) 之间的残留整段吃掉。
（**教训**：行区间切片要**吃干净整段**，别只切到"我以为的终点" ——
  终点之后的尾巴（方法体、收尾括号）同样属于这一段。）

跑法：python build\\zftools\\_zf134_apply2.py
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
M = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

# 新文本的结尾（Wave 类的收尾）→ 下一段的起点
START = "        /** 阵面前缘中心的 Z。 */\n" \
        "        private double frontZ(double originZ) {\n" \
        "            return originZ + dirZ * travelled * STEP_PER_TICK;\n" \
        "        }\n" \
        "    }\n"
END = "    /**\n     * 右键出手：起一道波。"


def strip_comments(src):
    out = re.sub(r"/\*[\s\S]*?\*/", "", src)
    return re.sub(r"//[^\n]*", "", out)


def main():
    s = io.open(M, encoding="utf-8").read()
    assert "dirZ * travelled" in s, "上一刀（Wave 新文本）还没落盘，先跑 _zf134_apply.py"
    assert s.count(START) == 1, "起点 %d 次" % s.count(START)
    assert s.count(END) == 1, "终点 %d 次" % s.count(END)

    i = s.index(START)
    j = s.index(END)
    assert j > i, "终点在起点前"
    tail = s[i + len(START):j]
    print("将吃掉的残留（%d 字符）：" % len(tail))
    for l in tail.split("\n")[:8]:
        print("   | " + l)
    s = s[:i + len(START)] + "\n" + s[j:]

    code = strip_comments(s)
    for dead in ("alongX", "mainCoord", "int main =", "wave.sign"):
        assert dead not in code, "代码里还残留：%s（%d 次）" % (dead, code.count(dead))
    print("[OK ] 代码里旧字段全清")

    io.open(M, "w", encoding="utf-8", newline="\n").write(s)
    body = io.open(M, encoding="utf-8").read()
    print("已写盘：%d 字符（dirX %d / perpX %d）" % (len(body), body.count("dirX"), body.count("perpX")))


main()
