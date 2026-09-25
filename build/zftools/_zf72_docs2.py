# -*- coding: utf-8 -*-
u"""_zf72_docs2.py —— ZF72 第二轮档案编辑（三处，每处断言「正好命中 1 次」）

① 把 _zf72_docs.py 里**放错位置**的那条备份根记录（它落在 §9 末尾、§10 标题之前）搬进 §10；
② §10 追加「重打包自证」这条：反证动过两个源文件 ⇒ 真重打一遍 + 逐条目 CRC 对账，
   顺带暴露"成品里还留着已删的 lv_001.png、所以重打包不再逐字节相同"；
③ §9 记一条待用户拍板：要不要把 lv_001.png 从回收站还原回去。

锚点不中就不写（`replace_once` 命中数必须为 1）。
"""
import hashlib
import io
import sys

ARCH = r"E:\PotatoST\docs\开发档案.md"

fails = []

# ① 放错位置的那一段（§9 末尾）
MISPLACED = u"""- **⚠ ZF72 备份根换地方（并把事故记档）**：一直用的桌面根
  `C:\\Users\\Administrator\\Desktop\\PotatoST救援_<yyyyMMdd_HHmmss>\\` 里那份
  `..._20260917_183054`（记录大小 **424,191,790 B**，装着 zf68_pre…zf71_pre 与各轮的 `新增文件\\`）
  **已经被删进回收站**（删除时间 **2026-09-19 13:36:29**；`$R` 实体仍在 ⇒ **可以还原**。
  取证脚本 `build/zftools/_zf72_recycle_list.py`，**只读**，不解包、不动回收站）。
  ⇒ 新根源改到 **`C:\\PotatoST救援\\<阶段名>\\`**（C 盘、**不进桌面**，不再被「清桌面」带走）：
  ZF72 起先建 `zf72_pre`（1 个改前件 `docs\\开发档案.md`，逐份核哈希、失败 0）。
  桌面那份**要不要还原由用户定**，我不动回收站里的任何东西。
"""

ANCHOR_S10_HEAD = u"\n## 10. 备份策略"
ANCHOR_S10_TAIL = u"  确认等价再删除；并保证实例 mods 里同名 mod 的 jar **有且只有 1 个**"
ANCHOR_S9_TAIL = u"      本轮起改在 `C:\\PotatoST救援\\zf72_pre\\`。"

REBUILD_S10 = r"""- ✅ **ZF72（v0.11 规划轮）的「重打包自证」—— 反证动过源码，所以真重打一遍对账**：
  本轮反证的第 4/5 刀砍在**源码**上（`TankContents.java`、`FluidPumpBlockEntity.java`），
  脚本自己核过「还原后 SHA1 逐字节相同」，但那只是脚本自己说的。于是真跑了一遍
  `gradlew build --offline --no-build-cache`（17 秒；`compileJava UP-TO-DATE` —— 内容没变
  所以根本没重编，这本身就是一条旁证），再用 `_zf72_rebuild_diff.py` 把新 jar 与成品
  **逐条目 CRC 对账**：成品 **708** 条目 / 新打 **707** 条目，**唯一差异**是
  `assets/potato_s_t/textures/block/lv_001.png`（3352 B：成品里有、源码树里已被用户删），
  其余 **707 个同名条目逐条 CRC 完全相同** ⇒ 反证没留痕迹、源码树 == 成品。
  注意打包产物名是 `build\libs\potato_s_t-0.10.jar`（`archivesBaseName` 是小写 mod id），
  `release\PotatoST-0.10.jar` 是发布时**改名**的副本 —— 改名不改字节，所以能逐字节比。
- ⚠ **同一件事的另一面：成品里还留着用户已删的孤儿贴图** ⇒
  `release\PotatoST-0.10.jar` 里有 `lv_001.png`（用户 **2026-09-22 14:13:45** 删进回收站，
  `_zf72_recycle_probe.py` 取证），所以**从今往后「重打包 == 成品」这条自证不再成立**
  （新打 `0f6454abbdbc90e0361f555d18ca46ed87282710` / 2,214,039 B，**只是自证产物、不是新版本**，
  成品 SHA1 仍 `84d09345…`、未作废）。两条路，**由用户定**：
  ① 把 `lv_001.png` 从回收站还原回 `textures\block\`（那张图没人引用，代价只是 ModelCheck 会再报 2 条提示），
  自证能力恢复；② 承认这条差异，以后对账都按「成品 − 已知清单」看（本轮就是这么做的）。
  ⚠ 这条对账**只对本轮有效**：从 ZF73 起源码树要开始变，跟 v0.10 成品比就没意义了。

"""

S9_LV001 = u"""- [ ] **ZF72 顺带核出一件事：成品 jar 里还留着已被删掉的孤儿贴图** ——
      `release\\PotatoST-0.10.jar`（708 条目）里有 `assets/potato_s_t/textures/block/lv_001.png`
      （3352 B，你 **2026-09-22 14:13:45** 删进回收站的那张），所以现在**重打包不再与成品
      逐字节相同**（新打 707 条目，差的就是它；其余 707 个同名条目逐条 CRC 相同，见 §10）。
      功能无影响（本来就没人引用），但「重打包 == 成品」这条自证断了。
      要不要把它从回收站**还原**回 `textures\\block\\`（代价：ModelCheck 会再报 2 条孤儿提示），你定。
"""


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        fails.append(u"%s：锚点命中 %d 次（必须正好 1 次）" % (label, n))
        return text
    return text.replace(old, new, 1)


def main():
    with io.open(ARCH, "r", encoding="utf-8") as fh:
        text = fh.read()
    before_len = len(text)
    before_sha = sha1(ARCH)
    print(u"改前: %d 字符  %s" % (before_len, before_sha[:12]))

    # ① 搬走放错位置的那段（它紧贴 §10 标题，中间没有空行 —— 第一版锚点里多写了一个换行，
    #    命中 0 次、脚本按规矩整篇没写，这里按实际排版修正）
    text = replace_once(text, MISPLACED + u"## 10. 备份策略", u"## 10. 备份策略",
                        u"① §9 末尾那段备份记录")
    # ② 放进 §10 末尾，并追加「重打包自证」两条
    text = replace_once(text, ANCHOR_S10_TAIL,
                        ANCHOR_S10_TAIL + u"\n" + MISPLACED + REBUILD_S10.rstrip(u"\n"),
                        u"② §10 末尾插入点")
    # ③ §9 记一条待拍板
    text = replace_once(text, ANCHOR_S9_TAIL, ANCHOR_S9_TAIL + u"\n" + S9_LV001.rstrip(u"\n"),
                        u"③ §9 插入点")

    if fails:
        print(u"\n锚点有问题，**整篇不写**：")
        for f in fails:
            print(u"  !! " + f)
        return 1

    with io.open(ARCH, "w", encoding="utf-8", newline=u"\n") as fh:
        fh.write(text)
    print(u"改后: %d 字符（%+d）  %s" % (len(text), len(text) - before_len, sha1(ARCH)[:12]))
    print(u"三处编辑全部命中 1 次、已写入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
