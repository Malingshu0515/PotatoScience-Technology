# -*- coding: utf-8 -*-
"""_zf135_dedupe.py —— 删 `build/用户素材/` 里「同一张图两种名字」的重复件

用户指令：「用户素材里已经上线且已有留档的重复件」删掉，「原件一律保留」。

## 判据（不靠猜名字，靠**逐字节**）

对每个**中文名**文件，在同一个目录里找**内容逐字节相同**的另一份：
  · 找得到 ⇒ 那是同一份素材的两个名字（一个留档名、一个原名），**删中文名那份**，
    并把凭据表里的「原名」字段保留下来（记账不丢）；
  · 找不到 ⇒ 它是**唯一副本**（例如 银线_001.png / 柴油发电机工作.mp3 从没被复制过）
    ⇒ **保留**（用户说原件一律保留）。

⚠ 全程只删「内容在别处也有一份」的文件 —— 任何一个删除都先备份到 `zf135_pre/`，
   且删完立刻回读断言"被删的名字没了、留档那份还在、内容没变"。
"""
import hashlib
import io
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

U = r"E:\PotatoST\build\用户素材"
PRE = r"E:\PotatoST\build\zftools\zf135_pre"
PROV = os.path.join(U, "_来源凭据.json")
SKIP = {"_来源凭据.json"}


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    os.makedirs(PRE, exist_ok=True)
    files = [f for f in os.listdir(U)
             if os.path.isfile(os.path.join(U, f)) and f not in SKIP]
    by_hash = {}
    for f in files:
        by_hash.setdefault(sha1(os.path.join(U, f)), []).append(f)

    prov = json.loads(io.open(PROV, encoding="utf-8").read())

    print(u"目录里 %d 个文件，按内容归并成 %d 组" % (len(files), len(by_hash)))
    print()
    dups, uniq = [], []
    for h, names in sorted(by_hash.items(), key=lambda kv: kv[1][0]):
        if len(names) == 1:
            uniq.append(names[0])
            continue
        # 有重复：优先留"ASCII 名"（留档命名），删中文名那份
        ascii_names = [n for n in names if all(ord(c) < 128 for c in n)]
        keep = ascii_names[0] if ascii_names else sorted(names)[0]
        drop = [n for n in names if n != keep]
        dups.append((h, keep, drop))
        print(u"  重复组 %s…" % h[:10])
        for n in names:
            mark = u"保留" if n == keep else u"删除"
            print(u"      [%s] %-38s %d B" % (mark, n, os.path.getsize(os.path.join(U, n))))

    print(u"\n唯一副本（**一律保留**）%d 个：" % len(uniq))
    for n in sorted(uniq):
        print(u"      %-38s %d B" % (n, os.path.getsize(os.path.join(U, n))))

    if not dups:
        print(u"\n没有重复件，什么都不用删。")
        return 0

    print(u"\n== 开始删除（每个都先备份到 zf135_pre）==")
    fails = []
    for h, keep, drop in dups:
        for n in drop:
            src = os.path.join(U, n)
            if sha1(src) != h:
                fails.append(u"%s 在删除前内容变了，跳过" % n)
                print(u"  !! %s 内容变了，跳过" % n)
                continue
            shutil.copyfile(src, os.path.join(PRE, n))
            if sha1(os.path.join(PRE, n)) != h:
                fails.append(u"%s 备份校验失败，未删" % n)
                print(u"  !! %s 备份校验失败，未删" % n)
                continue
            os.remove(src)
            ok_gone = not os.path.exists(src)
            ok_keep = os.path.exists(os.path.join(U, keep)) and sha1(os.path.join(U, keep)) == h
            print(u"  删 %-38s 备份 OK=%s  留档仍在=%s"
                  % (n, ok_gone, ok_keep))
            if not (ok_gone and ok_keep):
                fails.append(u"%s 删除后回读断言失败" % n)
            # 凭据里保留"原名"信息（如果原来就是记在留档名下的）
            if keep in prov and u"原名" not in prov[keep]:
                prov[keep][u"原名"] = n

    io.open(PROV, "w", encoding="utf-8", newline="\n").write(
        json.dumps(prov, indent=2, ensure_ascii=False) + "\n")

    left = [f for f in os.listdir(U) if os.path.isfile(os.path.join(U, f)) and f not in SKIP]
    print(u"\n目录里剩 %d 个文件（删前 %d）" % (len(left), len(files)))
    print(u"备份目录 zf135_pre: %d 个" % len(os.listdir(PRE)))
    if fails:
        print(u"\n失败项 %d：" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    print(u"\n完成，0 失败。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
