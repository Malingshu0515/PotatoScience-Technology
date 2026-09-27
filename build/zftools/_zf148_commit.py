# -*- coding: utf-8 -*-
u"""_zf148_commit.py —— ZF148 只提交**本轮自己的路径**（绝不 `git add -A`，§ 多线共树）。

清单三类：
  ① 源码 / 资源 / 依赖：build.gradle、mods.toml、GuideBook.java、书数据 26 份、模型、贴图、
     配方、五份 lang、libs/ 的帕秋莉 jar；
  ② 文档三份；
  ③ 门与脚本：本轮跟平的 34 份门（按 mtime > 13:00 认定）+ 全部 `build/zftools/_zf148_*` +
     归档探针 `build/zftools/check/Zf148Check.java`。

跑法：python build\\zftools\\_zf148_commit.py [--write]
"""
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\cmd\git.exe"

GATES = [u"_zf100_recipe_guard.py", u"_zf100_verify.py", u"_zf101_verify.py", u"_zf102_verify.py",
         u"_zf103_verify.py", u"_zf107_verify.py", u"_zf109_verify.py", u"_zf111_verify.py",
         u"_zf112_verify.py", u"_zf114_verify.py", u"_zf117_verify.py", u"_zf118_verify.py",
         u"_zf119_verify.py", u"_zf122_verify.py", u"_zf125_verify.py", u"_zf126_verify.py",
         u"_zf127_verify.py", u"_zf128_verify.py", u"_zf139_verify.py", u"_zf141_verify.py",
         u"_zf145_verify.py", u"_zf71_verify.py", u"_zf73_repro.py", u"_zf73_verify.py",
         u"_zf75_verify.py", u"_zf78_verify.py", u"_zf79_verify.py", u"_zf80_verify.py",
         u"_zf82_verify.py", u"_zf93_verify.py", u"_zf96_verify.py", u"_zf97_verify.py",
         u"_zf98_verify.py"]

FIXED = [
    u"build.gradle",
    u"src/main/resources/META-INF/neoforge.mods.toml",
    u"src/main/java/com/potatost/mod/GuideBook.java",
    u"src/main/resources/data/potato_s_t/patchouli_books/guide/book.json",
    u"src/main/resources/data/potato_s_t/recipe/guide_book.json",
    u"src/main/resources/assets/potato_s_t/models/item/guide_book.json",
    u"src/main/resources/assets/potato_s_t/textures/item/guide_book.png",
    u"src/main/resources/assets/potato_s_t/lang/zh_cn.json",
    u"src/main/resources/assets/potato_s_t/lang/en_us.json",
    u"src/main/resources/assets/potato_s_t/lang/ja_jp.json",
    u"src/main/resources/assets/potato_s_t/lang/ru_ru.json",
    u"src/main/resources/assets/potato_s_t/lang/lzh.json",
    u"libs/Patchouli-1.21.1-93-NEOFORGE.jar",
    u"docs/开发档案.md",
    u"docs/多会话协作交接.md",
    u"docs/UpdateAnnouncement_EN.md",
]

MSG = u"""ZF148 帕秋莉教程手册：开局送一本 + 书 + 铁锭可再合（0.12）

用户原话：「你看看能不能联动帕秋莉手册或者自己做个书 教程向的 开局给一个
或者一本书+一个铁锭合成」⇒ 拍板：**联动帕秋莉** + 开局送一本 + 书+铁锭可再合。

① 依赖：Patchouli `1.21.1-93-NEOFORGE`（`libs/` 本地 jar、`compileOnly`，工程一直 --offline 构建），
   `neoforge.mods.toml` 加 `type="required"` 硬依赖、区间 `[1.21.1-93,)`。
② 书：`data/potato_s_t/patchouli_books/guide/book.json` +
   `assets/potato_s_t/patchouli_books/guide/en_us/{categories×6, entries×18}`，
   37 个文本页 + 3 个配方页；`i18n: true` ⇒ 正文全是语言键。
③ 物品：帕秋莉自己的 `patchouli:guide_book` + 组件 `patchouli:book=potato_s_t:guide`
   （**不新增物品类**）；物品模型 + 脚本生成的 16×16 RGBA 占位贴图。
④ 配方：书 + 铁锭（shapeless，产物带组件）⇒ 配方 73 → 74（`shaped` 仍 63）。
⑤ Java：只多一个类 `GuideBook.java`（登录送一本；标记走玩家持久化数据；
   **拿不到书堆就不打标记**，下次登录还能再试）。
⑥ 五语言：+71 键 ⇒ 508 → **579**（lzh 510 → **581**），四份键集合仍完全一致。

证据：
- 探针 `Zf148Check`（真 `runServer`）**92 项 ALL OK**（书被 BookRegistry 认下来、13 个字段、
  书堆/组件、配方产物与原料、26 个资源文件、图标/配方页/分类三处交叉引用、五语言 71 键一条不缺）；
  报告 `build/zftools/_zf148_probe_utf8.txt`；归档件 `build/zftools/check/Zf148Check.java`；
  挂载/卸载严格互逆（`PotatoST.java` 逐字节回改前件）。
- 常驻门 `_zf148_verify.py`：**83 项 0 失败**。
- 反证：静态 **14 把** + 开服 **2 把**，全部"改坏必红 / 逐字节还原 / 还原回绿"。
- 门跟平 **34 份**（键数 508→579、配方 73→74、5 份拆 `RELEASE_KEYS`、
  2 份「后续轮次加的键」、1 份配方白名单）。

⚠ 边界与已知：
- `release/PotatoST-0.12.jar`（12:56 那份）**早于本轮** ⇒ 打包轮要重打（交接 §6 第 29 条）。
- 手册只写了 6 类 18 条（起步 / 电力 / 材料 / 石油 / 星陨 / 疑难），**没写满全 mod**。
- §4 编号连撞两次（4.151 / 4.152 都已被占）⇒ 本轮用 **§4.158**，取号口径写进该节。
"""


def main(argv):
    write = u"--write" in argv
    paths = list(FIXED)
    paths += [os.path.join(u"build", u"zftools", g) for g in GATES]
    paths += [os.path.join(u"build", u"zftools", u"check", u"Zf148Check.java")]
    for fn in sorted(os.listdir(os.path.join(ROOT, "build", "zftools"))):
        if fn.startswith(u"_zf148_"):
            paths.append(os.path.join(u"build", u"zftools", fn))
    # 书目录下的 24 份 JSON（分类 6 + 条目 18）
    base = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t",
                        "patchouli_books", "guide", "en_us")
    for sub in (u"categories", u"entries"):
        for dirpath, _d, files in os.walk(os.path.join(base, sub)):
            for fn in files:
                full = os.path.join(dirpath, fn)
                paths.append(os.path.relpath(full, ROOT).replace(os.sep, u"/"))

    paths = sorted(set(paths))
    missing = [p for p in paths if not os.path.exists(os.path.join(ROOT, p.replace(u"/", os.sep)))]
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
    st = subprocess.run([GIT, u"-c", u"core.quotepath=false", u"status", u"--porcelain", u"--"] + paths,
                        cwd=ROOT, capture_output=True).stdout.decode(u"utf-8", u"replace")
    staged = [l for l in st.split(u"\n") if l.strip()]
    print(u"已暂存 %d 条（前 12）：" % len(staged))
    for l in staged[:12]:
        print(u"   " + l)
    if u"--write" not in argv:
        print(u"（没加 --write：只暂存，不提交）")
        return 0

    msgfile = os.path.join(ROOT, "build", "zftools", u"_zf148_commit_msg.txt")
    io.open(msgfile, u"w", encoding=u"utf-8", newline=u"\n").write(MSG)
    r = subprocess.run([GIT, u"commit", u"-F", msgfile], cwd=ROOT, capture_output=True)
    print(r.stdout.decode(u"utf-8", u"replace"))
    if r.returncode != 0:
        print(u"提交失败：" + r.stderr.decode(u"utf-8", u"replace"))
        return 1
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
