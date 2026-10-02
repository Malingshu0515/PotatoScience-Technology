# -*- coding: utf-8 -*-
"""_zf133_cleanup6.py —— 探针里最后一处对已删字段的引用（`ShockwaveManager.TRACE = true;`）

`ShockwaveManager` 里的 trace 已经撤掉了（那是产品代码，不能留诊断），
探针里这一行于是编译不过。删掉它 —— 探针自己的 `[WAVES]` 打印足够定位问题。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

OLD = """        ShockwaveManager.TRACE = true;   // 全程 trace（诊断用，修好前不关）
"""
s = io.open(CHK, encoding="utf-8").read()
n = s.count(OLD)
assert n == 1, "锚点 %d 次" % n
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s.replace(OLD, "", 1))
print("[OK] 已删（探针里不再引用已撤掉的诊断字段）")
print("残留 ShockwaveManager.TRACE =", "ShockwaveManager.TRACE" in
      io.open(CHK, encoding="utf-8").read())
