@echo off
cd /d "%~dp0"
title VehicleGuard AI - Backend Gateway Server
echo ======================================================
echo   Starting VehicleGuard AI Gateway Server (Port 5000)
echo ======================================================
node server.js
pause
