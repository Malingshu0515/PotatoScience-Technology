# -*- coding: utf-8 -*-
r"""_zf92_preserve_disc.py —— 按 §4.24 处理用户新丢进来的 `音乐唱片茉莉花.png`

事实：`src\main\resources\assets\potato_s_t\textures\item\音乐唱片茉莉花.png`（3170 字节）
是用户在 2026-09-25 00:07 放进来的**新素材**（文件名带中文 ⇒ 不能留在资源目录里，
§4.90 那条"成品侧条目名必须全 ASCII"的断言当场就抓到了）。

**本轮不建新物品**：这看起来是第二张音乐唱片（现有那张是 `music_disc_anvil_of_the_republic`），
而一张唱片要动的是 §6.1 那 6 处（物品注册 / 音效事件 / 点唱机曲目 / 四语言 / 配方 / 模型），
其中**音效 .ogg 我手里没有** —— 凭空造一个物品不是我该自作主张的事。所以：
  ① 原字节挪到 `build/用户素材/music_disc_jasmine_flower.png`（ASCII 名，字节不动）；
  ② 记进 `_来源凭据.json`；
  ③ 资源目录里**不留**它（否则成品里就带一个非 ASCII 条目，且它还是一张没人引用的孤儿图）；
  ④ 汇报里点名，问用户要不要做成一整张唱片。

用法：
    python _zf92_preserve_disc.py            # 预演（只打印现状与将要做的事）
    python _zf92_preserve_disc.py --write    # 真做
"""
import hashlib
import io
import json
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, u"src", "main", "resources", "assets", "potato_s_t",
                   u"textures", "item", u"音乐唱片茉莉花.png")
USERART = os.path.join(ROOT, "build", u"用户素材")
KEEP = os.path.join(USERART, "music_disc_jasmine_flower.png")
CRED = os.path.join(USERART, u"_来源凭据.json")
NOTE = u"用户在 2026-09-25 00:07 直接丢进 textures/item 的第二张唱片素材（音乐唱片·茉莉花）；本轮只留档、未建物品；原文件名不可留在资源目录（§4.24）"
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(argv):
    write = "--write" in argv
    if not os.path.exists(SRC):
        print(u"源文件不在（可能已经处理过了）：%s" % SRC)
        if os.path.exists(KEEP):
            print(u"留档件在：%s（sha1 %s…，%d 字节）" % (KEEP, sha1(KEEP)[:16], os.path.getsize(KEEP)))
            return 0
        return 1
    h = sha1(SRC)
    size = os.path.getsize(SRC)
    print(u"源：%s" % SRC)
    print(u"    %d 字节  sha1 %s" % (size, h))
    print(u"将：① 复制到 %s（ASCII 名，字节不动）" % KEEP)
    print(u"    ② 记进 %s" % CRED)
    print(u"    ③ 从资源目录删除原件（§4.24：资源目录里不留中文名）")
    d = json.loads(io.open(CRED, encoding="utf-8").read())
    print(u"当前凭据条目 %d 条；最后一条的样子：" % len(d))
    k = list(d)[-1]
    print(u"    %s → %s" % (k, json.dumps(d[k], ensure_ascii=False)[:200]))
    if not write:
        print(u"\n预演：没加 --write，什么都不做")
        return 0
    if "music_disc_jasmine_flower.png" in d:
        print(u"[SKIP] 凭据里已经有这一条了（幂等）")
    os.makedirs(USERART, exist_ok=True)
    shutil.copy2(SRC, KEEP)
    if sha1(KEEP) != h:
        fails.append(u"复制后哈希不一致")
    else:
        print(u"[OK] 留档 %s（sha1 一致）" % KEEP)
    d["music_disc_jasmine_flower.png"] = {
        u"原名": u"音乐唱片茉莉花.png",
        u"sha1": h,
        u"bytes": size,
        u"说明": NOTE,
    }
    io.open(CRED, "w", encoding="utf-8", newline=u"\n").write(
        json.dumps(d, ensure_ascii=False, indent=2) + u"\n")
    print(u"[OK] 凭据写到 %d 条" % len(d))
    os.remove(SRC)
    print(u"[OK] 已从资源目录删除原件（留档件在 build/用户素材）")
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
