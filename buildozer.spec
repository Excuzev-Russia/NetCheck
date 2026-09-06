[app]

# --- Основная информация о приложении ---
title = Проверка доступа
package.name = netcheck
package.domain = org.example.netcheck

source.dir = .
source.include_exts = py,kv,png,jpg,atlas

version = 0.1
requirements = python3,kivy
icon.filename = %(source.dir)s/file_0000000062f081f4a6596f9d31c0d497.png

orientation = portrait
fullscreen = 0

# --- Android ---
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True

# Отключаем резервную копию (в приложении нет пользовательских данных)
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
