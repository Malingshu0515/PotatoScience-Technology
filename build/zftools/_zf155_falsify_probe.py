# -*- coding: utf-8 -*-
u"""_zf155_falsify_probe.py —— ZF155 开服反证刀：**只有真开服才抓得住**的那种坏法。

坏法：`UniversalUpgradeTemplate.install()` 里照旧调 `replaceRecipes`、照旧算得出计划，
但**故意不把加宽版塞进新表**（把 `byId.put(holder.id(), holder);` 抽掉）。
静态门看不出来（计划里 9 条照样"加宽"、`replaceRecipes` 调用还在），
但真表里那 9 条**不认**通用模板 ⇒ 探针 A6 / B1 / B2 / F2 必须红。

流程：挂探针 → 改坏 → 开服（红）→ 还原（逐字节）→ 开服（回绿）→ 摘探针。
⚠ 最后那次开服是必须的：报告文件**必须留在全绿那一版**（归档件与报告要对得上，§4.145）。

跑法：python build\\zftools\\_zf155_falsify_probe.py
"""
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
ENGINE = os.path.join(ROOT, r"src\main\java\com\potatost\mod\UniversalUpgradeTemplate.java")
SRC_CHECK = os.path.join(ROOT, r"src\main\java\com\potatost\mod\Zf155Check.java")
ARC_CHECK = os.path.join(ZT, "check", u"Zf155Check.java")
REPORT = os.path.join(ZT, u"_zf155_probe_utf8.txt")
LOG = os.path.join(ZT, u"_zf155_falsify_probe.log")
OLD = u"""            for (RecipeHolder<?> holder : plan.replacements()) {
                byId.put(holder.id(), holder);
            }"""
NEW = u"""            for (RecipeHolder<?> holder : plan.replacements()) {
                // [ZF155 反证] 故意不塞加宽版：计划照算、replaceRecipes 照调，但表里还是原样的
            }"""

fails = []


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run(cmd, timeout=900):
    r = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def gradle(*tasks):
    return run([os.path.join(ROOT, "gradlew.bat")] + list(tasks) + ["--offline", "-q"], timeout=1200)


def server_run():
    if os.path.exists(REPORT):
        os.remove(REPORT)
    rc, out = gradle(u"runServer")
    io.open(LOG, "w", encoding="utf-8", newline="\n").write(out)
    return rc


def report():
    return io.open(REPORT, encoding="utf-8").read() if os.path.exists(REPORT) else u""


def main():
    print(u"① 挂探针")
    shutil.copy2(ARC_CHECK, SRC_CHECK)
    rc, out = run([sys.executable, os.path.join(ZT, u"_zf155_probe_mount.py"), u"--write"])
    print(u"   " + out.strip().replace(u"\n", u"\n   "))
    if rc != 0:
        fails.append(u"挂探针失败")

    original = open(ENGINE, "rb").read()
    h0 = hashlib.sha1(original).hexdigest()
    text = io.open(ENGINE, encoding="utf-8", newline="").read()
    if text.count(OLD) != 1:
        fails.append(u"反证锚点命中 %d 次（应为 1）" % text.count(OLD))
        return finish(original, h0, None, None)

    print(u"② 改坏（不把加宽版塞进表）")
    io.open(ENGINE, "w", encoding="utf-8", newline="").write(text.replace(OLD, NEW, 1))
    print(u"③ 编译 + 开服（期望探针变红）")
    rc, out = gradle(u"compileJava", u"processResources")
    if rc != 0:
        fails.append(u"改坏后编译失败：%s" % out[-400:])
    else:
        server_run()
    bad_rep = report()
    bad_fail_lines = [l.strip() for l in bad_rep.split(u"\n") if u"[FAIL]" in l]
    hit_a6 = any(u"A6" in l for l in bad_fail_lines)
    hit_f2 = any(u"F2" in l for l in bad_fail_lines)
    print(u"   红项 %d 条；A6 命中=%s，F2 命中=%s" % (len(bad_fail_lines), hit_a6, hit_f2))
    for l in bad_fail_lines:
        print(u"     " + l)
    if not bad_fail_lines:
        fails.append(u"改坏后探针**没红**（报告判词：%s）"
                     % [l for l in bad_rep.split(u"\n") if u"判词" in l])
    if not (hit_a6 and hit_f2):
        fails.append(u"改坏后没有命中该红的项（A6=%s / F2=%s）" % (hit_a6, hit_f2))

    print(u"④ 静态门在改坏状态下：**源码层那批（A~C / D1~D7 / E）应该还是绿的**")
    print(u"   —— 否则这一刀证明不了「探针不可替代」。（D8/D9/D10 是**读报告**的判据，它们红是对的）")
    rc, out = run([sys.executable, os.path.join(ZT, u"_zf155_verify.py")])
    fail_lines = [l.strip() for l in out.split(u"\n") if u"[FAIL]" in l]

    def label_of(line):
        m = re.match(u"\\[FAIL\\]\\s+(\\S+)", line)
        return m.group(1) if m else u"?"

    src_fail = [l for l in fail_lines if label_of(l) not in (u"D8", u"D9", u"D10")]
    rep_fail = [l for l in fail_lines if label_of(l) in (u"D8", u"D9", u"D10")]
    print(u"   静态门 rc=%d；源码层红 %d 条；报告层红 %d 条" % (rc, len(src_fail), len(rep_fail)))
    for l in rep_fail:
        print(u"     (报告层，红是对的) " + l)
    for l in src_fail:
        print(u"     (源码层，不该红) " + l)
    if src_fail:
        fails.append(u"改坏状态下**源码层**判据也红了 ⇒ 这只刀证不了「探针不可替代」")
    if not rep_fail:
        fails.append(u"改坏状态下报告层判据（D8/D9/D10）没红 —— 报告没被读？")

    print(u"⑤ 逐字节还原")
    open(ENGINE, "wb").write(original)
    restored = sha(ENGINE) == h0
    print(u"   还原=%s（%s）" % (restored, sha(ENGINE)))
    if not restored:
        fails.append(u"还原后不是逐字节相同")

    print(u"⑥ 重新编译开服（期望回绿）")
    rc, out = gradle(u"compileJava", u"processResources")
    if rc != 0:
        fails.append(u"还原后编译失败：%s" % out[-400:])
    else:
        server_run()
    good_rep = report()
    good_fail = [l.strip() for l in good_rep.split(u"\n") if u"[FAIL]" in l]
    all_ok = u"判词：ALL OK" in good_rep
    print(u"   判词 %s；FAIL %d 条" % (u"ALL OK" if all_ok else u"**不是 ALL OK**", len(good_fail)))
    if not all_ok or good_fail:
        fails.append(u"还原后没回绿（FAIL %d 条）" % len(good_fail))

    return finish(original, h0, len(bad_fail_lines), all_ok)


def finish(original, h0, red_count, all_ok):
    print(u"⑦ 摘探针")
    rc, out = run([sys.executable, os.path.join(ZT, u"_zf155_unprobe.py")])
    print(u"   " + out.strip().replace(u"\n", u"\n   "))
    if rc != 0:
        fails.append(u"摘探针失败")
    print(u"")
    print(u"================ 开服反证刀 ================")
    print(u"改坏后红项 = %s   还原后判词 = %s" % (red_count, u"ALL OK" if all_ok else u"—"))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
