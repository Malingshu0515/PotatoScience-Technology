# -*- coding: utf-8 -*-
u"""_zf117_falsify.py —— ZF117 的反证刀（K138~K149，12 把）

口径同前：先确认基线绿 → 改一处语义 ⇒ 门必须 FAIL 且**咬住指定的那条检查** ⇒
逐字节还原 ⇒ 收尾回到全绿。一把刀 180 秒超时（§4.77）。

刀面覆盖这一轮说出口的每一类话：
  结构（父链 / hidden / 图标 / 「与」写成「或」）、账目（老节点被改 / 多出野文件）、
  语言（键被删 / 老键被改值 / 中文串里出现 ASCII 引号 / 状态文案退回旧数字）、
  活体数字（`_zf107_verify` 的节点数被改回去 / 往轮校验里冒出旧键数 432）。
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
ZT = os.path.join(ROOT, r"build\zftools")
ADIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\advancement")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")

GATES = {
    "zf117": os.path.join(ZT, u"_zf117_verify.py"),
    "zf107": os.path.join(ZT, u"_zf107_verify.py"),
    "zf112": os.path.join(ZT, u"_zf112_verify.py"),
}
A = lambda n: os.path.join(ADIR, n + u".json")            # noqa: E731
L = lambda n: os.path.join(LANG, n + u".json")            # noqa: E731

KNIVES = [
    # ---- 结构 ----
    dict(id="K138", gate="zf117", why=u"采油机那条的父链改挂 steel（不该是它）",
         path=A("oil_pump"), old=u'"parent": "potato_s_t:distillation"',
         new=u'"parent": "potato_s_t:steel"', expect=u"B1 oil_pump 的父链"),
    dict(id="K139", gate="zf117", why=u"星轨坠那条不再隐藏（彩蛋位变成明面）",
         path=A("starfall"), old=u'"hidden": true', new=u'"hidden": false',
         expect=u"B4 starfall 的 hidden"),
    dict(id="K140", gate="zf117", why=u"海盐那条的图标换成不在判据里的物品",
         path=A("salt"), old=u'"id": "potato_s_t:sea_salt"',
         new=u'"id": "potato_s_t:star_steel_ingot"', expect=u"B2 salt 的图标"),
    dict(id="K141", gate="zf117", why=u"星璨钢套装四条判据并成一组（「与」写成「或」）",
         path=A("star_steel_armor"),
         old=(u'  "requirements": [\n    [\n      "got0"\n    ],\n    [\n      "got1"\n    ],\n'
              u'    [\n      "got2"\n    ],\n    [\n      "got3"\n    ]\n  ],'),
         new=(u'  "requirements": [\n    [\n      "got0",\n      "got1",\n      "got2",\n'
              u'      "got3"\n    ]\n  ],'),
         expect=u"B12 star_steel_armor 是「与」"),
    # ---- 账目 ----
    dict(id="K142", gate="zf117", why=u"动了一份老节点（给 acid.json 换个 frame）",
         path=A("acid"), old=u'"frame": "goal"', new=u'"frame": "task"',
         expect=u"A4 27 份老节点"),
    dict(id="K143", gate="zf117", why=u"目录里多塞一份野 advancement",
         path=os.path.join(ADIR, u"zz_junk.json"),
         mode="create", content=u'{\n  "display": {}\n}\n',
         expect=u"A1 advancement 目录正好 35 份"),
    dict(id="K144", gate="zf117", why=u"删掉一条语言键（星轨坠的说明）",
         path=L("zh_cn"), mode="line",
         old=u'"advancements.potato_s_t.starfall.description":',
         expect=u"D1 四语言各 448 键"),
    # ---- 语言 ----
    dict(id="K145", gate="zf117", why=u"把老键（硫）的值改掉",
         path=L("en_us"), old=u'"item.potato_s_t.sulfur":  "Sulfur"',
         new=u'"item.potato_s_t.sulfur":  "Sulphur"',
         expect=u"D7 en_us：老键里只有状态文案那一处被改值"),
    dict(id="K146", gate="zf117", why=u"成就说明里塞一个 ASCII 双引号",
         path=L("zh_cn"),
         old=u'"advancements.potato_s_t.oil_pump.title":  "海底油田",',
         new=u'"advancements.potato_s_t.oil_pump.title":  "海底\\"油田",',
         expect=u"D4 成就文案里没有 ASCII 双引号"),
    dict(id="K147", gate="zf112", why=u"状态文案退回 ZF115 的旧数字（1 mB → 10 mB）",
         path=L("ru_ru"),
         old=u'"\\u043d\\u0435 \\u0445\\u0432\\u0430\\u0442\\u0430\\u0435\\u0442"',  # 占位，见下面的 K147_*
         new=u'"\\u043d\\u0435 \\u0445\\u0432\\u0430\\u0442\\u0430\\u0435\\u0442"',
         expect=u"状态文案念的是每 tick 1 mB"),
    # ---- 活体数字 ----
    dict(id="K148", gate="zf117", why=u"`_zf107_verify.py` 的节点数改回 27",
         path=os.path.join(ZT, u"_zf107_verify.py"), old=u"EXPECT_NODES = 35",
         new=u"EXPECT_NODES = 27", expect=u"E4 `_zf107_verify.py` 的 EXPECT_NODES = 35"),
    dict(id="K149", gate="zf117", why=u"往轮校验里冒出旧键数 432",
         path=os.path.join(ZT, u"_zf100_verify.py"), old=u"EXPECT_KEYS = 448",
         new=u"EXPECT_KEYS = 432", expect=u"E1 21 份往轮校验里没有残留旧键数 432"),
]

# K147 的锚点单独写：俄语那句在盘上是**真西里尔字母**（`ensure_ascii=False` 写出来的），
# 不是 \uXXXX 转义 —— 第一版我按转义写，锚点当然命中 0 次（反证刀自己的账要算准）。
K147_OLD = u'"Не хватает серной кислоты: 1 mB за тик (600 mB на партию)"'
K147_NEW = u'"Не хватает серной кислоты: 10 mB за тик (6000 mB на партию)"'

fails = []


def run_gate(key):
    p = GATES[key]
    try:
        r = subprocess.run([sys.executable, p], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=300)
        return r.returncode, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 99, u"**超时**"


def summary(out):
    line = [l for l in out.split(u"\n") if (u"通过" in l and u"失败" in l)
            or (u"失败 = " in l)]
    return line[-1].strip() if line else u"?"


def main():
    # ---- 基线 ----
    for key in ("zf117", "zf112"):
        rc, out = run_gate(key)
        print(u"基线 %-6s %s（退出码 %d）" % (key, summary(out), rc))
        if rc != 0:
            print(u"  [STOP] 基线不绿，先修")
            for l in out.split(u"\n"):
                if l.strip().startswith(u"!!"):
                    print(u"    " + l.strip())
            return 1

    n_ok = 0
    for k in KNIVES:
        path = k["path"]
        orig = open(path, "rb").read() if os.path.exists(path) else None
        before = hashlib.sha1(orig).hexdigest() if orig is not None else u"(不存在)"
        mode = k.get("mode", "replace")
        if k["id"] == "K147":
            old, new = K147_OLD, K147_NEW
        else:
            old, new = k.get("old"), k.get("new")
        try:
            if mode == "create":
                if orig is not None:
                    fails.append(u"%s：目标文件已存在，不敢覆盖" % k["id"])
                    continue
                io.open(path, "w", encoding="utf-8", newline=u"\n").write(k["content"])
            elif mode == "line":
                text = orig.decode("utf-8")
                lines = [l for l in text.split(u"\n") if not l.strip().startswith(old)]
                if len(lines) == len(text.split(u"\n")):
                    fails.append(u"%s：要删的行没找到" % k["id"])
                    continue
                open(path, "wb").write(u"\n".join(lines).encode("utf-8"))
            else:
                text = orig.decode("utf-8")
                if text.count(old) != 1:
                    fails.append(u"%s：锚点命中 %d 次" % (k["id"], text.count(old)))
                    continue
                open(path, "wb").write(text.replace(old, new, 1).encode("utf-8"))
            rc, out = run_gate(k["gate"])
        finally:
            if orig is None:
                if os.path.exists(path):
                    os.remove(path)
            else:
                open(path, "wb").write(orig)
        after = hashlib.sha1(open(path, "rb").read()).hexdigest() if os.path.exists(path) else u"(不存在)"
        if after != before:
            fails.append(u"%s：还原失败" % k["id"])
            break
        if rc != 0 and k["expect"] in out:
            n_ok += 1
            print(u"  [OK]   %s %s ⇒ 咬住「%s」（%s）" % (k["id"], k["why"], k["expect"], k["gate"]))
        else:
            print(u"  [BAD]  %s %s（退出码 %d，咬住的检查没出现）" % (k["id"], k["why"], rc))
            fails.append(u"%s %s ⇒ %s" % (k["id"], k["why"],
                                          u"门还是绿的" if rc == 0 else u"咬错了检查"))

    # ---- 收尾 ----
    for key in ("zf117", "zf112", "zf107"):
        rc, out = run_gate(key)
        print(u"收尾 %-6s %s（退出码 %d）" % (key, summary(out), rc))
        if rc != 0 and key != "zf107":
            fails.append(u"收尾 %s 不是全绿" % key)
        if key == "zf107":
            bad = [l for l in out.split(u"\n") if l.strip().startswith(u"!!")
                   and u"448 键" not in l]
            if bad:
                fails.append(u"收尾 zf107 有非预期失败：%s" % bad[:2])
    print(u"刀 = %d，咬住 = %d，失败项 = %d" % (len(KNIVES), n_ok, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
