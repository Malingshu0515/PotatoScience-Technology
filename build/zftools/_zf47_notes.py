# -*- coding: utf-8 -*-
"""写 zf47_pre 的 _说明.txt"""
import hashlib
import io
import os
import time

BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf47_pre"

TEXT = u"""\
ZF47 备份说明（阶段目录 zf47_pre）
=====================================
建立时刻：{now}
建立时机：**动手之前**（§10）

本阶段做了什么
--------------
用户原话：「耐热金属块加一个配方；【铁板】【高碳钢】【铁板】，【热力金属】【一般金属块】【热力金属】，
【铁板】【高碳钢】【铁板】」

新增一个配方：
    PSP      P = 铁板 iron_plate
    TMT      S = 高碳钢 high_carbon_steel
    PSP      T = 热力金属 thermal_metal
             M = 一般金属块 common_metal_block
    ⇒ 1 个 heat_resistant_metal_block（耐热金属块）

这块方块 **ZF34 就注册了、一直没有配方**，本阶段补上。

做法（没写新代码）
------------------
把图纸加进 ZF45 那个生成器 `_zf45_recipes.py` 的 RECIPES 表里再重跑：
  · 白拿"物品 id 真实存在"的机械核对（本模组查注册、原版查 client.jar 的 item 模型）；
  · 生成器可复现 —— 重跑后**另外 14 份配方文件的 SHA256 一字未变**（已核对）。

目录里都有什么
--------------
  _改前_PotatoST-0.10.jar  SHA1 = ec9382087d291a48e9194cbb6a24842d1c035df0（本阶段结束后作废）
  _改后_PotatoST-0.10.jar  SHA1 = {new_sha1}
                           大小 = {new_size} 字节
  改后_*                   改完后的样子
  新增文件\\                9 份：新配方 JSON + 3 个脚本 + 探针源码 + 2 份取证 + 检查日志
  _sha256_改后与新增.txt    每一份的 SHA256 + 一致性

自检与取证
----------
  build\\zftools\\check\\RecipeProbe.java   探针源码
  build\\zftools\\check\\zf47_探针.log      17 项全 [OK]；日志里 `Loaded 1321 recipes`（+1）
  build\\zftools\\check\\zf47_反证.log      把 result.count 改成 2 ⇒ 2 项 FAIL（读数正是"x2"）
  build\\zftools\\zf47_gates.txt            七项检查全绿；RecipeCheck 定形通过 24 → 25

探针验了什么 / 没验什么（诚实说明，见档案 §4.30 末尾的补充）
-----------------------------------------------------------
  验了：15 条配方逐条能加载、产物与数量对、耐热金属块**真摆一遍调 assemble() 出 1 个**、无余料。
  没验：**原料**。探针的材料是从配方自己的 getIngredients() 取出来的 ⇒ 对原料是同义反复。
        原料的正确性由另一条独立链保证：`_zf45_recipes.py` 里那张人抄过一遍的图纸表 → 生成 JSON。
        反证也印证了这一点：改 count 能被抓到（2 项 FAIL），改原料则抓不到。

已知偏差
--------
  没有。这条配方完全照用户给的图纸实现（铁板/高碳钢/热力金属/一般金属块都是精确 id，
  按长期规则板材与化合物不属于"默认兼容别的 mod"的那一类）。

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
