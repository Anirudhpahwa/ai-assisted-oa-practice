@echo off
if not exist build mkdir build
g++ -std=c++17 -Wall -Isrc src\text.cpp src\timeutil.cpp src\parser.cpp src\pay.cpp src\engine.cpp src\report.cpp tests\test_main.cpp -o build\tests.exe
if errorlevel 1 exit /b 1
build\tests.exe
