# Script para compilar APK en Google Colab
# Ejecutar en: https://colab.research.google.com/

# 1. Instalar dependencias
!pip install buildozer
!apt-get update
!apt-get install -y openjdk-8-jdk zlib1g-dev libjpeg-dev libfreetype6-dev libffi-dev libssl-dev

# 2. Configurar variables de entorno
import os
os.environ['JAVA_HOME'] = '/usr/lib/jvm/java-8-openjdk-amd64'
os.environ['ANDROID_HOME'] = '/root/.buildozer/android/platform/android-sdk'
os.environ['ANDROID_NDK_HOME'] = '/root/.buildozer/android/platform/android-ndk'

# 3. Compilar APK
!buildozer android debug

# 4. Descargar APK
from google.colab import files
files.download('bin/bingoeducativo-0.1-arm64-v8a-debug.apk')