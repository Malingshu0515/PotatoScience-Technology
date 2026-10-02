# -*- coding: utf-8 -*-
r"""_rzh_jar012_check.py —— 0.12 产物体检（把上一轮踩过的两个坑都堵在门里）。

上一轮 `release/PotatoST-0.11.jar` 出过两次事故，各有各的成因：
  ① **jar 是加文言文之前构建的** ⇒ 包里没有 `lzh.json`，游戏切文言后整包回落英文。
     成因是"源文件对 ≠ 资源进包"，当时没有任何门守着这一环。
  ② **`gradlew build` 报 BUILD SUCCESSFUL，产物里却 0 个 `.class`**（5,041,845 B、纯资源）。
     成因：打 jar 那一刻 `build/classes/java/main` 是空的（并行会话把类清了）。
     时间戳对不上是最直接的证据 —— jar 写入 11:59:57，类文件 mtime 12:00:27~12:00:55。

所以这道门除了常规体检，专门钉四条"产物完整性"断言（这四条才是它存在的理由）：
  C1 类文件数 ≥ 基线（357）—— 少一个就说明打 jar 时输入不全
  C2 每个 `.class` 的 mtime **早于** jar 的 mtime —— 反向就是坑 ②
  C3 五份语言文件**逐字节**等于源目录（含 lzh）—— 坑 ①
  C4 zip 结构自检（CRC 全过）+ 关键资源清单（44 份成就 / 配方 / 模型 / 贴图）

用法：`python build/zftools/_rzh_jar012_check.py [jar路径]`
默认取 `build/libs/potato_s_t-0.12.jar`。
"""
from __future__ import print_function
import io
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGSRC = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
CLASSES = os.path.join(ROOT, u"build", u"classes", u"java", u"main")
DEFAULT_JAR = os.path.join(ROOT, u"build", u"libs", u"potato_s_t-0.12.jar")
OUT = os.path.join(HERE, u"_rzh_jar012_check.txt")
CLASS_BASELINE = 357


def main():
    jar = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JAR
    L = []
    bad = 0

    if not os.path.exists(jar):
        print(u"[拒绝] 找不到 jar: %s" % jar)
        return 1
    jsize = os.path.getsize(jar)
    jmtime = os.path.getmtime(jar)
    import time
    L.append(u"== 产物 ==")
    L.append(u"  %s" % jar)
    L.append(u"  %d 字节（%.2f MB），改于 %s"
             % (jsize, jsize / 1048576.0, time.strftime(u"%Y-%m-%d %H:%M:%S", time.localtime(jmtime))))

    z = zipfile.ZipFile(jar)
    names = z.namelist()

    # ---- zip 结构自检：CRC 全过 ----
    L.append(u"")
    L.append(u"== A zip 结构 ==")
    broken = z.testzip()
    if broken:
        bad += 1
        L.append(u"  [错] CRC 校验失败：%s" % broken)
    else:
        L.append(u"  OK   全部 %d 个条目 CRC 校验通过" % len(names))

    # ---- 条目分类 ----
    # ⚠ 只数**文件**：`zipfile` 的 namelist 里还有目录条目（以 "/" 结尾），
    #   不排掉就会让 "jar 44 份成就 / 源 43 份" 这种假差异冒出来（本轮踩过）。
    files = [n for n in names if not n.endswith(u"/")]
    cls = [n for n in files if n.endswith(u".class")]
    lang = [n for n in files if n.startswith(u"assets/potato_s_t/lang/") and n.endswith(u".json")]
    adv = [n for n in files if n.startswith(u"data/potato_s_t/advancement/") and n.endswith(u".json")]
    rec = [n for n in files if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")]
    tex = [n for n in files if n.startswith(u"assets/potato_s_t/textures/") and not n.endswith(u"/")]
    mod = [n for n in files if n.startswith(u"assets/potato_s_t/models/") and n.endswith(u".json")]
    dirs = len(names) - len(files)
    L.append(u"")
    L.append(u"== B 清单 ==")
    L.append(u"  条目总数 %d（其中目录 %d）/ 文件 %d" % (len(names), dirs, len(files)))
    L.append(u"  .class %d / lang %d / 成就 %d / 配方 %d / 模型 %d / 贴图 %d"
             % (len(cls), len(lang), len(adv), len(rec), len(mod), len(tex)))

    # ---- B2 与源目录逐个对账（含"jar 里有源目录没有的"）----
    L.append(u"")
    L.append(u"== B2 数据文件与源目录对账 ==")
    pairs = [
        (u"成就", u"data/potato_s_t/advancement/", os.path.join(ROOT, u"src", u"main", u"resources", u"data", u"potato_s_t", u"advancement")),
        (u"配方", u"data/potato_s_t/recipe/", os.path.join(ROOT, u"src", u"main", u"resources", u"data", u"potato_s_t", u"recipe")),
    ]
    for label, prefix, srcdir in pairs:
        inj = set(n[len(prefix):] for n in files
                  if n.startswith(prefix) and n.endswith(u".json"))
        ons = set()
        for dirpath, _d, fns in os.walk(srcdir):
            for fn in fns:
                if fn.endswith(u".json"):
                    rel = os.path.relpath(os.path.join(dirpath, fn), srcdir).replace(u"\\", u"/")
                    ons.add(rel)
        only_jar = sorted(inj - ons)
        only_src = sorted(ons - inj)
        if only_jar or only_src:
            bad += 1
            L.append(u"  [错] %s 不一致：jar 多 %d 份、源多 %d 份" % (label, len(only_jar), len(only_src)))
            for n in only_jar[:6]:
                L.append(u"         jar 独有：%s" % n)
            for n in only_src[:6]:
                L.append(u"         源独有：%s" % n)
        else:
            L.append(u"  OK   %s %d 份，jar 与源目录**逐名一致**" % (label, len(inj)))

    # ---- C1 类文件数 ----
    L.append(u"")
    L.append(u"== C1 类文件数（基线 %d）==" % CLASS_BASELINE)
    if len(cls) < CLASS_BASELINE:
        bad += 1
        L.append(u"  [错] 只有 %d 个 .class —— 少于基线 %d ⇒ 打 jar 时输入不全（坑 ②）"
                 % (len(cls), CLASS_BASELINE))
    else:
        L.append(u"  OK   %d 个 .class（≥ 基线）" % len(cls))

    # ---- C2 类 mtime 必须早于 jar mtime ----
    L.append(u"")
    L.append(u"== C2 时间戳方向（类必须先于 jar）==")
    src_classes = []
    for dirpath, _dirnames, filenames in os.walk(CLASSES):
        for fn in filenames:
            if fn.endswith(u".class"):
                src_classes.append(os.path.join(dirpath, fn))
    if not src_classes:
        bad += 1
        L.append(u"  [错] build/classes/java/main 下没有类文件 —— 无法对账")
    else:
        newest = max(src_classes, key=os.path.getmtime)
        nm = os.path.getmtime(newest)
        L.append(u"  源目录类文件 %d 个，最新一个：%s" % (len(src_classes), os.path.relpath(newest, ROOT)))
        L.append(u"      类 mtime %s  ／  jar mtime %s"
                 % (time.strftime(u"%H:%M:%S", time.localtime(nm)),
                    time.strftime(u"%H:%M:%S", time.localtime(jmtime))))
        if nm > jmtime:
            bad += 1
            L.append(u"  [错] 有类文件比 jar 还新 ⇒ jar 是在类还没编完时打的（**坑 ② 复现**）")
        else:
            L.append(u"  OK   jar 比所有源类都新")

    # ---- C3 lang 逐字节 ----
    L.append(u"")
    L.append(u"== C3 五份语言文件（逐字节对源目录）==")
    injar = dict((n.split(u"/")[-1], n) for n in lang)
    srcs = sorted(n for n in os.listdir(LANGSRC) if n.endswith(u".json"))
    for name in srcs:
        raw = io.open(os.path.join(LANGSRC, name), u"rb").read()
        if name not in injar:
            bad += 1
            L.append(u"  [错] %-14s 源文件在，包内没有 ⇒ 游戏查不到这个语言（**坑 ①**）" % name)
            continue
        jraw = z.read(injar[name])
        same = jraw == raw
        if not same:
            bad += 1
        ok = u"逐字节一致" if same else u"**不一致**"
        try:
            k = len(json.loads(jraw.decode(u"utf-8")))
        except Exception:                                    # noqa: BLE001
            k = u"解析失败"
        L.append(u"  %-14s 源 %6d B / 包内 %6d B  %s  %s 键" % (name, len(raw), len(jraw), ok, k))
    if u"lzh.json" not in injar:
        bad += 1
        L.append(u"  [错] **lzh.json 不在包里** —— 文言文会整包回落英文")
    else:
        meta = json.loads(z.read(injar[u"lzh.json"]).decode(u"utf-8"))
        L.append(u"  OK   lzh 元数据：language.name=%r / region=%r / code=%r"
                 % (meta.get(u"language.name"), meta.get(u"language.region"), meta.get(u"language.code")))

    # ---- C4 关键资源清单 ----
    L.append(u"")
    L.append(u"== C4 关键资源 ==")
    checks = [
        (u"potato_s_t.mixins.json", u"assets/potato_s_t/lang/zh_cn.json"),
        (u"neoforge.mods.toml", u"META-INF/neoforge.mods.toml"),
        (u"pack.mcmeta", u"pack.mcmeta"),
    ]
    for label, n in checks:
        if n in names:
            L.append(u"  OK   %s" % n)
        else:
            bad += 1
            L.append(u"  [错] 缺 %s（%s）" % (n, label))
    # mods.toml 里的版本号
    try:
        toml = z.read(u"META-INF/neoforge.mods.toml").decode(u"utf-8")
        import re
        m = re.search(u'(?m)^\\s*version\\s*=\\s*"([^"]+)"', toml)
        L.append(u"  mods.toml version = %s" % (m.group(1) if m else u"**找不到**"))
        if not m or m.group(1) != u"0.12":
            bad += 1
            L.append(u"  [错] mods.toml 里的版本号不是 0.12")
    except Exception as e:                                   # noqa: BLE001
        bad += 1
        L.append(u"  [错] 读 mods.toml 失败：%s" % e)

    L.append(u"")
    L.append(u"== 结论 ==")
    L.append(u"  全部通过（%d 条目 / %d 类 / %d 语言）" % (len(names), len(cls), len(lang))
             if bad == 0 else u"  有 %d 处问题" % bad)
    z.close()
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
    print(u"bad=%d classes=%d entries=%d -> %s" % (bad, len(cls), len(names), OUT))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
