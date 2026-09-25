# -*- coding: utf-8 -*-
u"""_zf118_mkgatesnap.py —— 从上轮那份全门快照脚本派生 ZF118 的（只加 ZF118 那道门）"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ZT = r"E:\PotatoST\build\zftools\\"
SRC = ZT + u"_zf117_gatesnap.py"
DST = ZT + u"_zf118_gatesnap.py"

raw = io.open(SRC, encoding="utf-8").read()
raw = raw.replace(u"_zf117_gatesnap.py", u"_zf118_gatesnap.py")
raw = raw.replace(u"（ZF117 轮，**只读**）", u"（ZF118 轮，**只读**）")
raw = raw.replace(u"（ZF117）", u"（ZF118）")
raw = raw.replace(u'"_zf114_verify.py", "_zf117_verify.py"]',
                  u'"_zf114_verify.py", "_zf117_verify.py", "_zf118_verify.py"]')
raw = raw.replace(u"名单加上\nZF114 与 ZF117 两道新门", u"名单加上\nZF114 / ZF117 / ZF118 三道新门")
io.open(DST, "w", encoding="utf-8", newline=u"").write(raw)
back = io.open(DST, encoding="utf-8").read()
print(u"写好了：%s（%d B）" % (DST, len(back.encode("utf-8"))))
print(u"含 _zf118_verify.py：%s" % (u'"_zf118_verify.py"' in back))
print(u"含 _zf117_verify.py：%s" % (u'"_zf117_verify.py"' in back))
sys.exit(0 if u'"_zf118_verify.py"' in back else 1)
