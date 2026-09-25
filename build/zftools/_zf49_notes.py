# -*- coding: utf-8 -*-
"""写 zf49_pre 的 _说明.txt"""
import hashlib
import io
import os
import time

BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf49_pre"

TEXT = u"""\
ZF49 备份说明（阶段目录 zf49_pre）
=====================================
建立时刻：{now}
建立时机：**动手之前**（§10）

用户原话
--------
「加入【合金冶炼炉】类似于电力高炉 …（4 层 × 5 排 × 4 列的图纸）…
  合金冶炼炉自身储能32k 五个输入槽（只能接受锭标签） 三个输出槽 2个消耗槽
  （目前放不了东西 以后出类似于沉浸电弧炉石墨电极的东西）先不做配方
  还有以后配方太麻烦了 我用数字代替 例如【一般金属块】=【1】」

动手前问清的两个歧义点（都已按答复实现）
----------------------------------------
  ① 主控方块 → **新加一个控制器方块**（放在图纸里【标靶】那一格：第 2 层 · 最前排 · 最左列）
  ② 第四层「后面四行与前面一致」→ **只重复"耐热金属块环"，最后一行不重复**
     ⇒ 炼药锅/散热装置只有 1 层高（探针专门断言了这一条）

做了什么
--------
  新增方块 2 个：alloy_smelter（控制器）+ alloy_smelter_port（接线口，无物品形态）
  新增方块实体 2 个、菜单 1 个、界面 1 个、结构定义 1 个
  结构：4 层 × 5 排 × 4 列 = **80 格**；58 个方块 + 22 格空气
        （一般金属块 14 / 加热装置 6 / 耐热金属块 26 / 接线块 2 / 高炉 6 /
          控制器·漏斗·炼药锅·散热装置 各 1）
  方块实体：储能 **32768 FE**、**5 输入**（只放行 `c:ingots`）、**3 输出**、**2 消耗槽**（锁死）
  **本阶段不做配方**（用户明确）

与电力高炉的两处不同（值得记）
------------------------------
  1. **不替换结构里的方块**：58 格保持玩家摆的原样 ⇒ 不需要 OBJ 模型、也不需要部件方块。
     只有控制器与两处接线口是特殊格。
  2. 因此"接线口"用的是**和接线块一模一样的贴图**（模型直接指向 wiring_block）——玩家看不出被换过，
     但它是唯一能进电的地方；挖掉会掉回一个接线块。

目录里都有什么
--------------
  _改前_PotatoST-0.10.jar  SHA1 = 2e5f3ac93cf116656ce46b6333fb04fe30478669（本阶段结束后作废）
  _改后_PotatoST-0.10.jar  SHA1 = {new_sha1}
                           大小 = {new_size} 字节
  改后_* / 新增文件\\        改后 14 份 + 新增 22 份
  _sha256_改后与新增.txt    每一份的 SHA256 + 一致性

自检与取证
----------
  build\\zftools\\check\\AlloySmelterCheck.java  探针源码
  build\\zftools\\check\\zf49_探针.log           114 项全 [OK]（含图纸格数与材料数、成型、通电、槽位、拆解）
  build\\zftools\\check\\zf49_反证.log           把第四层改成"重复第三层最后一行" ⇒ 3 项 FAIL
  build\\zftools\\zf49_gates.txt                 七项交付检查全绿（Audit 0 / LangCheck 0 / RecipeCheck 0 /
                                                ModelCheck 0 / JsonCheck 0 / SoundCheck 0）
  build\\zftools\\zf49_regression__zf4[68].txt   前两阶段的盘面复核回归（0 失败）

已知偏差 / 我替你定的（都写进档案 §9）
-------------------------------------
  1. 控制器放在【标靶】那一格（你没说换哪一格；改三个常数即可换位置）
  2. 左右手性：控制器与炼药锅同侧、漏斗与散热装置同侧（图纸没说哪边算左；改一行即可反转）
  3. 控制器正面是新画的 16×16；顶面/侧面复用现成的耐热金属块与一般金属块贴图
  4. 接线口与接线块外观相同（故意的）
  5. 电只能从那两处接线口进；结构没成型时不传电
  6. 2 个消耗槽画在界面上但放不进任何东西
  7. 配方没做（按用户要求），tick 里只做"结构还在不在"的每秒复查

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
