import io, json, os, subprocess
ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
GIT = r"C:\Program Files\Git\cmd\git.exe"
zh = json.load(io.open(os.path.join(LANG, "zh_cn.json"), encoding="utf-8"))
old = json.loads(subprocess.run([GIT, "show", "HEAD:src/main/resources/assets/potato_s_t/lang/zh_cn.json"],
                                cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))
changed = [k for k in zh if k in old and old[k] != zh[k]]
L = ["# 用户本轮改动的 9 键（中文定稿）", ""]
for k in changed:
    L.append("### %s" % k)
    L.append(zh[k])
    L.append("")
L.append("# 配置说明：31 键全文（查破折号/括号/口语）")
L.append("")
for k in sorted(x for x in zh if x.startswith("potato_s_t.configuration")):
    L.append("### %s" % k)
    L.append(zh[k])
    L.append("")
io.open(os.path.join(ROOT, r"build\zftools\_rzh_sync_src.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("changed=%d" % len(changed))
