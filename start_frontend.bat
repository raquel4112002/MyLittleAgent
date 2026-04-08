@echo off
cd /d %~dp0\frontend
set VITE_API_BASE_URL=http://localhost:6400
npm run dev
