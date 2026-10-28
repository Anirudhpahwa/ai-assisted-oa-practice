#!/bin/sh
mkdir -p build out
g++ -std=c++17 -Wall -Isrc src/*.cpp -o build/roster || exit 1
./build/roster data/sample out
