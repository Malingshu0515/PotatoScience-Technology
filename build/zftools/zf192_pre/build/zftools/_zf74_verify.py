# -*- coding: utf-8 -*-
u"""_zf74_verify.py —— ZF74（流体挂 c: 通用标签 + 判定认标签）常驻校验

四组：
  A. 7 份标签文件的形状（路径/`replace:false`/源+流动都挂/值正确；ZF97 加了 nitrogen/ammonia）；
  B. Java：`isGas` 既认自家 5 种、也认 `#c:gaseous`；
  C. 发布：新 SHA1、jar 里 5 份标签、上一版 SHA1 已在档案里声明作废；
  D. 文档：§6.19 规矩、规划文档口径已改、公告补了标签一句。
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

PROJ = r"E:\PotatoST"
RES = os.path.join(PROJ, u"src", u"main", u"resources")
TAGS = os.path.join(RES, u"data", u"c", u"tags", u"fluid")
JAVA = os.path.join(PROJ, u"src", u"main", u"java", u"com", u"potatost", u"mod")
ARCH = os.path.join(PROJ, u"docs", u"开发档案.md")
PLAN = os.path.join(PROJ, u"docs", u"v0.11规划.md")
ANN = os.path.join(PROJ, u"docs", u"UpdateAnnouncement_EN.md")
JAR = os.path.join(PROJ, u"release", u"PotatoST-0.11.jar")
JAR_BUILT = os.path.join(PROJ, u"build", u"libs", u"potato_s_t-0.11.jar")
VOIDED = u"2a35a9eeda99"   # ZF73 发布过的 0.11 成品，本轮同版本重打包 ⇒ 作废

checks = 0
fails = []


def check(name, cond, detail=u""):
    global checks
    checks += 1
    if not cond:
        fails.append(name if not detail else u"%s  (%s)" % (name, detail))
    print(u"  %s %s" % (u"[OK]  " if cond else u"[FAIL]", name))


def read(path):
    if not os.path.isfile(path):
        return u""
    return io.open(path, "r", encoding="utf-8", errors="replace").read()


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    fluids = read(os.path.join(JAVA, u"ModFluids.java"))
    arch = read(ARCH)
    plan = read(PLAN)
    ann = read(ANN)

    # ---------------- A. 标签文件 ----------------
    print(u"\n=== A. 12 份 c: 流体标签（ZF97 加 nitrogen/ammonia、ZF100 加 carbon_dioxide、"
     u"ZF101 加三种酸）===")
    want = {
        u"gaseous.json": [u"potato_s_t:oxygen", u"potato_s_t:flowing_oxygen",
                          u"potato_s_t:hydrogen", u"potato_s_t:flowing_hydrogen",
                          u"potato_s_t:chlorine", u"potato_s_t:flowing_chlorine",
                          u"potato_s_t:nitrogen", u"potato_s_t:flowing_nitrogen",
                          u"potato_s_t:ammonia", u"potato_s_t:flowing_ammonia",
                          u"potato_s_t:carbon_dioxide", u"potato_s_t:flowing_carbon_dioxide"],
        u"nitrogen.json": [u"potato_s_t:nitrogen", u"potato_s_t:flowing_nitrogen"],
        u"ammonia.json": [u"potato_s_t:ammonia", u"potato_s_t:flowing_ammonia"],
        u"carbon_dioxide.json": [u"potato_s_t:carbon_dioxide", u"potato_s_t:flowing_carbon_dioxide"],
        u"carbonic_acid.json": [u"potato_s_t:carbonic_acid", u"potato_s_t:flowing_carbonic_acid"],
        u"nitric_acid.json": [u"potato_s_t:nitric_acid", u"potato_s_t:flowing_nitric_acid"],
        u"sulfuric_acid.json": [u"potato_s_t:sulfuric_acid", u"potato_s_t:flowing_sulfuric_acid"],
        u"hydrochloric_acid.json": [u"potato_s_t:hydrochloric_acid",
                                    u"potato_s_t:flowing_hydrochloric_acid"],
        u"crude_oil.json": [u"potato_s_t:crude_oil", u"potato_s_t:flowing_crude_oil"],
        u"oxygen.json": [u"potato_s_t:oxygen", u"potato_s_t:flowing_oxygen"],
        u"hydrogen.json": [u"potato_s_t:hydrogen", u"potato_s_t:flowing_hydrogen"],
        u"chlorine.json": [u"potato_s_t:chlorine", u"potato_s_t:flowing_chlorine"],
    }
    for name, values in want.items():
        path = os.path.join(TAGS, name)
        try:
            data = json.loads(read(path))
        except Exception as exc:
            check(u"A %s 存在且是合法 JSON" % name, False, str(exc))
            continue
        got = data.get(u"values", [])
        check(u"A %s：replace:false（不覆盖别人挂的条目）" % name, data.get(u"replace") is False)
        check(u"A %s：值齐全且只有自己的流体（%d 条）" % (name, len(values)),
              sorted(got) == sorted(values), u"读到 %s" % got)
    check(u"A6 路径就在 data/c/tags/fluid/ 下（不是 potato_s_t 命名空间）", os.path.isdir(TAGS))

    # ---------------- B. Java ----------------
    print(u"\n=== B. 判定认标签（双向通用） ===")
    m = re.search(r"public static boolean isGas\(Fluid fluid\)\s*\{(.*?)\n    \}", fluids, re.S)
    body = m.group(1) if m else u""
    check(u"B1 isGas 仍写死自家 6 种（数据包没加载时也认得出）",
          len(re.findall(r"fluid == \w+\.get\(\)", body)) == 12)
    # ⚠ 第一版这里查的是子串 `Tags.Fluids.GASEOUS` —— 反证第 3 刀把**代码**换成 `return false;`
    # 时校验没挂，因为上面那段注释里也写着这个词。改成断言**真的调用**（与 ZF73 的 A14 同一个教训）。
    check(u"B2 isGas 真的调用 #c:gaseous 判定（不是只在注释里提到）",
          u"fluid.defaultFluidState().is(Tags.Fluids.GASEOUS)" in body)
    check(u"B3 导入了 net.neoforged.neoforge.common.Tags",
          u"import net.neoforged.neoforge.common.Tags;" in fluids)
    check(u"B4 isLiquid 仍是「非空且非气体」（所以别人的气体会被油桶拒收）",
          u"return !isGas(fluid);" in fluids)

    # ---------------- C. 发布 ----------------
    print(u"\n=== C. 发布：同版本重打包，旧 SHA1 作废 ===")
    check(u"C1 成品存在", os.path.isfile(JAR))
    if os.path.isfile(JAR):
        got = sha1(JAR)
        check(u"C2 成品 == 构建产物（逐字节）",
              os.path.isfile(JAR_BUILT) and got == sha1(JAR_BUILT))
        check(u"C3 .sha1 文件与新成品一致", read(JAR + u".sha1").strip() == got)
        check(u"C4 新成品 SHA1 已不是上一版（%s…）" % VOIDED, not got.startswith(VOIDED))
        with zipfile.ZipFile(JAR) as zf:
            names = zf.namelist()
        check(u"C5 jar 里 7 份 c: 标签都在（ZF97 加了 nitrogen/ammonia）",
              all(u"data/c/tags/fluid/%s" % n in names for n in want))
        check(u"C6 jar 里没有探针 class", not [n for n in names if u"Check" in n])
    check(u"C7 档案里声明了上一版 SHA1 作废（%s…）" % VOIDED, VOIDED in arch)
    check(u"C8 档案里记了新成品哈希", sha1(JAR)[:12] in arch if os.path.isfile(JAR) else False)
    check(u"C9 0.10 成品仍是 84d09345…（没被动）",
          sha1(os.path.join(PROJ, u"release", u"PotatoST-0.10.jar"))
          == u"84d09345f6095408ae462dabb536307141904ea3")

    # ---------------- D. 文档 ----------------
    print(u"\n=== D. 文档 ===")
    check(u"D1 档案新增 §6.19（加流体要挂哪些通用标签）", u"### 6.19" in arch)
    check(u"D2 §6.19 写了 replace:false 这条自伤防范", u"replace\": false" in arch or u"replace:false" in arch)
    check(u"D3 §5 有 ZF74 行", u"| ZF74 |" in arch)
    check(u"D4 规划文档口径已从「不加」改成「已挂」",
          u"ZF74 更新：从" in plan and u"c:crude_oil" in plan and u"Tags.Fluids.GASEOUS" in plan)
    check(u"D5 公告补了流体标签一句", u"`c:crude_oil`" in ann and u"`c:gaseous`" in ann)

    print(u"\n============================================")
    print(u"检查项 = %d   失败项 = %d" % (checks, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
