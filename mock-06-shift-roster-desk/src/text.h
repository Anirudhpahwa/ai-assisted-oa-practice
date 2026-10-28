#pragma once

#include <string>
#include <vector>

std::string trim(const std::string& text);
std::vector<std::string> split_fields(const std::string& line);
bool parse_count(const std::string& text, int& out);
