#pragma once

#include <string>

int days_from_civil(int year, int month, int day);
bool parse_date(const std::string& text, int& days);
bool parse_clock(const std::string& text, int& minutes);
int week_index(int days);
