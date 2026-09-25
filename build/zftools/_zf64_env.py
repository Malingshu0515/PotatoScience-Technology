# -*- coding: utf-8 -*-
"""ZF64 环境探针：python 侧有没有能读写 Ogg/Vorbis 的库，以及能不能上网装包。"""
import importlib.util
import sys

print("python      :", sys.version.split()[0], sys.executable)
for m in ["numpy", "soundfile", "pydub", "av", "scipy", "wave", "audioop", "ogg", "vorbis"]:
    try:
        spec = importlib.util.find_spec(m)
    except Exception as exc:                      # noqa: BLE001
        print("ERR  %-12s %s" % (m, exc))
        continue
    print(("HAS  " if spec else "NO   ") + m)

print("---- network ----")
try:
    import urllib.request
    with urllib.request.urlopen("https://pypi.org/simple/soundfile/", timeout=12) as resp:
        print("pypi reachable, HTTP", resp.status)
except Exception as exc:                          # noqa: BLE001
    print("pypi NOT reachable:", type(exc).__name__, exc)
