# -*- coding: utf-8 -*-
u"""_zf134_falsify.py —— **本轮自己的反证刀**：证明 `_zf134_verify.py` 真的会失败

档案 §4.17：「能失败的检查」才算检查。
本轮只有一张配方，所以刀都砍在**那张图纸最容易被写错的地方**——而它们全都是
"游戏里只是做不出来、不报任何错"的那一类：

  K1 材料那格换成铁锭（忘了换材料 = 用户要的那件事没做）
  K2 图纸少一行（写成 2 行）
  K3 第三行第一格补上（空槽被填掉）
  K4 两根木棍错列
  K5 手改盘上 JSON 的产物数量（不改生成器表）—— 砍的是 §4.93 那条"表与盘逐字节一致"
  K6 生成器表里那条被删掉（盘上还在）
  K7 配方文件被删

本轮的刀**不需要重编**（全是 JSON / 生成器表的编辑），所以跑得很快。

跑法：
    $env:PYTHONIOENCODING='utf-8'
    python build/zftools/_zf134_falsify.py            # 全部
    python build/zftools/_zf134_falsify.py K3 K5      # 只跑名字里含 K3/K5 的
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
ZT = os.path.join(PROJ, "build", "zftools")
BAK = os.path.join(PROJ, "build", "tmp", "zf134_falsify_bak_%d" % os.getpid())
RECIPE = os.path.join(PROJ, r"src\main\resources\data\potato_s_t\recipe\star_steel_axe.json")
GEN = os.path.join(ZT, u"_zf45_recipes.py")

fails = []

# 每把刀：(名字, 文件, 原文, 改成, 整份重写吗)
KNIVES = [
    (u"K1 材料那格换成铁锭（用户要的「换成星璨钢」没做）",
     RECIPE, u'"item": "potato_s_t:star_steel_ingot"', u'"item": "minecraft:iron_ingot"', False),
    (u"K2 图纸少写一行（三行写成两行）",
     RECIPE, u'    "XX",\n    "X#",\n    " #"\n', u'    "XX",\n    "X#"\n', False),
    (u"K3 第三行第一格的空槽被补上（「 #」写成「X#」）",
     RECIPE, u'    " #"\n', u'    "X#"\n', False),
    (u"K4 两根木棍错列（「 #」写成「# 」）",
     RECIPE, u'    " #"\n', u'    "# "\n', False),
    (u"K5 手改盘上 JSON 的产物数量（不改生成器表）—— 砍 §4.93",
     RECIPE, u'"count": 1', u'"count": 4', False),
    (u"K6 生成器表里那条被删掉（盘上还在）",
     GEN, u'    dict(name="star_steel_axe", category="equipment",\n'
           u'         result=("potato_s_t:star_steel_axe", 1),\n'
           u'         pattern=["XX", "X#", " #"],\n'
           u'         key={"X": ("item", "potato_s_t:star_steel_ingot"),\n'
           u'              "#": ("item", "minecraft:stick")}),\n', u'', False),
    (u"K7 配方文件被删",
     RECIPE, None, None, False),
]


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def run_verify():
    p = subprocess.run([sys.executable, os.path.join(ZT, u"_zf134_verify.py")],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


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
        print(u"  [OK]   %-24s %s" % (os.path.basename(t), h[:16]))

    def restore():
        for t, dst, h in manifest:
            if not os.path.isfile(dst):
                fails.append(u"备份副本不见了：%s" % dst)
                print(u"         ↳ [FAIL] 备份副本不见了：%s" % dst)
                continue
            shutil.copy2(dst, t)
            if sha(t) != h:
                fails.append(u"还原后哈希不符：%s" % t)

    # 基线必须是绿的，否则后面分不清是谁咬住的
    rc0, out0 = run_verify()
    print(u"\n基线：探针退出码 %s（必须 0）" % rc0)
    if rc0 != 0:
        print(u"  [FAIL] 基线不是绿的，先修好再做反证")
        print(u"\n".join(l for l in out0.split(u"\n") if l.strip().startswith(u"!!"))[:800])
        return 1

    print(u"\n================ 逐刀 ================")
    for name, path, old, new, _rewrite in KNIVES:
        if only and not any(o in name for o in only):
            continue
        before = sha(path) if os.path.isfile(path) else None
        if before is None:
            print(u"  [SKIP] %s —— 目标文件不存在" % name)
            fails.append(u"目标缺失：%s" % name)
            continue
        if old is None:                      # K7：删文件
            os.remove(path)
        else:
            text = io.open(path, encoding="utf-8").read()
            if text.count(old) != 1:
                print(u"  [FAIL] %s —— 锚点命中 %d 次（应为 1）" % (name, text.count(old)))
                fails.append(u"锚点不唯一：%s" % name)
                continue
            io.open(path, "w", encoding="utf-8", newline=u"").write(text.replace(old, new))

        rc, out = run_verify()
        caught = (rc != 0)
        print(u"  [%s] %s" % (u"OK" if caught else u"FAIL", name))
        print(u"         ↳ 探针退出码 %s（要求非 0）" % rc)
        for l in [x for x in out.split(u"\n") if x.strip().startswith(u"!!")][:2]:
            print(u"         ↳ %s" % l.strip()[:110])
        if not caught:
            fails.append(name)

        restore()
        rc2, out2 = run_verify()
        if before is None:
            back = os.path.isfile(path)
        else:
            back = os.path.isfile(path) and sha(path) == before
        print(u"         ↳ 还原后%s %s，探针回到全绿 %s"
              % (u"文件回来了" if before is None else u"哈希一致",
                 u"✓" if back else u"✗", u"✓" if rc2 == 0 else u"✗"))
        if not (back and rc2 == 0):
            fails.append(u"还原失败：%s" % name)
        print(u"")

    print(u"================ 收尾 ================")
    for t, _dst, h in manifest:
        same = os.path.isfile(t) and sha(t) == h
        print(u"  [%s] %s 回到备份状态" % (u"OK" if same else u"FAIL", os.path.basename(t)))
        if not same:
            fails.append(u"收尾哈希不符：%s" % t)

    # 顺手核一下盘上还是合法的 JSON（防止哪把刀把文件写坏还"还原成功"）
    try:
        json.loads(io.open(RECIPE, encoding="utf-8").read())
        print(u"  [OK]   star_steel_axe.json 仍是合法 JSON")
    except Exception as e:
        print(u"  [FAIL] star_steel_axe.json 解析不了：%s" % e)
        fails.append(u"收尾 JSON 坏了")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
