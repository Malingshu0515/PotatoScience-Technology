import io, json, subprocess, os
ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
GIT = r"C:\Program Files\Git\cmd\git.exe"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
old = json.loads(subprocess.run([GIT,"show","HEAD:src/main/resources/assets/potato_s_t/lang/zh_cn.json"],
                                cwd=ROOT,capture_output=True,check=True).stdout.decode("utf-8"))
new = json.load(io.open(os.path.join(LANG,"zh_cn.json"),encoding="utf-8"))
ch = [k for k in new if k in old and old[k]!=new[k]]
guide = [k for k in ch if k.startswith("potato_s_t.guide")]
cfg   = [k for k in ch if k.startswith("potato_s_t.configuration")]
other = [k for k in ch if k not in guide and k not in cfg]
print("changed=%d  guide=%d  config=%d  other=%d" % (len(ch), len(guide), len(cfg), len(other)))
for k in other: print("   other: %s" % k)
print("added=%d removed=%d" % (len([k for k in new if k not in old]), len([k for k in old if k not in new])))
