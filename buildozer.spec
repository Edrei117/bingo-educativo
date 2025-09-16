[app]
title = Bingo Educativo
package.name = bingoeducativo
package.domain = org.bingo
source.dir = .
source.include_exts = py,png,jpg,kv,json
source.include_patterns = assets/*,images/*,cartones/*
source.exclude_dirs = tests, bin, venv
version = 0.1
requirements = python3,kivy==2.3.1,kivymd==1.2.0,pyjnius,pillow,requests
orientation = portrait
fullscreen = 0

[android]
api = 33
minapi = 21
ndk = 25b
sdk = 33
permissions = INTERNET,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_CONNECT,BLUETOOTH_SCAN,BLUETOOTH_ADVERTISE
archs = arm64-v8a, armeabi-v7a
accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1 