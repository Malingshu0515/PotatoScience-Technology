# -*- coding: utf-8 -*-
r'''_zf144_probefix2.py —— 第二次修探针：把 `recenter(caster)` 插进该插的地方。

第六次实测的结论：⑧ 那一节 302 次 tick 之后，施法者从 y=100 **下沉到 96.23**
（连 `setNoGravity(true)` 都没挡住），而剑气的纵向窗口只有 ±1.5 ⇒ 后面依赖位置的判据全废。
⇒ 两处调用：① 清空试验场、开始跑几何之前；② 端到端"打死靶子"之前。

跑法：python build\zftools\_zf144_probefix2.py [--write]
'''
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf144Check.java"

PAIRS = [
    (u"        loadChunks(level);\n        clearChamber(level);\n",
     u"        loadChunks(level);\n        clearChamber(level);\n"
     u"        recenter(caster);\n"),
    (u"        Zombie slashed = dummyAt(level, 0.0D, 0.0D, 4.0D);\n",
     u"        recenter(caster);   // ⚠ ⑧ 那 302 次 tick 会把施法者拽下去 3.77 格\n"
     u"        Zombie slashed = dummyAt(level, 0.0D, 0.0D, 4.0D);\n"),
]


def main(argv):
    write = u"--write" in argv
    t = io.open(P, encoding="utf-8", newline="").read()
    fails = []
    for old, new in PAIRS:
        if t.count(old) != 1:
            fails.append(u"命中 %d 次：%s" % (t.count(old), old.strip().split(u"\n")[0][:60]))
            continue
        t = t.replace(old, new, 1)
    if fails:
        print(u"失败项 = %d（一个字节都没写）" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    if write:
        io.open(P, u"w", encoding="utf-8", newline=u"").write(t)
        print(u"已写盘。")
    else:
        print(u"（没加 --write，只算不写）")
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
