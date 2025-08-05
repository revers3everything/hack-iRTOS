#!/bin/bash

echo "[*] Downloading apktool script..."
wget https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool -O apktool

echo "[*] Downloading apktool JAR..."
wget https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.9.3.jar -O apktool.jar

echo "[*] Making apktool script executable..."
chmod +x apktool

echo "[*] Moving apktool files to /usr/local/bin/..."
sudo mv apktool /usr/local/bin/
sudo mv apktool.jar /usr/local/bin/

echo "[*] Installing adb and apksigner..."
sudo apt update
sudo apt install -y adb apksigner

echo "[✓] apktool and required tools installed successfully."
