import io, json, subprocess
GIT = r"C:\Program Files\Git\cmd\git.exe"
ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
BASE = "src/main/resources/assets/potato_s_t/lang/en_us.json"
old = json.loads(subprocess.run([GIT,"show","HEAD:"+BASE],cwd=ROOT,capture_output=True,check=True).stdout.decode("utf-8"))
new = json.load(io.open(ROOT+"\\"+BASE.replace("/","\\"), encoding="utf-8"))
ch = [k for k in new if old.get(k) != new[k]]
print("changed=%d" % len(ch))
for k in ch:
    print("  %s" % k)
