# -*- coding: utf-8 -*-
u"""_zf162_commit.py —— 只把我的路径 `git add` 进暂存区并提交（§4：绝不 `git add -A`）。

路径来源：
  · 本轮改/删的 java 与资源（写死清单）
  · 三份文档
  · `build\\zftools\\_zf162_*.py` 全部（本轮的新脚本）+ `_zf45_recipes.py` / `_zf148_book.py`
  · `_zf162_retarget.py` 里点名跟平过的那些门
  · 成品 jar + `.sha1`

跑法：python build\\zftools\\_zf162_commit.py            # 只列清单
      python build\\zftools\\_zf162_commit.py --write    # add + commit
"""
import glob
import io
import os
import re
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")

JAVA = [u"ModItems.java", u"ModBlocks.java", u"PotatoST.java", u"ElectricBlastFurnaceBlock.java",
        u"ElectricBlastFurnacePartBlock.java", u"ElectricBlastFurnaceWrench.java",
        u"AlloySmelterBlock.java", u"BlastFurnaceAssembly.java", u"EbfFormedTrigger.java",
        u"FillingMachineBlockEntity.java", u"FillingMachineMenu.java", u"FillingMachineBlock.java",
        os.path.join(u"client", u"jei", u"PotatoSTJeiPlugin.java")]
RES = [r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
       r"src\main\resources\assets\potato_s_t\lang\en_us.json",
       r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
       r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
       r"src\main\resources\assets\potato_s_t\lang\lzh.json",
       r"src\main\resources\data\potato_s_t\advancement\blast_furnace.json",
       r"src\main\resources\assets\potato_s_t\patchouli_books\guide\en_us\categories\faq.json",
       r"src\main\resources\assets\potato_s_t\patchouli_books\guide\en_us\entries\faq\machine.json",
       r"src\main\resources\assets\potato_s_t\patchouli_books\guide\en_us\entries\getting_started\rules.json",
       r"src\main\resources\assets\potato_s_t\patchouli_books\guide\en_us\entries\materials\blast_alloy.json",
       r"src\main\resources\assets\potato_s_t\models\item\wrench.json",
       r"src\main\resources\assets\potato_s_t\textures\item\wrench.png",
       r"src\main\resources\assets\potato_s_t\models\item\electric_blast_furnace.json",
       r"src\main\resources\assets\potato_s_t\textures\item\electric_blast_furnace.png",
       r"src\main\resources\data\potato_s_t\recipe\electric_blast_furnace.json"]
DOCS = [r"docs\开发档案.md", r"docs\多会话协作交接.md", r"docs\UpdateAnnouncement_EN.md",
        r"docs\贴图清单.md"]
ART = [r"release\PotatoST-0.13.jar", r"release\PotatoST-0.13.jar.sha1"]
TOOLS_FIX = [r"build\zftools\_zf45_recipes.py", r"build\zftools\_zf148_book.py"]
MSG = u"ZF162 0.13：删扳手 + 删电力高炉物品形态 + 灌装机「什么都能放」（0.13）"


def retarget_gates():
    t = io.open(os.path.join(ZT, u"_zf162_retarget.py"), encoding="utf-8").read()
    gates = set(re.findall(u'u"(_zf[0-9a-z_]+\\.py)"', t))
    edits = set(re.findall(u'\\(u"(_zf[0-9a-z_]+\\.py)",', t))
    return sorted(gates | edits)


def git(args, **kw):
    return subprocess.run([u"git", u"-C", ROOT] + args, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, **kw).stdout.decode("utf-8", "replace")


def main(argv):
    write = u"--write" in argv
    paths = []
    for n in JAVA:
        paths.append(os.path.join(u"src\\main\\java\\com\\potatost\\mod", n))
    paths += RES + DOCS + ART + TOOLS_FIX
    paths += sorted(glob.glob(os.path.join(ZT, u"_zf162_*.py")))
    paths += [os.path.join(u"build", u"zftools", g) for g in retarget_gates()]
    paths = sorted(set(p.replace(u"/", os.sep) for p in paths))
    exist, missing = [], []
    for p in paths:
        full = os.path.join(ROOT, p)
        (exist if os.path.exists(full) else missing).append(p)
    print(u"要 add 的路径 %d 个（不存在的 %d 个，git add 会整体失败 ⇒ 已过滤）"
          % (len(exist), len(missing)))
    for m in missing:
        print(u"  （不在盘上，跳过）%s" % m)
    if not write:
        for p in exist:
            print(u"  " + p)
        return 0
    r = subprocess.run([u"git", u"-C", ROOT, u"add", u"--"] + exist,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(r.stdout.decode("utf-8", "replace"))
    # 删掉的文件：`git add -A -- <路径>` 才能把"删除"记进暂存区（普通 add 会报 pathspec 不匹配）
    tracked_gone = []
    for m in missing:
        chk = subprocess.run([u"git", u"-C", ROOT, u"ls-files", u"--error-unmatch", u"--", m],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if chk.returncode == 0:
            tracked_gone.append(m)
    if tracked_gone:
        r1 = subprocess.run([u"git", u"-C", ROOT, u"add", u"-A", u"--"] + tracked_gone,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(u"（把 %d 个删除也记进暂存区）%s" % (len(tracked_gone),
                                                r1.stdout.decode("utf-8", "replace").strip()))
    staged = git([u"diff", u"--cached", u"--name-status"])
    print(u"----- 暂存区（name-status）-----")
    print(staged)
    n_lines = len([l for l in staged.split(u"\n") if l.strip()])
    print(u"暂存条目 = %d" % n_lines)
    if u"--commit" in argv:
        r2 = subprocess.run([u"git", u"-C", ROOT, u"commit", u"-m", MSG],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(r2.stdout.decode("utf-8", "replace"))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
