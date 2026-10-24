@echo off
cd /d "%~dp0"
title VehicleGuard AI - Surveillance Engine
echo ======================================================
echo   Starting VehicleGuard AI Surveillance Engine
echo ======================================================
python -m ai_engine.main
pause
