# -*- coding: utf-8 -*-
u"""_zf186_falsify.py —— ZF186 的**反证刀**：砍一刀，`_zf186_verify.py` 必须当场变红。

刀刀都砍在"本轮真正做的事"上：配置默认值 / 兜底取值 / 注册 / 依赖清单 / 客户端隔离 /
三个点名项的接线 / 两个开关独立 / 五语种键齐。

跑法：python build\\zftools\\_zf186_falsify.py
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
SRC = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
GATE = os.path.join(ZT, u"_zf186_verify.py")
TMP = os.path.join(ZT, u"_zf186_falsify_bak")

CFG = os.path.join(SRC, u"PotatoSTConfig.java")
GRAV = os.path.join(SRC, u"GravityDeviceItem.java")
HOLE = os.path.join(SRC, u"BlackHoleManager.java")
BATT = os.path.join(SRC, u"LithiumBatteryBlockEntity.java")
MAIN = os.path.join(SRC, u"PotatoST.java")
SCREEN = os.path.join(SRC, u"client", u"PotatoSTConfigScreen.java")
TOML = os.path.join(ROOT, r"src\main\resources\META-INF\neoforge.mods.toml")
LANG_EN = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang\en_us.json")

KNIVES = [
    dict(id=u"K1", why=u"把「蓄力默认 30 秒」改回 25 秒（A1 的默认值表要抓到）", path=CFG,
         old=u'.defineInRange("charge_seconds", 30, 5, 60);',
         new=u'.defineInRange("charge_seconds", 25, 5, 60);', want=u"A1"),
    dict(id=u"K2", why=u"兜底判据去掉 isLoaded（A2 要抓到：配置没加载就会抛异常）", path=CFG,
         old=u"return SPEC != null && SPEC.isLoaded();", new=u"return SPEC != null;", want=u"A2"),
    dict(id=u"K3", why=u"主类不注册配置（A3 要抓到）", path=MAIN,
         old=u"        net.neoforged.fml.ModList.get().getModContainerById(MODID)\n"
             u"                .ifPresent(c -> c.registerConfig(net.neoforged.fml.config.ModConfig.Type.COMMON,\n"
             u"                        PotatoSTConfig.SPEC));",
         new=u"        // 刀口：故意不注册（反证用）", want=u"A3"),
    dict(id=u"K4", why=u"给 mods.toml 加一条**必需**依赖（A4「依赖一个字没加」要抓到）", path=TOML,
         old=u"[[dependencies.potato_s_t]]",
         new=u"[[dependencies.potato_s_t]]\nmodId=\"zf186_fake\"\ntype=\"required\"\nversionRange=\"[1,)\"\nordering=\"NONE\"\nside=\"BOTH\"\n\n[[dependencies.potato_s_t]]",
         want=u"A4"),
    dict(id=u"K5", why=u"配置界面类不再限定客户端（A5 要抓到：服务端也会加载它）", path=SCREEN,
         old=u"@EventBusSubscriber(modid = PotatoST.MODID, value = Dist.CLIENT)",
         new=u"@EventBusSubscriber(modid = PotatoST.MODID)", want=u"A5"),
    dict(id=u"K6", why=u"把 CAPACITY 常量写回去（B1「常量删干净」要抓到）", path=GRAV,
         old=u"    /** 每多少 tick 报一次进度（顺带一声「充能」）。 */",
         new=u"    public static final int CAPACITY = 8_000_000;\n\n"
             u"    /** 每多少 tick 报一次进度（顺带一声「充能」）。 */", want=u"B1"),
    dict(id=u"K7", why=u"损坏那一刀不再看配置（B2 点名①要抓到）", path=GRAV,
         old=u"        if (PotatoSTConfig.oneShotBlackHole()) {\n"
             u"            stack.hurtAndBreak(stack.getMaxDamage(), player, EquipmentSlot.MAINHAND);\n        }",
         new=u"        stack.hurtAndBreak(stack.getMaxDamage(), player, EquipmentSlot.MAINHAND);",
         want=u"B2"),
    dict(id=u"K8", why=u"黑洞寿命写死回 400 tick（B3 要抓到）", path=HOLE,
         old=u"            if (hole.age >= lifetime()) {", new=u"            if (hole.age >= 400) {",
         want=u"B3"),
    dict(id=u"K9", why=u"把 PER_BLOCK 常量写回锂电池（B4 点名③要抓到）", path=BATT,
         old=u"    /** 单块容量（FE）—— 0.14 ZF186 起由配置给，默认 4M（= 老常量）。 */",
         new=u"    public static final long PER_BLOCK = 4_000_000L;\n\n"
             u"    /** 单块容量（FE）—— 0.14 ZF186 起由配置给，默认 4M（= 老常量）。 */", want=u"B4"),
    dict(id=u"K10", why=u"两个开关又嵌套起来（B5 要抓到：关吸生物会把伤害也关掉）", path=HOLE,
          old=u"        if (!pull && !hurt) {", new=u"        if (!pull) {", want=u"B5"),
    dict(id=u"K11", why=u"删掉 en_us 里一个配置界面键（C1 键齐要抓到）", path=LANG_EN,
          old=u'  "potato_s_t.configuration.black_hole.one_shot": "One-shot black hole",\n',
          new=u"", want=u"C1"),
]


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_gate():
    r = subprocess.run([sys.executable, GATE], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=300)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def main():
    # 先确认"不砍的时候门是绿的（除了 D2 那种打包前的账）"，否则反证没有意义
    rc0, out0 = run_gate()
    pre_red = [l.strip() for l in out0.split(u"\n") if l.strip().startswith(u"!!")]
    print(u"砍之前：rc=%d，红 %d 条：%s" % (rc0, len(pre_red), pre_red))

    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)
    ok, bad = 0, []
    for k in KNIVES:
        path = k[u"path"]
        bak = os.path.join(TMP, k[u"id"] + u"__" + os.path.basename(path))
        shutil.copy2(path, bak)
        before = sha1(path)
        cut = True
        try:
            text = io.open(path, encoding="utf-8", newline=u"").read()
            if k[u"old"] not in text:
                cut = False
                bad.append(k[u"id"] + u"(锚点找不到)")
                print(u"  [FAIL] %s 刀砍不下去 —— %s" % (k[u"id"], k[u"why"]))
            else:
                io.open(path, "w", encoding="utf-8", newline=u"").write(
                    text.replace(k[u"old"], k[u"new"], 1))
            if cut:
                rc, out = run_gate()
                caught = [l.strip() for l in out.split(u"\n")
                          if l.strip().startswith(u"[FAIL]") and k[u"want"] in l]
                new_red = len([l for l in out.split(u"\n") if l.strip().startswith(u"!!")])
                if rc != 0 and caught and new_red > len(pre_red):
                    ok += 1
                    print(u"  [OK]   %s 门红了（红 %d→%d），抓到：%s"
                          % (k[u"id"], len(pre_red), new_red, caught[0][:56]))
                else:
                    bad.append(k[u"id"])
                    print(u"  [FAIL] %s 门没抓到（rc=%d，红 %d→%d，想看到 %s）"
                          % (k[u"id"], rc, len(pre_red), new_red, k[u"want"]))
        finally:
            if cut:
                shutil.copy2(bak, path)
            if sha1(path) != before:
                bad.append(k[u"id"] + u"(还原不一致)")
    print(u"\n反证刀：%d/%d 抓到（漏网 %s）" % (ok, len(KNIVES), u" / ".join(bad) if bad else u"无"))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
