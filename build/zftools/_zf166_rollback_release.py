# -*- coding: utf-8 -*-
u"""_zf166_rollback_release.py —— 把成品**退回上一份干净版**（并让三处哈希联动跟着退）。

**为什么**：这一轮从工作树打出来的 jar 里带着另一条线（ZF165）的**临时探针**
`com/potatost/mod/Zf165Check.class`（`_zf162_pkg.py` 审计当场抓到）。探针会在玩家服务端启动时
跑测试代码（我们自己的探针就是以 `halt` 收尾的）⇒ **这份 jar 绝不能当发布件**。
但另一条线还在树上干活（探针未摘、5 个 java 进程在跑），现在没法打出一份"含本机、且不含探针"的 jar。

所以：**先把 `release\\PoatoST-0.13.jar` 退回 git 里那份干净版**（ZF164 的 3cf65616…），
把三处哈希联动（档案 §5/§9、交接 §1、公告、`_zf149_verify.py` 的两个靶子）一起退回去；
等下一轮他们摘掉探针，再重打 + 重跑 `_zf166_docs.py --write` 自动跟平。

跑法：python build\\zftools\\_zf166_rollback_release.py [--write]
"""
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
GOOD_SHA = u"3cf65616ab285dbd865de955bdd9dc612296cb89"
GOOD_SIZE_RAW = 5938638
GOOD_SIZE = u"5,938,638"
GOOD_CLS = u"365"
BAD_SHA = u"84d0016cdebe2e057fc92f486817f1b72af64dc3"
BAD_SIZE = u"5,980,826"
BAD_CLS = u"378"
FILES = [os.path.join(ROOT, "docs", u"开发档案.md"),
         os.path.join(ROOT, "docs", u"多会话协作交接.md"),
         os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md"),
         os.path.join(ZT, u"_zf149_verify.py")]


def main(argv):
    write = u"--write" in argv
    fails, notes = [], []
    if write:
        r = subprocess.run([u"git", u"-C", ROOT, u"checkout", u"--",
                            u"release/PotatoST-0.13.jar", u"release/PotatoST-0.13.jar.sha1"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = r.stdout.decode("utf-8", "replace").strip()
        print(u"git checkout 成品：%s" % (out or u"（已退回）"))
    for p in FILES:
        if not os.path.isfile(p):
            fails.append(u"%s 不在" % p)
            continue
        text = io.open(p, encoding="utf-8", newline=u"").read()
        before = text
        text = text.replace(BAD_SHA, GOOD_SHA)
        text = text.replace(BAD_SIZE, GOOD_SIZE)
        text = text.replace(u"**%s classes" % BAD_CLS, u"**%s classes" % GOOD_CLS)
        text = text.replace(u"跟到 %s /" % BAD_CLS, u"跟到 %s /" % GOOD_CLS)
        text = text.replace(u"class %s；§4.159" % BAD_CLS, u"class %s；§4.159" % GOOD_CLS)
        text = text.replace(u"WANT_SIZE = 5980826", u"WANT_SIZE = %d" % GOOD_SIZE_RAW)
        changed = sum(1 for a, b in zip(before.split(u"\n"), text.split(u"\n")) if a != b)
        if text != before:
            notes.append(u"%s：换了 %d 行" % (os.path.basename(p), changed))
            if write:
                io.open(p, "w", encoding="utf-8", newline=u"").write(text)
    # 复核：release 那份的 sha1 必须等于 GOOD_SHA
    sha_p = os.path.join(ROOT, "release", u"PotatoST-0.13.jar.sha1")
    jar_p = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")
    import hashlib
    h = hashlib.sha1(open(jar_p, "rb").read()).hexdigest()
    ok_sha = h == GOOD_SHA
    print(u"release/PotatoST-0.13.jar sha1 = %s（要 == %s…：%s）"
          % (h[:16], GOOD_SHA[:16], u"是" if ok_sha else u"**否**"))
    if not ok_sha:
        fails.append(u"成品没退回去")
    if os.path.isfile(sha_p):
        want = io.open(sha_p, encoding="ascii").read().strip()
        if want != h:
            fails.append(u".sha1 与 jar 不一致")
    print(u"模式：%s" % (u"落盘" if write else u"干跑（不写）"))
    for n in notes:
        print(u"  " + n)
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
