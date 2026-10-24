@echo off
cd /d "%~dp0"
title VehicleGuard AI - Mobile Expo Server
set NODE_OPTIONS=--max-old-space-size=4096
echo ======================================================
echo   Starting VehicleGuard AI Mobile App (Expo Go)
echo   Memory allocation: 4096 MB
echo ======================================================
npx expo start -c
pause
