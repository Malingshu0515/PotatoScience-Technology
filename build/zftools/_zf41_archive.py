# -*- coding: utf-8 -*-
"""ZF41 收尾：档案补记 §12.9 + 备份收尾。"""
import hashlib
import io
import os
import shutil

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf41_pre"
ARCH = os.path.join(PROJ, r"docs\开发档案.md")

ADD = u"""
### 12.9 ZF41：接电口、扳手、Jade 名字

**① 「原来接线块的地方也不传电」—— 两个原因叠在一起，两个都是真 bug。**

- **这台机器压根没有注册能量能力。** `PotatoST` 里只给它注册了 `ItemHandler`，
  没有 `EnergyStorage` ⇒ 电缆/端子接上去一点电都进不来。
  已补 ㉔，接口是 `MachineEnergyStorage.receiveOnly`（只收不放，容量 320）。
- **那两格接线块的"接电口"身份在装配后丢了。** 用户 ZF37 定的规则是
  「多方块结构只有接线块的地方可以用端子传输电力」，可装配后那两格变成了部件格，
  而能力**只能挂在方块实体上** ⇒ 新加 `ElectricBlastFurnacePartBlockEntity`（ZF41），
  它对外的 `getEnergyStorage()` **只在这格"原本是接线块"时才返回控制器的储能**，
  其余 23 格一律返回 `null` —— 规则是用户定的，不是省事。
  判定方式：问控制器 `originalAt(这一格)` 是不是接线块。

**② 拆解改用扳手。** 用户：「不要改成 shift+空手拆掉了 加个扳手 手持扳手 shift+右键拆掉 材质你随意」。
⇒ 新增物品 `potato_s_t:wrench`（图标是程序生成的 16×16 开口扳手占位图），
拆解逻辑抽到 `ElectricBlastFurnaceWrench.disassembleByWrench(...)`，
控制器与部件格两条入口都调它。**空手 Shift 右键不再拆解**（未成型的控制器仍然用它成型）。
⚠ **扳手目前没有合成配方**（用户没给）—— 只能在创造模式标签页里拿，挂在 §9。

**③ Jade 显示一大串 id。** 部件格没有 lang，Jade 就把 `block.potato_s_t.electric_blast_furnace_part`
原样念出来。修法是给部件格加 lang，**并且故意与控制器同名**（电力高炉 / Electric Blast Furnace /
電力高炉 / Электрическая доменная печь）—— 于是整台机器在 Jade 里从头到尾都念同一个名字。

取证：`build\\zftools\\check\\zf41_接电与扳手取证.log`（22 项全过）。
同目录的 `..._反证.log` 是**探针自己写错**的那一版（19 过 2 挂），两条都是探针的锅：
其一用 `extractEnergy` 去腾空一个"只收不放"的缓冲（恒为 0，于是缓冲还是满的）；
其二在结构已经被拆掉之后去世界里取部件格的 `descriptionId`（那格早变回铁栏杆了）。
"""

with io.open(ARCH, "r", encoding="utf-8") as f:
    cur = f.read()
if "### 12.9" in cur:
    print("[SKIP] 已有 12.9")
else:
    with io.open(ARCH, "w", encoding="utf-8", newline="") as f:
        f.write(cur + ADD)
    print("[OK] 档案已补记 12.9")

CHANGED = [
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\java\com\potatost\mod\ModBlocks.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\java\com\potatost\mod\ElectricBlastFurnaceBlock.java",
    r"src\main\java\com\potatost\mod\ElectricBlastFurnacePartBlock.java",
    r"src\main\java\com\potatost\mod\ElectricBlastFurnaceBlockEntity.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"docs\开发档案.md",
]
NEW_FILES = [
    r"src\main\java\com\potatost\mod\ElectricBlastFurnacePartBlockEntity.java",
    r"src\main\java\com\potatost\mod\ElectricBlastFurnaceWrench.java",
    r"src\main\resources\assets\potato_s_t\textures\item\wrench.png",
    r"src\main\resources\assets\potato_s_t\models\item\wrench.json",
]
dst = os.path.join(BK, "新增文件")
os.makedirs(dst, exist_ok=True)
for rel in NEW_FILES:
    d = os.path.join(dst, os.path.basename(rel))
    shutil.copy2(os.path.join(PROJ, rel), d)
for s in ("_zf41_backup.ps1", "_zf41_apply.py", "_zf41_archive.py", "EbfPowerCheck.java"):
    for base in ("build/zftools", "build/zftools/check"):
        p = os.path.join(PROJ, base.replace("/", os.sep), s)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(dst, s))
            break
for rel in CHANGED:
    shutil.copy2(os.path.join(PROJ, rel), os.path.join(BK, "改后_" + os.path.basename(rel)))
shutil.copy2(os.path.join(PROJ, "release", "PotatoST-0.10.jar"),
             os.path.join(BK, "_改后_PotatoST-0.10.jar"))


def sha(p):
    h = hashlib.sha256()
    with io.open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


bad = sum(1 for rel in NEW_FILES if sha(os.path.join(PROJ, rel)) != sha(os.path.join(dst, os.path.basename(rel))))
print("新增文件 %d 个，副本校验不一致 %d 个" % (len(NEW_FILES), bad))

note = u"""ZF41：接电口 + 扳手 + Jade 名字
========================================================
备份时刻：2026-09-19 03:2x（动手前建的，清单 11 项交叉核对通过）

用户原话
--------
  「原来接线块的地方也不传电 然后不要改成shift+空手拆掉了 加个扳手 手持扳手shift+右键拆掉
   材质你随意 先用原版也可以 然后就是除了控制器以外jade显示的都是一大串id
   如果能解决就太好了 不能也没关系」

改了什么
--------
  ① **接电**（两个真 bug 叠在一起）
     A. 这台机器**压根没注册能量能力** —— 只注册了 ItemHandler。补 ㉔，
        接口 receiveOnly，容量 320。
     B. 装配后那两格接线块变成部件格，接电口身份丢了。新增
        `ElectricBlastFurnacePartBlockEntity`：**只有"原本是接线块"的格子**才把
        控制器的储能暴露出去，其余 23 格返回 null（用户定的规则）。
  ② **扳手拆解**：新物品 `wrench`（程序生成的 16×16 开口扳手占位图），
     逻辑抽到 `ElectricBlastFurnaceWrench`。**空手 Shift 不再拆解**；
     未成型的控制器仍用空手 Shift 成型。
     ⚠ 扳手**没有合成配方**（用户没给），只能创造模式拿 —— 已在档案 §9 标注。
  ③ **Jade 名字**：给部件格加 lang，**故意与控制器同名** ⇒ 整台机器在 Jade 里念同一个名字。

验证到哪一步
------------
  [x] 探针 EbfPowerCheck：**22 项全 [OK]**
      · 控制器暴露能量能力、能收满 320、只收不放、满电再收为 0
      · 两个接线块位都暴露能量能力，**从接线块位灌电，控制器存量 0 → 320**
      · **非接线块位不给电**（getCapability 返回 null）+ isPowerPort 为假（反向断言）
      · 扳手拆解：26 格全还原、控制器格变空气、掉出原版高炉 + GUI 里的粗银、
        **不掉电力高炉本体**
      · 部件格 descriptionId 正确、名字解析成人话
      取证 build\\zftools\\check\\zf41_接电与扳手取证.log
  [x] **探针第一版自己写错了两条**（19 过 2 挂，都是探针的锅）：
      ① 用 extractEnergy 去腾空"只收不放"的缓冲（恒 0 ⇒ 缓冲还是满的 ⇒ 假 FAIL）；
      ② 在结构已被拆掉之后去世界里取部件格的 descriptionId（那格早变回铁栏杆）。
      取证 ..._反证.log
  [x] runServer：Loaded 1306 recipes（不变）、Done (0.463s)、零 ERROR
  [x] 七项：Audit 失败 0 / 提示 5；LangCheck 4×**176** 失败 0；RecipeCheck 失败 0；
      ModelCheck 失败 0 / 提示 2；JsonCheck 非法 0；SoundCheck 失败 0
  [x] 探针已删；产物 jar 内 *Check.class 条目 = 0
  [x] 产物 release\\PotatoST-0.10.jar SHA1 c7e91247…（2,061,869 B）；上一版 1fd7b558… 作废
  [ ] **游戏内未验**：接端子到原来接线块那两格能不能供电；扳手 Shift 右键能不能拆；
      空手 Shift 右键不再拆；Jade 里每一格是不是都念"电力高炉"

回退办法
--------
  本目录根部的 11 个改前副本覆盖回原路径；删 新增文件\\ 里的 4 个新文件；
  成品 jar 用 _改前_PotatoST-0.10.jar。
"""
io.open(os.path.join(BK, "_说明.txt"), "w", encoding="utf-8", newline="\r\n").write(note)
print("[OK] 已写 zf41_pre\\_说明.txt")
