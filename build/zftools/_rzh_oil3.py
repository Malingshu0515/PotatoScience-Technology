import io, json, subprocess
GIT = r"C:\Program Files\Git\cmd\git.exe"
ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
K = "block.potato_s_t.oil_pump"
log = subprocess.run([GIT, "log", "--oneline", "-S", '"%s"' % K, "--",
                      "src/main/resources/assets/potato_s_t/lang/en_us.json"],
                     cwd=ROOT, capture_output=True).stdout.decode().strip()
print("commits touching this key:")
print(log or "(none)")
print()
# value at a few commits
for ref in ("HEAD", "HEAD~1", "5b0c0da" ):
    try:
        d = json.loads(subprocess.run([GIT, "show", "%s:src/main/resources/assets/potato_s_t/lang/en_us.json" % ref],
                                      cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))
        print("%-10s %s" % (ref, d.get(K)))
    except Exception as e:
        print("%-10s <%s>" % (ref, e))
print()
zh = json.loads(subprocess.run([GIT, "show", "HEAD:src/main/resources/assets/potato_s_t/lang/zh_cn.json"],
                               cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))
print("zh block name:", zh[K])
