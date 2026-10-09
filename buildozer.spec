[app]
title = Дуб
package.name = dub
package.domain = org.dub
source.dir = .
# Лише код: у APK ідуть main.py, polotno.py, versiya.py (імена латиницею —
# кириличні імена файлів розпаковувач p4a на телефоні псує).
source.include_exts = py
source.exclude_dirs = .git,.github,.pytest_cache,__pycache__,тести,.buildozer,bin
source.exclude_patterns = *.pyc,*.spec.local
version.regex = ВЕРСІЯ = "([^"]+)"
version.filename = %(source.dir)s/versiya.py
# versionCode — підставляється з versiya.py у workflow
android.numeric_version = 1
requirements = python3,kivy==2.3.0
p4a.branch = v2024.01.21
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a
android.build_tools_version = 34.0.0
android.api = 34
android.ndk = 25b
log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
