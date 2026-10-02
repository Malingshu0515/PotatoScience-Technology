# -*- coding: utf-8 -*-
u"""_zf166_commit.py —— 只把我的路径 `git add` 进暂存区并提交（§4：绝不 `git add -A`）。

⚠ 本轮**必须**等另一条线（ZF165）把它的临时探针 `Zf165Check.java` 摘掉之后再重打成品：
   从工作树打出来的 jar 里带着 `com/potatost/mod/Zf165Check.class`（探针会在玩家服务器上跑！），
   `_zf162_pkg.py` 的审计当场抓到。本脚本只 add 我自己的路径，不碰别人的。

跑法：python build\\zftools\\_zf166_commit.py            # 只列清单
      python build\\zftools\\_zf166_commit.py --write --commit
"""
import glob
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
PATHS = [
    # 机器本体
    r"src\main\java\com\potatost\mod\FluidConverterBlock.java",
    r"src\main\java\com\potatost\mod\FluidConverterBlockEntity.java",
    r"src\main\java\com\potatost\mod\FluidConverterMenu.java",
    r"src\main\java\com\potatost\mod\client\FluidConverterScreen.java",
    # 四处注册（各只加了一行/一段）
    r"src\main\java\com\potatost\mod\ModBlocks.java",
    r"src\main\java\com\potatost\mod\ModMenus.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\java\com\potatost\mod\PotatoSTClient.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    # 资源
    r"src\main\resources\assets\potato_s_t\blockstates\fluid_converter.json",
    r"src\main\resources\assets\potato_s_t\models\block\fluid_converter.json",
    r"src\main\resources\assets\potato_s_t\models\item\fluid_converter.json",
    r"src\main\resources\data\potato_s_t\recipe\fluid_converter.json",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"src\main\resources\assets\potato_s_t\lang\lzh.json",
    # 生成器表与文档
    r"build\zftools\_zf45_recipes.py",
    r"build\zftools\check\Zf166Check.java",
    r"build\zftools\_zf166_probe_utf8.txt",
    r"build\zftools\_zf166_gatesnap.txt",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    # 成品（等重打之后再 add；现在这份带着别人的探针，**先别提交**）
    # r"release\PotatoST-0.13.jar",
    # r"release\PotatoST-0.13.jar.sha1",
]
MSG = u"ZF166 0.13：新增流体转化器 —— 同标签流体跨 mod 1:1 互转（0.13）"


def main(argv):
    write = u"--write" in argv
    paths = list(PATHS) + sorted(glob.glob(os.path.join(ZT, u"_zf166_*.py")))
    paths = sorted(set(p.replace(u"/", os.sep) for p in paths))
    exist, missing = [], []
    for p in paths:
        (exist if os.path.exists(os.path.join(ROOT, p)) else missing).append(p)
    print(u"要 add 的路径 %d 个（不在盘上的 %d 个）" % (len(exist), len(missing)))
    for m in missing:
        print(u"  （不在盘上）%s" % m)
    if not write:
        for p in exist:
            print(u"  " + p)
        return 0
    r = subprocess.run([u"git", u"-C", ROOT, u"add", u"--"] + exist,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(r.stdout.decode("utf-8", "replace"))
    staged = subprocess.run([u"git", u"-C", ROOT, u"diff", u"--cached", u"--name-status"],
                            stdout=subprocess.PIPE).stdout.decode("utf-8", "replace")
    print(u"----- 暂存区 -----")
    print(staged)
    if u"--commit" in argv:
        r2 = subprocess.run([u"git", u"-C", ROOT, u"commit", u"-m", MSG],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(r2.stdout.decode("utf-8", "replace"))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
