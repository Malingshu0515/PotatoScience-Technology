# -*- coding: utf-8 -*-
"""_zf65_publish.py —— ZF65 出成品（循环音停不下来的 bug 修复）

⚠ 沿用 ZF63 的教训：**先查完、全过才拷**（那个脚本先拷再报错，害我虚报过一次）。
"""
import hashlib
import io
import json
import os
import shutil
import sys
import zipfile

SRC = r"E:\PotatoST\build\libs\potato_s_t-0.10.jar"
DST = r"E:\PotatoST\release\PotatoST-0.10.jar"
SHA = DST + ".sha1"
OGG_SRC = r"E:\PotatoST\src\main\resources\assets\potato_s_t\sounds\alloy_smelter_running.ogg"
OLD_JAR = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf64_pre\新增文件\release\PotatoST-0.10.jar"
VOID = "c305c922c307253c2432623c8a8bc6f8d6233cfe"      # ZF64 那一版，本轮作废

# 这三个 class 必须与 ZF64 那版**不一样** —— 否则说明修复根本没进成品
CHANGED = [
    "com/potatost/mod/AlloySmelterBlockEntity.class",
    "com/potatost/mod/client/sound/MachineRunningSound.class",
]

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    if not os.path.isfile(SRC):
        return u"源 jar 不存在: %s" % SRC

    old = sha1(DST) if os.path.isfile(DST) else u"(无)"
    print(u"旧 release jar    : %s  (%d B)" % (old, os.path.getsize(DST) if os.path.isfile(DST) else 0))
    print(u"应当作废的旧 SHA1 : %s" % VOID)
    if old != VOID:
        fails.append(u"release 里的旧 jar 不是 ZF64 那一版（%s）" % old)

    with zipfile.ZipFile(SRC) as z:
        names = z.namelist()
        if [n for n in names if "Check" in n]:
            fails.append(u"新 jar 里混进了探针类")
        if [n for n in names if n.startswith("mezz/")]:
            fails.append(u"新 jar 里混进了 JEI 的东西（红线）")

        if os.path.isfile(OLD_JAR):
            with zipfile.ZipFile(OLD_JAR) as zo:
                for entry in CHANGED:
                    a = hashlib.sha1(z.read(entry)).hexdigest() if entry in names else u"(缺)"
                    b = hashlib.sha1(zo.read(entry)).hexdigest() if entry in zo.namelist() else u"(缺)"
                    same = a == b
                    if same:
                        fails.append(u"%s 与 ZF64 那版一模一样 ⇒ 修复没进成品" % entry.split("/")[-1])
                    print(u"  %-38s ZF64 %s  ZF65 %s  %s"
                          % (entry.split("/")[-1], b[:12], a[:12], u"相同(!!)" if same else u"已改"))
        else:
            fails.append(u"找不到 ZF64 的存档 jar，没法对比（%s）" % OLD_JAR)

        if u"assets/potato_s_t/sounds/alloy_smelter_running.ogg" not in names:
            fails.append(u"新 jar 里缺循环音 ogg")
        else:
            a = hashlib.sha1(z.read(u"assets/potato_s_t/sounds/alloy_smelter_running.ogg")).hexdigest()
            if a != sha1(OGG_SRC):
                fails.append(u"jar 里的 ogg 与源码树那一份不一致")

        lang = json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
        print(u"zh_cn 键数        : %d（应为 202）" % len(lang))
        if len(lang) != 202:
            fails.append(u"zh_cn 键数变了: %d" % len(lang))

    if fails:
        print(u"\n**有失败项，未拷任何文件**：")
        for f in fails:
            print(u"  !! " + f)
        return 1

    shutil.copy2(SRC, DST)
    new = sha1(DST)
    io.open(SHA, "w", encoding="ascii", newline="\n").write(new + "\n")
    print(u"新 release jar    : %s  (%d B, %d 条目)" % (new, os.path.getsize(DST), len(names)))
    print(u"sha1 文件         : %s" % io.open(SHA, encoding="ascii").read().strip())
    print(u"作废              : %s" % VOID)
    print(u"失败项 = 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
