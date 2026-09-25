# -*- coding: utf-8 -*-
u"""_zf72_archive.py —— ZF72 归档（v0.11 石油线规划轮；**本轮不动 jar**）

归档到 `C:\\PotatoST救援\\zf72_pre\\新增文件\\`，逐份核 SHA1，另写 MANIFEST.txt。
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\PotatoST救援\zf72_pre"
NEW = os.path.join(ROOT, u"新增文件")

FILES = [
    # 本轮唯一的交付物：v0.11 石油线规划
    u"docs\\v0.11规划.md",
    # 改了的档案（改前件在 ..\\docs\\ 下，SHA1 a28680cd6c8a…）
    u"docs\\开发档案.md",
    # 本轮新增的工具
    u"build\\zftools\\_zf72_backup.py",
    u"build\\zftools\\_zf72_docs.py",
    u"build\\zftools\\_zf72_docs2.py",
    u"build\\zftools\\_zf72_docs3.py",
    u"build\\zftools\\_zf72_docs4.py",
    u"build\\zftools\\_zf72_verify.py",
    u"build\\zftools\\_zf72_falsify.py",
    u"build\\zftools\\_zf72_archive.py",
    u"build\\zftools\\_zf72_gates.ps1",
    u"build\\zftools\\_zf72_vanilla_evidence.py",
    u"build\\zftools\\_zf72_rebuild_diff.py",
    u"build\\zftools\\_zf72_recycle_probe.py",
    u"build\\zftools\\_zf72_recycle_list.py",
    # 从 jar 现抠的原版证据
    u"build\\zftools\\_zf72_vanilla_evidence.json",
    # 取证日志（UTF-8）
    u"build\\zftools\\_zf72_backup_utf8.txt",
    u"build\\zftools\\_zf72_vanilla_evidence_utf8.txt",
    u"build\\zftools\\_zf72_verify_utf8.txt",
    u"build\\zftools\\_zf72_falsify_utf8.txt",
    u"build\\zftools\\_zf72_build_utf8.txt",
    u"build\\zftools\\_zf72_rebuild_diff_utf8.txt",
    u"build\\zftools\\_zf72_gates_utf8.txt",
    # 成品（本轮没动，一起留档以证明「没动」）
    u"release\\PotatoST-0.10.jar",
    u"release\\PotatoST-0.10.jar.sha1",
]


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    fails = []
    rows = []
    for rel in FILES:
        src = os.path.join(PROJ, rel)
        dst = os.path.join(NEW, rel)
        if not os.path.isfile(src):
            fails.append(u"缺文件: %s" % rel)
            continue
        folder = os.path.dirname(dst)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        shutil.copy2(src, dst)
        a, b = sha1(src), sha1(dst)
        if a != b:
            fails.append(u"拷贝后哈希不一致: %s" % rel)
        rows.append(u"%-58s %10d  %s" % (rel, os.path.getsize(dst), a))
        print(u"  [OK] %s" % rel)

    manifest = os.path.join(NEW, u"MANIFEST.txt")
    io.open(manifest, "w", encoding="utf-8", newline=u"\n").write(
        u"ZF72 归档清单（v0.11 石油线「规划轮」：只写文档，不动 jar）\n"
        u"主题：用户给了 PotatoS&T v0.11 规划（石油相关）第一部分 ⇒ 逐字存档 + 技术落点 + 踩雷 + 待拍板。\n"
        u"交付物：docs\\v0.11规划.md —— 逐字规格 / 20 行「规格→落点」对照 / 10 个侦察出来的雷 /\n"
        u"        11 条待用户拍板 / 分轮建议（ZF73 石油本体+油桶、ZF74 油田特征+海洋油田群系）/\n"
        u"        3 张待画贴图 / 验收思路。\n"
        u"★ 头号雷（已立档案 §4.44）：现有气体判定是**负向**的（TankContents.isGas 与\n"
        u"  FillingMachineBlockEntity.isGasFluid 都写「非水非岩浆 ⇒ 气体」）⇒ 一注册原油，\n"
        u"  高压气罐就会把原油当气体收下，直接违反用户「不可以罐装气体」。ZF73 第一刀 = 改成正向白名单。\n"
        u"  同源第二雷：灌装机界面按整数 id 同步流体，ModFluids.idOf/byId 只认 3 种气体 ⇒ 装了原油显示「空」。\n"
        u"★ 其它雷：本工程从没**注册**过液体方块（原油是第一个 LiquidBlock；而流体泵只认液体方块实例\n"
        u"  ⇒ 必须做成方块）；群系源 codec 已写进 3 个世界预设且旧存档把配置存进 level.dat（只能加带默认值\n"
        u"  的可选字段）；is_overworld 标签是同工程覆盖的（新群系要追加）；原版 placed_feature 没有\n"
        u"  「排除某群系」写法（沙漠/恶地 3 倍要拆成 1 份基础 + 2 份额外）。\n"
        u"★ 原版事实不靠记忆：_zf72_vanilla_evidence.py 每次从 client-extra.jar 与 NeoForge sources.jar 现抠\n"
        u"  （地表岩浆湖 rarity_filter chance=200 / lake 的 barrier=stone fluid=lava level=0 /\n"
        u"   NeoForge Tags.java 里没有原油通用 c: 标签 ⇒ 本轮不加标签 / 石岸水色 4159204 / 4047AD=4212653）。\n"
        u"★ 校验：_zf72_verify.py **57 项**（A 规格逐字 13 / B 文档 vs 代码 19 / C 文档 vs 原版证据 10 /\n"
        u"  D 冻结状态 5 / E 档案已记录 4 / F 文档自身 6），0 失败。\n"
        u"★ 校验抓到我自己写错一处：文档初稿说「工程里从没出现过 LiquidBlock」，实际 FluidPumpBlockEntity:400\n"
        u"  的泵判定就是 instanceof LiquidBlock —— 断言写得太粗（抓字面而非抓注册）先报 FAIL，收窄成\n"
        u"  「没有 new LiquidBlock( 注册」后过，并把「泵认液体方块」升级成待决 11（泵能不能抽原油）。\n"
        u"★ 反证 5 刀全被抓住：① 文档 chance 200→250（C3 挂）② 文档规格原句 3000mB→3500mB（A9 挂）\n"
        u"  ③ 档案 4.44→4.45（E1 挂）④ **源码** TankContents.CAPACITY 3500→3600（B1 挂）\n"
        u"  ⑤ **源码** 泵的 instanceof LiquidBlock（B12b 挂）；每刀还原后核 SHA1 逐字节相同，复跑校验全绿。\n"
        u"★ 备份根事故：一直用的桌面根 ...\\PotatoST救援_20260917_183054（424,191,790 B，装着 zf68_pre…zf71_pre）\n"
        u"  已在 2026-09-19 13:36:29 被删进回收站；$R 实体仍在 ⇒ **可还原**（取证 _zf72_recycle_list.py，只读）。\n"
        u"  本轮起备份根改到 C:\\PotatoST救援\\<阶段名>\\（C 盘、不进桌面）。改前件 1 个（docs\\开发档案.md，\n"
        u"  SHA1 a28680cd6c8a… → 改后 1771a11bf1ab…），脚本加了幂等保护：已存在的改前件**不会被覆盖**。\n"
        u"★ **用户 2026-09-24 拍板两条**（原话「5.配方吃两个 嗯 没提到0.12任务的话都是0.11」）：\n"
        u"  ⑤ 油桶配方**吃 2 个铁桶**、产出按默认 **1 个**；\n"
        u"  ⑩ 长期口径：**没提到 0.12 任务的话，后面所有任务都算 v0.11**（石油线全部后续部分都在 v0.11 里）\n"
        u"     ⇒ ZF73 打包时 mod_version → 0.11，产出 PotatoST-0.11.jar；PotatoST-0.10.jar 原样并存（非作废关系）。\n"
        u"  其余 9 条按规划文档 §5 的默认值走（舀 1000 mB/次、不做倒出、含水与岩浆、灌装机水箱开放、\n"
        u"  海洋油田本轮不加油苗、不算 is_ocean、群系源加带默认值的可选字段、原油不烧不爆、泵允许抽原油）。\n"
        u"★ **重打包自证**（反证动过源码，所以真重打一遍）：gradlew build --offline --no-build-cache 17 秒，\n"
        u"  compileJava UP-TO-DATE（内容没变所以根本没重编）；_zf72_rebuild_diff.py 把新 jar 与成品**逐条目 CRC**\n"
        u"  比 —— 成品 708 条目 / 新打 707，唯一差异是 assets/potato_s_t/textures/block/lv_001.png（3352 B，\n"
        u"  成品里有、源码树里已被用户 2026-09-22 删掉），其余 **707 个同名条目逐条 CRC 完全相同**\n"
        u"  ⇒ 反证没留痕迹、源码树 == 成品（新打 0f6454abbdbc90e0361f555d18ca46ed87282710 / 2,214,039 B，\n"
        u"  只是自证产物、不是新版本）。⇒ 副作用：从今往后「重打包 == 成品」这条自证不再成立，\n"
        u"  要恢复只有把 lv_001.png 从回收站还原回去【待用户拍板】；本条对账只对本轮有效（ZF73 起源码树要变）。\n"
        u"★ 顺带核到：贴图目录里 lv_001.png 已不在（ZF71 门跑时还在，回收站记录删除时间 2026-09-22 14:13:45），\n"
        u"  孤儿提示因此从 2 条降到 1 条（只剩拼错名的 deepslate_aluminiu_ore.png）；TextureCheck 警告 24→23。\n"
        u"门：九道门 + 往轮校验全绿（Audit 0 失败/7 提示、ToolLint 221 个脚本 0 语法错/0 流程错/27 历史提示、\n"
        u"    LangCheck 四语言各 210 键 0 失败、RecipeCheck -All 0 失败、ModelCheck 0 失败/1 提示、\n"
        u"    TextureCheck 0 失败/23 警告/8 待画、JsonCheck 340 个 JSON 0 非法、SoundCheck 0 失败、\n"
        u"    ZF72 verify 57 项 0 失败）。\n"
        u"成品：release\\PotatoST-0.10.jar **仍是 ZF70 的**\n"
        u"      84d09345f6095408ae462dabb536307141904ea3（2,217,321 B）—— 本轮不动 jar，**不作废**；\n"
        u"      mod_version 仍 0.10（v0.11 的版本号等第一次真正加内容那轮再提）。\n"
        u"\n" + u"\n".join(rows) + u"\n")
    print(u"\n归档目录: %s" % NEW)
    print(u"文件数 = %d   失败项 = %d" % (len(rows), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
