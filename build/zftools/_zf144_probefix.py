# -*- coding: utf-8 -*-
r'''_zf144_probefix.py —— 把探针里 `dummy()/place()` 那套调用改成 `dummyAt()/reset()`。

背景：第二版探针把「先 add 再 setPos」改成「先 setPos 再 add」（位置必须在入世之前给，
否则实体管理器里它永远留在原点那个 section，`level.getEntities` 数不到）。
这一改牵动 8 处调用点 —— 用脚本一次改完并**逐处断言命中 1 次**，比手改 8 个 edit 稳。

跑法：python build\zftools\_zf144_probefix.py [--write]
'''
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf144Check.java"

PAIRS = [
    (u"        Zombie probeDummy = dummy(level);\n        place(probeDummy, 0.0D, 0.0D, 3.0D);\n",
     u"        Zombie probeDummy = dummyAt(level, 0.0D, 0.0D, 3.0D);\n"),
    (u"        Zombie front = dummy(level);\n        place(front, 0.0D, 0.0D, 3.0D);\n",
     u"        Zombie front = dummyAt(level, 0.0D, 0.0D, 3.0D);\n"),
    (u"        Zombie behind = dummy(level);\n        place(behind, 0.0D, 0.0D, -3.0D);\n",
     u"        Zombie behind = dummyAt(level, 0.0D, 0.0D, -3.0D);\n"),
    (u"        Zombie far = dummy(level);\n        place(far, 0.0D, 0.0D, 12.0D);\n",
     u"        Zombie far = dummyAt(level, 0.0D, 0.0D, 12.0D);\n"),
    (u"        Zombie side = dummy(level);\n        place(side, 4.0D, 0.0D, 3.0D);\n",
     u"        Zombie side = dummyAt(level, 4.0D, 0.0D, 3.0D);\n"),
    (u"        Zombie walled = dummy(level);\n        place(walled, 0.0D, 0.0D, 4.0D);\n",
     u"        Zombie walled = dummyAt(level, 0.0D, 0.0D, 4.0D);\n"),
    (u"        place(walled, 0.0D, 0.0D, 4.0D);\n        float b6 = walled.getHealth();",
     u"        reset(walled);\n        float b6 = walled.getHealth();"),
    (u"        Zombie twoA = dummy(level);\n        Zombie twoB = dummy(level);\n"
     u"        place(twoA, 0.0D, 0.0D, 2.0D);\n        place(twoB, 1.0D, 0.0D, 6.0D);\n",
     u"        Zombie twoA = dummyAt(level, 0.0D, 0.0D, 2.0D);\n"
     u"        Zombie twoB = dummyAt(level, 1.0D, 0.0D, 6.0D);\n"),
    (u"        Zombie victim = dummy(level);\n        place(victim, 0.0D, 0.0D, 3.0D);\n",
     u"        Zombie victim = dummyAt(level, 0.0D, 0.0D, 3.0D);\n"),
    # 加载区块 + 试验场前提：插在清空试验场那一段之后
    (u"        clearChamber(level);\n",
     u"        loadChunks(level);\n        clearChamber(level);\n"
     u"        check(\"灵敏度对照：靶子真的进得了世界（addFreshEntity 成功）\", dummyAdded);\n"),
]


def main(argv):
    write = u"--write" in argv
    t = io.open(P, encoding="utf-8", newline="").read()
    fails = []
    for old, new in PAIRS:
        n = t.count(old)
        if n != 1:
            fails.append(u"命中 %d 次：%s" % (n, old.strip().split(u"\n")[0][:70]))
            continue
        t = t.replace(old, new, 1)
    if fails:
        print(u"失败项 = %d（一个字节都没写）" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    if write:
        io.open(P, u"w", encoding="utf-8", newline=u"").write(t)
        assert io.open(P, encoding="utf-8", newline=u"").read() == t
        print(u"已写盘；回读一致。")
    else:
        print(u"（没加 --write，只算不写）")
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
