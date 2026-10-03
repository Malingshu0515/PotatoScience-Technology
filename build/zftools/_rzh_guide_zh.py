# -*- coding: utf-8 -*-
r"""_rzh_guide_zh.py —— 帕秋莉手册正文**去 AI 味**（中文侧重写）。

用户原话：「帕秋莉手册内容去ai味道一点；请用正常成年人的语言写，不要用感叹号、
破折号、括号解释和口语化备注。不要用"可以""能够"这类废话词。句子要短，主谓宾清晰。
不要输出"这是……的证明""那副躯体从不索取"这类抒情句。数据、参数、限定词必须准确，
不能为了顺口省略"仅""须""不可"。」

风格口径（写进代码，后续轮次照这个改）：
  · 不用「！」「——」「……」；解释性括号一律拆成独立句
  · 不用「可以 / 能够 / 就能 / 就能把」这类空转词；能用「须 / 仅 / 不可 / 只」的地方必须写出来
  · 一句一个信息点，主谓宾齐全；不写抒情句与收尾感叹
  · **数字与限定词一字不动**（3×3×3、12/32 槽、10 秒、800 FE、8n²+80n、10n mB/s、
    2048 / 16134 FE/t、7~20 威力、20×20、5 桶大罐……）
  · `$(br2)` 是帕秋莉的换行宏，保留

⚠ 只改 guide.* 的**正文与描述**（.p1/.p2/.p3/.landing/.desc），
  分类标题与书标题不动。

用法：`python build/zftools/_rzh_guide_zh.py`
"""
from __future__ import print_function
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")

B2 = u"$(br2)"

# 键 -> 新中文（旧值运行时读盘，绝不手抄）
NEW = {}

NEW[u"potato_s_t.guide.category.getting_started.desc"] = (
    u"第一台机器、第一条产线，以及所有机器共通的规矩。")
NEW[u"potato_s_t.guide.category.materials.desc"] = (
    u"矿物变成粉、锭、板的流程，以及高炉、合金与钛这条线。")
NEW[u"potato_s_t.guide.category.power.desc"] = (
    u"接线、发电、储能，以及流体与气体的搬运方式。")
NEW[u"potato_s_t.guide.category.oil.desc"] = (
    u"原油的来路、分馏塔的摆法，以及四台化工机器。")
NEW[u"potato_s_t.guide.category.starfall.desc"] = (
    u"观星、召唤陨石，以及用星璨钢与振金武装自己。")
NEW[u"potato_s_t.guide.category.faq.desc"] = (
    u"机器不动与流体对不上，先看这两页。")

NEW[u"potato_s_t.guide.landing"] = (
    u"这本手册跟随版本更新。每一步都指到 JEI 里查得到的配方。左侧选一章，从「起步」开始读。"
    + B2 + u"书丢一本，原版书加一个铁锭重做一本。")

NEW[u"potato_s_t.guide.entry.getting_started.start.p1"] = (
    u"本模组的主线分五步：粗矿磨成粉，粉进电力高炉炼成锭，液压机把锭压成板，铺开电力与化工，"
    u"以星陨收尾。" + B2 + u"没有粉就做不了任何东西，因此第一件事是造一台微型粉碎机。"
    u"它需要持续供电，最初用低级发电机烧煤炭或木炭带动。")
NEW[u"potato_s_t.guide.entry.getting_started.start.p2"] = (
    u"粉碎机摆在工作区中间，正面留一格站人。接着接电：造一台低级发电机，"
    u"用接线端子或线缆把电送过去，见「电力」一章。" + B2
    + u"粉是后面一切的地基。见到粗矿就磨，不必顾虑数量。")

NEW[u"potato_s_t.guide.entry.getting_started.first_line.p1"] = (
    u"完整的起步线分四步：粗矿进微型粉碎机变成粉，粉进电力高炉变成锭，锭进液压机变成板。"
    + B2 + u"板是几乎所有机器的通用零件。缺板就先压一批。锭也能直接合成，不必全部压成板。"
    u"压沥青一次须放 12 个。")

NEW[u"potato_s_t.guide.entry.getting_started.rules.p1"] = (
    u"所有机器都认一条铁律：通入红石信号即停机，进度保留。要做开关，在机器旁放拉杆或红石线。"
    + B2 + u"机器只吃自己那种原料。放错东西时，界面会写明它不要什么。")
NEW[u"potato_s_t.guide.entry.getting_started.rules.p2"] = (
    u"空手潜行右键任意机器即逐槽诊断。它会逐行说明哪个槽缺什么、哪个罐是空的、是否缺电。"
    + B2 + u"界面上的能量条、流体罐、进度条与状态灯都是实时的。状态灯变红时先看诊断，再对症处理。")

NEW[u"potato_s_t.guide.entry.materials.ore_chain.p1"] = (
    u"一共九种矿：铝、钴、镍、银、铀、锰、锂、黑钨矿与钛。其中七种带深层变体。" + B2
    + u"标准流程分三步：粗矿进微型粉碎机变成粉，粉进电力高炉变成锭。"
    u"沙、粗铝、粗银也能用原版熔炉烧，但粉进高炉产量更高。")
NEW[u"potato_s_t.guide.entry.materials.ore_chain.p2"] = (
    u"锭用液压机压成板：铁板、铜板、镍板、钴板、银板、铝板、钢板等。"
    u"板是几乎所有机器的通用零件，缺什么就先压一批。" + B2
    + u"压机通入红石信号即停机，进度保留。")

NEW[u"potato_s_t.guide.entry.materials.blast_alloy.p1"] = (
    u"电力高炉是 3×3×3 的多方块，直接架在原版高炉上装配。它有 12 个输入槽、32 个输出槽，"
    u"每个槽 10 秒烧完，每件物品耗电 800 FE。" + B2
    + u"除本模组的矿物处理外，原版高炉能烧的东西这里都能烧。粉进高炉，产量高于原版熔炉。")
NEW[u"potato_s_t.guide.entry.materials.blast_alloy.p2"] = (
    u"合金炉主控须按图纸摆 4 层、共 58 格：底面、三格高的墙，以及顶面那两列耐热金属块。"
    u"外壳上至少有 1 个接线块才会自动激活。" + B2
    + u"界面是 5 个输入槽，只收锭；3 个输出槽；2 个消耗槽。储能 32768 FE，电只从接线口进。")
NEW[u"potato_s_t.guide.entry.materials.blast_alloy.p3"] = (
    u"钛这条线：粗钛先粉碎成钛粉，钛粉进电力高炉炼成钛锭。" + B2
    + u"钛的下一站是合金：轻质钛合金、硬质钛合金、稳定金属块。酸性反应室与锂电池都需用到它们。"
    u"钛合金剑与镐也用轻质钛合金做。")

NEW[u"potato_s_t.guide.entry.materials.salt.p1"] = (
    u"晒盐机须在海洋或咸水河群系、Y 从 0 到 64、且下方有水源方块才工作，被动晒盐每 120 秒产出 1 个海盐。"
    + B2 + u"接上电后每 20 秒 1 个。")
NEW[u"potato_s_t.guide.entry.materials.salt.p2"] = (
    u"注意：海盐掉进水里会溶解消失。" + B2
    + u"盐分解器每次投入 64 个海盐，40 秒后产出 1 个氯化钠。有六成概率返还那 64 个海盐，"
    u"另有 5% 概率额外产出一个随机粗矿。电解器的电解质槽里放海盐，电解水时会多产氯气，"
    u"每 500 mB 水多消耗 1 个海盐。")

NEW[u"potato_s_t.guide.entry.power.wiring.p1"] = (
    u"接线端子用于远程输电。右键放下第一个端子选中它，再右键另一个端子，两者即连上。"
    u"距离过远时它会拒绝，并给出上限。" + B2
    + u"机器外壳上的接线块才是电的进出口，多方块成型后那一格变成接线口。把端子连到这些位置。")
NEW[u"potato_s_t.guide.entry.power.wiring.p2"] = (
    u"线缆轴也能连端子。铜线轴与银线轴都最长 16 格、都是 32 点耐久，耗尽后返还空线轴。"
    u"区别在速率：铜线 2048 FE/t，银线 16134 FE/t。" + B2
    + u"动力线缆轴传的是动力而非电。动力能源捕获器靠它把动力拉过来。")

NEW[u"potato_s_t.guide.entry.power.generation.p1"] = (
    u"低级发电机烧煤炭或木炭发电，通入红石信号即停机。它是最简便的开局电源，"
    u"一台即足以带动微型粉碎机。")
NEW[u"potato_s_t.guide.entry.power.generation.p2"] = (
    u"太阳能板只在白天发电，越靠正午越强。正上方须是空气或无色玻璃。"
    u"水平相邻的太阳能板自动并联，发电量与储能整组共享。" + B2
    + u"雨天输出六成，雷暴输出两成，夜间不发电。")
NEW[u"potato_s_t.guide.entry.power.generation.p3"] = (
    u"需要更大的电量就走动力线。动力能源捕获器紧邻动力源时获取动力，靠动力线缆传输，"
    u"发电机再把动力换成电，每点动力 2 FE/t。" + B2 + u"这三台配合起来才进入工业阶段。")

NEW[u"potato_s_t.guide.entry.power.storage.p1"] = (
    u"三元聚合物锂电池单块储能 4M FE。把锂电池紧贴着摆成完整长方体，它们会自动合并成多方块，"
    u"容量按块数叠加。仅顶面能传输 FE。" + B2
    + u"底面只认 2×2、2×3、3×3、3×4、4×4、5×5 这六种。2×2 最高 6 层，"
    u"2×3、3×3、3×4 最高 12 层，4×4 与 5×5 最高 32 层。")
NEW[u"potato_s_t.guide.entry.power.storage.p2"] = (
    u"做电池须先有元件。锂电池构造间要吃四样原料：粗锰或粗铝、镍锭或粗镍、碳酸锂、钴锭或粗钴，"
    u"通入硫酸，30 秒产出一件锂电池元件。" + B2
    + u"这台机器不耗电，靠的是化学。碳酸锂的来路是粗锂粉碎成锂矿精粉，精粉再进电力高炉烧出来。")

NEW[u"potato_s_t.guide.entry.power.fluids.p1"] = (
    u"液体走油桶，气体走高压气罐。两者都靠灌装机灌。灌装机内部有五个 5000 mB 的罐，"
    u"一个罐只装一种流体。手拿油桶或气罐右键机器，把里面的东西倒进罐。" + B2
    + u"灌装时每罐 5 mB/t，每个正在工作的罐耗 60 FE/t。")
NEW[u"potato_s_t.guide.entry.power.fluids.p2"] = (
    u"想把机器里的流体装回桶里就用容器换流器：左槽放装有流体的油桶或气罐，右槽放一个空桶，"
    u"它会把空桶换成装着那种流体的桶。" + B2
    + u"没有桶形态的流体，即原油、石脑油、液化石油气，一律拒收，只能用泵抽。")
NEW[u"potato_s_t.guide.entry.power.fluids.p3"] = (
    u"流体泵：正面是输入，背面是输出，管道只能接在这两面。右键打开界面调速，范围 0% 到 800%。"
    u"泵本身不存液体，只送目标收得下的流体。" + B2 + u"气体须走流体泵，容器换流器不处理气罐。")

NEW[u"potato_s_t.guide.entry.oil.crude.p1"] = (
    u"地表与海洋都有油田。拎着空油桶右键油田所在的方块，舀出一桶原油，空桶不算数。" + B2
    + u"要走量须靠采油机。它只在海洋油田群系开工，脚下不是海洋油田即停机。")
NEW[u"potato_s_t.guide.entry.oil.crude.p2"] = (
    u"采油机在机器正下方往下挂锁链，且锁链须泡在水里。含水锁链的根数记作 n。"
    u"耗电 8n² 加 80n FE/t，产油 10n mB/s，自带 25 桶大罐。" + B2
    + u"每采出 25 到 80 桶，以机器为中心 10×10 个区块的海洋油田会变成旁边的普通海洋。"
    u"那 100 个区块包含机器自身，抽完须把机器挪到还剩油田的位置。")

NEW[u"potato_s_t.guide.entry.oil.distillation.p1"] = (
    u"分馏塔控制器认的是一座 4×4×7、共 7 层的塔。第 1、2 层四角放一般金属块。"
    u"第 3、5 层的角是一般金属块，边是耐热金属块，正中 2×2 是加热装置。"
    u"第 4、6 层围一圈耐热金属块。第 7 层 4×4 全铺一般金属块。" + B2 + u"图纸上画成空心的那些格子不放方块。")
NEW[u"potato_s_t.guide.entry.oil.distillation.p2"] = (
    u"分馏塔操作器才是真正干活的那台。每座塔的容量是原油 12 桶、每种产品 2.5 桶。"
    u"给它红石信号即开始工作。" + B2
    + u"一座塔把原油分成五份：柴油、汽油、石脑油、液化石油气与沥青。塔越多，产能与罐容越大。")

NEW[u"potato_s_t.guide.entry.oil.chemistry.p1"] = (
    u"燃烧反应室：燃料槽放原版熔炉认的燃料，岩浆桶 10 秒、柴油或汽油桶 30 秒、其余 3 秒。"
    u"消耗 1 份燃料加 10 mB 氧气开始反应。反应期间每 tick 给动力能源捕获器 800 点动力，"
    u"柴油 1200、汽油 1000。" + B2 + u"把它贴在捕获器旁边。")
NEW[u"potato_s_t.guide.entry.oil.chemistry.p2"] = (
    u"空气分离器每 tick 要 200 FE，产出氮气与氧气。原料是空气，取之不尽。" + B2
    + u"合成氨反应室要三样：原料罐里的氮气与氢气，再加一个铁粉当催化剂，铁粉不消耗。"
    u"产出的氨气是硝酸的原料。")
NEW[u"potato_s_t.guide.entry.oil.chemistry.p3"] = (
    u"加氢脱硫反应室每批吃 16 个沥青加 1000 mB 氢气，产出硫。硫是硫酸的原料。"
    u"这台机器不耗电，靠的是化学。" + B2
    + u"酸性反应室每 tick 要 500 FE，四条配方见 JEI：碳酸、硝酸、硫酸、盐酸。")

NEW[u"potato_s_t.guide.entry.oil.diesel_gen.p1"] = (
    u"大型柴油发电机是 3×5×2、30 格的多方块。以控制器朝向为正面，朝它背后铺 5 排、向上 2 层，"
    u"一格都不能少。" + B2 + u"里面的铜块与铜格栅不限氧化程度，打蜡与否都行，16 种全收。"
    u"摆齐后控制器正上方那格接线块变成接线口。电只从那里出。")
NEW[u"potato_s_t.guide.entry.oil.diesel_gen.p2"] = (
    u"界面只有一个 8000 mB 柴油罐和一盏工作灯。每 tick 烧 1 mB 柴油，发 7200 FE。"
    u"通入红石信号即停机。" + B2
    + u"柴油接泵灌入，也可拿柴油桶右键控制器倒。里面那台流体泵、两台低级发电机、"
    u"一台燃烧反应室成型后照样是它们自己。")

NEW[u"potato_s_t.guide.entry.starfall.sky_and_star.p1"] = (
    u"星仪图之章右键顺次切换主世界的天空盒，潜行右键往回切。四张星图与原版星空循环。" + B2
    + u"这个设定记在书自己的组件里，只有你自己看得见。同服的人看到的仍是原版天空。")
NEW[u"potato_s_t.guide.entry.starfall.sky_and_star.p2"] = (
    u"星轨坠右键甩出，30 秒后陨石从 y 等于 200 砸下。前 10 秒可再右键一次取消，之后锁定，"
    u"全服都会看到倒计时与坐标。" + B2
    + u"落地是 7 到 20 威力的爆炸，并喷出一批粗矿。威力 7 到 12 只有粗铁与粗铜，"
    u"13 以上是全部粗矿，15 以上额外加 3 个粗振金。")

NEW[u"potato_s_t.guide.entry.starfall.star_steel.p1"] = (
    u"星璨钢套与夜同频。夜幕落下时每一件都获得抗性提升 I，此时装备不磨损。"
    u"四件共振后在末地之中永不磨损。" + B2
    + u"它还会在 20×20 内寻一处落脚的方块，先托住你，再抹去坠落。若四下无物，"
    u"便与附近的生物交换位置。")
NEW[u"potato_s_t.guide.entry.starfall.star_steel.p2"] = (
    u"星璨钢剑 Shift 加右键消耗 100 点耐久，斩出一道 8 格长的星辉剑气，贯穿沿途所有敌人，"
    u"各受 12 点伤害，并被星辉照亮 5 秒。星璨钢斧同理，放出的是 6 格宽、专拆原木的冲击波。" + B2
    + u"振金套是另一条路：全套无限耐久，免疫弹射物与摔落伤害，抗性提升 I 常驻。")

NEW[u"potato_s_t.guide.entry.faq.machine.p1"] = (
    u"按这个顺序查。一是旁边有没有红石信号，通着就停机。二是多方块外壳上有没有接线块，"
    u"电进不来就不干活。三是结构缺口，右键主控，缺哪一格它会把坐标打在聊天栏。"
    u"四是空手潜行右键看逐槽诊断，它会说清缺什么。" + B2
    + u"罐满、输出槽堵住、催化剂没放，都会让机器停下。")
NEW[u"potato_s_t.guide.entry.faq.fluid.p1"] = (
    u"多半是这三件事。一个罐只装一种流体，装过别的须先清空。"
    u"原油、石脑油、液化石油气没有桶形态，容器换流器一律拒收，只能用流体泵抽。"
    u"气体须走高压气罐和泵。" + B2 + u"还有一条：机器的流体罐通常只出不进或只进不出，接管子前先看清提示。")


def read_val(loc, key):
    with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
        return json.load(f)[key]


def main():
    zh = json.load(io.open(os.path.join(LANGDIR, u"zh_cn.json"), encoding=u"utf-8"))
    edits = []
    skip = []
    for key, new in sorted(NEW.items()):
        old = zh[key]
        if old == new:
            skip.append(key)
            continue
        edits.append((u"zh_cn", key, old, new))

    import _rzh_fix_batch as fb
    fb.SUBSTITUTIONS = []
    fb.REGEX_SUBST = []
    fb.EDITS = edits
    if skip:
        print(u"（%d 条已是目标值，跳过）" % len(skip))
    print(u"待改 %d 条" % len(edits))
    return fb.main()


if __name__ == u"__main__":
    sys.exit(main())
