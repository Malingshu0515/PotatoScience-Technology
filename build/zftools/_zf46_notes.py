# -*- coding: utf-8 -*-
"""写 zf46_pre 的 _说明.txt（Python 写，避开 PowerShell here-string 吃反引号的坑）。"""
import io
import os
import time

BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf46_pre"

TEXT = u"""\
ZF46 备份说明（阶段目录 zf46_pre）
=====================================
建立时刻：{now}
建立时机：**动手之前**（§10 的规矩：先备份、后改第一个字节）

本阶段做了什么
--------------
用户原话：「加入黑钨矿 和粗钨 目前不可以被任何东西冶炼」

新增（3 个注册物）：
  · 方块 `wolframite_ore`       黑钨矿（浅层）
  · 方块 `deepslate_wolframite_ore` 深层黑钨矿（⚠ 这一个是我按项目惯例加的，见下）
  · 物品 `raw_tungsten`         粗钨（黑钨矿的掉落物）

配套（照 §6.7 的加矿流程走第二次，清单固化成 12 处写进档案 §6.7.1）：
  贴图 3 张（改色得来）、blockstate 2、方块模型 2、物品模型 3、掉落表 2、
  世界生成 2（configured + placed）、biome_modifier 1、原版方块标签 2、
  c: 通用标签 7（由 GenCommonTags.py 重新生成）、四语言各 3 键。

「不可以被任何东西冶炼」怎么做的
--------------------------------
**一条冶炼配方都不加**，并且用探针在真服务端上把五条路全查了一遍：
熔炉 / 高炉 / 烟熏炉 / 营火 / 电力高炉 —— 外加"世界里真喂 64 个粗钨 + 满电跑 400 tick"。
连微型粉碎机也没给配方（用户只说了"冶炼"，这条是额外的，想放开说一声）。

目录里都有什么
--------------
  _改前_PotatoST-0.10.jar   SHA1 = 6ea6d0665bc410f3416f5a9d26d4ad79572317f9（本阶段结束后作废）
  _改后_PotatoST-0.10.jar   SHA1 = {new_sha1}
                            大小 = {new_size} 字节
                            （Audit 的 H 项复核：产物名 / mod_version / .sha1 三方一致）
  改后_*                    同一批文件改完之后的样子
  新增文件\\                 本阶段新建的 28 份（贴图/模型/掉落表/世界生成/标签/脚本/探针/取证）
                            ⚠ 其中 8 份**同名不同物**（`wolframite_ore.json` 同时是
                            blockstate / 方块模型 / 物品模型 / 掉落表），扁平归档会自动加
                            父目录名前缀（`block_` / `item_` / `blocks_`），脚本里已核对份数
  _sha256_改后与新增.txt     每一份的 SHA256 + 与项目当前文件的一致性

自检与取证
----------
  build\\zftools\\check\\TungstenCheck.java  探针源码
  build\\zftools\\check\\zf46_探针.log       42 项全 [OK]
  build\\zftools\\check\\zf46_反证.log       注入 1 条假 blasting 配方 + 删 1 条标签 ⇒ 6 项 FAIL
  build\\zftools\\zf46_verify.txt            盘面复核（键集/贴图/模型/掉落表/世界生成数值/标签）0 失败
  build\\zftools\\zf46_gates.txt             七项交付检查（Audit 0 / LangCheck 0 / RecipeCheck 0 /
                                             ModelCheck 0 / JsonCheck 0 / SoundCheck 0）

已知偏差（都写进档案 §9）
------------------------
  1. **深层变种是我加的**：用户只说了"黑钨矿"，但项目惯例是深处矿配深层变种
     （钴/镍/银/铀/锰都有；只有铝与锂是纯浅层），且只写浅层 target 的话深板岩层完全不生成。
  2. **世界生成数值是我定的**：每区块 6 簇、每簇最多 4 块、Y -64~16。
     对照：钴 6/4/-64~32、银 9/3/-48~32、铀 10/10/-64~16。
  3. 挖掘等级 = 铁镐（和锂、钴、镍、银、铀同档）。
  4. `c:` 标签用材料名 `tungsten`（不是矿物名 wolframite）：掉落物叫 raw_tungsten。
  5. 贴图是改色来的（黑钨矿 = 锰矿石颗粒改成冷灰黑，粗钨 = 粗锂改成灰蓝）。

重建来源优先级（§10）
---------------------
  已发布 jar（字节权威） > 本目录的改后副本 > 反推 + 编译比对
"""


def main():
    new_jar = os.path.join(BK, "_改后_PotatoST-0.10.jar")
    sha1 = u"（还没发布）"
    size = u"?"
    try:
        import hashlib
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
