# -*- coding: utf-8 -*-
u"""_zf72_falsify.py —— ZF72 反证：把「真值」改坏，校验**必须**挂

四类各来一刀，其中两刀砍在**源码**上：

  1. 规划文档里的原版事实（`chance 200` → `250`）        ⇒ C3 必须 FAIL
  2. 规划文档里的**规格原句**（`3000mB` → `3500mB`）      ⇒ A9 必须 FAIL（证明逐字存档是真断言）
  3. 档案里的锚点（`### 4.44` → `### 4.45`）              ⇒ E1 必须 FAIL
  4. **源码**：`TankContents.CAPACITY = 3500` → `3600`    ⇒ B1 必须 FAIL（文档那句 3500 与代码绑死）
  5. **源码**：泵的 `instanceof LiquidBlock` → 换个类型    ⇒ B12b 必须 FAIL（待决 11 的前提是真的）

每一刀都**先读原文到内存、改坏、跑校验、再按字节还原**，还原后核 SHA1 与改前完全相同；
只要有一刀「改坏了校验却不挂」，脚本自己报 FAIL —— 那说明断言是摆设。
"""
import hashlib
import io
import os
import subprocess
import sys

PROJ = r"E:\PotatoST"
VERIFY = os.path.join(PROJ, u"build", u"zftools", u"_zf72_verify.py")
DOC = os.path.join(PROJ, u"docs", u"v0.11规划.md")
ARCH = os.path.join(PROJ, u"docs", u"开发档案.md")
TANK = os.path.join(PROJ, u"src", u"main", u"java", u"com", u"potatost", u"mod", u"TankContents.java")
PUMP = os.path.join(PROJ, u"src", u"main", u"java", u"com", u"potatost", u"mod",
                    u"FluidPumpBlockEntity.java")

CASES = [
    (u"1 规划文档 · 原版事实（chance 200 → 250）", DOC,
     u"`rarity_filter: chance 200`", u"`rarity_filter: chance 250`", u"C3"),
    (u"2 规划文档 · 规格原句（3000mB → 3500mB）", DOC,
     u"单个油桶为3000mB的容积", u"单个油桶为3500mB的容积", u"A9"),
    (u"3 开发档案 · 雷条编号（4.44 → 4.45）", ARCH,
     u"### 4.44", u"### 4.45", u"E1"),
    (u"4 源码 · 气罐容量（3500 → 3600）", TANK,
     u"CAPACITY = 3500", u"CAPACITY = 3600", u"B1"),
    (u"5 源码 · 泵的液体方块判定", PUMP,
     u"instanceof LiquidBlock)", u"instanceof WaterLiquidBlock)", u"B12b"),
]


def sha1_bytes(data):
    return hashlib.sha1(data).hexdigest()


def run_verify():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run([sys.executable, u"-X", u"utf8", VERIFY],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    out = proc.stdout.decode("utf-8", "replace")
    return proc.returncode, out


def main():
    bad = []
    print(u"反证开始：%d 刀\n" % len(CASES))
    for label, path, old, new, expect in CASES:
        with io.open(path, "rb") as fh:
            original = fh.read()
        before_sha = sha1_bytes(original)
        text = original.decode("utf-8")
        hits = text.count(old)
        if hits != 1:
            bad.append(u"%s：锚点命中 %d 次，无法反证" % (label, hits))
            print(u"  [SKIP] %s（锚点 %d 次）" % (label, hits))
            continue
        try:
            with io.open(path, "wb") as fh:
                fh.write(text.replace(old, new, 1).encode("utf-8"))
            rc, out = run_verify()
            caught = (rc != 0) and any((u"[FAIL]" in ln and expect in ln)
                                       for ln in out.split(u"\n"))
            first_fail = u""
            for ln in out.split(u"\n"):
                if u"[FAIL]" in ln:
                    first_fail = ln.strip()
                    break
            if caught:
                print(u"  [OK]   %s ⇒ 校验挂在这条: %s" % (label, first_fail))
            else:
                bad.append(u"%s：改坏了却没挂（rc=%d）" % (label, rc))
                print(u"  [FAIL] %s ⇒ 校验没抓到（rc=%d）" % (label, rc))
        finally:
            with io.open(path, "wb") as fh:
                fh.write(original)
            restored_sha = sha1_bytes(open(path, "rb").read())
            same = restored_sha == before_sha
            print(u"         还原: %s  %s" % (u"逐字节相同" if same else u"!! 不一致",
                                            restored_sha[:12]))
            if not same:
                bad.append(u"%s：还原后哈希不一致！" % label)

    print(u"\n--- 反证后复跑一遍校验（应当全绿） ---")
    rc, out = run_verify()
    tail = [ln for ln in out.split(u"\n") if u"检查项 =" in ln]
    print(u"  " + (tail[0].strip() if tail else u"(没拿到汇总行)"))
    if rc != 0:
        bad.append(u"还原后校验仍然不绿（rc=%d）" % rc)

    print(u"\n反证刀数 = %d   异常 = %d" % (len(CASES), len(bad)))
    for b in bad:
        print(u"  !! " + b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
