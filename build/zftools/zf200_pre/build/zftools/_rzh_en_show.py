import io, json, subprocess
GIT = r"C:\Program Files\Git\cmd\git.exe"
ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
BASE = "src/main/resources/assets/potato_s_t/lang/en_us.json"
old = json.loads(subprocess.run([GIT,"show","HEAD:"+BASE],cwd=ROOT,capture_output=True,check=True).stdout.decode("utf-8"))
new = json.load(io.open(ROOT+"\\"+BASE.replace("/","\\"), encoding="utf-8"))
for k in ("potato_s_t.guide.category.power.desc",
          "potato_s_t.guide.entry.materials.salt.p1",
          "potato_s_t.guide.entry.oil.crude.p2"):
    print("### %s" % k)
    print("   HEAD: %s" % old[k])
    print("   NOW : %s" % new[k])
    print("   same: %s" % (old[k] == new[k]))
    print()
