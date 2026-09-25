# -*- coding: utf-8 -*-
u"""_zf122_backup.py —— ZF122 的**事后补账**快照（动手前忘了建，违反 §10）

诚实记录：本轮改源码之前没先建 `zf122_pre`（第三次犯了，前两次是 ZF78/ZF83）。
补救照先例做**可验证的减法重建**：

  · 三个 Java + 配方生成器：把本轮每一处插入**逐条反向替换**回去。每处都断言
    "锚点恰好命中 1 次" ⇒ 漏改一处会表现为命中 0/2 次，而不是悄悄错过去（等级③ 减法重建）。
  · 四份 lang：本轮只是"插 10 个键"，改前件直接从 **git HEAD** 取
    （等级① 已提交的权威快照；里面**含别轮的工作**、但不含本轮的 10 键）。

跑法：python build\\zftools\\_zf122_backup.py
"""
import hashlib
import io
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf122_pre"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
GIT = r"C:\Users\Administrator\AppData\Local\GitHubDesktop\app-3.6.5\resources\app\git\cmd\git.exe"

TAB_LINE = (u"                        output.accept(STAR_CHART_TOME.get());"
            u"// ← 新增（0.11 ZF122 星仪图之章）\n")

RECIPE_ADD = u'''\n    # ===== ZF122 追加（星仪图之章；这一轮的图纸我自己定的 —— 用户说"你看着办"）=====
    # 【纸】【紫水晶碎片】【纸】 / 【紫水晶碎片】【荧石】【紫水晶碎片】 / 【纸】【紫水晶碎片】【纸】
    dict(name="star_chart_tome", category="misc",
         result=("potato_s_t:star_chart_tome", 1),
         pattern=["PAP", "AGA", "PAP"],
         key={"P": ("item", "minecraft:paper"),
              "A": ("item", "minecraft:amethyst_shard"),
              "G": ("item", "minecraft:glowstone")}),'''


def block(name):
    u"""取某个插入块的**字面量值**。

    ⚠ 第一版是"读 _zf122_java.py 的源码、数引号抠字符串" —— 数出来的结果是**源码里的转义写法**
    （`recipe\\\\*.json` 两个反斜杠），而 Python 插进文件的**值**只有一个反斜杠 ⇒ 反向锚点永远 0 命中。
    正确做法：**import 那个模块直接拿常量**（模块顶层没有副作用，main() 有 __main__ 守卫）。
    """
    import importlib
    sys.path.insert(0, os.path.join(ROOT, "build", "zftools"))
    mod = importlib.import_module("_zf122_java")
    return getattr(mod, name)


def strip_recipe_entry(path):
    u"""把配方生成器里我追加的那段删掉。

    ⚠ 不拿"注释原文"当锚点：第一次补账时我照着记忆重写了一遍注释（"今年轮" vs "这一轮"），
    一个字的差别就 0 命中。改用**结构标记**：从 `# ===== ZF122 追加` 那一行起，
    到 `"G": ("item", "minecraft:glowstone")}),` 那一行为止（含前面的空行）。
    """
    text = io.open(path, encoding="utf-8").read()
    start_mark = u"    # ===== ZF122 追加（星仪图之章"
    end_mark = u'"G": ("item", "minecraft:glowstone")}),'
    i = text.find(start_mark)
    j = text.find(end_mark)
    if i < 0 or j < 0 or j < i:
        raise SystemExit(u"配方生成器里找不到本轮追加段的起止标记（i=%d j=%d）" % (i, j))
    j = text.find(u"\n", j) + 1
    cut = text[i:j]
    if u"star_chart_tome" not in cut:
        raise SystemExit(u"要删的那段里没有 star_chart_tome，先别动手")
    before = text[:i] + text[j:]
    return text, before


def main():
    if os.path.exists(BK):
        print(u"备份根已存在，按 §10 规矩中止（要重来先确认它是空的再删）")
        return 1
    os.makedirs(BK, exist_ok=True)

    jobs = [
        (os.path.join(JAVA, "ModItems.java"), [block("ITEM_ADD"), TAB_LINE]),
        (os.path.join(JAVA, "PotatoST.java"), [block("MAIN_ADD")]),
        (os.path.join(JAVA, "PotatoSTClient.java"), [block("CLIENT_ADD")]),
    ]
    rows = []
    for path, adds in jobs:
        cur = io.open(path, encoding="utf-8").read()
        before = cur
        for add in adds:
            n = before.count(add)
            if n != 1:
                print(u"[FAIL] %s：反向锚点命中 %d 次（要求 1），片段头 %r"
                      % (os.path.basename(path), n, add[:70]))
                return 1
            before = before.replace(add, u"")
        rel = os.path.relpath(path, ROOT)
        dst = os.path.join(BK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        io.open(dst, "w", encoding="utf-8", newline=u"").write(before)
        h = hashlib.sha256(io.open(dst, "rb").read()).hexdigest()
        rows.append(u"%s  %s  （重建：现文件 %d 字符 − %d = %d）"
                    % (h, rel, len(cur), len(cur) - len(before), len(before)))
        print(u"   重建 %-28s 去掉 %d 字符（%d 处插入全部命中）"
              % (os.path.basename(path), len(cur) - len(before), len(adds)))

    # 配方生成器：按结构标记删（不靠注释原文，见 strip_recipe_entry 的注释）
    rp = os.path.join(ROOT, r"build\zftools\_zf45_recipes.py")
    cur, before = strip_recipe_entry(rp)
    rel = os.path.relpath(rp, ROOT)
    dst = os.path.join(BK, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    io.open(dst, "w", encoding="utf-8", newline=u"").write(before)
    rows.append(u"%s  %s  （重建：现文件 %d 字符 − %d = %d）"
                % (hashlib.sha256(io.open(dst, "rb").read()).hexdigest(), rel,
                   len(cur), len(cur) - len(before), len(before)))
    print(u"   重建 %-28s 去掉 %d 字符（结构标记命中）"
          % (os.path.basename(rp), len(cur) - len(before)))

    for l in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        rel = u"src/main/resources/assets/potato_s_t/lang/%s.json" % l
        try:
            blob = subprocess.run([GIT, "-C", ROOT, "show", "HEAD:" + rel],
                                  capture_output=True, check=True).stdout
        except Exception as exc:
            print(u"   [警告] %s 取不到 HEAD 版本：%s" % (l, exc))
            return 1
        dst = os.path.join(BK, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(blob)
        rows.append(u"%s  %s  （来自 git HEAD，等级① 已提交权威快照）"
                    % (hashlib.sha256(blob).hexdigest(), rel.replace("/", u"\\")))
        print(u"   %-8s 改前件取自 git HEAD（%d 字节）" % (l, len(blob)))

    io.open(os.path.join(BK, "_sha256.txt"), "w", encoding="utf-8", newline=u"\r\n").write(
        u"ZF122 补账哈希清单\r\n" + u"\r\n".join(rows) + u"\r\n")
    io.open(os.path.join(BK, "_说明.txt"), "w", encoding="utf-8", newline=u"\r\n").write(
        u"""ZF122（0.11）星仪图之章 —— **事后补的**快照（动手前忘了建，违反 §10）

诚实记录：本轮改源码之前没有先建 zf122_pre（第三次犯，前两次是 ZF78/ZF83）。
补救照先例做可验证的减法重建：
  · 三个 Java + 配方生成器：逐条反向替换，每处都断言"锚点恰好命中 1 次"（等级③）；
  · 四份 lang：改前件取自 **git HEAD**（等级① 已提交权威快照，含别轮工作、不含本轮 10 键）。

本轮改了什么：
  ModItems.java        +星仪图之章注册 +创造页一行
  PotatoST.java        +ModDataComponents.DATA_COMPONENTS.register（§4.72 构造期触碰）
  PotatoSTClient.java  +SkyboxRenderer.init()
  四份 lang            +10 键（454 → 464）
  _zf45_recipes.py     +star_chart_tome 图纸（四角纸 + 四边紫水晶碎片 + 中间荧石）

新增文件（改前不存在，不在快照里）：ModDataComponents / StarChartTomeItem /
client/SkyboxRenderer / models/item/star_chart_tome.json / textures/item/star_chart_tome.png /
textures/skybox/*.png（四张 1024×512，程序从用户原图裁切缩放）/ _zf122_*.py

回退：把本目录文件按原路径拷回即可（三个 Java 是改前件）。
""")
    print(u"备份根：%s（%d 份 + 说明）" % (BK, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
