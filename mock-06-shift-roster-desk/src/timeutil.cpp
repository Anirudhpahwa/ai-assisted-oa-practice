#include "timeutil.h"

#include "text.h"

namespace {

bool is_leap(int year) {
    return (year % 4 == 0 && year % 100 != 0) || year % 400 == 0;
}

int days_in_month(int year, int month) {
    static const int lengths[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    if (month == 2 && is_leap(year)) {
        return 29;
    }
    return lengths[month - 1];
}

}  // namespace

int days_from_civil(int year, int month, int day) {
    year -= month <= 2;
    int era = (year >= 0 ? year : year - 399) / 400;
    int year_of_era = year - era * 400;
    int day_of_year = (153 * (month + (month > 2 ? -3 : 9)) + 2) / 5 + day - 1;
    int day_of_era = year_of_era * 365 + year_of_era / 4 - year_of_era / 100 + day_of_year;
    return era * 146097 + day_of_era - 719468;
}

bool parse_date(const std::string& text, int& days) {
    if (text.size() != 10 || text[4] != '-' || text[7] != '-') {
        return false;
    }
    int year = 0;
    int month = 0;
    int day = 0;
    if (!parse_count(text.substr(0, 4), year) || !parse_count(text.substr(5, 2), month) ||
        !parse_count(text.substr(8, 2), day)) {
        return false;
    }
    if (month < 1 || month > 12 || day < 1 || day > days_in_month(year, month)) {
        return false;
    }
    days = days_from_civil(year, month, day);
    return true;
}

bool parse_clock(const std::string& text, int& minutes) {
    if (text.size() != 5 || text[2] != ':') {
        return false;
    }
    int hours = 0;
    int mins = 0;
    if (!parse_count(text.substr(0, 2), hours) || !parse_count(text.substr(3, 2), mins)) {
        return false;
    }
    if (hours > 23 || mins > 59) {
        return false;
    }
    minutes = hours * 60 + mins;
    return true;
}

int week_index(int days) {
    return (days + 4) / 7;
}
