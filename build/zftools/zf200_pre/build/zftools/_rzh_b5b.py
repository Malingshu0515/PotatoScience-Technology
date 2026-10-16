import io, json, os, sys, subprocess
sys.path.insert(0, r"E:\PotatoST\PotatoSTneoforge1.21.1\build\zftools")
from _rzh_lzh_sameok import S2T
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
GIT = r"C:\Program Files\Git\cmd\git.exe"
zh = json.load(io.open(os.path.join(LANG, "zh_cn.json"), encoding="utf-8"))
lzh = json.load(io.open(os.path.join(LANG, "lzh.json"), encoding="utf-8"))
hzh = json.loads(subprocess.run([GIT,"show","HEAD:src/main/resources/assets/potato_s_t/lang/zh_cn.json"],
                                cwd=r"E:\PotatoST\PotatoSTneoforge1.21.1",capture_output=True,check=True).stdout.decode("utf-8"))
KEYS = ["potato_s_t.configuration.section.black_hole",
        "potato_s_t.configuration.section.black_hole.button",
        "potato_s_t.configuration.black_hole.one_shot",
        "potato_s_t.configuration.black_hole.pull_entities",
        "potato_s_t.configuration.lithium_battery.transfer_rate_fe"]
print("key | value | 异形字 | 旧值==中文?")
for k in KEYS:
    v = lzh[k]
    hit = sorted(set(c for c in v if c in S2T))
    print("%-52s %-14s %-6s %s" % (k.split(".")[-2:], v, "".join(hit) or "无", hzh.get(k) == v))
