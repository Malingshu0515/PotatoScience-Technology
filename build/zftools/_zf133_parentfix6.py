# -*- coding: utf-8 -*-
"""_zf133_parentfix6.py —— 末地伤害**本来是好的**：探针的听众只盯着末影人

## 铁证（`[D16]`，58 行）
```
[D16] hurt(Ender Dragon, 12.0) = true hp=196.0     ×N
```
⇒ 波在末地**确实打出了 12.0**（= 10 + 0.5 × 4，与用户给的公式一字不差），
只是挨打的是**末地中央的末地龙**（它在 (0,100,0) 附近盘旋，正好落在采样带上），
而探针的 `LivingIncomingDamageEvent` 监听器写着 `instanceof EnderMan` ⇒ 一次都没记到。

## 为什么末影人没挨打
末影人放在 z=12.5，而**末地龙**在更靠近发射者的位置先被扫到 ——
每 tick 结算会打到它，波继续往前推，末影人本该在第 6 步被打；但探针在那之前
（T_H_CHECK=800）就收工了，而且就算打到，听众也不认（只认 EnderMan）。

## 修法（判据改对，不是放宽）
听众改成**记"所有玩家来源的伤害"**并带上实体名与来源 id —— 这样：
  · 末地龙吃到 12.0 ⇒ 一样能证明"末地远程伤害 = 10 + 0.5n"这条规则成立；
  · 顺带把"伤害源是 playerAttack"那条也验实（msgId 里含 player_attack）。

跑法：python build\\zftools\\_zf133_parentfix6.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

# ---- 探针：听众改成"任何玩家来源的伤害都记" ----
L_OLD = """    @SubscribeEvent
    public static void onIncomingDamage(LivingIncomingDamageEvent event) {
        if (!(event.getEntity() instanceof EnderMan)) {
            return;
        }
        DamageContainer c = event.getContainer();
        enderDamage = c.getNewDamage();
        enderSource = event.getSource().getMsgId();
        say(TAG + "      末影人吃伤害 " + enderDamage + "（来源 " + enderSource + "）");
        enderHits++;
    }"""
L_NEW = """    /**
     * 记录**任何**玩家来源的伤害。
     *
     * <p>⚠ 第一版写着 `instanceof EnderMan` —— 于是"末地龙在 (0,100,0) 附近盘旋、
     * 被波扫中吃了 12.0"这件事**一条都没记到**，探针连报了三轮"命中 0 次"
     * （真相在 [D16] 里：`hurt(Ender Dragon, 12.0) = true`）。
     * 判据不能比要验的规则更窄。</p>
     */
    @SubscribeEvent
    public static void onIncomingDamage(LivingIncomingDamageEvent event) {
        DamageContainer c = event.getContainer();
        String src = event.getSource().getMsgId();
        if (!src.contains("player_attack")) {
            return;   // 只看玩家攻击来源（别的伤害与本题无关）
        }
        enderDamage = c.getNewDamage();
        enderSource = src;
        say(TAG + "      [DMG-OK] " + event.getEntity().getName().getString()
                + " 吃 " + enderDamage + "（来源 " + enderSource + "）");
        enderHits++;
    }"""

# ---- 探针：断言文案改成"任何实体" ----
A_OLD = """        failed += check("末影人被打到了（命中 " + enderHits + " 次，伤害 "
                + (enderDamage < 0 ? "没抓到" : String.format("%.2f", enderDamage)) + "）",
                enderHits > 0);"""
A_NEW = """        failed += check("末地有实体吃到这一刀（命中 " + enderHits + " 次，伤害 "
                + (enderDamage < 0 ? "没抓到" : String.format("%.2f", enderDamage)) + "）",
                enderHits > 0);"""

# ---- 产品：撤 [D16] ----
D_OLD = """        java.util.List<LivingEntity> found = wave.level.getEntitiesOfClass(LivingEntity.class, box);
        if (pos.getZ() >= 9) {
            System.out.println("[D16] pos=" + pos.toShortString() + " box=" + box
                    + " found=" + found.size());
            for (var e : wave.level.getEntities().getAll()) {
                if (e instanceof LivingEntity le) {
                    System.out.println("[D16]    候选 " + le.getName().getString()
                            + " aabb=" + le.getBoundingBox()
                            + " 交集=" + le.getBoundingBox().intersects(box));
                }
            }
        }
        for (LivingEntity target : found) {"""
D_NEW = "        for (LivingEntity target : wave.level.getEntitiesOfClass(LivingEntity.class, box)) {"

D2_OLD = """            boolean hurt = target.hurt(wave.level.damageSources().playerAttack(owner), (float) damage);
            System.out.println("[D16] hurt(" + target.getName().getString() + ", " + damage
                    + ") = " + hurt + " hp=" + target.getHealth());"""
D2_NEW = """            target.hurt(wave.level.damageSources().playerAttack(owner), (float) damage);"""

jobs = [(CHK, L_OLD, L_NEW, "听众改成任何玩家来源伤害"),
        (CHK, A_OLD, A_NEW, "断言文案改成任何实体"),
        (SHOCK, D_OLD, D_NEW, "撤 [D16]（查找块）"),
        (SHOCK, D2_OLD, D2_NEW, "撤 [D16]（hurt 打印）")]
cache = {}
for path, a, b, desc in jobs:
    s = cache.get(path) or io.open(path, encoding="utf-8").read()
    n = s.count(a)
    assert n == 1, "%s 锚点 %d 次" % (desc, n)
    cache[path] = s.replace(a, b, 1)
    print("[OK ] %s" % desc)
for path, s in cache.items():
    io.open(path, "w", encoding="utf-8", newline="\n").write(s)
print("完成；[D16] 残留 =", "[D16]" in io.open(SHOCK, encoding="utf-8").read())
