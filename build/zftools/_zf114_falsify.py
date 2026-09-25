# -*- coding: utf-8 -*-
u"""_zf114_falsify.py —— ZF114 反证：往被测代码里注入 12 个**外科式** bug，
要求 `_zf114_verify.py` **每一条都挂**，而且挂的必须是我指定的那一条断言。

为什么必须做（档案 §4.27/§4.30）：*通过的检查*与*根本验不了的检查*长得一模一样。
ZF34 出过"假失败"（断言自己写错），ZF38 出过更危险的"假通过"（注入 bug 也全绿）。

反证纪律（照 ZF57/ZF64/ZF72 的先例）：
  · 每次只动**一处**、锚点必须恰好命中 1 次；
  · 注入后必须看到**指定的那条断言**出现在失败列表里（不是我随便挂一条就算数）；
  · 还原后核 sha256，**必须与改前一模一样**（ZT72 的做法：为了反证动了源码，就要证明源码回来了）。

跑法：python build\\zftools\\_zf114_falsify.py
"""
import hashlib
import io
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
CLIENT = os.path.join(JAVA, "client")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
TEX = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
VERIFY = os.path.join(ROOT, r"build\zftools\_zf114_verify.py")


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# (编号, 文件, 模式, 锚点, 替换, 期望挂掉的那条断言里的关键字)
INJECTIONS = [
    (u"J01 先撒矿后爆炸（物品会被自己的爆炸清掉）",
     os.path.join(JAVA, "StarfallRitualManager.java"), "swap_impact_order", None, None,
     u"D1 先爆炸"),
    (u"J02 爆炸不带火", os.path.join(JAVA, "StarfallRitualManager.java"), "literal",
     u"power, true, Level.ExplosionInteraction.BLOCK", u"power, false, Level.ExplosionInteraction.BLOCK",
     u"D2 爆炸带火"),
    (u"J03 粗矿档位从 12 放宽到 20（变成永远只出铁铜）",
     os.path.join(JAVA, "StarfallRitualManager.java"), "literal",
     u"TAG_POWER = 12", u"TAG_POWER = 20", u"C9 12 以上"),
    (u"J04 粗振金从 3 个改成 1 个", os.path.join(JAVA, "StarfallRitualManager.java"), "literal",
     u"VIBRANIUM_COUNT = 3", u"VIBRANIUM_COUNT = 1", u"C10 15 以上"),
    (u"J05 取消窗口从 10 秒砍到 5 秒", os.path.join(JAVA, "StarfallRitualManager.java"), "literal",
     u"CANCEL_TICKS = 20 * 10", u"CANCEL_TICKS = 20 * 5", u"C6 前 10 秒"),
    (u"J06 陨石不从 y=200 而是从 y=100 来", os.path.join(JAVA, "StarfallMeteorEntity.java"), "literal",
     u"SPAWN_Y = 200.0D", u"SPAWN_Y = 100.0D", u"C14 从 y=200"),
    (u"J07 HUD 挂到快捷栏下面（玩家看不见）", os.path.join(CLIENT, "..", "PotatoSTClient.java"), "literal",
     u"registerAbove(VanillaGuiLayers.HOTBAR", u"registerBelow(VanillaGuiLayers.HOTBAR", u"B6 HUD"),
    (u"J08 变成可以附魔", os.path.join(JAVA, "StarfallPendantItem.java"), "literal",
     u"    public boolean isEnchantable(ItemStack stack) {\n        return false;\n    }",
     u"    public boolean isEnchantable(ItemStack stack) {\n        return true;\n    }", u"C3 不可附魔"),
    (u"J09 忘了在构造期碰 ModEntities（§4.72 那个崩溃）", os.path.join(JAVA, "PotatoST.java"), "literal",
     u"        ModEntities.ENTITY_TYPES.register(modEventBus);\n", u"", u"B1 构造期注册"),
    (u"J10 尾迹粒子从 8 颗加到 40 颗（卡）", os.path.join(JAVA, "StarfallMeteorEntity.java"), "literal",
     u"ParticleTypes.FLAME, x, y, z, 8,", u"ParticleTypes.FLAME, x, y, z, 40,", u"E1 尾迹"),
    (u"J11 删掉一条语言键（tooltip.1，非末条）", os.path.join(LANG, "zh_cn.json"), "drop_key",
     u"tooltip.potato_s_t.starfall_pendant.1", None, u"G1 四语言键数"),
    (u"J12 贴图换成假 PNG（webp 改名那种）", os.path.join(TEX, "starfall_pendant.png"), "bytes",
     None, b"\x89PNG\r\n\x1a\nnot-a-real-png", u"F1 starfall_pendant"),
    (u"J13 语言文件被写成非法 JSON（校验不准崩栈）", os.path.join(LANG, "zh_cn.json"), "append_junk",
     None, u"\n}}}}", u"G0 zh_cn.json"),
]


def apply_injection(item):
    name, path, mode, anchor, repl, _key = item
    path = os.path.normpath(path)
    original = open(path, "rb").read()
    if mode == "bytes":
        open(path, "wb").write(repl)
        return path, original

    text = original.decode("utf-8")
    if mode == "literal":
        n = text.count(anchor)
        if n != 1:
            raise AssertionError(u"%s：锚点命中 %d 次（要求 1）" % (name, n))
        text = text.replace(anchor, repl)
    elif mode == "drop_key":
        pattern = re.compile(u'^    "%s":.*\n' % re.escape(anchor), re.M)
        text, n = pattern.subn(u"", text)
        if n != 1:
            raise AssertionError(u"%s：要删的键命中 %d 次（要求 1）" % (name, n))
    elif mode == "append_junk":
        text = text + repl
    elif mode == "swap_impact_order":
        # 把"喷射粗矿"那一段整体搬到 explode 之前 —— 最忠实地模拟"先撒后炸"
        start = text.index(u"        // ③ 喷射粗矿")
        end = text.index(u"        // ④ 通知施法者收尾")
        block = text[start:end]
        text = text[:start] + text[end:]
        explode_at = text.index(u"        // ① 爆炸（带火")
        text = text[:explode_at] + block + text[explode_at:]
    else:
        raise AssertionError(u"未知注入模式 %s" % mode)
    open(path, "wb").write(text.encode("utf-8"))
    return path, original


def run_verify():
    proc = subprocess.run([sys.executable, VERIFY], capture_output=True)
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace")
    lines = [l for l in (out + err).splitlines() if l.strip().startswith(u"!!")]
    return proc.returncode, lines


def main():
    print(u"=== 反证：12 次注入，每次必须让 _zf114_verify.py 挂，而且要挂对那一条 ===")
    code0, lines0 = run_verify()
    print(u"   基线：退出码 %d，失败 %d 条（应当 0）" % (code0, len(lines0)))
    if code0 != 0:
        print(u"   [FAIL] 基线就不干净，反证无意义")
        return 1

    ng = 0
    for item in INJECTIONS:
        name = item[0]
        expect = item[5]
        path, original = apply_injection(item)
        before = hashlib.sha256(original).hexdigest()
        try:
            code, lines = run_verify()
            hit = any(expect in l for l in lines)
            caught = (code != 0) and hit
            print(u"   %-46s 注入后失败 %2d 条，命中「%s」= %s  ⇒ %s"
                  % (name, len(lines), expect, u"是" if hit else u"否", u"[OK] 抓住了" if caught else u"[FAIL] 没抓住"))
            if not caught:
                ng += 1
                for l in lines[:4]:
                    print(u"        %s" % l)
        finally:
            open(path, "wb").write(original)
            restored = sha(path)
            if restored != before:
                print(u"   [FAIL] %s 还原后 sha256 不一致！" % name)
                ng += 1
            else:
                print(u"        └ 还原并核 sha256 ✓ %s" % restored[:12])

    code1, lines1 = run_verify()
    print(u"   收尾：退出码 %d，失败 %d 条（应当回到 0）" % (code1, len(lines1)))
    if code1 != 0:
        ng += 1
    print(u"反证结论：%s（未抓住 / 还原失败 = %d）" % (u"全部抓住" if ng == 0 else u"有问题", ng))
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
