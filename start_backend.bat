@echo off
cd /d "%~dp0backend"
title VehicleGuard AI - Backend Gateway Server (Port 5000)
echo ======================================================
echo   Starting VehicleGuard AI Gateway Server (Port 5000)
echo   Accessible from Laptop: http://localhost:5000
echo   Accessible from Phone:  http://172.21.211.170:5000
echo ======================================================
node server.js
pause
