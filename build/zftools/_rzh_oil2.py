import io, json, os, subprocess
LANG = r"E:\PotatoST\PotatoSTneoforge1.21.1\src\main\resources\assets\potato_s_t\lang"
GIT = r"C:\Program Files\Git\cmd\git.exe"
cur = json.load(io.open(os.path.join(LANG,"en_us.json"),encoding="utf-8"))
base = json.loads(subprocess.run([GIT,"show","HEAD~1:src/main/resources/assets/potato_s_t/lang/en_us.json"],
                                 cwd=r"E:\PotatoST\PotatoSTneoforge1.21.1",capture_output=True,check=True).stdout.decode("utf-8"))
k = "potato_s_t.guide.entry.oil.crude.p2"
print("block.potato_s_t.oil_pump :", cur["block.potato_s_t.oil_pump"])
print()
print("guide HEAD~1:", base[k][:130])
print("guide now   :", cur[k][:130])
print()
print("HEAD~1 用 Oil Extractor:", "Oil Extractor" in base[k])
print("now  用 Oil Extractor:", "Oil Extractor" in cur[k])
print("now  用 Oil Pump     :", "Oil Pump" in cur[k])
