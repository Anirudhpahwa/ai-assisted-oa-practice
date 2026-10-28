@echo off
if not exist build mkdir build
if not exist out mkdir out
g++ -std=c++17 -Wall -Isrc src\text.cpp src\timeutil.cpp src\parser.cpp src\pay.cpp src\engine.cpp src\report.cpp src\main.cpp -o build\roster.exe
if errorlevel 1 exit /b 1
build\roster.exe data\sample out
