# -*- coding: utf-8 -*-
u"""_zf186_configured_check.py —— 只读核查：本机那份「配置界面」(Configured) 到底认不认
NeoForge 的 ModConfigSpec 配置（也就是认不认我们 ZF186 刚加的那份配置）。

为什么用字节搜 class 常量池：class 文件里的类型名/字符串就是明文，
`zipfile` 读出来直接 `in` 一下就知道它有没有引用 NeoForge 的配置 API —— 不需要反编译。

跑法：python build\\zftools\\_zf186_configured_check.py
"""
import io
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
JAR = os.path.join(ROOT, "run", "client", "mods",
                   u"[配置界面] configured-neoforge-1.21.1-2.6.3.jar")

NEEDLES = {
    u"NeoForge 配置规格 ModConfigSpec": b"net/neoforged/neoforge/common/ModConfigSpec",
    u"FML 配置容器 ModConfig": b"net/neoforged/fml/config/ModConfig",
    u"配置界面工厂 IConfigScreenFactory": b"net/neoforged/neoforge/client/gui/IConfigScreenFactory",
    u"取模组容器 getCustomExtension": b"getCustomExtension",
    u"注册扩展点 registerExtensionPoint": b"registerExtensionPoint",
    u"模组列表 ModList": b"net/neoforged/fml/ModList",
}


def main():
    if not os.path.isfile(JAR):
        print(u"找不到 %s" % JAR)
        return 1
    print(u"核查对象：%s（%d 字节）" % (os.path.basename(JAR), os.path.getsize(JAR)))
    z = zipfile.ZipFile(JAR)
    names = z.namelist()
    classes = [n for n in names if n.endswith(u".class")]
    print(u"class %d ｜ 条目 %d" % (len(classes), len(names)))

    toml = u""
    for cand in (u"META-INF/neoforge.mods.toml", u"META-INF/mods.toml"):
        if cand in names:
            toml = z.read(cand).decode(u"utf-8", u"replace")
            break
    m = re.search(u'modId\\s*=\\s*"([^"]+)"', toml)
    v = re.search(u'version\\s*=\\s*"([^"]+)"', toml)
    print(u"mods.toml：modId=%s version=%s ｜ 依赖段 %d 行"
          % (m.group(1) if m else u"?", v.group(1) if v else u"?",
             len([l for l in toml.split(u"\n") if l.strip().startswith(u"modId")])))

    print(u"\n---- 常量池里有没有这些引用 ----")
    hits = {k: [] for k in NEEDLES}
    for n in classes:
        data = z.read(n)
        for label, needle in NEEDLES.items():
            if needle in data:
                hits[label].append(n)
    for label in NEEDLES:
        lst = hits[label]
        print(u"  %s：%d 个类" % (label, len(lst)))
        for x in lst[:6]:
            print(u"      %s" % x)

    print(u"\n---- 名字里带 config 的类（看它的适配层） ----")
    interesting = sorted(n for n in classes
                         if u"config" in n.lower() and u"$" not in n)
    for n in interesting[:40]:
        print(u"  %s" % n)
    z.close()
    return 0


if __name__ == u"__main__":
    sys.exit(main())
