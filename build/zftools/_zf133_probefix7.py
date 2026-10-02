# -*- coding: utf-8 -*-
"""_zf133_probefix7.py —— 把 CommonListenerCookie 存成局部变量（`connection.cookie` 不是公开字段）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

OLD = """        p.connection = new net.minecraft.server.network.ServerGamePacketListenerImpl(
                server, conn, p,
                net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false));
        // ⚠⚠ 必须真的进服务端玩家表：`ShockwaveManager` 靠 UUID 从 PlayerList 里把发射者找回来
        //   （人下线/死了波就散），假玩家不登记的话 `getPlayer(uuid)` 恒 null ⇒
        //   每道波在出生的下一 tick 就地消失（诊断 trace 一行都没打出来，就是卡在这一句）。
        //   ⚠ 1.21.1 的 PlayerList **没有** add(...)：官方入口是 placeNewPlayer。
        server.getPlayerList().placeNewPlayer(conn, p, p.connection.cookie);"""

NEW = """        net.minecraft.server.network.CommonListenerCookie cookie =
                net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false);
        p.connection = new net.minecraft.server.network.ServerGamePacketListenerImpl(
                server, conn, p, cookie);
        // ⚠⚠ 必须真的进服务端玩家表：`ShockwaveManager` 靠 UUID 从 PlayerList 里把发射者找回来
        //   （人下线/死了波就散），假玩家不登记的话 `getPlayer(uuid)` 恒 null ⇒
        //   每道波在出生的下一 tick 就地消失（诊断 trace 一行都没打出来，就是卡在这一句）。
        //   ⚠ 1.21.1 的 PlayerList **没有** add(...)：官方入口是 placeNewPlayer，
        //   而且 cookie 要自己留着（`connection.cookie` 不是公开字段）。
        server.getPlayerList().placeNewPlayer(conn, p, cookie);"""


def main():
    s = io.open(P, encoding="utf-8").read()
    assert s.count(OLD) == 1, "锚点 %d 次" % s.count(OLD)
    io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(OLD, NEW, 1))
    print("[OK] 已改用局部 cookie")


main()
