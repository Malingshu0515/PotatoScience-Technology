# -*- coding: utf-8 -*-
"""_zf133_probefix6.py —— 假玩家"入表"的正确写法：`PlayerList.placeNewPlayer(...)`

`PlayerList` 在 1.21.1 **没有** `add(ServerPlayer)` 这个方法（javap 查过全表：只有
`placeNewPlayer(Connection, ServerPlayer, CommonListenerCookie)`）。所以走官方那条：
建好 connection + ServerPlayer 之后调 `placeNewPlayer` —— 它会把玩家登记进 `byUUID`，
`getPlayer(uuid)` 于是查得到，服务端也会 tick 它。

顺带把末地那台玩家也改成走同一个工厂（原来那段是复制粘贴的，重复代码正是修一处漏一处的源头）。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

s = io.open(P, encoding="utf-8").read()

# ---- 1) makePlayer：placeNewPlayer 入表 ----
old1 = re.search(r"    private static ServerPlayer makePlayer\(ServerStartedEvent event, String name, GameType mode\) \{.*?\n    \}\n", s, re.S)
assert old1, "找不到 makePlayer"
new1 = '''    private static ServerPlayer makePlayer(MinecraftServer server, ServerLevel where,
                                          String name, GameType mode) {
        GameProfile profile = new GameProfile(
                UUID.nameUUIDFromBytes(name.getBytes(StandardCharsets.UTF_8)), name);
        ServerPlayer p = new ServerPlayer(server, where, profile, ClientInformation.createDefault());
        // ⚠ 无头服务端里 new 出来的玩家没有连接：发任何包都会 NPE（档案 §4.43），
        //   而 Connection.channel() 为 null 时连系统聊天包都会炸（§4.86）⇒ 塞个 EmbeddedChannel。
        net.minecraft.network.Connection conn = new net.minecraft.network.Connection(
                net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
        try {
            java.lang.reflect.Field channelField =
                    net.minecraft.network.Connection.class.getDeclaredField("channel");
            channelField.setAccessible(true);
            channelField.set(conn, new io.netty.channel.embedded.EmbeddedChannel());
        } catch (Throwable t) {
            say(TAG + "EmbeddedChannel 注入失败（后面发消息会 NPE）：" + t);
        }
        p.connection = new net.minecraft.server.network.ServerGamePacketListenerImpl(
                server, conn, p,
                net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false));
        // ⚠⚠ 必须真的进服务端玩家表：`ShockwaveManager` 靠 UUID 从 PlayerList 里把发射者找回来
        //   （人下线/死了波就散），假玩家不登记的话 `getPlayer(uuid)` 恒 null ⇒
        //   每道波在出生的下一 tick 就地消失（诊断 trace 一行都没打出来，就是卡在这一句）。
        //   ⚠ 1.21.1 的 PlayerList **没有** add(...)：官方入口是 placeNewPlayer。
        server.getPlayerList().placeNewPlayer(conn, p, p.connection.cookie);
        p.setGameMode(mode);   // ⚠ 必须在入表之后（否则 changeGameModeForPlayer 会 NPE）
        return p;
    }

'''
s = s[:old1.start()] + new1 + s[old1.end():]

# ---- 2) 开场调用点 ----
s = s.replace(
    '''            player = makePlayer(event, "zf133probe", GameType.SURVIVAL);
            player.moveTo(X0 + 0.5D, Y0, Z0 + 0.5D, -90.0F, 0.0F);
            level.addFreshEntity(player);
            creativePlayer = makePlayer(event, "zf133creative", GameType.CREATIVE);
            creativePlayer.moveTo(X0 + 0.5D, Y0, Z0 + 0.5D, -90.0F, 0.0F);
            level.addFreshEntity(creativePlayer);''',
    '''            player = makePlayer(event.getServer(), level, "zf133probe", GameType.SURVIVAL);
            player.moveTo(X0 + 0.5D, Y0, Z0 + 0.5D, -90.0F, 0.0F);
            failed += check("假玩家已进服务端玩家表（getPlayer 查得到）",
                    event.getServer().getPlayerList().getPlayer(player.getUUID()) != null);
            creativePlayer = makePlayer(event.getServer(), level, "zf133creative", GameType.CREATIVE);
            creativePlayer.moveTo(X0 + 0.5D, Y0, Z0 + 0.5D, -90.0F, 0.0F);''', 1)

# ---- 3) 末地那台玩家改成走同一个工厂 ----
old3 = re.search(r"        ServerPlayer endPlayer = new ServerPlayer\(player\.getServer\(\), end.*?player\.getServer\(\)\.getPlayerList\(\)\.add\(endPlayer\);\n", s, re.S)
assert old3, "找不到末地玩家那一段"
new3 = '''        ServerPlayer endPlayer = makePlayer(player.getServer(), end, "zf133end", GameType.SURVIVAL);
        endPlayer.moveTo(0.5D, 100.0D, 0.5D, -90.0F, 0.0F);
'''
s = s[:old3.start()] + new3 + s[old3.end():]

# ---- 4) import MinecraftServer ----
s = s.replace("import net.minecraft.server.level.ClientInformation;",
              "import net.minecraft.server.MinecraftServer;\nimport net.minecraft.server.level.ClientInformation;", 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("[OK] 探针已改：placeNewPlayer 入表 + 末地玩家走同一工厂")
print("     残留 'getPlayerList().add(' =", s.count("getPlayerList().add("))
