# -*- coding: utf-8 -*-
"""写 zf45_pre 的 _说明.txt（用 Python 写，避开 PowerShell here-string 吃反引号的老坑，§4.9）。"""
import io
import os
import time

BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf45_pre"

TEXT = u"""\
ZF45 备份说明（阶段目录 zf45_pre）
=====================================
建立时刻：{now}
建立时机：**动手之前**（§10 的规矩：先备份、后改第一个字节）

本阶段做了什么
--------------
用户原话：「下面是配方 工作量有可能有点大 新物品材质你简单画一下或者用原版相近的代替」
一次做完的整批配方：
  ① 4 个新物品：iron_powder 铁粉 / magnet 磁铁 / thermal_metal 热力金属 /
     photovoltaic_component 光伏原件（贴图 2 张改色 + 2 张手画）
  ② 微型粉碎机 2 条：煤炭或木炭 -> 碳粉（3s、10 FE/t）；铁锭 -> 铁粉（20s、70 FE/t）
  ③ 电力高炉 2 条**双输入**：铁粉+碳粉 -> 高碳钢；铁粉+沙砾 -> 磁铁
  ④ 14 份合成配方 JSON（微型粉碎机 / 液压机 / 灌装机 / 晒盐机 / 发电机 / 流体管道 x16 /
     流体泵 / 盐分解构器 / 光伏原件 / 太阳能板 / 热力金属 / 加热装置 / 空线轴 / 铜丝 x4）
  ⑤ 顺手改名：carbon 碳 -> 碳粉；toner 碳粉 -> 墨粉（否则包里有两个"碳粉"）
  ⑥ 给电力高炉补了 JEI 分类（24 条）

目录里都有什么
--------------
  改前_*.java / 改前_*.json   —— 动手前那 12 个文件的原样副本（另见 _改前_PotatoST-0.10.jar）
  _改前_PotatoST-0.10.jar   —— 本阶段开始时的已发布产物
                                SHA1 = 750b97c27bc33a9bab71827972059daee7e4a643
                                （这一版在本阶段结束后**作废**，以 release 里的 .sha1 为准）
  _改后_PotatoST-0.10.jar   —— 本阶段发布的产物
                                SHA1 = 6ea6d0665bc410f3416f5a9d26d4ad79572317f9
                                大小 = 2,079,468 字节
                                （Audit 的 H 项已复核：产物名 / mod_version / .sha1 三方一致）
  改后_*                    —— 同一批文件改完之后的样子（归档脚本 _zf45_archive.py 拷的）
  _sha256_改后与新增.txt     —— 上面每一份的 SHA256 + "与项目里的当前文件一致"的核对结果
  新增文件\\                 —— 本阶段**新建**的 34 份：4 张贴图 + 4 个模型 + 14 份配方 JSON
                                + 8 个脚本 + 探针源码 + 3 份取证
                                ⚠ 其中两份**同名不同物**（`thermal_metal.json` 与
                                `photovoltaic_component.json` 既是模型又是配方），
                                扁平归档时后一份会盖掉前一份 ⇒ 配方那两份改名成
                                `recipe_thermal_metal.json` / `recipe_photovoltaic_component.json`

自检与取证
----------
  探针 build\\zftools\\check\\Zf45Check.java 在**真专用服务端**上跑：
    build\\zftools\\check\\zf45_探针.log   = 56 项全 [OK]
    build\\zftools\\check\\zf45_反证.log   = 故意短路"换料清零"后重跑 ⇒ 1 项 FAIL（读数 101）
    （两份 log 是从控制台按 GBK 转存的 UTF-8；捕获时尾部个别汉字丢了替换符，
      但 [OK]/[FAIL]、数字、物品 id 全部完好 —— 取证看的就是这些。）
  七项交付检查：build\\zftools\\zf45_gates.txt（Audit 0 失败 / LangCheck 0 / RecipeCheck 0 /
    ModelCheck 0 / JsonCheck 0 / SoundCheck 0；GroupEnergyCheck 本阶段没动 GroupEnergy，不需要跑）

已知偏差（不藏，都写进档案 §9 了）
----------------------------------
  1. 用户写的"（消耗桶）"**做不到**：原版配方 JSON 无法取消物品自带的返还，
     液压机里的 2 个水桶合成后会**返还 2 个空桶**（探针已取证）。要真吃桶得写自定义配方序列化器。
  2. 铁粉 20s x 70 FE/t = **28000 FE/个**，是照用户字面值实现的；比它做出来的高碳钢（800 FE）贵 35 倍。
  3. "光伏原件"照用户原文（不是"元件"）。
  4. 沙子那条在 JEI 里画成 2 格（沙子/红沙任选），与两条配对配方（两格都要）外观相同。

重建来源优先级（§10）
---------------------
  已发布 jar（字节权威） > 本目录的改后副本 > 反推 + 编译比对
"""

with io.open(os.path.join(BK, "_说明.txt"), "w", encoding="utf-8", newline="\r\n") as fh:
    fh.write(TEXT.format(now=time.strftime(u"%Y-%m-%d %H:%M:%S")))
print(u"写出 " + os.path.join(BK, "_说明.txt"))
