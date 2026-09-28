# -*- coding: utf-8 -*-
u"""_zf137_nv3.py —— 用户第三次改口：头盔夜视 **8 s / III**，并且**要它别闪**

用户原话：「头盔改成8s夜视III吧 **或者**让视野不会因为夜视快没了而一闪一闪也可以」。

## 这两条**不能同时成立**（本轮从源码核实的硬事实）

`net/minecraft/client/renderer/GameRenderer.java`：

```java
public static float getNightVisionScale(LivingEntity livingEntity, float nanoTime) {
    MobEffectInstance mobeffectinstance = livingEntity.getEffect(MobEffects.NIGHT_VISION);
    return !mobeffectinstance.endsWithin(200) ? 1.0F
         : 0.7F + Mth.sin(((float)mobeffectinstance.getDuration() - nanoTime) * (float) Math.PI * 0.2F) * 0.3F;
}
```

`MobEffectInstance.endsWithin(n)` = `!isInfiniteDuration() && this.duration <= n`。

⇒ **剩余时长 ≤ 200 tick（10 s）就会闪**（亮度 0.4~1.0、每 tick 走 0.2π ⇒ 周期 10 tick = 0.5 秒），
而且**跟等级无关**（那个公式根本不看 amplifier）。所以 4 s / 5 s / **8 s 全都会闪**。
要"不闪"，唯一办法是让剩余时长**永远 > 200 tick** ⇒ 单次时长必须 > 10 s。

**本轮取"不闪"那条**（用户说"或者…也可以"已经授权），顺带把等级按他说的给到 III：
时长 **260 tick（13 s）**、剩余掉到 **220 tick（11 s）** 就续 ⇒ 剩余恒在 220~260 ⇒ 视野恒定；
续的节奏仍是每 2 秒一次。代价（躲不掉）：摘下头盔最多再亮 13 秒。

## 这个脚本干两件事

  ① 四语言说明里把夜视那句**补实**：翻译线把星璨钢说明整段重写过，删掉了具体数字
     （"头盔还会点亮相貌之外的视野"），玩家看不出它到底给什么 ⇒ 补一句带等级与节奏的；
  ② 把档案那一节里"4 s → 5 s"的段落续上这次改口的结论。

（探针 `_zf137_verify.py` 与反证刀 `_zf137_falsify.py` 的改动在下一个脚本里做，
 因为那里改的是判据本身，不适合和文案混在一起。）

跑法：
    python build/zftools/_zf137_nv3.py            # 只体检
    python build/zftools/_zf137_nv3.py --write
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
LANG = os.path.join(PROJ, r"src\main\resources\assets\potato_s_t\lang")
ARCH = os.path.join(PROJ, "docs", "开发档案.md")
KEY = u"tooltip.potato_s_t.star_steel_set"

# (语言文件, 要在说明第一段里找到的锚（翻译线现在那句的尾巴）, 追加到它后面的句子, 必须出现的词)
CASES = [
    (u"zh_cn.json", u"头盔还会点亮相貌之外的视野。",
     u"那是**夜视 III**：每次 13 秒、戴着就一直续，亮度恒定不闪。", u"夜视 III"),
    (u"en_us.json", u"the helmet opens a sight beyond sight.",
     u" That is Night Vision III: 13 s at a time, renewed while worn, never flickering.",
     u"Night Vision III"),
    (u"ja_jp.json", u"ヘルメットは視界の外を照らす。",
     u"それは暗視 III ——1 回 13 秒、装着中は途切れず更新され、明滅しません。", u"暗視 III"),
    (u"ru_ru.json", u"шлем открывает зрение за пределами зрения.",
     u" Это Ночное зрение III: по 13 с, продлевается, пока он надет, — ровный свет без мерцания.",
     u"Ночное зрение III"),
]

fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def main(argv):
    write = u"--write" in argv
    before = {}
    after = {}
    for name, anchor, sentence, word in CASES:
        p = os.path.join(LANG, name)
        raw = read(p)
        obj = json.loads(raw)
        before[name] = obj
        text = obj.get(KEY, u"")
        if not text:
            fails.append(u"%s：没有 %s" % (name, KEY))
            continue
        if word in text:
            print(u"  [SKIP] %s：已经有「%s」" % (name, word))
            after[name] = obj
            continue
        if anchor not in text:
            fails.append(u"%s：锚点不在说明里 —— %s" % (name, anchor[:60]))
            print(u"  [FAIL] %s：锚点没命中（翻译线又改过文案？）" % name)
            continue
        new_text = text.replace(anchor, anchor + sentence, 1)
        if not write:
            print(u"  [将改] %s：在「%s」后补一句" % (name, anchor[:24]))
            after[name] = dict(obj, **{KEY: new_text})
            continue
        # ⚠ 只重写那一行；且先把新文本算好再 open("w")（§4.99）
        lines = raw.split(u"\n")
        idx = [i for i, l in enumerate(lines) if l.startswith(u'  "%s":' % KEY)]
        if len(idx) != 1:
            fails.append(u"%s：`%s` 那一行命中 %d 次" % (name, KEY, len(idx)))
            continue
        lines[idx[0]] = u'  "%s": %s,' % (KEY, json.dumps(new_text, ensure_ascii=False))
        # 保持原有的行内格式（`": ` 后面一个空格，与翻译线那份一致）
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(lines))
        after[name] = json.loads(read(p))
        print(u"  [写出] %s" % name)

    print(u"")
    for name, _a, _s, word in CASES:
        if name not in after:
            continue
        t = after[name]
        ok = (word in t.get(KEY, u"")) and len(t) == len(before[name])
        print(u"  [%s] %-12s 键数 %d（未变）  说明里有「%s」" % (u"OK" if ok else u"FAIL", name, len(t), word))
        if not ok:
            fails.append(u"%s：补句后核对不过（键数 %d → %d）" % (name, len(before[name]), len(t)))

    # 档案：把"改口"那一段续上
    text = read(ARCH)
    i = text.find(u"#### 五、⚠ 用户随后改口：**4 s → 5 s**")
    if i < 0:
        fails.append(u"档案里找不到「五、用户随后改口」那一节")
    else:
        j = text.find(u"#### 六、", i)
        end = j if j > 0 else len(text)
        add = (u"\n#### 五之二、⚠ 用户**又**改口：8 s / III，并且要它别闪（同一节的续）\n\n"
               u"「头盔改成8s夜视III吧 **或者**让视野不会因为夜视快没了而一闪一闪也可以」。\n\n"
               u"**这两条不能同时成立** —— 本轮把闪的判据从源码里挖出来了\n"
               u"（`GameRenderer.getNightVisionScale` + `MobEffectInstance.endsWithin`）：\n\n"
               u"```java\n"
               u"return !mobeffectinstance.endsWithin(200) ? 1.0F\n"
               u"     : 0.7F + Mth.sin((duration - nanoTime) * (float) Math.PI * 0.2F) * 0.3F;\n"
               u"// endsWithin(n) = !isInfiniteDuration() && duration <= n\n"
               u"```\n\n"
               u"⇒ **剩余时长 ≤ 200 tick（10 s）就闪**（亮度 0.4~1.0，周期 10 tick = **0.5 秒**），\n"
               u"而且**不看等级** ⇒ **4 s / 5 s / 8 s 全都会闪**；\n"
               u"要「不闪」只有一个办法：**剩余时长永远 > 200 tick** ⇒ 单次时长必须 > 10 s。\n\n"
               u"**本轮取「不闪」那条**（用户原话里「或者…也可以」已经授权），等级按他说的给到 **III**：\n"
               u"单次 **260 tick（13 s）**、剩余掉到 **220 tick（11 s）** 就续 ⇒ 剩余恒在 220~260\n"
               u"⇒ 视野恒定；续的节奏仍是每 2 秒一次。**摘头盔后最多再亮 13 秒**（「不闪」的下界就是 10 s，\n"
               u"再加 2 s 续期节奏 ⇒ 退场时间不可能更短）。\n\n"
               u"⚠ 翻译线在这之后把星璨钢说明**整段重写**成散文体，夜视那句被删掉了具体数字\n"
               u"（「头盔还会点亮相貌之外的视野」）⇒ `_zf137_nv3.py` 把「夜视 III：每次 13 秒、\n"
               u"戴着就一直续，亮度恒定不闪」这句补了回去（**四语言只改值、不加键**）。\n")
        print(u"  [%s] 开发档案.md：%s那一节的续" % (u"改" if write else u"将改", u""))
        if write:
            io.open(ARCH, "w", encoding="utf-8", newline=u"").write(text[:end] + add + text[end:])

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
