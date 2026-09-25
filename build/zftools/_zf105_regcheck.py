# -*- coding: utf-8 -*-
r"""_zf105_regcheck.py —— 【新门】"注册窗口关了才第一次初始化那个类"的机械防线（0.11 ZF105）

**要挡的是什么**：某个类在**静态初始化**里调 `DeferredRegister.register(...)`，
但没人在这之前碰过它 ⇒ JVM 把静态初始化拖到"第一次真正访问"那一刻。
如果第一次访问晚于 `RegisterEvent`（典型：创造模式标签页在**开物品栏**时才去读它），
NeoForge 抛：

    IllegalStateException: Cannot register new entries to DeferredRegister after RegisterEvent has been fired.
  ⇒ ExceptionInInitializerError ⇒ 之后碰它的任何代码都变成 NoClassDefFoundError ⇒ 开物品栏必崩

**为什么需要机械检查**：这个错**编译不报、启动不报**，只在"人按 E 开物品栏"那一瞬间炸，
崩点还报在**调用方**（`ModItems`）而不是真正的错处 —— 与 §4.2「编译绿 ≠ 能加载」同一性质。
2026-09-25 18:40:17 那次客户端崩溃就是它（崩溃报告第 217 / 259 / 327 行）。

**判据（读 javap 反汇编，不启动游戏）**：
  ① 每个类的 `static {};` 段里有没有 `DeferredRegister.register:` 这种方法引用 ⇒ "注册型类"；
  ② 注册型类必须在**模组构造期**被碰过。判据 = `javap PotatoST` 的 `PotatoST(...)` 构造器
     段里出现该类的名字（`ModArmorItems.touch` / `ModItems.ITEMS` 这种形态），
     因为 `invokestatic` / `getstatic` 都会触发目标类的初始化；
  ③ 另外单独钉 `ModArmorItems.touch()` 这条特例：方法在不在、在不在类尾部、构造器里调没调。

⚠ **为什么用 javap 而不是自己解常量池**：本轮先手写了一个常量池解析器，
  它把 `methods[]` 的名称索引解错（`utf8()` 全返回 None），判据因此"一个注册型类都扫不到"。
  换成 javap 文本后一次就对 —— 与 §4.71 的教训同源：**取证工具本身也要先自证**。

⚠ **反证**：`--knife` 会把 `PotatoST.java` 里 `ModArmorItems.touch();` 临时注释掉、重新编译，
  要求本脚本报 FAIL，然后逐字还原（§4.17：能失败的检查才算检查）。
"""
import io
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
CLASSES = os.path.join(PROJ, "build", "classes", "java", "main")
PKG = u"com.potatost.mod"
PKG_DIR = os.path.join(CLASSES, *PKG.split(u"."))
SRC_DIR = os.path.join(PROJ, "src", "main", "java", *PKG.split(u"."))
SRC_MAIN = os.path.join(SRC_DIR, "PotatoST.java")
SRC_ARMOR = os.path.join(SRC_DIR, "ModArmorItems.java")
CRASH_DIR = os.path.join(PROJ, "run", "client", "crash-reports")
CRASH_FINGERPRINT = u"Cannot register new entries to DeferredRegister"

fails = []


def javap(class_name):
    exe = os.path.join(os.environ.get("JAVA_HOME", ""), "bin", "javap.exe")
    if not os.path.isfile(exe):
        exe = "javap"
    p = subprocess.run([exe, "-p", "-c", "-constants", "-classpath", CLASSES, class_name],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.decode("utf-8", "replace")


def method_bodies(disasm):
    u"""把 javap 输出切成 {方法签名行: 正文}（javap 的方法签名缩进 2 空格）。"""
    out = {}
    cur, buf = None, []
    for line in disasm.split(u"\n"):
        if re.match(u"^  [^ ]", line) and re.search(u"\\(.*\\)", line) or line.strip() == u"static {};":
            if cur is not None:
                out[cur] = u"\n".join(buf)
            cur, buf = line.strip(), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = u"\n".join(buf)
    return out


def clinit_body(disasm):
    for key, body in method_bodies(disasm).items():
        if key == u"static {};":
            return body
    return u""


def main():
    print(u"=============== ① 找『注册型类』（static{} 里调 register）===============")
    registered = []
    for name in sorted(os.listdir(PKG_DIR)):
        if not name.endswith(".class") or u"$" in name:
            continue
        cls = name[:-6]
        body = clinit_body(javap(PKG + u"." + cls))
        # 三种形态都算"注册型"（判据必须全，否则会**漏掉本次崩溃的主角**）：
        #   ① 直接调 `DeferredRegister.register(...)`（ModItems / ModBlocks / ModFluids / ModMenus）
        #   ② 调 `DeferredRegister$Items.register(...)` —— javac 把 `DeferredRegister.createItems()`
        #      的返回类型编成内部子类，所以 `ModItems.ITEMS.register(...)` 反汇编出来
        #      其实是 `DeferredRegister$Items.register`，只数 ① 会漏
        #   ③ 调**本类自己的** `register(...)` 辅助方法（ModArmorItems 就是这样：
        #      真正那 9 次注册在辅助方法体内，static{} 里只有 9 条 `invokestatic register:`）
        direct = len(re.findall(
            u"//\\s*Method\\s+net/neoforged/neoforge/registries/DeferredRegister\\$?[A-Za-z]*\\.register:",
            body))
        # 同类调用的反汇编形如 `// Method register:(...)`（不带 owner）
        helper = len(re.findall(u"//\\s*Method\\s+register:", body))
        if direct or helper:
            registered.append(cls)
            print(u"  [注册型] %-24s static{}：DeferredRegister*.register ×%d，本类 register(...) ×%d"
                  % (cls, direct, helper))
    print(u"  ⇒ 共 %d 个：%s" % (len(registered), registered))
    if not registered:
        fails.append(u"一个注册型类都没扫到 ⇒ 判据失效（这本身要查）")
        print(u"  [FAIL] 判据失效")

    print(u"")
    print(u"=============== ② 它们在模组构造期是否被碰过 ===============")
    main_bodies = method_bodies(javap(PKG + u".PotatoST"))
    ctor = u""
    for key, body in main_bodies.items():
        if key.startswith(u"public com.potatost.mod.PotatoST("):
            ctor = body
            break
    if not ctor:
        fails.append(u"没找到 PotatoST 的构造器（判据失效）")
        print(u"  [FAIL] 没找到 PotatoST 的构造器")
    print(u"  构造器长度 = %d 字符" % len(ctor))
    for cls in registered:
        ok = (cls + u".") in ctor
        if ok:
            print(u"  [OK]   %-24s 构造期被碰过（静态初始化发生在注册窗口还开着时）" % cls)
        else:
            print(u"  [FAIL] %-24s **没被碰过** ⇒ 静态初始化拖到开物品栏那一刻 ⇒ 崩溃" % cls)
            fails.append(u"%s 未在构造期被碰过" % cls)

    print(u"")
    print(u"=============== ③ ModArmorItems.touch() 这条特例（本次崩溃的主角）===============")
    src = io.open(SRC_ARMOR, encoding="utf-8").read() if os.path.isfile(SRC_ARMOR) else u""
    main_src = io.open(SRC_MAIN, encoding="utf-8").read() if os.path.isfile(SRC_MAIN) else u""
    i_touch = src.find(u"public static void touch()")
    i_last_reg = src.rfind(u"register(\"")            # 最后一个静态字段的注册调用（形如 register("xxx", ...)）
    checks = [
        (u"ModArmorItems 里有 public static void touch()", i_touch >= 0),
        (u"touch() 在类的尾部（静态字段之后 —— 挪到前面等于没起作用）", i_touch > i_last_reg >= 0),
        (u"PotatoST 构造器里调了 ModArmorItems.touch();", u"ModArmorItems.touch();" in main_src),
        (u"ModArmorItems 被扫成注册型类（所以它**必须**被碰）", u"ModArmorItems" in registered),
        (u"构造器的反汇编里确实能看到 ModArmorItems.touch（不是只写在注释里）",
         u"ModArmorItems.touch" in ctor),
    ]
    for label, ok in checks:
        print(u"  [%s] %s" % (u"OK" if ok else u"FAIL", label))
        if not ok:
            fails.append(label)

    print(u"")
    print(u"=============== ④ 历史崩溃指纹（对照物）===============")
    hit = None
    if os.path.isdir(CRASH_DIR):
        files = sorted((f for f in os.listdir(CRASH_DIR) if f.endswith(u".txt")),
                       key=lambda x: os.path.getmtime(os.path.join(CRASH_DIR, x)), reverse=True)
        for f in files:
            t = io.open(os.path.join(CRASH_DIR, f), encoding="utf-8", errors="replace").read()
            if CRASH_FINGERPRINT in t:
                hit = f
                break
    if hit:
        print(u"  [指纹] 历史崩溃报告 `%s` 逐字带着这句话：" % hit)
        print(u"         %s after RegisterEvent has been fired." % CRASH_FINGERPRINT)
        print(u"         ⇒ 以后若再犯，报告里的指纹与它完全相同")
    else:
        print(u"  [OK]   现有崩溃报告里没有这个指纹")

    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
