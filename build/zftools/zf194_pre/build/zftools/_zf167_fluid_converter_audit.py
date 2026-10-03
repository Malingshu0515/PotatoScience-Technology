# -*- coding: utf-8 -*-
u"""_zf167_fluid_converter_audit.py —— 查清 `tooltip.potato_s_t.fluid_converter` 那一处值变化

三种可能，结论完全不同：
  ① 别的线在我建备份之后、我写回之前**把这条写完了** ⇒ 我文件里是"更全"的版本 ✓ 无事；
  ② 我写回时**覆盖了他们刚写的东西**（我先读、他们后写、我再写）⇒ 我丢了他们的字 ✗ 要补回去；
  ③ 那条键在 HEAD 里根本不存在（他们整轮都还没提交）⇒ 只能拿"改前件 vs 现在"的长度与内容判。

判据：把三个来源并排（HEAD / 改前件 / 现在），看**现在**是不是包含改前件的内容（前缀包含），
以及是不是包含 HEAD 的内容。
"""
import io
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
PRE = r"C:\PotatoST救援\zf167_pre\src\main\resources\assets\potato_s_t\lang"
KEY = u"tooltip.potato_s_t.fluid_converter"

for c in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"):
    rel = u"src/main/resources/assets/potato_s_t/lang/%s.json" % c
    r = subprocess.run(["git", "show", u"HEAD:" + rel], cwd=ROOT, capture_output=True)
    head = None
    if r.returncode == 0:
        try:
            head = json.loads(r.stdout.decode("utf-8")).get(KEY)
        except Exception as e:
            head = u"<解析失败 %s>" % e
    pre = json.loads(io.open(os.path.join(PRE, c + u".json"), encoding="utf-8").read()).get(KEY)
    now = json.loads(io.open(os.path.join(LANG, c + u".json"), encoding="utf-8").read()).get(KEY)
    print(u"\n================ %s ================" % c)
    print(u"  HEAD  长度=%s" % (len(head) if isinstance(head, str) else head))
    print(u"  改前件 长度=%s" % (len(pre) if isinstance(pre, str) else pre))
    print(u"  现在  长度=%s" % (len(now) if isinstance(now, str) else now))
    if isinstance(head, str) and isinstance(now, str):
        print(u"  现在 == HEAD ？ %s" % (now == head))
        print(u"  现在 以 HEAD 为前缀？ %s" % now.startswith(head))
    if isinstance(pre, str) and isinstance(now, str):
        print(u"  现在 == 改前件？ %s" % (now == pre))
        print(u"  现在 以改前件为前缀？ %s（= 他们的改动还在、后面又长了）" % now.startswith(pre))
        if not now.startswith(pre) and not pre.startswith(now):
            # 找出第一处不同
            i = 0
            while i < min(len(pre), len(now)) and pre[i] == now[i]:
                i += 1
            print(u"  第一处不同在第 %d 字符：" % i)
            print(u"    改前件: …%s" % pre[max(0, i - 30):i + 60].replace(u"\n", u"\\n"))
            print(u"    现在  : …%s" % now[max(0, i - 30):i + 60].replace(u"\n", u"\\n"))
