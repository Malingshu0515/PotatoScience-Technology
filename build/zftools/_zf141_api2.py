# -*- coding: utf-8 -*-
r"""_zf141_api2.py —— 只读：修两个编译错误要用到的真实签名。

探针第一版挂在两处（都写进了 probe.log）：
  ① `p.detectEquipmentUpdates()` —— 找不到符号 ⇒ 它多半不是 public（或不在这个类上）
  ② `Resource.openAsInputStream()` —— 不存在 ⇒ 真实方法名要现查

跑法：python build\zftools\_zf141_api2.py
"""
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SOURCES = r"E:\PotatoST\build\neoForm\neoFormJoined1.21.1-20240808.144430\sources.jar"

WANT = [
    (u"net/minecraft/world/entity/LivingEntity.java", [u"detectEquipmentUpdates"]),
    (u"net/minecraft/server/packs/resources/Resource.java", [u"public"]),
    (u"net/minecraft/server/level/ServerPlayer.java", [u"detectEquipmentUpdates", u"public void doTick"]),
    (u"net/minecraft/world/entity/player/Player.java", [u"detectEquipmentUpdates"]),
]


def main():
    zf = zipfile.ZipFile(SOURCES)
    names = zf.namelist()
    for want, marks in WANT:
        hit = [n for n in names if n.endswith(want)]
        if not hit:
            print(u"!! 没有 %s" % want)
            continue
        src = zf.read(hit[0]).decode(u"utf-8", u"replace")
        lines = src.split(u"\n")
        print(u"")
        print(u"---- %s ----" % want.split(u"/")[-1])
        for i, line in enumerate(lines, 1):
            s = line.strip()
            if not any(m in line for m in marks):
                continue
            # 只打"声明行"（带括号的），跳过纯调用
            if u"(" in s and (s.startswith(u"public") or s.startswith(u"protected")
                              or s.startswith(u"private") or s.startswith(u"@Override")
                              or s.endswith(u";")):
                print(u"  %5d | %s" % (i, s))


main()
