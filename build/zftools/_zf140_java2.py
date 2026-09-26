# -*- coding: utf-8 -*-
u"""_zf140_java2.py —— ZF140 第二刀：给盖片加一条**开机自检**

为什么还要这一条：`_zf140_mapping.py` 是**读源码**验几何的 —— 它能证明"这份算式是对的"，
但证明不了"编译出来跑起来到底算出什么顶点"。这一条把真正的顶点数组在 `init()` 里量一遍，
把结果**打进游戏日志**：位置是否落在盖片球面上、UV 与位置是否构成"正对极点看过去不变形"的恒等。

于是 `runClient` 那一路就有了**正面证据**（日志里必须出现那行 OK 汇总），
而不是只看"没崩" —— 没崩只能说明没崩。

⚠ 自检**不抛异常**（玩家的客户端不能因为一行自检挂掉）：算不平就记 ERROR，
由 `_zf140_verify.py` 的 A20 与 runClient 日志检查两头兜。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

JAVA = os.path.join(r"E:\PotatoST", "src", "main", "java", "com", "potatost", "mod",
                    "client", "SkyboxRenderer.java")

ANCHOR_FIELD = u"""    /** 黑洞盖片网格：`caps[0]` 北极、`caps[1]` 南极（同样每 5 个 float 一个顶点）。 */
    private static float[][] caps;
"""
INSERT_FIELD = ANCHOR_FIELD + u"""    /** 与 ModArmorItems 同一个写法：全限定名，省得动 import 表。 */
    private static final org.slf4j.Logger LOGGER = com.mojang.logging.LogUtils.getLogger();
"""

ANCHOR_INIT = u"""        mesh = buildDome();
        caps = buildCaps();
"""
INSERT_INIT = u"""        mesh = buildDome();
        caps = buildCaps();
        verifyCaps();
"""

ANCHOR_TAIL = u"""        RenderSystem.disableBlend();
    }
}
"""
INSERT_TAIL = u"""        RenderSystem.disableBlend();
    }

    /**
     * 开机自检（0.11 ZF140）：把**真的顶点数组**量一遍，结果打进日志。
     *
     * <p>量两件事，都是"盖片对不对"的定义：</p>
     * <ol>
     *   <li>每个顶点都必须落在半径 {@link #HOLE_RADIUS} 的球面上；</li>
     *   <li>uv 必须与位置构成恒等 —— 顶点方向的 gnomonic 坐标
     *       {@code (x, z) / |y|} 要**恰好等于** {@code (2u-1, 2v-1)·tanθmax}。
     *       这一条成立，正对极点看过去就是原图；不成立就是被拉过或翻过。</li>
     * </ol>
     *
     * <p>⚠ 只记日志、**不抛异常**：玩家的客户端不该因为一行自检挂掉。
     * 判据由 `_zf140_verify.py`（A20）和 runClient 的日志检查两头兜住。</p>
     */
    private static void verifyCaps() {
        double tmax = Math.tan(Math.toRadians(HOLE_DEGREES));
        double worst = 0.0D;
        int vertices = 0;
        for (float[] cap : caps) {
            for (int i = 0; i < cap.length; i += 5) {
                double x = cap[i];
                double y = cap[i + 1];
                double z = cap[i + 2];
                double len = Math.sqrt(x * x + y * y + z * z);
                double wantA = (2.0D * cap[i + 3] - 1.0D) * tmax;
                double wantB = (2.0D * cap[i + 4] - 1.0D) * tmax;
                worst = Math.max(worst, Math.abs(x / Math.abs(y) - wantA));
                worst = Math.max(worst, Math.abs(z / Math.abs(y) - wantB));
                worst = Math.max(worst, Math.abs(len - HOLE_RADIUS) / HOLE_RADIUS);
                vertices++;
            }
        }
        if (worst > 1.0E-6D) {
            LOGGER.error("SkyboxRenderer: black-hole cap geometry BROKEN, max error {} "
                    + "(expected <= 1e-6) - the pole view will be distorted.", worst);
        } else {
            LOGGER.info("SkyboxRenderer: black-hole caps OK - {} poles, {} vertices, "
                    + "grid {}x{}, half-angle {} deg, max error {}.",
                    caps.length, vertices, HOLE_GRID, HOLE_GRID, HOLE_DEGREES, worst);
        }
    }
}
"""

PATCHES = [
    (u"日志器", ANCHOR_FIELD, INSERT_FIELD),
    (u"init 调自检", ANCHOR_INIT, INSERT_INIT),
    (u"自检方法", ANCHOR_TAIL, INSERT_TAIL),
]


def main(argv):
    write = "--write" in argv
    text = io.open(JAVA, "r", encoding="utf-8", newline="").read()
    print(u"改前 %d 字节 / %d 行" % (len(text.encode("utf-8")), text.count("\n") + 1))
    for name, old, new in PATCHES:
        n = text.count(old)
        assert n == 1, u"锚点[%s]命中 %d 次（必须恰好 1 次）" % (name, n)
        assert len(new) > len(old)
        for line in old.split("\n"):
            assert not line.strip() or line in new, u"锚点[%s]的原文行丢了：%r" % (name, line)
        print(u"  ✓ 锚点[%s] 命中 1 次" % name)
    for name, old, new in PATCHES:
        text = text.replace(old, new, 1)

    for needle in (u"private static void verifyCaps()", u"verifyCaps();",
                   u"LOGGER.error(\"SkyboxRenderer: black-hole cap geometry BROKEN",
                   u"LOGGER.info(\"SkyboxRenderer: black-hole caps OK"):
        assert text.count(needle) == 1, u"自检失败：%s 出现 %d 次" % (needle, text.count(needle))
    assert text.count(u"buildOrThrow()") == 2
    print(u"改后 %d 字节 / %d 行" % (len(text.encode("utf-8")), text.count("\n") + 1))
    if write:
        io.open(JAVA, "w", encoding="utf-8", newline="").write(text)
        print(u"  >>> 已写入")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
