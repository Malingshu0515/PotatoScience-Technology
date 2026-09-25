# -*- coding: utf-8 -*-
r"""_zf119_backup.py —— ZF119 的改前件（§10）

用户原话：「加个振金锭（目前没配方）这是振金锭贴图 做成动态贴图 3t播放一帧」

⚠⚠ **我这次的顺序错了，如实记下来**：探针/探针以外的三样（贴图、`.mcmeta`、`ModItems` 的两处插入）
是在建备份**之前**做的 —— 其中 `ModItems.java` 是**改盘**（另外两个是**新建文件**，新建不算改盘）。
所以本轮对 `ModItems.java` 走**事后补账**（等级 ① + ③ 双路证明）：

  ① `git cat-file blob HEAD:src/main/java/com/potatost/mod/ModItems.java`
     （本轮开工前它是干净的：git 三个 diff 都空 ⇒ HEAD 那份就是改前那份）；
  ③ 减法重建：把本轮插进去的两段文本从盘上文件里删掉 ⇒ 必须与 ① 逐字节相同。

**下不为例**（ZF117 我已经写过一次"下不为例"）：**先建备份，再动第一个字节**。
本轮起，脚本第一句就是建备份 —— 本轮自己就是反例。
"""
import glob
import hashlib
import io
import os
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf119_pre"
ADIR = r"src\main\resources\assets\potato_s_t\textures\item"
TOOLS = r"build\zftools"
CHECK = TOOLS + r"\check"
JAVA = r"src\main\java\com\potatost\mod"
TAGS = r"src\main\resources\data\c\tags\item"

FILES = [
    JAVA + r"\ModItems.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    TAGS + r"\ingots.json",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
# 盘上现有的**动画**贴图与它的 mcmeta（拿来做格式基准）
for p in sorted(glob.glob(os.path.join(ROOT, ADIR, "*.mcmeta"))):
    FILES.append(os.path.relpath(p, ROOT))

NEW = ([ADIR + r"\vibranium_ingot.png", ADIR + r"\vibranium_ingot.png.mcmeta",
        r"src\main\resources\assets\potato_s_t\models\item\vibranium_ingot.json",
        TAGS + r"\ingots\vibranium.json", TAGS + r"\vibranium_ingots.json",
        r"build\用户素材\振金锭.png", CHECK + r"\Zf119Check.java"]
       + [TOOLS + r"\_zf119_%s.py" % s for s in
          ("intake", "measure", "texture", "item", "retarget", "verify", "falsify",
           "docs", "gatesnap", "unprobe", "backup")])

fails, notes = [], []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s" % BK)
        return 1
    lines, ok = [], 0
    todo = list(FILES)
    for pat in ("_zf*_verify.py", "_zf*_falsify.py", "_zf*_gatesnap.py", "_zf*gates.ps1"):
        for p in sorted(glob.glob(os.path.join(ROOT, TOOLS, pat))):
            rel = os.path.relpath(p, ROOT)
            if rel not in todo:
                todo.append(rel)
    for rel in todo:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            fails.append(u"缺文件：%s" % rel)
            continue
        dst = os.path.join(BK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        b = sha1(src)
        shutil.copy2(src, dst)
        if b != sha1(dst):
            fails.append(u"%s：哈希不一致" % rel)
        else:
            ok += 1
            lines.append(u"%s  %10d  %s" % (b, os.path.getsize(dst), rel))

    # ---- ModItems.java 的补账（等级 ① + ③）----
    dst_java = os.path.join(BK, JAVA, "ModItems.java")
    blob = subprocess.run([r"C:\Program Files\Git\cmd\git.exe", "cat-file", "blob",
                           "HEAD:" + JAVA.replace("\\", "/") + "/ModItems.java"],
                          stdout=subprocess.PIPE, cwd=ROOT).stdout
    open(dst_java, "wb").write(blob)
    head_sha = sha1(dst_java)
    cur = io.open(os.path.join(ROOT, JAVA, "ModItems.java"), encoding="utf-8").read()
    # ③ 减法重建：把本轮插进去的两段删掉
    ins1 = u'''
    /**
     * 振金锭（0.11 ZF119）。用户原话：「加个振金锭（目前没配方）这是振金锭贴图 做成动态贴图 3t播放一帧」。
     *
     * <p><b>没有配方</b> —— 用户明说"目前没配方" ⇒ 盘上不许出现任何产出它的配方 JSON
     * （`_zf119_verify.py` 常驻盯着这一条）。粗振金（ZF114）→ 振金锭这条路留到以后。</p>
     *
     * <p>贴图是**动画**：`textures/item/vibranium_ingot.png`（32×320，10 帧 × 32）
     * + 同名 `.mcmeta`（`frametime = 3` ⇒ 3 tick 一帧、一轮 30 tick = 1.5 秒）。
     * 源图是用户给的 32×280 长条（10 个 32×24 的锭），重排脚本 `_zf119_texture.py`
     * 只做整行搬运（零重采样），摆位照盘上 `titanium_ingot.png`（同样 32×24 内容、上下各留 4 行）。</p>
     *
     * <p>按项目规则挂在 {@code c:ingots/vibranium} + {@code c:vibranium_ingots}
     * 与父标签 {@code c:ingots} 上（锭默认走兼容标签）。</p>
     */
    public static final DeferredItem<Item> VIBRANIUM_INGOT =
            ITEMS.register("vibranium_ingot", () -> new Item(new Item.Properties()));
'''
    ins2 = u'\n                        output.accept(VIBRANIUM_INGOT.get());// ← 新增（0.11 ZF119 振金锭）'
    rebuild = cur.replace(ins1, u"", 1).replace(ins2, u"", 1)
    reb_sha = hashlib.sha1(rebuild.encode("utf-8")).hexdigest()
    if reb_sha == head_sha:
        notes.append(u"ModItems.java 补账：减法重建 == git HEAD（sha1 %s，两条路一致）" % head_sha[:16])
    else:
        fails.append(u"ModItems.java 补账失败：减法重建 %s ≠ HEAD %s" % (reb_sha[:16], head_sha[:16]))
    lines = [l for l in lines if not l.endswith(JAVA.replace("\\", "/") + "/ModItems.java")]
    lines.append(u"%s  %10d  %s   ← 事后补账（①+③ 双路）" % (head_sha, len(blob), JAVA + "\\ModItems.java"))

    io.open(os.path.join(BK, u"_zf119_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"本轮开始前这些路径应当不存在：\n" + u"\n".join(NEW) + u"\n")
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改前件 %d 份（+1 份补账）→ %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
