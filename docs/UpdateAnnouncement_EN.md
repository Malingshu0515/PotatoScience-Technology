# PotatoS&T — 0.11 Content Overview & Update Notes

**Minecraft 1.21.1 · NeoForge 21.1.235 · Java 21 · English / 中文 / 日本語 / Русский**

PotatoS&T is an industrial tech mod. You mine ore, crush it, smelt it, press it, alloy it, and wire
the whole thing into a small power grid. Energy is measured in **FE** (NeoForge Energy), and there is a
second resource called **Power** — kinetic energy you capture from vanilla machines and turn back into
electricity through a Generator.

Everything listed below is implemented and shipped in 0.11. JEI support is built in (the mod runs fine
without it), Jade shows the energy buffers, and **27 advancements** walk you from your first machine
all the way to the acidic reaction chamber — one tab, four branches, no busywork steps.

---

## 1. The power network

| Block | What it does |
|---|---|
| **Terminal Block** | The mod's power node. 2,048 FE buffer (2,048 FE/t transfer) and 8,192 Power buffer (128 Power/t). Right-click to cycle its mode: **None / Input / Output**. |
| **Power Cable Spool** | The linking tool. Right-click one terminal, then right-click a second one to link them — **max link distance 16 blocks**. Linked terminals balance their buffers. |
| **Creative Cable** | Infinite FE source. Right-click to set the transfer rate (creative/testing). |

Machines do **not** need cables: any machine placed directly next to a terminal exchanges energy with
it. Link terminals to bridge distance, or to connect the two sides of a machine hall.

## 2. Power generation

| Source | Numbers |
|---|---|
| **Low-Tier Generator** | Burns coal or charcoal: **45 s at 100 FE/t per fuel item = 90,000 FE**. 1,000 FE buffer. Burning pauses when full, so no fuel is wasted. Redstone signal = off. |
| **Solar Panel** | Daytime only: **60 FE/t** at dawn/dusk, **135** in the morning/afternoon, **180** at noon. Rain → 60 %, thunderstorm → 20 %. The block above must be air or colorless glass. 512 FE per panel; horizontally adjacent panels merge into a shared pool and push FE into the block below. |
| **Power Capturer** | Watches its 6 faces and produces Power from vanilla machines: flowing water **+8**, burning furnace/smoker **+8**, burning blast furnace **+16** Power/t. Feeds the terminal next to it. |
| **Generator** | Converts Power into FE at **2 FE per Power**, up to 128 Power/t (**256 FE/t**). 100,000 FE buffer. |
| **Lithium Battery** | **4,000,000 FE per block.** Solid cuboids merge into one multiblock: 2×2 up to 6 high, 2×3 / 3×3 / 3×4 up to 12 high, 4×4 / 5×5 up to 32 high. Only the top face accepts terminals. |
The joke in "A Stronger Power Source" is literal: you really do capture Power from a burning furnace,
send it through a terminal link, and convert it back into electricity.

## 3. Single-block machines

| Machine | What it does | Numbers |
|---|---|---|
| **Micro Crusher** | Crushes ores, gems, logs and ingots (full list in its tooltip and in JEI). Redstone signal turns it **off**. | 2,500 FE buffer; up to 400 FE/t |
| **Hydraulic Press** | Presses ingots into plates: copper, iron, nickel, cobalt, silver, aluminum, steel. **12 Bitumen → 1 Asphalt Block** (decorative). | 400 FE/t × 3 s = **24,000 FE per plate**; buffer is exactly one plate |
| **Filling Machine** | Fills High-Pressure Gas Tanks from five independent tanks (oxygen / hydrogen / chlorine). | 5 × 5,000 mB tanks, 5 mB/t per tank, 60 FE/t per working tank, 3,000 FE buffer |
| **Salt Dryer** | Ocean or Salty River biome, Y 0–64, water source below → sea salt. | passive: 1 salt / **120 s**; powered: 1 salt / **20 s** at 70 FE/t; 210 FE buffer |
| **Salt Decomposer** | 64 sea salt → sodium chloride, with a chance of extra loot. | 40 s, 20 FE/t; **100 %** sodium chloride, **60 %** returns 64 sea salt, **5 %** one random raw ore. Stores only **20 FE**, so it needs a continuous supply — by design |
| **Electrolyzer** | Splits water into gases. Without sea salt: **3 oxygen + 6 hydrogen** per tick. With sea salt in the electrolyte slot: **3 chlorine + 6 hydrogen**. | 1,000 FE/t + 10 mB water/t; 1 sea salt per 500 mB; 20,000 FE buffer |
| **Fluid Pump** + **Fluid Pipe** | Moves fluids. The pump's front face is the input, the back face is the output; right-click to set the rate (0–800 %). | **The pump stores no fluid itself** (0.11 ZF98): whatever it pulls out goes straight into the destination in the same tick, and it only moves fluids the destination accepts — anything refused is left in the source. Two pumps can no longer be chained nose-to-tail (there is no internal tank); raise the rate for more range, or put a tank in between. |
| **Hydrodesulfurization Chamber** (new in 0.11) | Turns bitumen into **sulfur** with hydrogen: **16 Bitumen + 1000 mB hydrogen → 1 Sulfur**. Feed it through pipes/pumps, or right-click the machine with a gas tank full of hydrogen to pour 1000 mB per click. | **10 s per batch**; 4,000 mB hydrogen tank; **no energy at all** (it does not take FE); a redstone signal stops it and the progress is kept |
| **Air Separator** (new in 0.11) | Splits air into **8 mB nitrogen + 2 mB oxygen every 30 s**. **The two tanks are output-only**: pumps can drain them, but nothing can be piped or poured in. Its panel has exactly two tanks and a status lamp - no energy bar, no progress bar. While it is actually running it puffs **white smoke** from its top face (vanilla cloud particles; nothing while it is unpowered, full or switched off). | 200 FE/t; **5,000 FE** buffer; a redstone signal stops it (progress is kept) |
| **Ammonia Synthesis Chamber** (new in 0.11) | **1 mB nitrogen + 1 mB hydrogen + 200 FE → 1 mB ammonia** every tick. The catalyst slot takes **iron dust** and never consumes it; the gas-tank slots under the input tanks feed nitrogen/hydrogen **into** the machine (50 mB/t) while the one under the output tank works the other way (ammonia **out** into a gas tank, 50 mB/t). Pipes may only push nitrogen/hydrogen in and pull ammonia out. | 200 FE/t; 4,096 FE buffer; three 4,000 mB tanks; a redstone signal stops it |
| **Test Fluid Tank** / **Creative Cable** | Creative-mode testing blocks. | — |

## 4. Multiblocks

### Electric Blast Furnace
Build a **3×3×3 shell around a vanilla Blast Furnace** (25 blocks: common metal blocks, 1 heater,
2 wiring blocks, iron bars and an iron trapdoor), then **shift + right-click it with an empty hand**.
The anchor may be **either a vanilla blast furnace or this mod's own controller block** (0.11 ZF100 -
craft the controller from a blast furnace + a capacitor + a heater + 2 wiring blocks + 4 iron plates,
place it where the blast furnace would go, build the same shell and shift + right-click the
controller). Hold a **Wrench** and shift + right-click to take it apart again.

- 12 input + 32 output slots; each slot finishes in **10 seconds**; **800 FE per item**; 4,096 FE
  buffer; a full load draws about **3,072 FE/t**.
- Raw ore → **2 ingots**; ore blocks → **3–6 ingots**; sand → silicon;
  **iron dust + carbon dust → high carbon steel**; **iron dust + gravel → magnet**
  (any two input slots pair up automatically).
- It also smelts everything a vanilla blast furnace can, including other mods' blasting recipes.

### Alloy Smelter
A 4-layer, 80-block machine built from a blueprint — the controller's tooltip contains the exact
drawing. It **activates by itself** once the shell is complete (58 cells are checked, and at least one
wiring block must be in the shell); right-clicking the controller also activates it and names the
missing cell. 5 input slots (ingots only) / 3 output / 2 consumable, 32,768 FE, power enters through
the ports only.

Current recipe: **1 aluminium + 1 titanium + 1 silver → 1 Lightweight Titanium Alloy**
(30 s, 800 FE/t = 480,000 FE per item).

### Fractional Distillation Tower (new in 0.11)

Three pieces: the **tower** itself, a **controller**, and an **operator** (the machine with the GUI).

- **The tower** is a 4×4×7 shape you build out of ordinary blocks — you need the Common Metal Block
  (layer 1–2 corners, and layer 7 as a full 4×4 cap), the Heat-Resistant Metal Block (the ring on
  layers 4 and 6, plus the edges of layers 3 and 5) and 8 Heaters (the 2×2 centre of layers 3 and 5).
  Every cell that the blueprint draws as empty must really be air. It is rotation-agnostic.
- **The Controller** scans a 32×32×10 box around itself, counts the completed towers and reports that
  number to every Operator placed next to it. It has no GUI and stores nothing.
- **The Operator** is the machine: right-click it for a large, zero-texture panel with five tanks
  (oil → diesel → naphtha → gasoline → LPG, left to right), a vertical energy bar, a bitumen slot in
  the bottom-right corner and a status line. **It only distills while it has a redstone signal.**
- **Numbers (per tower):** every tick it consumes **8 mB of crude oil and 8096 FE**, and produces
  **3 mB diesel + 2 mB naphtha + 2 mB gasoline + 1 mB LPG** (8 in, 8 out). Every 5 ticks it also
  makes **1 Bitumen**. Buffers scale with the tower count: **8096 FE**, **12 buckets of oil** and
  **2.5 buckets per product tank** — up to **4 towers** are recognised.
- **It stops** when the bitumen slot is full (64 and no room left), when a product tank is full, when
  the oil or the power runs out, or when the redstone signal goes away.
- Pipes can feed crude oil in and pull the four products out; the four product fluids are new
  (diesel / naphtha / gasoline / LPG) and each carries its `c:` common tag.

### Lithium Battery
A stackable multiblock power bank: 4M FE per block, top face only. See the table in section 2.

## 5. Ores, materials and fluids

- **9 new ores** with 7 deepslate variants: aluminum, silver, nickel, cobalt, uranium, manganese,
  lithium, titanium and wolframite. (Aluminum and lithium only generate in their stone variant.)
- The **Salty River** biome, plus **sea salt** (it dissolves if you drop it in water).
- Processing chains: ore → 2 ingots (EBF), ore block → 3–6 ingots, ingot → plate (press),
  copper ingot → 4 copper wire (crusher), lithium → lithium concentrate → lithium carbonate,
  iron dust + carbon dust → high carbon steel, iron dust + gravel → magnet, sand → silicon →
  photovoltaic component → solar panel.
- **Fluids:** oxygen, hydrogen, chlorine, **nitrogen** and **ammonia** (new in 0.11),
  **crude oil** (new in 0.11) and the four
  distillation products — **diesel, naphtha, gasoline and LPG** (new in 0.11).
  High-Pressure Gas Tanks store them — and yes, the hydrogen
  warning is real.

### Crude oil and the Oil Bucket (new in 0.11)

**Crude oil** is a dark, viscous liquid. It is deliberately *not* water-like:

- it **never multiplies** — flowing oil does not turn back into a source block, so a pool you
  scoop out stays empty;
- it spreads at **lava's pace** (30 ticks per step, slope distance 2, level drop 2);
- it does not wet farmland, does not put out fires, and no vanilla bucket can pick it up.

The **Oil Bucket** holds **3000 mB** and is the only container that can take oil:

| | |
|---|---|
| Scooping | right-click a source block: **1000 mB per click** (three clicks fill it) |
| Contents | **one liquid only** — a different fluid, or any gas, simply will not go in |
| Also works on | water and lava (any liquid except the three process gases) |
| Bar | the same white fill bar as the High-Pressure Gas Tank |
| Recipe | copper ingot / bucket / copper ingot, steel plate / bucket / steel plate, iron plate / aluminium ingot / iron plate → **1 Oil Bucket (eats two iron buckets)** |

Crude oil, the three process gases and the four distillation products carry the common `c:` fluid
tags (`c:crude_oil`, `c:gaseous`, `c:oxygen` / `c:hydrogen` / `c:chlorine` and
`c:diesel` / `c:naphtha` / `c:gasoline` / `c:lpg`), so other mods'
recipes and machines can accept them — and this mod accepts anyone else's gas as a gas.

Oil can also be **pumped** with the Fluid Pump and moved through Fluid Pipes — that is how the
distillation tower will be fed once it exists.


## 6. Tools and gear

| Item | Stats |
|---|---|
| **Titanium Alloy Sword** | 6.5 attack damage, 2,048 durability |
| **Titanium Alloy Pickaxe** | 4 attack damage, 4,219 durability, **netherite mining level** |
| Both | mining speed 9.0, enchantability 25, repaired with Lightweight Titanium Alloy, and they sit on the vanilla sword/pickaxe enchantment tags — the enchanting table treats them like any vanilla tool |
| **Wrench** | Shift + right-click to disassemble multiblocks |

### Two new armour sets (new in 0.11 ZF104)

Both sets are crafted nowhere yet — **they are creative-only for now** (ask and recipes can be added).
Inventory icons currently borrow the vanilla **iron** armour sprites, as requested; the worn models
do too, so they look like iron until real art arrives.

| Piece | Titanium Alloy — durability / armour | Star Steel — durability / armour / toughness |
|---|---|---|
| Helmet | 2,801 / **+2.5** | 2,012 / **+5.5** / +0.5 |
| Chestplate | 4,096 / +8 | 3,876 / **+9.5** / **+1** |
| Leggings | 3,412 / +6 | 2,790 / **+7.5** / +0.5 |
| Boots | 2,048 / **+4.5** | 1,754 / **+5.5** / +0.5 |

- **Titanium Alloy set**: enchantability **25** (higher than gold's 22), repaired with
  **Lightweight Titanium Alloy**. The half-point armour values are real — they are written as
  `double` attribute modifiers, not the vanilla integer armour table.
- **Star Steel set**: enchantability **20**, repaired with the new **Star Steel Ingot**
  (no recipe yet — it exists only as a repair material for now).
- **Per piece (no full set needed):** at night you get **Resistance I** — wearing all four is still
  only Resistance I, it does **not** stack — and your armour **does not lose durability at night**.
  During the day (and in the End/Nether) durability is consumed normally.
- **Full set, Overworld, night:** Strength I, Resistance II, plus **10 s of Absorption III every 45 s**.
- **Full set, The End:** Regeneration I, Resistance III, Strength II, plus
  **12 s of Absorption VI every 15 s**.
- **Full set, void damage:** you are teleported to the nearest solid block within **20 × 20 blocks,
  any height** (the search runs from world bottom to world top). If there is truly no block,
  you **swap places with the nearest mob** instead. Both outcomes are reported on the action bar.

## 7. Advancements

One tab ("PotatoS&T"), **27 advancements**, deliberately coarse: only whole machines, key materials and
key recipes get one — intermediate parts (heater, heat sink, spools, plates) are folded into the
description of the step they unlock. Every description tells you **what to do next**, not what you just
picked up.

The tree (indentation = parent chain, `*` = goal frame, `+` = hidden challenge):

```
A New Beginning!        obtain a Micro Crusher
├── Grind It Down       Iron Dust / Carbon Dust
├── Press It Flat       any metal plate
├── Wire It Up          Terminal Block / Wiring Block
├── First Watt          Low-Tier Generator
│   ├── A Stronger Power Source   Generator + Power Capturer
│   └── Clean Energy 101          place a Solar Panel
├── Capacitor           Capacitor
│   ├── * Electric Blast Furnace  controller + 3×3×3 shell
│   │   ├── * Thus Steel Was Made High Carbon Steel
│   │   │   ├── * Titanium        Titanium Ingot
│   │   │   ├── Electrolysis      Electrolyzer
│   │   │   ├── Storing Gas       Gas Tank + Filling Machine
│   │   │   └── Oil               scoop crude oil with an Oil Bucket
│   │   │       └── * Distillation Tower
│   │   │           ├── Diesel & Gasoline
│   │   │           ├── Sulfur
│   │   │           └── * Combustion Chamber ── * Acidic Reaction Chamber
│   │   └── * Alloy Smelter
│   │       ├── Lightweight Titanium Alloy
│   │       │   ├── Titanium Tools
│   │       │   └── * Hard Titanium Alloy ── Stable Metal Block
│   │       └── (…) 
│   └── (Electrolysis ── Ammonia)
└── + The Anvil and the Republic / + Jasmine Flower   the two music discs
```

Notes worth knowing:

- **"A New Beginning!" moved earlier.** It used to require the Low-Tier Generator; it now requires the
  **Micro Crusher** (the first machine you build). Its old wording ("A simple power source - handy and
  sufficient") moved to the new **First Watt** node, so nothing was lost. Already-earned advancements
  are never revoked.
- **Oil is checked properly.** "Oil" does not fire when you craft the empty Oil Bucket — it fires when
  the bucket actually holds crude oil.
- The two music discs are **hidden challenges**: they stay invisible in the tab until you earn them.

## 8. Quality of life

- **JEI:** 11 machine categories with time/energy printed on every recipe
- **Jade:** energy buffers on every machine
- **4 languages:** English, 中文, 日本語, Русский (398 keys each)
- **Sounds:** machine loops for the crusher, press, generator, electrolyzer, filling machine and alloy
  smelter, plus the music discs **"Malingshu - Anvil of the Republic"** (1:43) and
  **"Jasmine Flower (Orchestral)"** (2:27) — both ship as mono 44.1 kHz Ogg Vorbis and stream from disk

## 9. Known gaps (not done yet)

- **Still creative-only (a few items, not blocks you need)**: the **Wrench**, the **Advanced Metal
  Block** and the **Stable Metal Block** have no crafting recipe yet. The **Lithium Battery** and the
  **Electric Blast Furnace controller** **got their recipes in this build** (0.11 ZF100), and so did
  the Alloy Smelter Controller, both Distillation Tower pieces and both music discs earlier in 0.11.
  The Wrench matters most: multiblocks are disassembled with it, so it is still creative-only for now.
- **Tungsten is a dead end for now**: wolframite ore exists and drops raw tungsten, but nothing
  consumes it yet (it is deliberately not smeltable).
- **Some textures are placeholders** borrowed from vanilla (13 models still do this — the count
  went up because the eight new armour pieces borrow the vanilla iron armour sprites); on top of
  that the distillation assets are placeholders too — Bitumen is a copy of the vanilla
  gunpowder sprite and the Tower Controller / Operator block textures are generated grey metal.
  The **Hydrodesulfurization Chamber** and **Sulfur** (new in 0.11) are generated placeholders as
  well: a grey chamber with an amber reaction window, and a yellow powder pile. So are the
  **Air Separator**, the **Ammonia Synthesis Chamber** and the two new gases (nitrogen / ammonia).
- **Bitumen's only use so far** is the **Hydrodesulfurization Chamber** (16 bitumen + 1000 mB
  hydrogen → 1 sulfur); it is still deliberately not a fuel.
- **Sulfur has no use yet** — the new Chamber is the only thing that makes it, and nothing consumes
  it. It is deliberately not a fuel either.
- **Ammonia has no use yet** either: the Ammonia Synthesis Chamber makes it, nothing consumes it,
  and it has no bucket (like every other gas). Nitrogen and ammonia can be stored in
  High-Pressure Gas Tanks and moved with pumps/pipes.
- **The Air Separator's tanks are output-only by design** — you cannot feed nitrogen or oxygen back
  into it; hook a pump to its drain side instead. Its panel deliberately shows only the two tanks
  and a status lamp (no energy bar, no progress bar).
- **Crude oil now generates in the world.** Small surface oil lakes (`mini_oilfield`) appear
  anywhere in the overworld at roughly the same rarity as vanilla lava lakes — and **three times
  as often in deserts and badlands**. The **Ocean Oilfield** biome (dark blue water, `#4047AD`)
  shows up along stony shores at a deliberately low rate. **Existing worlds get it too**: the
  biome source falls back to the registry when an old save has no oil-biome entry.
- **The Oil Bucket only scoops.** It cannot pour oil back out or place a source block yet.
- **Recipes do not auto-unlock** in the recipe book. JEI shows all of them and manual crafting works
  normally; the advancements track **milestones** (obtain an item / place a block), never recipe
  unlocks, so nothing is added to the recipe book by them.
- **Iron Dust is intentionally expensive** (20 s at 70 FE/t = 28,000 FE per item). That number comes
  from the design spec, not from a balance accident.

---

*Version 0.11 · mod id `potato_s_t` · built for NeoForge 21.1.235 on Minecraft 1.21.1*

- **Filling Machine (0.11 ZF80)** - right-click the machine with an oil bucket / gas tank to pour its contents into a tank (1000 mB per click; it keeps filling the same tank, otherwise takes the first empty one), and **shift-right-click with an empty hand** to get a per-slot diagnosis of why nothing is filling (empty tank / no container / container full / not enough FE / container refuses that fluid / currently filling). Plain empty-hand right-click still opens the GUI.

- **Diesel / Gasoline Buckets (0.11 ZF82)** - two fluid buckets that work exactly like the vanilla bucket: pour the fluid out (place a source block) and get an empty bucket back, or pick a source block back up with an empty bucket. Diesel and gasoline are now real world fluids with their own blocks.
- **Container Fluid Exchanger (0.11 ZF82)** - left slot: an oil bucket / gas tank with fluid in it, right slot: exactly 1 empty bucket. After 3 s it takes 1000 mB out of the container and turns that empty bucket into the bucket of that fluid (water -> water bucket, diesel -> diesel bucket; other mods' fluids work too as long as they have a bucket form). Fluids without a bucket form (crude oil / naphtha / LPG) are refused. A fluid pump connected to the block drains the container in the left slot directly (gases included - gas tanks must be pumped out).

- **Hydrodesulfurization Chamber + Sulfur (0.11 ZF96)** - the new single-block machine: **16 Bitumen + 1000 mB hydrogen -> 1 Sulfur**, one batch every **10 seconds**. Its panel has exactly one hydrogen tank (4,000 mB, hydrogen only), the bitumen slot on the left, the sulfur output on the right, a progress arrow and a status lamp. Hydrogen goes in two ways: hook up a fluid pump/pipe, or **right-click the machine with a gas tank full of hydrogen** (1000 mB per click); an empty-hand right-click still opens the GUI. **It uses no energy** - there is no FE requirement and no energy bar, so the lamp's red "no power" state never appears on this machine; both kinds of missing input (not enough bitumen, not enough hydrogen) show as a yellow lamp. Its crafting recipe is iron ingot / 2 silver ingots on top, 2 iron blocks around a High-Pressure Gas Tank, and 2 redstone blocks around a Common Metal Block. **Sulfur is a brand-new item** and nothing consumes it yet.

- **Air Separator + Ammonia Synthesis Chamber + Nitrogen/Ammonia (0.11 ZF97)** - two new machines and the two gases they need. The **Air Separator** splits air into **8 mB nitrogen + 2 mB oxygen every 30 s** at 200 FE/t with a 5,000 FE buffer; its two tanks are strictly **output-only** (a pump can drain them, nothing can be piped or poured in) and its panel deliberately shows just the two tanks and one status lamp. The **Ammonia Synthesis Chamber** runs continuously: **1 mB nitrogen + 1 mB hydrogen + 200 FE -> 1 mB ammonia per tick**, gated by an **iron-dust catalyst that is never consumed**; the gas-tank slot under each input tank pushes nitrogen/hydrogen into the machine at 50 mB/t while the slot under the ammonia tank works in reverse (50 mB/t out into a gas tank); pipes may only push nitrogen/hydrogen in and pull ammonia out. Both machines stop on a redstone signal, and both drop their slot contents (but not their tank contents) when broken. **Nitrogen and ammonia are new gases**: they carry `c:nitrogen` / `c:ammonia` and are listed in `c:gaseous`, so High-Pressure Gas Tanks accept them, oil buckets refuse them, and the Filling Machine can fill them.

- **Fluid Pump stores no fluid (0.11 ZF98)** - the pump no longer keeps an internal tank: every tick it moves fluid **straight from the source network into the destination network**, and it **only moves what the destination accepts** (a destination that refuses a fluid is skipped, and that fluid is never pulled out of the source at all). Targets are visited nearest-first, and for each one the fluid it already holds is tried first, so a partially filled tank gets topped up instead of being asked to take something it cannot hold. Two consequences worth knowing: **two pumps can no longer be chained nose-to-tail** (with no tank a pump is neither a source nor a destination - raise the rate for more range, or put a tank in between), and if an old save still had fluid inside a pump, that fluid is **flushed into the destination network** on the first working tick instead of being deleted.

- **Air Separator puffs white smoke (0.11 ZF99)** - while the Air Separator is genuinely separating (powered, room left in both tanks, no redstone signal) it now blows **white smoke** out of the top of the block, roughly 12 vanilla cloud particles per second. It stays visually silent when it is out of power, when a tank is full, or when a redstone signal has switched it off.

- **Two machine recipes + the Combustion Reaction Chamber (0.11 ZF100)** - the **Lithium Battery** (aluminium plate / capacitor / aluminium plate, copper plate / lithium carbonate / copper plate, aluminium plate / common metal block / aluminium plate) and the **Electric Blast Furnace controller** (iron plate / heater / iron plate, wiring block / **vanilla blast furnace** / wiring block, iron plate / capacitor / iron plate) are craftable now, and the blast furnace can be assembled around **either a vanilla blast furnace or this mod's own controller block**.
- **Combustion Reaction Chamber (0.11 ZF100)** - a fuel-powered chamber that turns fuel into **Power** for an adjacent Power Capturer, plus carbon dioxide and a byproduct. The fuel slot takes **anything a vanilla furnace burns**, plus this mod's **diesel and gasoline buckets**. One reaction eats **1 fuel item + 10 mB oxygen**, which are consumed the moment the reaction starts: **lava bucket 10 s, diesel/gasoline bucket 30 s, everything else 3 s**. Outputs: **logs -> 10 mB carbon dioxide + 1 charcoal**, **diesel/gasoline bucket -> 200 mB carbon dioxide + 50 mB water + an empty bucket**, **anything else -> 5 mB carbon dioxide**. While it burns it feeds **800 Power per tick** to an adjacent Power Capturer - **diesel 1200, gasoline 1000** - and puffs **black smoke** from its top face. Its three tanks follow the design you gave: the **oxygen tank (1,200 mB) only takes oxygen in**, the **carbon dioxide tank (10,000 mB) only lets fluid out**, and the third tank (4,000 mB, water so far) is an output too. **It uses no energy of its own** (there is no FE bar and the lamp's red state never appears). It stops on a redstone signal, and if the byproduct slot or an output tank is full it simply waits at the last tick instead of losing the batch. Its crafting recipe is empty / High-Pressure Gas Tank / empty, Heat Sink / iron plate / Heat-Resistant Metal Block, Capacitor / Heater / Flint and Steel. **Carbon dioxide is a new gas** (11 fluids now) and can be stored in High-Pressure Gas Tanks and moved with pumps; nothing consumes it yet.

- **Acidic Reaction Chamber + four acids (0.11 ZF101/ZF102)** - a four-recipe machine fed by six 1,000 mB input tanks (carbon dioxide / oxygen / ammonia / water / **hydrogen / chlorine**) that fills four 1,000 mB output tanks (carbonic / nitric / sulfuric / **hydrochloric** acid). **Four buttons under the output tanks pick the recipe**: (1) 10 mB carbon dioxide + 1 mB water -> 1 mB carbonic acid **per tick**, (2) 1 mB oxygen + 1 mB ammonia -> 1 mB nitric acid **per tick**, (3) 10 sulfur + 100 mB water -> 100 mB sulfuric acid as a **5-second batch** (the sulfur and water are only taken on the last tick), (4) **10 mB hydrogen + 10 mB chlorine + 5 mB water -> 5 mB hydrochloric acid per tick**. Every recipe draws **500 FE/t** with a **12,400 FE** buffer, so it needs a steady power supply; a redstone signal stops it. The lamp tells you how it is stuck: red = no power, yellow = not enough fluid input, yellow = an output tank is full, yellow = fewer than 10 sulfur. Its crafting recipe is copper block / Stable Metal Block / heater, titanium ingot / Filling Machine / titanium ingot, redstone torch / Electrolyzer / lever - **note that the Stable Metal Block still has no recipe of its own, so this machine cannot be built in survival yet**. **Carbonic, nitric, sulfuric and hydrochloric acid are new fluids** (15 in total) and they are **liquids, not gases**: oil buckets accept them, High-Pressure Gas Tanks refuse them.
