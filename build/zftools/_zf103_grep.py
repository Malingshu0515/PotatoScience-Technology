# -*- coding: utf-8 -*-
u"""_zf103_grep.py —— 只读：在 neoForm sources.jar / neoforge sources.jar 里按正则搜行

用法：
    $env:PYTHONIOENCODING='utf-8'
    python build\zftools\_zf103_grep.py <jar> <entry子串或glob> <正则> [上限]

例：
    python build\zftools\_zf103_grep.py vanilla "ItemStack.java" "damageItem|hurtAndBreak"
"""
import re
import sys
import zipfile

PROJ = r"E:\PotatoST"
GRADLE = r"E:\gradle-home"
VANILLA = PROJ + r"\build\neoForm\neoFormJoined1.21.1-20240808.144430\sources.jar"
NEOFORGE = GRADLE + r"\caches\modules-2\files-2.1\net.neoforged\neoforge\21.1.235" \
    r"\4566e557485e2cf5843d29a9c44795f5f731d36d\neoforge-21.1.235-sources.jar"


def main():
    which = sys.argv[1]
    entry_pat = sys.argv[2]
    regex = re.compile(sys.argv[3])
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 60
    path = VANILLA if which == "vanilla" else NEOFORGE
    ep = re.compile(entry_pat)
    shown = 0
    with zipfile.ZipFile(path) as zf:
        if entry_pat == "ALL":
            names = [n for n in zf.namelist() if n.endswith(".java")]
        else:
            names = [n for n in zf.namelist() if n.endswith(".java") and ep.search(n)]
        print(u"matched entries: %d" % len(names))
        for name in names:
            text = zf.read(name).decode("utf-8", "replace")
            hits = []
            for i, line in enumerate(text.split("\n"), 1):
                if regex.search(line):
                    hits.append((i, line.rstrip()))
            if hits:
                print(u"\n---- %s ----" % name)
                for i, line in hits:
                    print(u"%5d| %s" % (i, line[:180]))
                    shown += 1
                    if shown >= limit:
                        print(u"... (达到上限 %d)" % limit)
                        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
