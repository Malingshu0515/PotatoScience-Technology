# -*- coding: utf-8 -*-
r"""_rzh_patch_en.py —— 写 en_us 补丁（手册正文 44 + 配置 31 + 其余 4）。

口径（用户原话）：正常成年人语言；无感叹号、破折号、括号解释、口语备注；
不用 can / be able to 这类空转词；句子短、主谓宾清晰；不写抒情句；
数据、参数、限定词（only / must / cannot）必须准确。
数字一律阿拉伯数字（已由 `_rzh_numstyle.py` 确认：en_us 42 条含 FE 的值里 22 条用阿拉伯数字）。

本文件只产出 `_rzh_patch_A_en_us.json`，**不碰正式语言文件**；
落盘交给 `_rzh_guide_merge.py`（键集合 / 禁词 / $(br2) / 占位符 / 数字 五道校验）。

用法：`python build/zftools/_rzh_patch_en.py`
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

import _rzh_guide_zh as GZ                                   # noqa: E402

B2 = u"$(br2)"
G = u"potato_s_t.guide."
E = G + u"entry."

T = {}

# ---------------------------------------------------------------------------
# A 手册正文
# ---------------------------------------------------------------------------
T[G + u"category.getting_started.desc"] = u"The first machine, the first production line, and the rules every machine shares."
T[G + u"category.materials.desc"] = u"How ore becomes dust, ingots and plates, plus the blast furnace, alloys and titanium."
T[G + u"category.power.desc"] = u"Wiring, generation, storage, and how fluids and gases are moved."
T[G + u"category.oil.desc"] = u"Where crude oil comes from, how to lay out the distillation tower, and the four chemical machines."
T[G + u"category.starfall.desc"] = u"Stargazing, calling down meteors, and arming yourself with Star Steel and Vibranium."
T[G + u"category.faq.desc"] = u"A machine that will not run, or fluids that will not match. Read these two pages first."

T[G + u"landing"] = (
    u"This book tracks the mod version. Every step points to a recipe listed in JEI. "
    u"Pick a chapter on the left and start with Getting Started." + B2
    + u"If you lose the book, craft another from one vanilla book and one iron ingot.")

T[E + u"getting_started.start.p1"] = (
    u"The main line has five steps: grind raw ore into dust, smelt dust into ingots in the Electric Blast Furnace, "
    u"press ingots into plates, expand into power and chemistry, and finish with the meteor." + B2
    + u"Nothing is made without dust, so the first build is a Micro Crusher. "
    u"It needs a steady power supply, and a Low-Tier Generator burning coal or charcoal covers that at the start.")
T[E + u"getting_started.start.p2"] = (
    u"Place the crusher in the middle of your work area and leave one block of clearance in front of it. "
    u"Then run power to it: build a Low-Tier Generator and carry the power over with terminal blocks or cable. "
    u"See the Power chapter." + B2
    + u"Dust is the foundation of everything later. Grind every raw ore you find and do not worry about the amount.")

T[E + u"getting_started.first_line.p1"] = (
    u"A complete starter line has four steps: raw ore into the Micro Crusher becomes dust, dust into the "
    u"Electric Blast Furnace becomes an ingot, and an ingot into the Hydraulic Press becomes a plate." + B2
    + u"Plates are a common part of nearly every machine, so press a batch whenever you run low. "
    u"Ingots can also be crafted directly, so not every ingot has to become a plate. "
    u"Bitumen is pressed 12 at a time.")

T[E + u"getting_started.rules.p1"] = (
    u"Every machine follows one hard rule: a redstone signal stops it and the progress is kept. "
    u"For an on/off switch, place a lever or redstone line next to the machine." + B2
    + u"A machine accepts its own ingredients only. If you insert the wrong item, the interface states what it refuses.")
T[E + u"getting_started.rules.p2"] = (
    u"Sneak-right-click any machine with an empty hand for a slot-by-slot diagnosis. "
    u"It reports which slot lacks what, which tank is empty, and whether power is missing." + B2
    + u"The energy bar, fluid tanks, progress bar and status lamp on the interface are all live. "
    u"When the status lamp turns red, read the diagnosis first and act on what it names.")

T[E + u"materials.ore_chain.p1"] = (
    u"There are 9 ores: aluminum, cobalt, nickel, silver, uranium, manganese, lithium, tungsten and titanium. "
    u"7 of them have a deepslate variant." + B2
    + u"The standard process has three steps: raw ore into the Micro Crusher becomes dust, "
    u"and dust into the Electric Blast Furnace becomes an ingot. "
    u"Sand, raw aluminum and raw silver can also be smelted in a vanilla furnace, but dust in the blast furnace yields more.")
T[E + u"materials.ore_chain.p2"] = (
    u"Press ingots into plates with the Hydraulic Press: iron, copper, nickel, cobalt, silver, aluminum and steel plates. "
    u"Plates are a common part of nearly every machine, so press a batch of whatever you lack." + B2
    + u"A redstone signal stops the press and the progress is kept.")

T[E + u"materials.blast_alloy.p1"] = (
    u"The Electric Blast Furnace is a 3x3x3 multiblock, assembled directly on a vanilla blast furnace. "
    u"It has 12 input slots and 32 output slots. Each slot finishes in 10 seconds and every item costs 800 FE." + B2
    + u"Besides this mod's ore processing, anything a vanilla blast furnace can smelt works here. "
    u"Dust in the blast furnace yields more than in a vanilla furnace.")
T[E + u"materials.blast_alloy.p2"] = (
    u"The Alloy Smelter Controller must be laid out in 4 layers, 58 cells in total: the floor, "
    u"the three-high walls, and those two rows of heat-resistant metal on the roof. "
    u"The shell also needs at least 1 wiring block before it activates on its own." + B2
    + u"The interface has 5 input slots that accept ingots only, 3 output slots and 2 consumption slots. "
    u"Storage is 32768 FE and power enters through the port only.")
T[E + u"materials.blast_alloy.p3"] = (
    u"The titanium line: grind raw titanium into titanium dust, then smelt the dust into a titanium ingot "
    u"in the Electric Blast Furnace." + B2
    + u"Titanium then goes into alloys: light titanium alloy, hard titanium alloy and the stable metal block. "
    u"The Acidic Reaction Chamber and the Lithium Battery both need them. "
    u"The titanium alloy sword and pickaxe are also made from light titanium alloy.")

T[E + u"materials.salt.p1"] = (
    u"The Salt Dryer only works in an ocean or salty river biome, between Y 0 and 64, "
    u"with a water source block below it. Passive drying yields 1 sea salt every 120 seconds." + B2
    + u"Supply power and it yields 1 every 20 seconds.")
T[E + u"materials.salt.p2"] = (
    u"Note: sea salt that falls into water dissolves and is lost." + B2
    + u"The Salt Decomposer takes 64 sea salt and yields 1 sodium chloride after 40 seconds. "
    u"It returns those 64 sea salt with a 60% chance, and adds one random raw ore with a separate 5% chance. "
    u"Place sea salt in the Electrolyzer's electrolyte slot to produce extra chlorine while electrolysing water, "
    u"at the cost of 1 extra sea salt per 500 mB of water.")

T[E + u"power.wiring.p1"] = (
    u"Terminal blocks carry power over distance. Right-click to place the first terminal and select it, "
    u"then right-click a second terminal to link the two. If the distance is too great it refuses and states the limit." + B2
    + u"The wiring block on a machine shell is the power inlet and outlet; that cell becomes a port once the multiblock forms. "
    u"Connect terminals to those.")
T[E + u"power.wiring.p2"] = (
    u"Cable spools also link terminals. Copper and silver spools both reach 16 blocks and both have 32 durability, "
    u"and both return an empty spool when spent. The difference is the rate: copper carries 2048 FE/t and silver 16134 FE/t." + B2
    + u"A power cable spool carries power rather than FE. The Power Capturer uses it to draw power in.")

T[E + u"power.generation.p1"] = (
    u"The Low-Tier Generator burns coal or charcoal for power, and a redstone signal stops it. "
    u"It is the simplest power source at the start, and one unit is enough to run a Micro Crusher.")
T[E + u"power.generation.p2"] = (
    u"The Solar Panel generates power in daylight only and is strongest near noon. "
    u"The block directly above it must be air or colorless glass. "
    u"Horizontally adjacent panels link up on their own and share generation and storage across the group." + B2
    + u"Output is 60% in rain, 20% in a thunderstorm, and zero at night.")
T[E + u"power.generation.p3"] = (
    u"For larger amounts of power, use the power line. The Power Capturer draws power while it sits next to a power source "
    u"and delivers it over power cables. A generator then converts that power into FE at 2 FE/t per point." + B2
    + u"These three machines together are what starts the industrial stage.")

T[E + u"power.storage.p1"] = (
    u"One ternary polymer lithium battery stores 4M FE. Batteries placed edge to edge in a solid cuboid merge into "
    u"a single multiblock on their own, and the capacity adds up per block. The top face is the only face that transfers FE." + B2
    + u"The base accepts 6 footprints only: 2x2, 2x3, 3x3, 3x4, 4x4 and 5x5. "
    u"2x2 reaches 6 layers, 2x3, 3x3 and 3x4 reach 12 layers, and 4x4 and 5x5 reach 32 layers.")
T[E + u"power.storage.p2"] = (
    u"A battery needs components first. The Lithium Battery Plant takes four inputs: raw manganese or raw aluminum, "
    u"a nickel ingot or raw nickel, lithium carbonate, and a cobalt ingot or raw cobalt. "
    u"Feed in sulfuric acid and it yields one lithium battery component every 30 seconds." + B2
    + u"This machine uses no power, because it runs on chemistry. "
    u"Lithium carbonate comes from grinding raw lithium into lithium concentrate and smelting that in the Electric Blast Furnace.")

T[E + u"power.fluids.p1"] = (
    u"Liquids travel in oil buckets and gases in high pressure tanks. Both are filled by the Filling Machine. "
    u"The Filling Machine holds five 5000 mB tanks, and one tank holds one fluid only. "
    u"Right-click the machine with an oil bucket or a gas tank in hand to pour its contents into a tank." + B2
    + u"Filling runs at 5 mB/t per tank, and each working tank draws 60 FE/t.")
T[E + u"power.fluids.p2"] = (
    u"To put fluid from a machine back into a bucket, use the Fluid Exchanger: an oil bucket or gas tank holding fluid "
    u"in the left slot, one empty bucket in the right slot, and it turns the empty bucket into a bucket of that fluid." + B2
    + u"Fluids with no bucket form, namely crude oil, naphtha and LPG, are refused outright. A pump is the only way to move those.")
T[E + u"power.fluids.p3"] = (
    u"The Fluid Pump: the front face is the input and the back face is the output, and pipes attach to those two faces only. "
    u"Right-click for the rate control, which spans 0% to 800%. The pump stores no fluid itself and moves only what "
    u"the destination accepts." + B2 + u"Gases must go through a Fluid Pump. The Fluid Exchanger does not handle gas tanks.")

T[E + u"oil.crude.p1"] = (
    u"Oil fields occur on land and under the ocean. Right-click the block of an oil field with an empty oil bucket "
    u"to scoop one bucket of crude oil. An empty bucket alone does not work." + B2
    + u"Volume requires the Oil Pump. It runs in the Ocean Oilfield biome only, and stops anywhere else.")
T[E + u"oil.crude.p2"] = (
    u"The Oil Pump hangs a chain downward from directly below the machine, and that chain must be waterlogged. "
    u"The number of waterlogged chain blocks is n. It draws 8n² plus 80n FE/t and produces 10n mB/s, "
    u"and it carries a 25-bucket tank." + B2
    + u"Every 25 to 80 buckets pumped, the ocean oilfield in a 10x10 chunk area centred on the machine "
    u"turns into the ordinary ocean nearby. Those 100 chunks include the machine itself, so move the machine "
    u"to a remaining oilfield afterwards.")

T[E + u"oil.distillation.p1"] = (
    u"The Distillation Tower Controller recognises a tower of 4x4x7, 7 layers in total. "
    u"Layers 1 and 2 carry common metal blocks in the four corners. "
    u"In layers 3 and 5 the corners are common metal blocks, the edges are heat-resistant metal blocks, "
    u"and the central 2x2 is heaters. Layers 4 and 6 are a ring of heat-resistant metal blocks. "
    u"Layer 7 is common metal blocks across the whole 4x4." + B2 + u"Cells drawn hollow on the blueprint take no block.")
T[E + u"oil.distillation.p2"] = (
    u"The Distillation Operator is the machine that does the work. Each tower holds 12 buckets of crude oil "
    u"and 2.5 buckets of each product, and a redstone signal starts it." + B2
    + u"One tower splits crude oil into five parts: diesel, gasoline, naphtha, LPG and bitumen. "
    u"More towers mean more throughput and more tank capacity.")

T[E + u"oil.chemistry.p1"] = (
    u"Combustion Chamber: the fuel slot accepts what a vanilla furnace burns, which is a lava bucket for 10 seconds, "
    u"a diesel or gasoline bucket for 30 seconds, and anything else for 3 seconds. "
    u"One unit of fuel plus 10 mB of oxygen starts the reaction. While it runs, it feeds 800 power per tick to the "
    u"Power Capturer, or 1200 for diesel and 1000 for gasoline." + B2 + u"Place it next to the Capturer.")
T[E + u"oil.chemistry.p2"] = (
    u"The Air Separator draws 200 FE per tick and yields nitrogen and oxygen. The raw material is air, which never runs out." + B2
    + u"The Ammonia Synthesis Chamber needs three things: nitrogen and hydrogen in the input tanks, "
    u"plus one iron dust as a catalyst that is not consumed. The ammonia it yields is the raw material for nitric acid.")
T[E + u"oil.chemistry.p3"] = (
    u"The Hydrodesulfurization Chamber takes 16 bitumen plus 1000 mB of hydrogen per batch and yields sulfur, "
    u"which is the raw material for sulfuric acid. This machine uses no power, because it runs on chemistry." + B2
    + u"The Acidic Reaction Chamber draws 500 FE per tick, and its four recipes are listed in JEI: "
    u"carbonic acid, nitric acid, sulfuric acid and hydrochloric acid.")

T[E + u"oil.diesel_gen.p1"] = (
    u"The Large Diesel Generator is a 3x5x2 multiblock of 30 cells. With the controller's facing as the front, "
    u"it extends 5 rows back and 2 layers up, and not one cell may be missing." + B2
    + u"The copper blocks and grates inside accept any oxidation level, waxed or not, so all 16 variants count. "
    u"Once complete, the wiring block directly above the controller becomes a port, and power leaves through that port only.")
T[E + u"oil.diesel_gen.p2"] = (
    u"The interface holds one 8000 mB diesel tank and one status lamp. It burns 1 mB of diesel per tick and "
    u"generates 7200 FE. A redstone signal stops it." + B2
    + u"Diesel enters by pump, or right-click the controller with a diesel bucket. "
    u"The fluid pump, the two low-tier generators and the combustion chamber inside remain themselves after forming.")

T[E + u"starfall.sky_and_star.p1"] = (
    u"Right-click the Star Chart Tome to cycle the Overworld skybox forward, and sneak-right-click to cycle it back. "
    u"Four star charts plus the vanilla sky form the loop." + B2
    + u"The setting is stored in the tome's own components and is visible to you alone. "
    u"Other players on the server still see the vanilla sky.")
T[E + u"starfall.sky_and_star.p2"] = (
    u"Right-click the Starfall Pendant to throw it. The meteor falls from y = 200 after 30 seconds. "
    u"The first 10 seconds allow a second right-click to cancel it, after which it locks and the whole server "
    u"sees the countdown and the coordinates." + B2
    + u"Impact is an explosion of power 7 to 20 and sprays a batch of raw ore. "
    u"Power 7 to 12 yields raw iron and raw copper only, 13 and above yields every raw ore, "
    u"and 15 and above adds 3 raw vibranium.")

T[E + u"starfall.star_steel.p1"] = (
    u"The Star Steel set is in tune with the night. When darkness falls every piece grants Resistance I "
    u"and the gear does not wear. All four in resonance never wear in the End." + B2
    + u"It also finds a block to stand on within 20x20, catches you first and then erases the fall. "
    u"If nothing stands there, it trades your place with a creature nearby.")
T[E + u"starfall.star_steel.p2"] = (
    u"Shift plus right-click with the Star Steel Sword spends 100 durability and cuts an 8-block starlight slash "
    u"that pierces every enemy along its path for 12 damage each and lights them for 5 seconds. "
    u"The Star Steel Axe works the same way and releases a 6-block-wide shockwave that fells logs only." + B2
    + u"The Vibranium set is the other route: unbreakable throughout, immune to projectiles and fall damage, "
    u"with Resistance I at all times.")

T[E + u"faq.machine.p1"] = (
    u"Check in this order. First, whether a redstone signal is present, because that stops the machine. "
    u"Second, whether the multiblock shell carries a wiring block, because no power means no work. "
    u"Third, a structure gap: right-click the controller and it prints the coordinates of the missing cell to chat. "
    u"Fourth, sneak-right-click with an empty hand for the slot-by-slot diagnosis, which names what is missing." + B2
    + u"A full tank, a blocked output slot or a missing catalyst also stops a machine.")
T[E + u"faq.fluid.p1"] = (
    u"It is almost always one of three things. A tank holds one fluid only, so a tank that held something else "
    u"must be emptied first. Crude oil, naphtha and LPG have no bucket form, so the Fluid Exchanger refuses them "
    u"and only a pump can move them. Gases must go through high pressure tanks and pumps." + B2
    + u"One more: a machine's fluid tanks are usually output-only or input-only, so read the tooltip before attaching pipes.")

# ---------------------------------------------------------------------------
# B 配置说明
# ---------------------------------------------------------------------------
T[u"potato_s_t.configuration.black_hole.lifetime_seconds.tooltip"] = (
    u"How many seconds a black hole exists (5-120, default 20). A longer life pulls more blocks and costs more performance.")
T[u"potato_s_t.configuration.black_hole.max_blocks.tooltip"] = (
    u"How many blocks one black hole may move (100-5000, default 1500).")
T[u"potato_s_t.configuration.black_hole.scan_radius_blocks.tooltip"] = (
    u"Each axis spans +/- N blocks around the hole (8-80, default 40 = 5x5x5 chunks). Each added block grows the "
    u"scanned volume cubically. Raise it only after checking your TPS.")
T[u"potato_s_t.configuration.black_hole.pull_entities.tooltip"] = (
    u"Whether creatures, players included, are pulled toward the singularity. Default on. Off means blocks only.")
T[u"potato_s_t.configuration.black_hole.void_damage.tooltip"] = (
    u"Whether creatures inside the event horizon, 6 blocks, take continuous void damage. Default on. "
    u"Off means it pulls creatures only and deals no damage.")
T[u"potato_s_t.configuration.black_hole.one_shot.tooltip"] = (
    u"On: the gravity device places one black hole only. Off: it consumes power only and can be reused.")
T[u"potato_s_t.configuration.gravity_device.charge_seconds.tooltip"] = (
    u"How long right-click is held before the black hole is released (5-60, default 30 seconds).")
T[u"potato_s_t.configuration.gravity_device.capacity_fe.tooltip"] = (
    u"How much energy the gravity device holds (1,000,000-64,000,000, default 8,000,000).")
T[u"potato_s_t.configuration.lithium_battery.per_block_fe.tooltip"] = (
    u"How much energy one lithium battery stores (1,000,000-20,000,000, default 4,000,000); "
    u"the multiblock total is the block count times this value.")
T[u"potato_s_t.configuration.lithium_battery.transfer_rate_fe.tooltip"] = (
    u"How much energy may enter or leave each face per tick (1,024-1,048,576, default 65,536).")
T[u"potato_s_t.configuration.lithium_battery.max_size_blocks.tooltip"] = (
    u"How many blocks one battery may combine (27-800, default 800).")

T[u"potato_s_t.configuration.section.potato.s.t.common.toml.title"] = u"PotatoS&T common configuration"
T[u"potato_s_t.configuration.title"] = u"PotatoS&T configuration"
T[u"potato_s_t.configuration.black_hole.lifetime_seconds"] = u"Black hole lifetime (seconds)"
T[u"potato_s_t.configuration.black_hole.max_blocks"] = u"Blocks moved per black hole"
T[u"potato_s_t.configuration.black_hole.one_shot"] = u"One-shot black hole"
T[u"potato_s_t.configuration.black_hole.scan_radius_blocks"] = u"Scan radius (blocks)"
T[u"potato_s_t.configuration.black_hole.pull_entities"] = u"Pull creatures"
T[u"potato_s_t.configuration.black_hole.void_damage"] = u"Void damage inside the horizon"
T[u"potato_s_t.configuration.gravity_device.capacity_fe"] = u"Energy capacity (FE)"
T[u"potato_s_t.configuration.gravity_device.charge_seconds"] = u"Charge time (seconds)"
T[u"potato_s_t.configuration.lithium_battery.max_size_blocks"] = u"Multiblock block limit"
T[u"potato_s_t.configuration.lithium_battery.per_block_fe"] = u"Capacity per block (FE)"
T[u"potato_s_t.configuration.lithium_battery.transfer_rate_fe"] = u"Rate per face (FE/t)"
T[u"potato_s_t.configuration.section.black_hole"] = u"Black hole"
T[u"potato_s_t.configuration.section.black_hole.button"] = u"Black hole"
T[u"potato_s_t.configuration.section.gravity_device"] = u"Gravity device"
T[u"potato_s_t.configuration.section.gravity_device.button"] = u"Gravity device"
T[u"potato_s_t.configuration.section.lithium_battery"] = u"Lithium battery"
T[u"potato_s_t.configuration.section.lithium_battery.button"] = u"Lithium battery"
T[u"potato_s_t.configuration.section.potato.s.t.common.toml"] = u"Common"

# ---------------------------------------------------------------------------
# C 其余
# ---------------------------------------------------------------------------
T[u"tooltip.potato_s_t.cola.1"] = u"Gamer Fuel"
T[u"tooltip.potato_s_t.cola.2"] = u"Grants positive effects when drunk"
T[u"tooltip.potato_s_t.gravity_device.one_shot.on"] = u"Single-use item (can be disabled in the config)"
T[u"tooltip.potato_s_t.gravity_device.one_shot.off"] = u"Reusable: consumes power only"


def main():
    current = json.load(io.open(os.path.join(LANGDIR, u"en_us.json"), encoding=u"utf-8"))
    patch = {}
    for k, v in T.items():
        patch[k] = v
    p = os.path.join(HERE, u"_rzh_patch_A_en_us.json")
    io.open(p, u"w", encoding=u"utf-8", newline=u"\n").write(
        json.dumps(patch, ensure_ascii=False, indent=2) + u"\n")
    print(u"wrote %s（%d 键）" % (p, len(patch)))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
