# -*- coding: utf-8 -*-
u"""_zf75_fixprobe.py —— 探针里 `performPrefixedCommand` 在 1.21.1 返回 void（不是 int）"""
import io
import sys

OLD = u"""            int r = event.getServer().getCommands().performPrefixedCommand(
                    event.getServer().createCommandSourceStack().withSuppressedOutput(), cmd);
            System.out.println(TAG + "    command result = " + r + "   [" + cmd + "]");"""
NEW = u"""            event.getServer().getCommands().performPrefixedCommand(
                    event.getServer().createCommandSourceStack().withSuppressedOutput(), cmd);
            System.out.println(TAG + "    command executed   [" + cmd + "]");"""

PATHS = [
    r"E:\PotatoST\build\zftools\check\OilfieldCheck2.java",
    r"E:\PotatoST\src\main\java\com\potatost\mod\OilfieldCheck.java",
]


def main():
    for p in PATHS:
        t = io.open(p, "r", encoding="utf-8").read()
        n = t.count(OLD)
        print(u"  %s  hits=%d" % (p, n))
        if n == 1:
            io.open(p, "w", encoding="utf-8", newline=u"\n").write(t.replace(OLD, NEW, 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
