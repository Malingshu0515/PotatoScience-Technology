# -*- coding: utf-8 -*-
u"""_zf103_langdiff.py —— 只读取证：用户润色后的四份语言文件 vs **改前那份成品 jar**里冻着的那份

为什么不拿盘上别的副本比：盘上只有"改后"状态；`release\\PotatoST-0.11.jar`（ZF102 的
`48bc3358…`）是**用户动手之前**冻住的快照 —— 与 §4.17 的"等级 ①"是同一条口径。

打印：每份文件的键数、被改/新增/删掉的键（带改前改后原文），以及 JSON 能不能解析。
"""
import io
import json
import os
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
FILES = ("zh_cn.json", "en_us.json", "ja_jp.json", "ru_ru.json")


def main():
    out = []
    with zipfile.ZipFile(JAR) as zf:
        old = {f: json.loads(zf.read(u"assets/potato_s_t/lang/" + f).decode("utf-8")) for f in FILES}
    print(u"改前 jar（%s）里的键数：%s" % (
        u"、".join(u"%s=%d" % (f, len(old[f])) for f in FILES), u""))
    total_changed = 0
    for f in FILES:
        p = os.path.join(LANG, f)
        try:
            cur = json.loads(io.open(p, encoding="utf-8").read())
        except Exception as e:
            print(u"  [FAIL] %s 解析不过：%s" % (f, e))
            out.append(u"%s 解析失败" % f)
            continue
        changed = [k for k in old[f] if k in cur and cur[k] != old[f][k]]
        removed = [k for k in old[f] if k not in cur]
        added = [k for k in cur if k not in old[f]]
        print(u"\n=== %s：%d → %d 键；改动 %d / 删除 %d / 新增 %d ===" % (
            f, len(old[f]), len(cur), len(changed), len(removed), len(added)))
        total_changed += len(changed)
        for k in changed[:40]:
            print(u"  [改] %s" % k)
            print(u"       旧：%s" % old[f][k][:150])
            print(u"       新：%s" % cur[k][:150])
        for k in removed:
            print(u"  [删] %s" % k)
        for k in added:
            print(u"  [新] %s" % k)
        out.append(u"%s: 改 %d 删 %d 增 %d" % (f, len(changed), len(removed), len(added)))
    print(u"\n合计改动键数 = %d" % total_changed)
    return 1 if any(u"解析失败" in l for l in out) else 0


if __name__ == "__main__":
    sys.exit(main())
