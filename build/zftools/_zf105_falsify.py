# -*- coding: utf-8 -*-
r"""_zf105_falsify.py —— 【反证刀】证明 `_zf105_regcheck.py` 真的会失败（0.11 ZF105）

§4.17 的口径：**"能失败的检查"才算检查**。本轮的修复只有一行
（`PotatoST` 里 `ModArmorItems.touch();`），如果门抓不到"这一行被删掉"，那它就是装饰品。

两把刀：
  K1 **删掉 `PotatoST` 里那一行 `ModArmorItems.touch();`** ⇒ 要求门报 FAIL
     （判据：`ModArmorItems` 从"构造期被碰过"变成"没被碰过"）
  K2 **把 `touch()` 从类尾部挪到静态字段之前** ⇒ 要求门报 FAIL
     （判据：挪到前面时它不会触发字段初始化，等于没起作用）

每把刀都：改 → 重新编译 → 跑门（必须非 0）→ **逐字还原** → 重新编译 → 门回到全绿。
⚠ 备份目录名带进程号（并行流程会清 `_zf10*_bak`，上一轮 `_zf103_falsify` 因此丢过副本）。
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
ZT = os.path.join(PROJ, "build", "zftools")
SRC = os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod")
CLS = os.path.join(PROJ, "build", "classes", "java", "main", "com", "potatost", "mod")
# ⚠ 备份目录写在 `build/tmp/` 而**不是** `build/zftools/`：后者被 .gitignore 显式纳入仓库
#   （`build/*` + `!build/zftools/`），放那儿会被 `git add -A` 提交进去（建仓那次真发生了）。
#   目录名带进程号：并行流程各用各的。
BAK = os.path.join(PROJ, "build", "tmp", "zf105_falsify_bak_%d" % os.getpid())
LOG = os.path.join(ZT, "_zf105_falsify_compile.log")

fails = []


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def run_compile():
    with open(LOG, "wb") as fh:
        p = subprocess.run(["cmd", "/c",
                            "cd /d %s && .\\gradlew.bat compileJava --offline --no-build-cache" % PROJ],
                           stdout=fh, stderr=subprocess.STDOUT)
    return p.returncode


def run_gate():
    p = subprocess.run([sys.executable, os.path.join(ZT, "_zf105_regcheck.py")],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def move_touch_to_top():
    u"""真·位移：把整个 `touch()` 方法块（含 `/** ... */` javadoc 与 body）搬到第一个静态字段之前。

    ⚠ 首版这把刀写错了：它把方法**改名**成 `touch_MOVED_TO_TOP`，结果编译就挂了 ——
      拿"编译失败"当"门抓到了"是**假捕获**（§4.30 的口径：FAIL 先怀疑期望再怀疑被测物）。
      现在改成真位移：代码仍然编译通过，只有"位置"这一个语义被破坏。
    """
    path = os.path.join(SRC, "ModArmorItems.java")
    text = io.open(path, encoding="utf-8").read()
    i_doc = text.find(u"    /**\n     * **只为")
    i_sig = text.find(u"    public static void touch() {")
    if i_doc < 0 or i_sig < 0:
        return False
    i_end = text.find(u"\n    }\n", i_sig)
    if i_end < 0:
        return False
    i_end += len(u"\n    }\n")
    block = text[i_doc:i_end]
    rest = text[:i_doc] + text[i_end:]
    anchor = rest.find(u"    // ========== 星璨钢锭 ==========")
    if anchor < 0:
        anchor = rest.find(u"    public static final DeferredItem<Item> STAR_STEEL_INGOT =")
    if anchor < 0:
        return False
    io.open(path, "w", encoding="utf-8", newline=u"").write(rest[:anchor] + block + u"\n" + rest[anchor:])
    return True


# 每把刀：(名字, 变更函数, 期望门报出的关键断言)
def knife_k1():
    path = os.path.join(SRC, "PotatoST.java")
    text = io.open(path, encoding="utf-8").read()
    old = u"        ModArmorItems.touch();\n"
    if text.count(old) != 1:
        return False
    io.open(path, "w", encoding="utf-8", newline=u"").write(text.replace(old, u"", 1))
    return True


KNIVES = [
    (u"K1 删掉 PotatoST 里那行 ModArmorItems.touch();", knife_k1),
    (u"K2 把 touch() 方法块真·搬到第一个静态字段之前（编译仍通过，只破坏『位置』）",
     move_touch_to_top),
]


def main():
    only = sys.argv[1:] or None
    if os.path.isdir(BAK):
        shutil.rmtree(BAK)
    os.makedirs(BAK)

    targets = [os.path.join(SRC, "PotatoST.java"), os.path.join(SRC, "ModArmorItems.java"),
               os.path.join(CLS, "PotatoST.class"), os.path.join(CLS, "ModArmorItems.class")]
    print(u"================ 备份（逐份核副本自己的哈希）================")
    manifest = []
    for t in targets:
        if not os.path.isfile(t):
            print(u"  [SKIP] %s 不存在" % os.path.basename(t))
            continue
        dst = os.path.join(BAK, os.path.basename(t) + u"." + hashlib.md5(
            t.encode("utf-8")).hexdigest()[:8])
        shutil.copy2(t, dst)
        h = sha(dst)
        ok = sha(t) == h
        manifest.append((t, dst, h))
        print(u"  [%s] %-24s %s" % (u"OK" if ok else u"FAIL", os.path.basename(t), h[:16]))
        if not ok:
            fails.append(u"备份哈希不符：%s" % t)

    def restore():
        for t, dst, h in manifest:
            if not os.path.isfile(dst):
                fails.append(u"备份副本不见了：%s" % dst)
                continue
            shutil.copy2(dst, t)
            if sha(t) != h:
                fails.append(u"还原后哈希不符：%s" % t)

    print(u"")
    print(u"================ 逐刀 ================")
    for name, mutate in KNIVES:
        if only and not any(o in name for o in only):
            continue
        paths_before = {p: sha(p) for p in (os.path.join(SRC, "PotatoST.java"),
                                            os.path.join(SRC, "ModArmorItems.java"))}
        if not mutate():
            print(u"  [SKIP] %s —— 变更函数找不到锚点" % name)
            fails.append(u"锚点不唯一：%s" % name)
            continue
        rc_c = run_compile()
        rc_g, out = run_gate()
        caught = (rc_g != 0)
        # ⚠ 编译**必须通过** —— 否则"门抓到"其实是"编译挂了"，是假捕获（§4.30）
        honest = caught and rc_c == 0
        print(u"  [%s] %s" % (u"OK" if honest else u"FAIL", name))
        print(u"         ↳ 编译退出码 %s（必须 0），门退出码 %s（必须非 0）" % (rc_c, rc_g))
        for l in [l for l in out.split(u"\n") if l.strip().startswith(u"!!")][:3]:
            print(u"         ↳ %s" % l.strip()[:110])
        if not honest:
            fails.append(name)
        restore()
        run_compile()
        rc_g2, _ = run_gate()
        back = all(sha(p) == h for p, h in paths_before.items())
        print(u"         ↳ 还原后哈希一致 %s，门回到全绿 %s"
              % (u"✓" if back else u"✗", u"✓" if rc_g2 == 0 else u"✗"))
        if not (back and rc_g2 == 0):
            fails.append(u"还原失败：%s" % name)
        print(u"")

    print(u"================ 收尾 ================")
    for t, _dst, h in manifest:
        same = sha(t) == h
        print(u"  [%s] %s 回到备份哈希" % (u"OK" if same else u"FAIL", os.path.basename(t)))
        if not same:
            fails.append(u"收尾哈希不符：%s" % t)

    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
