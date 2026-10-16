import io, json, os, subprocess
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
GIT = r"C:\Program Files\Git\cmd\git.exe"
d = json.load(io.open(os.path.join(LANG, "en_us.json"), encoding="utf-8"))
print("block name :", d["block.potato_s_t.oil_pump"])
# older en guide (HEAD~1) still says Oil Pump?
old = json.loads(subprocess.run([GIT,"show","HEAD~1:src/main/resources/assets/potato_s_t/lang/en_us.json"],
                                cwd=r"E:\PotatoST\PotatoSTneoforge1.21.1",capture_output=True,check=True).stdout.decode("utf-8"))
print("guide HEAD~1:", "Oil Pump" in old["potato_s_t.guide.entry.oil.crude.p2"] and "Oil Pump" or "Oil Extractor")
print()
print("=== 中文 guide vs 旧四语：旧译文里有没有中文已删的事实 ===")
zh = json.load(io.open(os.path.join(LANG,"zh_cn.json"),encoding="utf-8"))
zh_old = json.loads(subprocess.run([GIT,"show","HEAD~1:src/main/resources/assets/potato_s_t/lang/zh_cn.json"],
                                   cwd=r"E:\PotatoST\PotatoSTneoforge1.21.1",capture_output=True,check=True).stdout.decode("utf-8"))
en_old = old
for k in sorted(x for x in zh if x.startswith("potato_s_t.guide")):
    a, b = zh_old.get(k,""), zh.get(k,"")
    # 旧英文里有、新中文里没有的"事实关键词"
    for needle in ("sunlight","32×32","durability 4","half","10%","look up","knockback"):
        if needle.lower() in en_old.get(k,"").lower() and needle.lower() not in b.lower():
            print("  %-56s 旧英有 %-12s 新中无" % (k.split(".")[-2:], needle))
