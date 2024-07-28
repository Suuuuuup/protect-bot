@echo off
color b
title Démarrage du Bot Discord
echo ===============================
echo  Démarrage du Bot Discord
echo ===============================
echo.

echo Installation des dependances...
pip install -r requirements.txt

echo.
echo ===============================
echo  Démarrage du Bot
echo ===============================
echo.


python main.py
pause


