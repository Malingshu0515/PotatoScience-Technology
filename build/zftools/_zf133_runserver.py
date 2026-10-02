# -*- coding: utf-8 -*-
"""_zf133_runserver.py —— 跑真服务端探针的**带闸门**启动器（ZF133 的两个坑都在这里挡住）

第一轮教训（两个都会让我"看着像跑过了，其实是别人的旧结果"）：

  ① **`gradlew runServer` 的 gradle 壳会先退出**（exit code 0），真服务端进程还活着
     ⇒ 作业报"完成"了，其实服务器还在跑。于是：
        · 报告文件是**上一次**跑出来的（我差点照着旧报错去修已经修好的地方）；
        · 下一次启动抢 `run/server/logs/latest.log` 失败（"另一个程序正在使用此文件"）。
  ② 所以我每次都先 `kill` 掉残留的服务端进程、**等到文件真的能独占打开**再启动。

跑法：
    python build\\zftools\\_zf133_runserver.py            # 清干净 → 启动 → 等结束 → 清干净
    python build\\zftools\\_zf133_runserver.py --kill     # 只清
"""
import io
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
LOG = os.path.join(ROOT, r"build\zftools\_zf133_runSrv.log")
REPORT = os.path.join(ROOT, r"build\zftools\check\zf133_axe_probe.log")
LOCK = os.path.join(ROOT, r"run\server\logs\latest.log")

KILL_PS = (
    "Get-CimInstance Win32_Process -Filter \"Name='java.exe'\" | "
    "Where-Object { $_.CommandLine -match 'forge.logging.console.level|gradle-wrapper.jar' } | "
    "ForEach-Object { Write-Output ('kill ' + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force }"
)


def kill(leftovers=True):
    print("--- 清残留服务端进程 ---")
    subprocess.run(["powershell", "-NoProfile", "-Command", KILL_PS], cwd=ROOT)
    for attempt in range(30):
        time.sleep(1)
        try:
            f = io.open(LOCK, "r+b")
            f.close()
            print("  [OK] %s 已可独占打开（第 %d 秒）" % (LOCK, attempt + 1))
            return True
        except Exception:
            pass
    print("  [FAIL] 20 秒了还占着 %s" % LOCK)
    return False


def main():
    if "--kill" in sys.argv:
        kill()
        return

    if not kill():
        return 1

    stamp = time.strftime("%H:%M:%S")
    print("--- 启动真服务端（%s）---" % stamp)
    if os.path.exists(REPORT):
        before = os.path.getmtime(REPORT)
        print("  旧报告 mtime = %s（跑完必须变新）" % time.strftime("%H:%M:%S", time.localtime(before)))
    else:
        before = None
        print("  还没有报告文件")

    import shutil
    shutil.copyfile(REPORT, REPORT + ".prev") if os.path.exists(REPORT) else None

    with io.open(LOG, "w", encoding="utf-8") as out:
        subprocess.run(["cmd", "/c",
                        r"cd /d E:\PotatoST && .\gradlew.bat runServer --offline --no-build-cache"],
                       stdout=out, stderr=subprocess.STDOUT, cwd=ROOT)

    print("--- gradle 壳已退出（真服务端可能还在跑），等报告落地 ---")
    for attempt in range(180):
        time.sleep(2)
        if os.path.exists(REPORT) and (before is None or os.path.getmtime(REPORT) > before):
            print("  [OK] 报告已更新（第 %d 秒）" % (2 * (attempt + 1)))
            break
    else:
        print("  [FAIL] 报告一直没更新 —— 看 %s" % LOG)

    kill()
    body = io.open(REPORT, encoding="utf-8", errors="replace").read() if os.path.exists(REPORT) else ""
    lines = [l for l in body.split("\n") if "verdict" in l]
    print("--- 报告判定：%s ---" % (lines[-1] if lines else "没有 verdict 行"))
    print("--- 完整报告：%s ---" % REPORT)


main()
