# -*- coding: utf-8 -*-
"""_zf133_verfix2.py —— 给这次客户端崩溃立一条常驻判据（C13）

用户实机抓到的崩溃：`BufferBuilder was empty`（`ShockwaveRenderer.drawWall` 的 else 分支）。
这类错误有**可判定的形状**，所以要变成一条会自己红的检查：

  · 客户端渲染类里，`buildOrThrow()` 只允许出现在 `drawWithShader(...)` 里面
    —— 单独一句 `buffer.buildOrThrow();` 就是"空 builder 会抛"的那颗雷；
  · `Tesselator...begin(` 出现几次，`drawWithShader(...buildOrThrow())` 就得出现几次
    —— **开了 builder 就必须收尾**（次数对上才不会有"空了"或"漏了"）。

⚠ 判据要**先剥掉注释**再数：我第一版复核就是被 javadoc 里提到的 `buildOrThrow()` 骗了
  （数出 3 次、断言失败、文件没写盘）。

跑法：python build\\zftools\\_zf133_verfix2.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf133_verify.py"

ANCHOR = """    ok("C12 广播半径 64 格", "RANGE = 64.0D" in net)"""

ADD = ANCHOR + '''

    # ---- C13：客户端渲染的 BufferBuilder 收尾规矩（ZF133 实机崩溃换来的一条）----
    # 把注释剥掉再数（否则 javadoc 里提到的 buildOrThrow() 会骗到判据本身）
    def code_only(src):
        out = re.sub(r"/\\*[\\s\\S]*?\\*/", "", src)
        return re.sub(r"//[^\\n]*", "", out)

    for name, src in (("ShockwaveRenderer", rend), ("SkyboxRenderer",
                      read(os.path.join(JAVA, r"client\\SkyboxRenderer.java")))):
        c = code_only(src)
        begins = c.count("Tesselator.getInstance()")
        draws = len(re.findall(r"drawWithShader\\(\\s*\\w+\\.buildOrThrow\\(\\)\\)", c))
        stray = len(re.findall(r"(?<!drawWithShader\\()(?<!\\.)\\bbuffer\\.buildOrThrow\\(\\)", c))
        # 单独成句的 buildOrThrow（不在 drawWithShader 括号里）
        bare = len(re.findall(r"^\\s*\\w+\\.buildOrThrow\\(\\);\\s*$", c, re.M))
        ok("C13 %s：begin 次数 == drawWithShader 次数（开了就必须收尾）" % name,
           begins == draws and begins >= 1, "begin=%d draw=%d" % (begins, draws))
        ok("C13b %s：没有单独成句的 buildOrThrow（空 builder 会抛）" % name,
           bare == 0, "bare=%d" % bare)'''

s = io.open(P, encoding="utf-8").read()
n = s.count(ANCHOR)
assert n == 1, "锚点 %d 次" % n
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(ANCHOR, ADD, 1))
print("[OK] C13 已加进常驻校验")
