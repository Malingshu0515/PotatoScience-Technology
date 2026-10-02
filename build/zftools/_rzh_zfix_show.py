# -*- coding: utf-8 -*-
"""Re-diff zh_cn vs HEAD and print ONLY the keys I just touched, so I can eyeball
that each fix landed on the intended key (and that I did not silently skip one)."""
import io, json, os, subprocess

ROOT = r"E:\PotatoST"
GIT = r"C:\Program Files\Git\cmd\git.exe"
REL = "src/main/resources/assets/potato_s_t/lang/zh_cn.json"
OUT = os.path.join(ROOT, "build", "zftools", "_rzh_zfix_show.txt")

old = json.loads(subprocess.run([GIT, "show", "HEAD:" + REL], cwd=ROOT,
                                capture_output=True, check=True).stdout.decode("utf-8"))
new = json.load(io.open(os.path.join(ROOT, REL), encoding="utf-8"))
ch = [k for k in new if k in old and old[k] != new[k]]

CHECK = [
    "tooltip.potato_s_t.star_steel_axe.3",
    "tooltip.potato_s_t.oil_pump",
    "tooltip.potato_s_t.star_steel_set",
    "tooltip.potato_s_t.titanium_alloy_set",
    "advancements.potato_s_t.steel.description",
    "tooltip.potato_s_t.ammonia_synthesis_chamber",
    "advancements.potato_s_t.capacitor.description",
    "advancements.potato_s_t.blast_furnace.description",
    "advancements.potato_s_t.vibranium.description",
    "advancements.potato_s_t.fuel.description",
    "advancements.potato_s_t.starfall.description",
    "advancements.potato_s_t.star_steel_slash.description",
    "advancements.potato_s_t.music_disc_anvil.title",
    "advancements.potato_s_t.music_disc_anvil.description",
    "gui.potato_s_t.fluid_exchanger.status.output_full",
]

L = []
L.append("changed-vs-HEAD total = %d" % len(ch))
L.append("")
for k in CHECK:
    v = new[k]
    L.append("### %s" % k)
    L.append("  NOW: %s" % v.replace("\n", "\\n"))
    flags = []
    if v.rstrip() != v:
        flags.append("TRAILING-WS")
    if "  " in v.replace("\n", ""):
        flags.append("DOUBLE-SPACE")
    if any(p in v for p in ("，；", "。；", "  ", "\n、", "的的")):
        flags.append("BROKEN")
    if v != new[k].strip():
        flags.append("LEAD/TRAIL")
    L.append("  flags: %s" % (", ".join(flags) if flags else "clean"))
    L.append("")

L.append("--- all other changed keys (should be the user's, untouched by me) ---")
for k in ch:
    if k not in CHECK:
        L.append("  %s" % k)

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("wrote", OUT)
