# -*- coding: utf-8 -*-
"""_zf134_manager6.py —— 「旧字段不许残留」的复核要**先剥注释**（否则判据自己撞自己）

两次都栽在这上面：我在新 javadoc 里解释「旧版存的是 XXX」，而 XXX 正是要禁止的标识符
⇒ `assert "XXX" not in s` 把注释里的那句算成"残留" ⇒ 正确的中止（不写盘）。

修法：复核前把 `/* */` 与 `//` 注释剥掉，再查标识符。
（这条规矩本身值得记：**"禁止某标识符"的检查，注释里也不能出现它 —— 或者检查时先剥注释**。）
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf134_manager5.py"

OLD = '''    # 全局复核
    for dead in ("alongX", "mainCoord", "int main =", "wave.sign"):
        assert dead not in s, "还残留：%s（%d 次）" % (dead, s.count(dead))'''

NEW = '''    # 全局复核：**先剥注释**再查（javadoc 里解释旧实现时会提到旧标识符，那是合法的）
    def strip_comments(src):
        out = re.sub(r"/\\*[\\s\\S]*?\\*/", "", src)
        out = re.sub(r"//[^\\n]*", "", out)
        return out

    code = strip_comments(s)
    for dead in ("alongX", "mainCoord", "int main =", "wave.sign"):
        assert dead not in code, "还残留：%s（代码里 %d 次）" % (dead, code.count(dead))
    print("[OK ] 代码里旧字段全清（注释里提到不算）")'''

s = io.open(P, encoding="utf-8").read()
n = s.count(OLD)
assert n == 1, "锚点 %d 次" % n
s = s.replace(OLD, NEW, 1)

# 需要 import re
if "import re\n" not in s:
    s = s.replace("import io\nimport sys", "import io\nimport re\nimport sys", 1)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("[OK] 复核已改成先剥注释")
