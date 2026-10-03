# -*- coding: utf-8 -*-
"""_zf69_repro.py —— 复现性论证：重跑配方生成器，除新增的那一份，别的文件一个字节都没动

做法：拿 §10 备份（zf69_pre，改前抄的 33 份配方 JSON）逐份比 SHA1。
      外加：新增的 heat_sink.json **必须**是备份里没有的（否则说明它早就存在、我改的是老文件）。

⚠ **2026-09-24（ZF73）起这条检查的数据源没了**：备份根
  `C:\\Users\\Administrator\\Desktop\\PotatoST救援_20260917_183054`（含 `zf69_pre`）
  被删进了回收站（`$R` 实体仍在 ⇒ 可还原，取证见 `_zf72_recycle_list.py`）。
  本脚本原来只打印一句「找不到备份目录」就 **exit 0** —— 那是**假绿**（跟 §4.32 同一个坑：
  「检查 0 个文件却报通过」）。现在改成**响亮地报 SKIP**并把标记写进输出，
  让门日志里一眼能看见"这一项本轮没做任何校验"。
  ZF73 起，复现性证据改用当轮自己的备份根（例：`_zf73_repro.py` 用 `zf73_pre`）。
"""
import hashlib
import io
import os
import sys

PROJ = r"E:\PotatoST"
PRE = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf69_pre"
REL = r"src\main\resources\data\potato_s_t\recipe"

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    ok = 0
    pre_dir = os.path.join(PRE, REL)
    now_dir = os.path.join(PROJ, REL)
    if not os.path.isdir(pre_dir):
        print(u"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(u"!! SKIP-NO-BACKUP: 本项**没有做任何校验**")
        print(u"!! 备份根已被删进回收站: %s" % pre_dir)
        print(u"!! 要恢复这条证据：把桌面那份 PotatoST救援_20260917_183054 从回收站还原，")
        print(u"!! 或者改用当轮备份（ZF73 起：_zf73_repro.py 用 C:\\PotatoST救援\\zf73_pre）")
        print(u"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return 0

    pre = sorted(n for n in os.listdir(pre_dir) if n.endswith(".json"))
    print(u"改前配方 JSON: %d 份    改后: %d 份" %
          (len(pre), len([n for n in os.listdir(now_dir) if n.endswith(".json")])))
    print(u"")

    for n in pre:
        a = sha1(os.path.join(pre_dir, n))
        b = sha1(os.path.join(now_dir, n))
        same = a == b
        if same:
            ok += 1
        else:
            fails.append(u"%s 被重跑改动了（改前 %s / 改后 %s）" % (n, a[:12], b[:12]))
        print(u"  [%s] %-46s %s" % (u"SAME" if same else u"DIFF", n, a[:12]))

    print(u"")
    new = "heat_sink.json"
    in_pre = os.path.isfile(os.path.join(pre_dir, new))
    exists = os.path.isfile(os.path.join(now_dir, new))
    if in_pre:
        fails.append(u"%s 在改前就存在 —— 本轮不是「新增」" % new)
    if not exists:
        fails.append(u"%s 没生成出来" % new)
    print(u"  [%s] %s 改前不存在 / 改后存在" % (u"OK" if (exists and not in_pre) else u"FAIL", new))

    print(u"")
    print(u"逐份哈希相同的 = %d / %d" % (ok, len(pre)))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
