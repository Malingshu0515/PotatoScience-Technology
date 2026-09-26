# -*- coding: utf-8 -*-
u"""_zf140_worldprobe.py —— 临时把星图**钉死在第 1 号**，好在没拿书的情况下也走一遍盖片渲染

为什么非走这一趟（§4.124）：盖片渲染是**纯客户端、纯画面**的代码，
`runServer` 那一路一行都碰不到它 —— ZF133 那次崩客户端就是这么溜过去的
（我只跑了 runServer，`ShockwaveRenderer` 是 `Dist.CLIENT`）。
所以这一趟要：**进真世界 + 真出图 + 看有没有崩**。

做法：把 `private static int applied;` 改成 `= 1;`（默认就是 1 号星图），
进世界后天空直接是星图 ⇒ 盖片必然被画。跑完**必须还原**（本脚本 `--off` 干这个），
还原后与改前逐字节比对。

用法：
    python build\\zftools\\_zf140_worldprobe.py           # 挂上（并打印改后哈希）
    python build\\zftools\\_zf140_worldprobe.py --off     # 摘掉（并断言与改前一致）
"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

JAVA = os.path.join(r"E:\PotatoST", "src", "main", "java", "com", "potatost", "mod",
                    "client", "SkyboxRenderer.java")
SAVE = os.path.join(r"E:\PotatoST", "build", "zftools", "_zf140_worldprobe.java")

OLD = u"    private static int applied;"
NEW = u"    private static int applied = 1;   // ZF140 世界探针：先钉死 1 号星图"
MARK = u"ZF140 世界探针"


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    off = "--off" in argv
    text = io.open(JAVA, "r", encoding="utf-8", newline="").read()
    if off:
        assert os.path.exists(SAVE), u"没有改前留档，不能瞎摘"
        n = text.count(NEW)
        assert n == 1, u"探针那句读到 %d 次" % n
        io.open(JAVA, "w", encoding="utf-8", newline="").write(text.replace(NEW, OLD, 1))
        now, ref = sha1(JAVA), sha1(SAVE)
        print(u"摘掉探针：%s" % (u"与改前逐字节一致" if now == ref else u"❌ 不一致！"))
        print(u"  现在 %s\n  改前 %s" % (now, ref))
        return 0 if now == ref else 1
    assert text.count(OLD) == 1, u"锚点 `private static int applied;` 命中 %d 次" % text.count(OLD)
    if not os.path.exists(SAVE):
        io.open(SAVE, "wb").write(io.open(JAVA, "rb").read())
        print(u"改前留档 -> %s（sha1 %s…）" % (SAVE, sha1(SAVE)[:12]))
    assert text.count(MARK) == 0, u"已经挂上了"
    io.open(JAVA, "w", encoding="utf-8", newline="").write(text.replace(OLD, NEW, 1))
    print(u"挂上探针：applied 默认 = 1（没拿书也是 1 号星图）")
    print(u"  改后 sha1 %s…" % sha1(JAVA)[:12])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
