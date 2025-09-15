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
osx.python_version = 3
osx.kivy_version = 2.0.0
fullscreen = 0

# Configuraciones adicionales para compatibilidad de pantallas
android.resizable = True
android.allow_backup = True
android.allow_clear_user_data = True
android.allow_clear_application_data = True
android.permissions = INTERNET,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_CONNECT,BLUETOOTH_SCAN,BLUETOOTH_ADVERTISE
android.api = 34
android.minapi = 24
android.ndk = 25b
android.sdk = 34
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a
p4a.branch = master
p4a.bootstrap = sdl2 

# Configuración del splash screen
android.presplash_color = #1a237e
android.presplash = assets/proedu.png
android.allow_backup = True 