# -*- coding: utf-8 -*-
r"""_rzh_make_initscript.py —— 生成一个 Gradle init 脚本（无 BOM），用来摸清 jar 的输入。

为什么要绕这一下：
  · PowerShell 的 `Set-Content -Encoding utf8` 会写 **BOM**，而 Gradle 的 init script
    **不接受 BOM**（`Unexpected character: '\ufeff'`）；
  · 在 init script 顶层写 `tasks.register(...)` 也不行 —— 那时还没有 Project，
    报 `Could not get unknown property 'tasks' for build of type DefaultGradle`。
    正确写法是 `gradle.projectsEvaluated { ... }`，拿到 project 再注册。

背景：`gradlew build` 报成功、`build/classes/java/main/.../*.class` 有 358 个，
但 `build/libs/potato_s_t-0.11.jar` 里 **0 个 .class**。得问 Gradle：
它认为源集的类输出目录是哪个、存不存在。
"""
from __future__ import print_function
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, u"cfg", u"zfprint.gradle")

SCRIPT = u"""// 由 _rzh_make_initscript.py 生成；只打印，不改任何东西
gradle.projectsEvaluated {
    def p = gradle.rootProject
    p.tasks.register("zfPrintJarInputs") {
        doLast {
            def ss = p.sourceSets.main
            println "== sourceSets.main =="
            println "java srcDirs  : " + ss.java.srcDirs
            println "allJava count : " + ss.allJava.files.size()
            println "classesDirs   :"
            ss.output.classesDirs.files.each { f ->
                def n = f.exists() ? f.listFiles()?.length : -1
                println "   exists=" + f.exists() + "  entries=" + n + "  " + f
            }
            println "resourcesDir  : " + ss.output.resourcesDir
            def jt = p.tasks.named("jar").get()
            println "== jar task =="
            println "archiveFile   : " + jt.archiveFile.get().asFile
            println "classpath set : " + jt.hasProperty("classpath")
            def css = ss.output.classesDirs.files
            println "will include classesDirs? " + css.collect{ it.exists() }
        }
    }
}
"""


def main():
    d = os.path.dirname(OUT)
    if not os.path.isdir(d):
        os.makedirs(d)
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(SCRIPT)
    raw = io.open(OUT, u"rb").read()
    assert not raw.startswith(u"\ufeff".encode(u"utf-8")), u"写出来带 BOM 了"
    print(u"wrote %s (%d bytes, no BOM)" % (OUT, len(raw)))
    return 0


if __name__ == u"__main__":
    raise SystemExit(main())
