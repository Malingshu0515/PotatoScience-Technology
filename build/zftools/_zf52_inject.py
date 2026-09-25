# -*- coding: utf-8 -*-
"""_zf52_inject.py —— 反证用：把中文介绍里第二层前排的 6337 改成 6339（漏斗→散热装置）。

跑完 `_zf52_verify.py` 应当**报错**（图纸画错一格 = 骗人）；之后重跑 `_zf52_lang.py` 即可还原。
"""
import io

P = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang\zh_cn.json"
text = io.open(P, encoding="utf-8").read()
if u"6337" not in text:
    raise SystemExit(u"没找到 6337（是不是已经被改过了？）")
io.open(P, "w", encoding="utf-8", newline="").write(text.replace(u"6337", u"6339"))
print(u"已注入：6337 -> 6339")
