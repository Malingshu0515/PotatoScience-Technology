# -*- coding: utf-8 -*-
u"""_zf128_repair.py —— 修 `_zf128_verify.py` 里被**转义**弄坏的那一小段

**怎么坏的（如实记，§4.24 家族的又一面）**：`_zf128_artfix.py` 用 `u'''...'''` 装替换文本，
里面写了 `r"src\\main\\resources\\..."` —— 那个 `r` 前缀只是**被写进文件**的内容，
在**生成它的那个字符串**里 `\\r`/`\\a`/`\\t` 是**真转义** ⇒ 写进盘上的就变成了
`src\main` + 回车 + `esources` + 响铃 + `ssets` + 制表符 + …（一行源码被拆成两行）。
凡是要往文件里写**反斜杠路径**，生成器里的那段文本必须自己也是 raw（或把 `\\` 写成 `\\\\`）。

跑法：
    python build\\zftools\\_zf128_repair.py
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = r"E:\PotatoST\build\zftools\_zf128_verify.py"
start_mark = u'    check(u"D6b'
end_mark = u'poisonous_potato.png")))'
NEW = (u'    _potato_tex = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t",\n'
       u'                               u"textures", u"item", u"poisonous_potato.png")\n'
       u'    check(u"D6b 我们**没有**为毒马铃薯画贴图（用的是原版物品）", not os.path.exists(_potato_tex))\n')

notes, fails = [], []


def main():
    t = io.open(P, encoding="utf-8", newline=u"").read()
    if u"_potato_tex" in t and start_mark not in t:
        notes.append(u"已经是修好的版本（幂等跳过）")
    else:
        i = t.find(start_mark)
        j = t.find(end_mark)
        if i < 0 or j < 0 or j < i:
            fails.append(u"定位失败（start=%d end=%d）" % (i, j))
        else:
            t = t[:i] + NEW + t[j + len(end_mark) + 1:]
            long = u"PYTHONIOENCODING"
            if u"PYTHONIOENCODING" not in t:
                old = (u'    _r = _sp.run([sys.executable, os.path.join(TOOLS, u"TextureCheck.py")],\n'
                       u'                 stdout=_sp.PIPE, stderr=_sp.STDOUT, cwd=TOOLS)\n')
                new = (u'    _r = _sp.run([sys.executable, os.path.join(TOOLS, u"TextureCheck.py")],\n'
                       u'                 stdout=_sp.PIPE, stderr=_sp.STDOUT, cwd=TOOLS,\n'
                       u'                 env=dict(os.environ, PYTHONIOENCODING=u"utf-8"))\n')
                if t.count(old) == 1:
                    t = t.replace(old, new, 1)
                    notes.append(u"顺手把子进程的编码钉成 UTF-8（PYTHONIOENCODING）")
                else:
                    fails.append(u"编码那处锚点命中 %d 次" % t.count(old))
            io.open(P, "w", encoding="utf-8", newline=u"").write(t)
            notes.append(u"修好 D6b 那一段（用切片替换，不碰别的字节）")

    t = io.open(P, encoding="utf-8", newline=u"").read()
    try:
        compile(t, P, u"exec")
        notes.append(u"语法自检通过")
    except SyntaxError as e:
        fails.append(u"语法还是不过：%s" % e)
    if u"\r" in t.replace(u"\r\n", u"") or u"\x07" in t or u"\t" in t.split(u"def ")[0]:
        fails.append(u"文件里还残留奇怪的控制字符")

    print(u"\n".join(u"  [OK] " + x for x in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
