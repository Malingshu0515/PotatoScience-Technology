# -*- coding: utf-8 -*-
"""ZF156 侦察②：扫整合包里的 mod jar，找「金属板」类物品与 c:plates / forge:plates 标签。

只读。目的：决定本 mod 的金属板配方该挂在哪些通用标签上、
以及哪些别的 mod 的板子要作为「可选条目」写进我们的标签文件（required: false）。

用法：python _zf156_recon2.py <mods 目录> [...]
"""
import io
import json
import os
import re
import sys
import zipfile

PLATE_HINT = re.compile(r"(plate|sheet)", re.I)
TAG_HINT = re.compile(r"^data/([^/]+)/tags/(?:item|items)/(?:plates|(?:item/)?plates)(?:/([^/]+))?\.json$")
OUR_PLATES = {"aluminum", "cobalt", "copper", "iron", "nickel", "silver", "steel"}


def scan(jar):
    """返回 (标签字典, 板类物品 id 列表, modid)"""
    tags = {}
    items = []
    names = set()
    modid = None
    with zipfile.ZipFile(jar) as zf:
        for info in zf.infolist():
            n = info.filename
            names.add(n)
            if n.startswith("data/") and "/tags/" in n:
                m = TAG_HINT.match(n)
                if m:
                    tags.setdefault(m.group(1), []).append(n)
            if n.startswith("assets/") and n.endswith(".json") and "/models/item/" in n:
                base = n.rsplit("/", 1)[-1][:-5]
                if PLATE_HINT.search(base):
                    mid = n.split("/")[1]
                    items.append(mid + ":" + base)
        # 读标签内容
        tagcontent = {}
        for owner, files in tags.items():
            for f in files:
                try:
                    data = json.loads(zf.read(f).decode("utf-8"))
                except Exception:
                    continue
                vals = []
                for v in data.get("values", []):
                    if isinstance(v, str):
                        vals.append(v)
                    elif isinstance(v, dict) and "id" in v:
                        vals.append(v["id"])
                tagcontent[f] = vals
        # modid：取 META-INF/neoforge.mods.toml 或 assets 下第一个目录
        for n in names:
            if n.endswith("neoforge.mods.toml") or n.endswith("mods.toml"):
                try:
                    txt = zf.read(n).decode("utf-8", "replace")
                except Exception:
                    continue
                mm = re.search(r'modId\s*=\s*"([^"]+)"', txt)
                if mm:
                    modid = mm.group(1)
                    break
    return tagcontent, sorted(set(items)), modid


def main():
    dirs = sys.argv[1:]
    for d in dirs:
        print("===== " + d)
        for name in sorted(os.listdir(d)):
            if not name.lower().endswith(".jar"):
                continue
            p = os.path.join(d, name)
            try:
                tagcontent, items, modid = scan(p)
            except Exception as exc:
                print("  !! " + name + " : " + str(exc))
                continue
            plate_tags = {k: v for k, v in tagcontent.items() if "/plates" in k}
            if not plate_tags and not items:
                continue
            print("-- " + name + "  (modid=" + str(modid) + ")")
            for k in sorted(plate_tags):
                print("     tag " + k + " = " + json.dumps(plate_tags[k], ensure_ascii=False))
            if items:
                shown = [i for i in items if any(x in i.rsplit(":", 1)[-1].lower() for x in
                                                 ("plate", "sheet"))]
                print("     items(" + str(len(shown)) + "): " + ", ".join(shown[:40]))


if __name__ == "__main__":
    main()
