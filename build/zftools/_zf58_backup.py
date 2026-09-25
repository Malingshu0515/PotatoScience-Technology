# -*- coding: utf-8 -*-
"""_zf58_backup.py —— ZF58（模型跟着机器翻边 + 第4层补第5排 + 部件格起名）改前备份

用户这次报了三件事：
  ① 第 4 层是 **5 排**【】【1】【1】【】（我上一版按 4 排 + 空补的）；
  ② 截图上**模型在左边、机器方块在右边** ⇒ OBJ 的包围盒还是 ZF49 那版（主控在最左列）烘的；
  ③ Jade 显示的是 id（`block.potato_s_t.alloy_smelter_part`）⇒ 部件格缺 lang 条目。
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf58_pre"

FILES = [
    r"src\main\java\com\potatost\mod\AlloySmelterStructure.java",
    r"src\main\resources\assets\potato_s_t\models\block\alloy_smelter_south.obj",
    r"src\main\resources\assets\potato_s_t\models\block\alloy_smelter_north.obj",
    r"src\main\resources\assets\potato_s_t\models\block\alloy_smelter_east.obj",
    r"src\main\resources\assets\potato_s_t\models\block\alloy_smelter_west.obj",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"build\zftools\_zf54_obj.py",
    r"build\zftools\_zf54_verify.py",
    r"build\zftools\_zf57_verify.py",
    r"build\zftools\_zf57_lang.py",
]

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    for rel in FILES:
        src = os.path.join(PROJ, rel)
        dst = os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            fails.append(u"源文件不存在: %s" % rel)
            continue
        folder = os.path.dirname(dst)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        shutil.copy2(src, dst)
        a, b = sha1(src), sha1(dst)
        ok = a == b
        if not ok:
            fails.append(u"拷贝后哈希不一致: %s" % rel)
        print(u"  [%s] %-64s %s" % (u"OK" if ok else u"FAIL", rel, a[:12]))

    print(u"\n备份目录: %s" % ROOT)
    print(u"文件数 = %d   失败项 = %d" % (len(FILES), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
