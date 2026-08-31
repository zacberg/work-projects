@echo off
title AR Collections Dashboard
cd /d C:\Users\ZachBergman\ar-dashboard
echo Starting AR Collections Dashboard...
start "AR Dashboard" cmd /k npm run dev
timeout /t 5 /nobreak > nul
start "" "http://localhost:5173"
