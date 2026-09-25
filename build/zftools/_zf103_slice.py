import zipfile, io, sys
jar = sys.argv[1]
entry = sys.argv[2]
a, b = int(sys.argv[3]), int(sys.argv[4])
with zipfile.ZipFile(jar) as zf:
    text = zf.read(entry).decode("utf-8", "replace")
lines = text.split("\n")
for i in range(a-1, min(b, len(lines))):
    print("%5d| %s" % (i+1, lines[i]))
