# -*- coding: utf-8 -*-
"""
ZF120 取证用：从本地 jar 里**抽真正的反编译源码**出来读（不是凭记忆）。

两个来源：
  MC   : E:\\PotatoST\\build\\neoForm\\neoFormJoined1.21.1-20240808.144430\\sources.jar
  NEO  : E:\\gradle-home\\caches\\modules-2\\files-2.1\\net.neoforged\\neoforge\\21.1.235\\<sha>\\neoforge-21.1.235-sources.jar

用法：
  python _zf120_src.py list   <子串>      # 在两边 jar 里按子串找条目
  python _zf120_src.py get    <全名...>   # 把条目解到 build/tmp/zf120_src/ 下（保留目录结构）
  python _zf120_src.py grep   <正则> [路径过滤子串]   # 直接在 jar 里全文搜（不解包）

为什么要有这个脚本：ZF120 要落地"弹射物免疫+反弹 / 爆炸减半 / 免疫击退 / 无限耐久 / 附魔光效"，
每一处都要先确认 1.21.1 + NeoForge 21.1.235 里**到底有没有那个 API、签名长什么样**。
凭印象写 API 名是本工程最容易翻车的一类错（§4.20）。
"""
import os
import sys
import zipfile

ROOT = r'E:\PotatoST'
OUT = os.path.join(ROOT, 'build', 'tmp', 'zf120_src')

MC_JAR = os.path.join(ROOT, 'build', 'neoForm',
                      'neoFormJoined1.21.1-20240808.144430', 'sources.jar')

NEO_DIR = r'E:\gradle-home\caches\modules-2\files-2.1\net.neoforged\neoforge\21.1.235'


def neo_jar():
    for sha in os.listdir(NEO_DIR):
        p = os.path.join(NEO_DIR, sha, 'neoforge-21.1.235-sources.jar')
        if os.path.isfile(p):
            return p
    raise SystemExit('找不到 neoforge sources.jar')


JARS = [('mc', MC_JAR), ('neo', neo_jar())]


def cmd_list(needle):
    hits = 0
    for tag, path in JARS:
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if needle.lower() in name.lower():
                    print('%-4s %s' % (tag, name))
                    hits += 1
    print('== 命中 %d 条 ==' % hits)


def cmd_get(names):
    got = []
    missing = []
    for name in names:
        found = False
        for tag, path in JARS:
            with zipfile.ZipFile(path) as z:
                if name in z.namelist():
                    dest = os.path.join(OUT, tag, name.replace('/', os.sep))
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with z.open(name) as src, open(dest, 'wb') as dst:
                        dst.write(src.read())
                    print('OK   %-4s %s -> %s' % (tag, name, dest))
                    got.append(dest)
                    found = True
        if not found:
            missing.append(name)
            print('MISS      %s' % name)
    print('== 抽出 %d 个，缺 %d 个 ==' % (len(got), len(missing)))
    return 0 if not missing else 1


def cmd_grep(pattern, path_filter=''):
    import re
    rx = re.compile(pattern)
    hits = 0
    for tag, path in JARS:
        if tag != 'mc':            # 同一个类两边都有，只看 mc 那份（它就是编译用的那份）
            continue
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if not name.endswith('.java'):
                    continue
                if path_filter and path_filter.lower() not in name.lower():
                    continue
                text = z.read(name).decode('utf-8', 'replace')
                for i, line in enumerate(text.splitlines(), 1):
                    if rx.search(line):
                        print('%s:%d: %s' % (name, i, line.strip()[:200]))
                        hits += 1
    print('== 命中 %d 行 ==' % hits)
    return 0


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    mode = sys.argv[1]
    if mode == 'list':
        cmd_list(sys.argv[2])
        return 0
    if mode == 'get':
        return cmd_get(sys.argv[2:])
    if mode == 'grep':
        return cmd_grep(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else '')
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
