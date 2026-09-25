# -*- coding: utf-8 -*-
"""_zf65_backup.py —— ZF65 改前件（循环音卡住 bug 的修复）

⚠ 这一轮我在动手前忘了先抄改前件（ZF63 立的规矩是"动第一个字节之前先抄"），
   所以这三份 **zf65_pre 是事后按"逐条反向套用本次编辑"重建的**。
   重建完必须能通过"编译后与 ZF64 成品 jar 里的 class 逐字节相同"这一关（见 _zf65_precheck.py），
   通不过就说明重建得不忠实，得重来。
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf65_pre"

SWAP = [
    # (源码树里的文件, 备份里的文件) —— 反向补丁：把 ZF65 的新文本换回 ZF64 的旧文本
    (r"src\main\java\com\potatost\mod\AlloySmelterBlockEntity.java", [
        # ① craftTick 的注释被 ZF65 扩写了
        (u'''        // ZF64：先当"这一 tick 没在烧"，只有真的扣了电、推进了进度才置真 —— 循环电机声看这个标记。
        //（ZF65 起每 tick 的**权威清零**在 serverTickBody() 开头，因为"拆解"根本不走这个函数；
        //  这里再清一次是为了"探针直接连调 craftTick()"时语义仍然完整）''',
         u'''        // ZF64：先当"这一 tick 没在烧"，只有真的扣了电、推进了进度才置真 —— 循环电机声看这个标记'''),
        # ② serverTickBody 开头 ZF65 加的权威清零
        (u'''        // ⚠ ZF65（用户实测报的 bug）：**每 tick 先把"在烧"清掉**，只有下面 craftTick() 真的扣了电、
        //    推进了进度才会再置真。这一句必须待在 `formed` 分支的**外面** ——
        //    拆解（挖部件格 / 挖接线口 / 扳手 / 控制器被挖）走的是 `disassemble()` → `setFormed(false)`，
        //    那条路**不经过 craftTick()**；上一版把清零交给 craftTick() ⇒ 拆完之后 `running` 永远停在 true，
        //    客户端每 tick 都收到"在烧"⇒ **循环电机声一直响到重新建一台为止**。
        this.running = false;
        // 自愈（ZF56）''',
         u'''        // 自愈（ZF56）'''),
        # ③ craftTick 那行注释尾巴 + 文件末尾被删掉的那段过时注释
        (u'''            craftTick();                                    // 配方推进（每 tick，真的烧起来了它会把 running 置真）
            return;''',
         u'''            craftTick();                                    // 配方推进（每 tick）
            return;'''),
        (u'''        if (this.level.getGameTime() % 10 == 0) {
            AlloySmelterBlock.tryAutoForm(this.level, this.worldPosition);
        }
    }''',
         u'''        if (this.level.getGameTime() % 10 == 0) {
            AlloySmelterBlock.tryAutoForm(this.level, this.worldPosition);
        }
        // ⚠ 配方留在这里：用户说「先不做配方」，所以本阶段 tick 里只做结构复查。
        //    以后加配方时，参照 ElectricBlastFurnaceBlockEntity.serverTickBody()：
        //    先算整批耗电（一件 FE 数 × 数量 / 时长），电够才推进，到点再结算产物。
    }'''),
    ]),
    (r"src\main\java\com\potatost\mod\client\sound\MachineRunningSound.java", [
        (u'''        if (s != null && (s.isStopped() || s.be.isRemoved())) {
            // ZF65：不能只把它从表里删掉 —— 表和声音引擎是两回事，删表不等于消音。先 stop() 再删。
            s.stop();
            ACTIVE.remove(key);''',
         u'''        if (s != null && (s.isStopped() || s.be.isRemoved())) {
            ACTIVE.remove(key);'''),
        (u'''    @Override
    public void tick() {
        // ZF65：不能只看 isRemoved()。再加一条"那格已经不是这个方块实体了"（挖掉 ⇒ 空气、换方块 ⇒ 另一个实例），
        // 两条中任一成立就停 —— 循环音一旦卡住是没有别的机会停的（方块没了就再没有 tick 去纠正它）。
        // 用 isLoaded 挡一下：区块没加载时 getBlockEntity 会是 null，那不是"方块没了"。
        net.minecraft.world.level.Level level = this.be.getLevel();
        boolean gone = this.be.isRemoved()
                || level == null
                || (level.isLoaded(this.pos) && level.getBlockEntity(this.pos) != this.be);
        if (gone) {
            this.stop();
            ACTIVE.remove(this.pos, this);
        }
    }''',
         u'''    @Override
    public void tick() {
        if (this.be.isRemoved()) {
            this.stop();
            ACTIVE.remove(this.pos, this);
        }
    }'''),
    ]),
    (r"src\main\java\com\potatost\mod\PotatoST.java", [
        (u'''        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(BlastFurnaceAssembly.class);

        AlloySoundStopCheck.register();              // ZF65 临时探针（验证完连同本行一起删）
    }''',
         u'''        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(BlastFurnaceAssembly.class);
    }'''),
    ]),
]


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    fails = []
    print(u"ROOT = %s" % ROOT)
    for rel, patches in SWAP:
        cur = io.open(os.path.join(PROJ, rel), encoding="utf-8").read()
        old = cur
        for new_text, old_text in patches:
            n = old.count(new_text)
            if n != 1:
                fails.append(u"%s：待反向替换的 ZF65 文本命中 %d 次（应为 1）" % (rel, n))
                continue
            old = old.replace(new_text, old_text, 1)
        dst = os.path.join(ROOT, rel)
        folder = os.path.dirname(dst)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        io.open(dst, "w", encoding="utf-8", newline="\n").write(old)
        print(u"  [%s] %-58s %s（%d -> %d 字节）"
              % (u"OK" if old != cur else u"??", rel, sha1(dst)[:12], len(cur.encode("utf-8")),
                 len(old.encode("utf-8"))))
    print(u"\n改前件目录: %s" % ROOT)
    print(u"文件数 = %d   失败项 = %d" % (len(SWAP), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
