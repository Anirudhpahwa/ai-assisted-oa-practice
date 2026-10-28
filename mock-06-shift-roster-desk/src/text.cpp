#include "text.h"

#include <cctype>

namespace {
const char* const kBlanks = " \t\r\n";
}

std::string trim(const std::string& text) {
    std::size_t first = text.find_first_not_of(kBlanks);
    if (first == std::string::npos) {
        return "";
    }
    return text.substr(first);
}

std::vector<std::string> split_fields(const std::string& line) {
    std::vector<std::string> fields;
    std::string current;
    for (char c : line) {
        if (c == ',') {
            fields.push_back(trim(current));
            current.clear();
        } else {
            current.push_back(c);
        }
    }
    fields.push_back(trim(current));
    return fields;
}

bool parse_count(const std::string& text, int& out) {
    if (text.empty() || text.size() > 9) {
        return false;
    }
    int value = 0;
    for (char c : text) {
        if (!std::isdigit(static_cast<unsigned char>(c))) {
            return false;
        }
        value = value * 10 + (c - '0');
    }
    out = value;
    return true;
}
