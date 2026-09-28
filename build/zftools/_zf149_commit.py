# -*- coding: utf-8 -*-
u"""_zf149_commit.py —— ZF149 只提交**本轮自己的路径**（绝不 `git add -A`，多线共树）。

清单：
  ① `release\\PotatoST-0.12.jar` + `.sha1`（本轮的主角：重打的成品）
  ② 三份文档
  ③ 本轮新增/改动的脚本与门：`build/zftools/_zf149_*` + 我改过的 `_zf148_verify.py` /
     `_zf148_gatesnap.py`
⚠ `build/libs/*.jar` 不进仓（.gitignore 里 build/* 已排除）；0.11 / 0.10 的成品也不动。

跑法：python build\\zftools\\_zf149_commit.py [--write]
"""
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\cmd\git.exe"

FIXED = [
    # ⚠ `release/` 是**故意**被 .gitignore 排除的（口径：成品走 GitHub Releases，不进 git 历史）
    #   ⇒ 成品 jar 不在这份清单里，它留在盘上、由发布那一步上传。
    u"docs/开发档案.md",
    u"docs/多会话协作交接.md",
    u"docs/UpdateAnnouncement_EN.md",
    u"build/zftools/_zf148_verify.py",
    u"build/zftools/_zf148_gatesnap.py",
]

MSG = u"""ZF149 打包：0.12 成品重打，教程手册进 jar（0.12）

用户原话：「现在是0.12版本！jar貌似没有教程书」。

① **根因**：`release\\PotatoST-0.12.jar` 是 12:56 打的（`45c061df…`），而 ZF148 的
   教程手册是 13:00 之后才做进源目录的 ⇒ 成品比源目录旧一轮（ZF148 §9 的「边界」那条已写明）。
② **做法**：`gradlew build --offline` → `59894a9efb7ba45cc811a558f1fea4a8dac56863`
   （5,812,286 B）→ 覆盖 `release\\PotatoST-0.12.jar` + 写 `.sha1`（纯哈希一行，§4.92）。
   ⚠ `PotatoST-0.11.jar` / 0.10 一个字没动（它们是别轮门的参照物，见 §4.159）。
③ **成品里现在有什么**：**358 class** / 74 配方 / 43 进度 / 五语言 579×4 + lzh 581 /
   手册 26 份资源（书定义、6 分类、18 条目、模型、贴图、配方）/ `patchouli` 硬依赖
   （`mods.toml` 渲染后 `type="required"`、版本 0.12）。

证据：
- 审计 `_zf149_jar.py`：**26 项 0 失败** —— 全条目 CRC、jar 内 lang 键数、手册资源与源目录
  逐字节相同、`mods.toml` 无占位符残留、产物里没有探针 class、也没有帕秋莉/JEI 的类（compileOnly 没漏）。
- 常驻门 `_zf149_verify.py`：**28 项 0 失败**（产物/记录/成品内容/文档三处联动/老成品没被动）。
- 反证 `_zf149_falsify.py`：**6 把全中**（含「把 jar 里的书定义抠掉」那把 —— 正是用户遇到的那件事，
  改坏必红、逐字节还原、还原回绿）。
- `_zf148_verify.py` 仍 **83 项 0 失败**（文档判据改成查「本轮记录在不在」，不再钉活体数字快照）。

⚠ 边界：
- 成品是 **13:33 的快照**：ZF150（金属粒）13:36 才落源目录 ⇒ **不在这一份里**，下一轮打包带上。
- 十几处写死 `PotatoST-0.11.jar` 的门按 §4.159 **不动**（那是那些线自己的参照物）。
"""


def main(argv):
    write = u"--write" in argv
    paths = list(FIXED)
    d = os.path.join(ROOT, "build", "zftools")
    for fn in sorted(os.listdir(d)):
        if fn.startswith(u"_zf149_"):
            paths.append(os.path.join(u"build", u"zftools", fn))
    paths = sorted(set(paths))
    missing = [p for p in paths if not os.path.isfile(os.path.join(ROOT, p.replace(u"/", os.sep)))]
    print(u"待提交 %d 个路径；不存在 %d" % (len(paths), len(missing)))
    for m in missing:
        print(u"  !! 不在盘上：" + m)
    if missing:
        return 1
    r = subprocess.run([GIT, u"-c", u"core.quotepath=false", u"add", u"--"] + paths,
                       cwd=ROOT, capture_output=True)
    if r.returncode != 0:
        print(u"git add 失败：" + r.stderr.decode(u"utf-8", u"replace"))
        return 1
    st = subprocess.run([GIT, u"-c", u"core.quotepath=false", u"diff", u"--cached", u"--name-status"],
                        cwd=ROOT, capture_output=True).stdout.decode(u"utf-8", u"replace")
    mine = [l for l in st.split(u"\n") if l.strip() and (u"release/" in l or u"docs/" in l
                                                         or u"_zf14" in l)]
    print(u"已暂存（本轮关心的）：")
    for l in mine:
        print(u"   " + l)
    if not write:
        print(u"（没加 --write：只暂存，不提交）")
        return 0
    msgfile = os.path.join(ROOT, "build", "zftools", u"_zf149_commit_msg.txt")
    io.open(msgfile, u"w", encoding=u"utf-8", newline=u"\n").write(MSG)
    r = subprocess.run([GIT, u"commit", u"-F", msgfile], cwd=ROOT, capture_output=True)
    print(r.stdout.decode(u"utf-8", u"replace")[-1200:])
    if r.returncode != 0:
        print(u"提交失败：" + r.stderr.decode(u"utf-8", u"replace"))
        return 1
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
