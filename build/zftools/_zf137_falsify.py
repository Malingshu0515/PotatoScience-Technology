# -*- coding: utf-8 -*-
u"""_zf137_falsify.py —— **本轮自己的反证刀**：证明 `_zf137_verify.py` 真的会失败

档案 §4.17：「能失败的检查」才算检查。
这一轮加的东西很少（一句话的效果），所以刀全砍在**用户没说、但写错就变成另一种东西**的地方：

  K1 时长 100 → 500（5 s 变成 25 s）
  K2 等级 0 → 1（夜视 I 变成 II）
  K3 效果换成别的（夜视 → 水下呼吸）
  K4 判据从「头盔」放宽成「任意一件星璨钢」
  K5 给它加一个「夜晚才有」的门（用户说的是"穿戴就有"）
  K6 补充余量换成 ABSORPTION_REFRESH（变成"周期给一次" ⇒ 亮 4 秒黑 4 秒）
  K7 判据读错槽（HEAD → CHEST）
  K8 四语言里把"头盔给夜视"那句删掉（玩家看不见这条）

跑法：
    $env:PYTHONIOENCODING='utf-8'
    python build/zftools/_zf137_falsify.py            # 全部
    python build/zftools/_zf137_falsify.py K3 K6      # 只跑名字里含 K3/K6 的
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
ZT = os.path.join(PROJ, "build", "zftools")
BAK = os.path.join(PROJ, "build", "tmp", "zf137_falsify_bak_%d" % os.getpid())
CLS = os.path.join(PROJ, "build", "classes", "java", "main", "com", "potatost", "mod")
SRC = os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod")
LANG = os.path.join(PROJ, r"src\main\resources\assets\potato_s_t\lang")

fails = []

SET = os.path.join(SRC, "ModArmorSet.java")
MATS = os.path.join(SRC, "ModArmorMaterials.java")
ZH = os.path.join(LANG, "zh_cn.json")

KNIVES = [
    (u"K1 夜视时长 100 → 500（5 s 变成 25 s）",
     SET, u"HELMET_NIGHT_VISION_TICKS = 100;", u"HELMET_NIGHT_VISION_TICKS = 500;", True),
    (u"K2 等级 0 → 1（夜视 I 变成 II）",
     SET, u"NIGHT_VISION_I = 0;", u"NIGHT_VISION_I = 1;", True),
    (u"K3 效果换成别的（夜视 → 水下呼吸）",
     SET, u"ensure(player, MobEffects.NIGHT_VISION,", u"ensure(player, MobEffects.WATER_BREATHING,", True),
    (u"K4 判据从「头盔」放宽成「任意一件星璨钢」",
     SET, u"if (ModArmorMaterials.hasStarSteelHelmet(player)) {",
     u"if (ModArmorMaterials.hasAnyStarSteelPiece(player)) {", True),
    (u"K5 给它加一个「夜晚才有」的门（用户说的是穿戴就有）",
     SET, u"if (ModArmorMaterials.hasStarSteelHelmet(player)) {",
     u"if (level.isNight() && ModArmorMaterials.hasStarSteelHelmet(player)) {", True),
    (u"K6 补充余量换成 ABSORPTION_REFRESH（变成周期给一次 ⇒ 亮 4 秒黑 4 秒）",
     SET, u"HELMET_NIGHT_VISION_TICKS,\n                    KNOCKBACK_MARGIN);",
     u"HELMET_NIGHT_VISION_TICKS,\n                    ABSORPTION_REFRESH);", True),
    (u"K7 判据读错槽（HEAD → CHEST）",
     MATS, u"isMaterial(entity.getItemBySlot(EquipmentSlot.HEAD), STAR_STEEL)",
     u"isMaterial(entity.getItemBySlot(EquipmentSlot.CHEST), STAR_STEEL)", True),
    (u"K8 zh_cn 里把「头盔给夜视」那句删掉（玩家看不见这条）",
     ZH, u"夜视 I，每次 5 秒，戴着便一直续。", u"", False),
]


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def run_verify():
    p = subprocess.run([sys.executable, os.path.join(ZT, u"_zf137_verify.py")],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def run_compile(retries=3):
    u"""跑一次 `compileJava`；失败就等 5 秒重试（最多 retries 次）。

    ⚠ 为什么要重试：这棵树**同时在跑好几条线**，各自都会调 gradle。实测撞到过三种并发假红：
      · `compileJava` 直接返回 1（拿不到锁 / 被别人的构建打断），日志里一条错误都没有；
      · `compileJava UP-TO-DATE` —— 还原用的是 `copy2`，它把 mtime 一起还原成**旧值**，
        gradle 的增量判断因此认为"源没变" ⇒ 类文件还停在刀那一版、探针一直红
        （见下面 `restore()` 里那句 `os.utime`）；
      · 编译进程被系统杀掉（退出码 `4294967295` = -1）。
    重试只影响"能不能编上"，**不放松任何判据**。
    """
    log = os.path.join(ZT, u"_zf137_falsify_compile.log")
    rc = 1
    for attempt in range(retries):
        with open(log, "wb") as fh:
            p = subprocess.run(["cmd", "/c", "cd /d %s && .\\gradlew.bat compileJava --offline "
                                "--no-build-cache" % PROJ], stdout=fh, stderr=subprocess.STDOUT)
        rc = p.returncode
        if rc == 0:
            return 0
        print(u"         ↳ 第 %d 次编译退出码 %s，等 5 秒重试" % (attempt + 1, rc))
        time.sleep(5)
    return rc


def main():
    only = sys.argv[1:] or None
    if os.path.isdir(BAK):
        shutil.rmtree(BAK)
    os.makedirs(BAK)

    print(u"================ 备份 ================")
    manifest = []
    for t in sorted(set(k[1] for k in KNIVES)):
        if not os.path.isfile(t):
            print(u"  [FAIL] 备份目标不存在：%s" % t)
            fails.append(u"备份目标缺失：%s" % t)
            continue
        dst = os.path.join(BAK, os.path.basename(t))
        shutil.copy2(t, dst)
        h = sha(dst)
        manifest.append((t, dst, h))
        print(u"  [OK]   %-26s %s" % (os.path.basename(t), h[:16]))

    def restore():
        for t, dst, h in manifest:
            if not os.path.isfile(dst):
                fails.append(u"备份副本不见了：%s" % dst)
                print(u"         ↳ [FAIL] 备份副本不见了：%s" % dst)
                continue
            shutil.copy2(dst, t)
            # ⚠ `copy2` 会把 mtime 一起还原成**备份时的旧值** ⇒ gradle 的增量判断可能
            #   直接报 `compileJava UP-TO-DATE`、根本不重编 ⇒ 类文件还停在刀那一版，
            #   于是"还原后探针回到全绿"永远是 ✗（本轮真踩到，K2 之后一路假红）。
            #   把 mtime 顶到"现在"就能强制它重编。
            os.utime(t, None)
            if sha(t) != h:
                fails.append(u"还原后哈希不符：%s" % t)

    rc0, out0 = run_verify()
    print(u"\n基线：探针退出码 %s（必须 0）" % rc0)
    if rc0 != 0:
        print(u"  [FAIL] 基线不是绿的，先修好再做反证")
        print(u"\n".join(l for l in out0.split(u"\n") if l.strip().startswith(u"!!"))[:800])
        return 1

    print(u"\n================ 逐刀 ================")
    for name, path, old, new, recompile in KNIVES:
        if only and not any(o in name for o in only):
            continue
        before = sha(path) if os.path.isfile(path) else None
        if before is None:
            print(u"  [SKIP] %s —— 目标文件不存在" % name)
            fails.append(u"目标缺失：%s" % name)
            continue
        text = io.open(path, encoding="utf-8").read()
        if text.count(old) != 1:
            print(u"  [FAIL] %s —— 锚点命中 %d 次（应为 1）" % (name, text.count(old)))
            fails.append(u"锚点不唯一：%s" % name)
            continue
        io.open(path, "w", encoding="utf-8", newline=u"").write(text.replace(old, new))

        rc_c = run_compile() if recompile else 0
        rc, out = run_verify()
        caught = (rc != 0)
        # 抓到的必须是"判据不对"，不是编译失败导致的假捕获
        gate_ok = caught and (rc_c == 0 or not recompile)
        print(u"  [%s] %s" % (u"OK" if gate_ok else u"FAIL", name))
        print(u"         ↳ 编译退出码 %s，探针退出码 %s（要求非 0）" % (rc_c, rc))
        for l in [x for x in out.split(u"\n") if x.strip().startswith(u"!!")][:2]:
            print(u"         ↳ %s" % l.strip()[:110])
        if not gate_ok:
            fails.append(name)

        restore()
        if recompile:
            run_compile()
        rc2, out2 = run_verify()
        if rc2 != 0 and recompile:
            # ⚠ 本轮真踩到过一次（K3）：还原 + 重编之后探针**仍然**报"没有夜视"，
            #   而盘上源码其实已经还原（收尾哈希一致）—— 是**编译没跟上**，
            #   `build/classes` 里还是刀那一版（这个工程同时在跑好几条线，gradle 的
            #   增量判断偶尔会和"外部把文件时间戳改回旧值"打架；`copy2` 会保留 mtime）。
            #   ⇒ 再编一次复核；**两次都红才算真失败**（这条不放松判据，只是防假红）。
            print(u"         ↳ 第一次重编后探针仍红，再编一次复核")
            run_compile()
            rc2, out2 = run_verify()
        back = os.path.isfile(path) and sha(path) == before
        print(u"         ↳ 还原后哈希一致 %s，探针回到全绿 %s"
              % (u"✓" if back else u"✗", u"✓" if rc2 == 0 else u"✗"))
        if not (back and rc2 == 0):
            fails.append(u"还原失败：%s" % name)
            for l in [x for x in out2.split(u"\n") if x.strip().startswith(u"!!")][:2]:
                print(u"         ↳ %s" % l.strip()[:110])
        print(u"")

    print(u"================ 收尾 ================")
    for t, _dst, h in manifest:
        same = os.path.isfile(t) and sha(t) == h
        print(u"  [%s] %s 回到备份状态" % (u"OK" if same else u"FAIL", os.path.basename(t)))
        if not same:
            fails.append(u"收尾哈希不符：%s" % t)

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
