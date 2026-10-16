import io, json, subprocess
GIT = r"C:\Program Files\Git\cmd\git.exe"
ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
cur = json.load(io.open(ROOT + r"\src\main\resources\assets\potato_s_t\lang\en_us.json", encoding="utf-8"))
head = json.loads(subprocess.run([GIT,"show","HEAD:src/main/resources/assets/potato_s_t/lang/en_us.json"],
                                 cwd=ROOT,capture_output=True,check=True).stdout.decode("utf-8"))
FPS = [("potato_s_t.guide.entry.materials.salt.p1", "Supply power and it yields"),
       ("potato_s_t.guide.entry.oil.crude.p2", "Oil Extractor"),
       ("potato_s_t.guide.category.power.desc", "Wiring, generation, storage")]
for k, needle in FPS:
    print("%-52s cur=%s head=%s" % (k.split(".")[-1], needle in cur[k], needle in head[k]))
