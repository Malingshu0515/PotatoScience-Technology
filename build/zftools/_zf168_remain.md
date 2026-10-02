# ZF168 收尾清单（只剩一件事：推送）

> **ZF168 = 修「流体转化器的输出罐改不了样板」**。功能、探针、门、反证刀、五语键、文档、重打成品
> **都已完成并验过**，唯一没做成的是 `git push` —— 到 GitHub 的连接被挡（不是仓库/凭据问题）。

## 已经完成的（都有证据）

| 项 | 证据 |
|---|---|
| 机器 → 容器路径（空容器右键装走；潜行 = 输入罐）+ 占领提示 | `_zf168_verify.py` A 段 |
| 真开服探针（设定 → 被拒+提示 → 装走 → 换成功 + 4 条负对照）**12/0** | `build/zftools/_zf168_probe_utf8.txt` |
| 常驻门 **20/0** | `_zf168_verify.py` |
| 反证刀 **6/6** | `build/zftools/_zf168_falsify.log` |
| 五语新键（620→621 / lzh 622→623） | `_zf168_lang.py` 日志 |
| 文档 §4.173 / §5 ZF168 行 / §9 / 交接第 38 条 / 英文公告 | `_zf168_docs.py --write`：失败 0 |
| 备份 `C:\PotatoST救援\zf168_pre`（1478 份，失败 0） | `_zf168_pre.py` 日志 |
| 重打成品 = 构建产物逐字节、零探针 class | `release\PotatoST-0.13.jar` **6,005,994 B / sha1 `0966ddbce7045fe08bbd0108c60ef15bc13767e2`** |
| 提交 | `c9c0766`（主体）+ `be4445f`（反证刀与门收紧） |

## 只剩：推送

```powershell
cd E:\PotatoST
git status -sb          # 现在是 `## main...origin/main [ahead 3]`
git push origin main    # 通了就完事
```

**诊断结论（本轮实测）**：`Resolve-DnsName github.com` 能出 IP（20.205.243.166），
但 `Test-NetConnection github.com -Port 443` 为 **False**、且没有配代理 ⇒
**DNS 正常、到 GitHub 的 443 打不通**（本轮之前成功推过两次，属间歇性阻断）。
后台重试在跑：`build/zftools/_zf168_push.log`（25 次 × 100 秒）。

## 推上去之后建议顺手核一遍

1. `git log --oneline -3` —— 顶上应该是 `be4445f`；
2. `python build\zftools\_zf168_verify.py` —— 应 **20/0**；
3. 若是**下一轮**才推：先 `git fetch` 看远端有没有别人的新提交，需要时 `git pull --rebase` 再推。
