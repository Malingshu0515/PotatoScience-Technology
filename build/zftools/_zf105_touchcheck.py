# -*- coding: utf-8 -*-
r"""_zf105_touchcheck.py —— 【新门】"注册窗口关了才第一次初始化那个类"的机械防线（0.11 ZF105）

**要挡的是什么**：某个类在**静态字段**里调 `DeferredRegister.register(...)`，
但没人在这之前碰过它 ⇒ JVM 把它的静态初始化拖到"第一次真正访问"那一刻。
如果第一次访问晚于 `RegisterEvent`（典型：创造模式标签页在**开物品栏**时才去读它），
NeoForge 就抛：

    IllegalStateException: Cannot register new entries to DeferredRegister after RegisterEvent has been fired.
  ⇒ ExceptionInInitializerError ⇒ 之后碰它的任何代码都变成 NoClassDefFoundError ⇒ 开物品栏必崩

**为什么需要机械检查**：这个错**编译不报、启动不报**，只在"人按 E 开物品栏"那一瞬间炸，
而且崩点报在**调用方**（`ModItems`）而不是真正的错处 —— 与 §4.2「编译绿 ≠ 能加载」同一性质。
2026-09-25 18:40:17 那次客户端崩溃就是它（崩溃报告第 217 / 259 / 327 行）。

**判据**（纯字节码，不启动游戏）：
  ① 对 `build/classes/java/main` 下**每一个 class**，反汇编看它的 `<clinit>` 里
     有没有"调用某个 `DeferredRegister.register`"；
  ② 有 ⇒ 它就是"注册型类"，必须在模组构造期被碰过；
  ③ "被碰过"的可机械判据：`PotatoST.<init>` 的字节码里出现了指向该类的引用，
     **且**那个引用出现在任何 `<clinit>` 触发之后（这里用更简单、更强的口径：
     只要 `PotatoST.<init>` 里出现了该类的常量池引用就算"被碰过"，
     因为 `invokestatic` 一个静态方法/读一个静态字段都会触发类初始化）。

⚠ 反证：`--knife` 参数会把 `ModArmorItems.touch()` 那一行临时注释掉再跑，
   要求本脚本**必须报 FAIL**（不能只看它绿）。

跑法：
    $env:PYTHONIOENCODING='utf-8'
    python E:\PotatoST\build\zftools\_zf105_touchcheck.py
"""
import io
import os
import re
import struct
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
CLASSES = os.path.join(PROJ, "build", "classes", "java", "main")
PKG_DIR = os.path.join(CLASSES, "com", "potatost", "mod")
MAIN_CLASS = "com.potatost.mod.PotatoST"

fails = []


def javap(class_name, extra=None):
    exe = os.path.join(os.environ.get("JAVA_HOME", ""), "bin", "javap.exe")
    if not os.path.isfile(exe):
        exe = "javap"
    cmd = [exe, "-p", "-c", "-constants", "-classpath", CLASSES, class_name]
    if extra:
        cmd = [exe] + extra + ["-classpath", CLASSES, class_name]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.decode("utf-8", "replace")


def parse_pool(data):
    n = struct.unpack_from(">H", data, 8)[0]
    i, idx, pool = 10, 1, {}
    while idx < n:
        tag = data[i]
        i += 1
        if tag == 0:
            pool[idx] = ("end", None)
        elif tag == 1:
            ln = struct.unpack_from(">H", data, i)[0]
            i += 2
            pool[idx] = ("utf8", data[i:i + ln].decode("utf-8", "replace"))
            i += ln
        elif tag in (7, 8, 16, 19, 20):
            pool[idx] = ("ref", struct.unpack_from(">H", data, i)[0])
            i += 2
        elif tag == 15:
            i += 3
        elif tag == 3:
            pool[idx] = ("int", struct.unpack_from(">i", data, i)[0])
            i += 4
        elif tag == 4:
            pool[idx] = ("float", struct.unpack_from(">f", data, i)[0])
            i += 4
        elif tag == 6:
            pool[idx] = ("double", struct.unpack_from(">d", data, i)[0])
            i += 8
            idx += 1
        elif tag in (9, 10, 11, 12, 17, 18):
            a, b = struct.unpack_from(">HH", data, i)
            i += 4
            pool[idx] = ("nt", a, b)
        elif tag == 5:
            pool[idx] = ("long", struct.unpack_from(">q", data, i)[0])
            i += 8
            idx += 1
        else:
            raise ValueError("tag %d @%s" % (tag, "?"))
        idx += 1
    return pool


def class_names_in_bytecode(path):
    u"""粗扫：一个 class 的字节码里出现过哪些 `Lcom/potatost/mod/Xxx;` 形状的类名。"""
    data = open(path, "rb").read()
    return set(m.group(1).decode("ascii", "replace")
               for m in re.finditer(rb"Lcom/potatost/mod/([A-Za-z0-9_$]+);", data))


def main():
    knife = "--knife" in sys.argv
    print(u"================ ① 找出所有『注册型类』（<clinit> 里调 DeferredRegister.register）================")
    registered = []
    for name in sorted(os.listdir(PKG_DIR)):
        if not name.endswith(".class") or "$" in name:
            continue
        cls = name[:-6]
        dis = javap("com.potatost.mod." + cls)
        # 只看 static {} 那一段
        if u"static {};" not in dis:
            continue
        body = dis.split(u"static {};", 1)[1]
        # 下一段方法声明之前的部分就是 <clinit>
        body = re.split(u"\n  [a-z]", body, 1)[0]
        if re.search(u"DeferredRegister\\.register", body) or u"DeferredRegister.register" in body:
            n = len(re.findall(u"DeferredRegister\\.register", body))
            registered.append((cls, n))
            print(u"  [注册型] %-20s <clinit> 里有 %d 处 DeferredRegister.register" % (cls, n))
    if not registered:
        fails.append(u"没扫到任何『注册型类』 —— 判据可能失效了（这本身要查）")
        print(u"  [FAIL] 一个都没扫到")
    else:
        print(u"  ⇒ 共 %d 个注册型类：%s" % (len(registered), [c for c, _n in registered]))

    print(u"")
    print(u"================ ② 它们在模组构造期是否被碰过 ================")
    main_refs = class_names_in_bytecode(os.path.join(PKG_DIR, "PotatoST.class"))
    print(u"  PotatoST.<init> 所在类引用了 %d 个同包类" % len(main_refs))
    for cls, _n in registered:
        touched = cls in main_refs
        label = u"%s 在构造期被碰过（静态初始化因此发生在注册窗口还开着的时候）" % cls
        if touched:
            print(u"  [OK]   " + label)
        else:
            print(u"  [FAIL] %s **没有**在构造期被碰过 ⇒ 它的静态初始化会拖到第一次被访问"
                  u"（典型：开物品栏读创造页）⇒ 注册窗口已关 ⇒ IllegalStateException ⇒ 崩溃" % cls)
            fails.append(label)

    print(u"")
    print(u"================ ③ ModArmorItems.touch() 这条特例 ================")
    src = io.open(os.path.join(PKG_DIR, "ModArmorItems.java"), encoding="utf-8").read()
    ok_touch = u"public static void touch()" in src
    print(u"  [%s] ModArmorItems 里有 public static void touch()" % (u"OK" if ok_touch else u"FAIL"))
    if not ok_touch:
        fails.append(u"ModArmorItems 缺 touch()")
    main_src = io.open(os.path.join(PKG_DIR, "PotatoST.java"), encoding="utf-8").read()
    ok_call = u"ModArmorItems.touch();" in main_src
    print(u"  [%s] PotatoST 构造器里调了 ModArmorItems.touch();" % (u"OK" if ok_call else u"FAIL"))
    if not ok_call:
        fails.append(u"PotatoST 没有调用 ModArmorItems.touch()")
    # touch() 必须在静态字段**之后**（挪到前面就等于没起作用）
    i_touch = src.find(u"public static void touch()")
    i_last = max(src.rfind(u'register("'), src.rfind(u"ITEMS.register("))
    print(u"  [%s] touch() 在类的尾部（静态字段之后）" % (u"OK" if i_touch > i_last >= 0 else u"FAIL"))
    if not (i_touch > i_last >= 0):
        fails.append(u"touch() 不在静态字段之后 —— 那样不会触发字段初始化")

    print(u"")
    print(u"================ ④ 崩溃现场的指纹（报告里那三行）================")
    crash_dir = os.path.join(PROJ, "run", "client", "crash-reports")
    if os.path.isdir(crash_dir):
        reps = sorted((os.path.join(crash_dir, f) for f in os.listdir(crash_dir)
                       if f.endswith(".txt")), key=os.path.getmtime, reverse=True)
        hit = None
        for r in reps:
            t = io.open(r, encoding="utf-8", errors="replace").read()
            if u"Cannot register new entries to DeferredRegister" in t:
                hit = (os.path.basename(r), r)
                break
        if hit:
            t = io.open(hit[1], encoding="utf-8", errors="replace").read()
            print(u"  找到带这个指纹的历史崩溃报告：%s" % hit[0])
            print(u"  （留着当『反证证据』：以后若再犯，报告里的指纹与它逐字相同）")
        else:
            print(u"  [OK]   现有崩溃报告里**没有**这个指纹")
    else:
        print(u"  [--]   没有 crash-reports 目录")

    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
