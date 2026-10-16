import io, json, re, subprocess
ROOT = r"E:\PotatoST\PotatoSTneoforge1.21.1"
REL = "src/main/resources/assets/potato_s_t/lang/ja_jp.json"
old = subprocess.run([r"C:\Program Files\Git\cmd\git.exe", "show", "HEAD:" + REL],
                     cwd=ROOT, capture_output=True, check=True).stdout
new = io.open(ROOT + "\\" + REL.replace("/", "\\"), "rb").read()
print("HEAD bytes=%d  now bytes=%d" % (len(old), len(new)))
print("HEAD ends with \\n:", old.endswith(b"\n"), " now ends with \\n:", new.endswith(b"\n"))
print("HEAD has CR:", b"\r" in old, " now has CR:", b"\r" in new)
print("HEAD has BOM:", old.startswith(b"\xef\xbb\xbf"), " now:", new.startswith(b"\xef\xbb\xbf"))
# key order identical?
a = json.loads(old.decode("utf-8")); b = json.loads(new.decode("utf-8"))
print("keys HEAD=%d now=%d  same order: %s" % (len(a), len(b), list(a) == list(b)))
# which values差
ch = [k for k in b if a.get(k) != b[k]]
print("changed values = %d" % len(ch))
# escape style: any \uXXXX in new?
print("has \\uXXXX escapes:", bool(re.search(rb"\\u[0-9a-fA-F]{4}", new)))
