# -*- coding: utf-8 -*-
"""写 zf48_pre 的 _说明.txt"""
import hashlib
import io
import os
import time

BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf48_pre"

TEXT = u"""\
ZF48 备份说明（阶段目录 zf48_pre）
=====================================
建立时刻：{now}
建立时机：**动手之前**（§10）

用户原话
--------
「加入钛矿（稀有度比黄金略高）和粗钛 粗钛需要粉碎机粉碎成钛粉 6s 300fe/t
  钛粉再由电力高炉烧制出钛锭 贴图暂时都用原版铁的 钛粉用火药」

新增 5 样
---------
  block  titanium_ore            钛矿
  block  deepslate_titanium_ore  深层钛矿（⚠ 按 §6.7.1 惯例配的深层变种）
  item   raw_titanium            粗钛（钛矿掉落物）
  item   titanium_powder         钛粉（粉碎机产物）
  item   titanium_ingot          钛锭（电力高炉产物）

**一张贴图都没画**（用户指定全借原版）：
  钛矿=iron_ore、深层钛矿=deepslate_iron_ore、粗钛=raw_iron、钛锭=iron_ingot、钛粉=gunpowder
  ⇒ 这些物品**和铁长得一模一样**，只能靠名字区分。

稀有度「比黄金略高」怎么落的
----------------------------
从 client.jar 读原版金矿的**真实数值**再折算（不是拍脑袋）：
  原版金矿：每区块 4 簇(+0~1 低位) × 9 块 = 上限 45 块，空气丢弃率 0.5，高度 -64~32（梯形）
  钛矿    ：每区块 4 簇 × 8 块 = 上限 32 块，空气丢弃率 0.5，高度 -64~16（均匀）
  ⇒ 比金矿少 29%。_zf48_verify.py 会把这段算给出来，并断言比值落在 10%~35% 才算「略高」。

加工链（用户指定的唯一一条路）
------------------------------
  钛矿 → 粗钛（掉落表）
       → 钛粉（微型粉碎机：6 秒 = 120 tick、300 FE/t = **36000 FE**，1:1）
       → 钛锭（电力高炉：200 tick、**800 FE**，1:1）

目录里都有什么
--------------
  _改前_PotatoST-0.10.jar  SHA1 = 2647bd975e310c0ee9744098ef29db1fad27d058（本阶段结束后作废）
  _改后_PotatoST-0.10.jar  SHA1 = {new_sha1}
                           大小 = {new_size} 字节
  改后_* / 新增文件\\        改后 20 份 + 新增 30 份（含 5 个 c: 标签、2 个世界生成、9 个模型/blockstate）
  _sha256_改后与新增.txt    每一份的 SHA256 + 一致性

自检与取证
----------
  build\\zftools\\check\\TitaniumCheck.java  探针源码
  build\\zftools\\check\\zf48_探针.log       44 项全 [OK]（两台机器都真跑：120 tick/36000 FE、200 tick/800 FE）
  build\\zftools\\check\\zf48_反证.log       注入"粗钛→钛锭"的 blasting 配方 ⇒ 3 项 FAIL（含电力高炉当场吃掉它）
  build\\zftools\\zf48_verify.txt            盘面复核（语言/贴图是否真借原版/掉落表/稀有度实算/标签）0 失败
  build\\zftools\\zf48_regression_zf46.txt   ZF46 那套矿石复核的回归（0 失败）
  build\\zftools\\zf48_gates.txt             七项交付检查全绿

已知偏差（都写进档案 §9）
------------------------
  1. 两个 1:1 是我定的（用户只给了秒数与 FE/t）：1 粗钛 → 1 钛粉、1 钛粉 → 1 钛锭。
  2. 一个钛矿方块 → 1 钛锭，而电力高炉烧矿石方块是 3~6 锭 ⇒ **钛的单位产出偏低**（1/3~1/6）。
  3. 深层变种是按惯例加的。
  4. 挖掘等级铁镐；世界生成数值（4 簇 × 8 块 / -64~16）是我按"比黄金略高"折算的。
  5. 贴图全借原版 ⇒ 与铁/火药外观完全相同。

重建来源优先级（§10）
---------------------
  已发布 jar（字节权威） > 本目录的改后副本 > 反推 + 编译比对
"""


def main():
    new_jar = os.path.join(BK, "_改后_PotatoST-0.10.jar")
    sha1, size = u"（还没发布）", u"?"
    try:
        h = hashlib.sha1()
        with open(new_jar, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 16), b""):
                h.update(block)
        sha1 = h.hexdigest()
        size = u"{0:,}".format(os.path.getsize(new_jar))
    except IOError:
        pass
    path = os.path.join(BK, "_说明.txt")
    with io.open(path, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write(TEXT.format(now=time.strftime(u"%Y-%m-%d %H:%M:%S"), new_sha1=sha1, new_size=size))
    print(u"写出 {0}（{1} 字节）".format(path, os.path.getsize(path)))
    print(u"改后 jar SHA1 = {0}".format(sha1))


if __name__ == "__main__":
    main()
