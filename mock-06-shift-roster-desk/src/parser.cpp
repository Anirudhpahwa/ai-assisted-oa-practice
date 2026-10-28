#include "parser.h"

#include <string>

#include "text.h"
#include "timeutil.h"

namespace {

struct Row {
    int line;
    std::vector<std::string> fields;
};

[[noreturn]] void fail(const std::string& kind, int line, const std::string& problem) {
    throw ParseError(kind + " line " + std::to_string(line) + ": " + problem);
}

std::vector<Row> read_rows(std::istream& in, const std::string& kind, std::size_t width) {
    std::vector<Row> rows;
    std::string text;
    int line = 0;
    while (std::getline(in, text)) {
        ++line;
        if (line == 1 || trim(text).empty()) {
            continue;
        }
        std::vector<std::string> fields = split_fields(text);
        if (fields.size() != width) {
            fail(kind, line, "expected " + std::to_string(width) + " fields");
        }
        rows.push_back({line, fields});
    }
    return rows;
}

int count_field(const std::string& kind, const Row& row, std::size_t index, const char* label) {
    int value = 0;
    if (!parse_count(row.fields[index], value)) {
        fail(kind, row.line, std::string(label) + " must be a whole number");
    }
    return value;
}

}  // namespace

std::vector<Staff> parse_staff(std::istream& in) {
    std::vector<Staff> staff;
    for (const Row& row : read_rows(in, "staff", 5)) {
        Staff member;
        member.id = row.fields[0];
        member.name = row.fields[1];
        member.role = row.fields[2];
        member.max_weekly_minutes = count_field("staff", row, 3, "max_weekly_minutes");
        member.hourly_rate_cents = count_field("staff", row, 4, "hourly_rate_cents");
        staff.push_back(member);
    }
    return staff;
}

std::vector<Shift> parse_shifts(std::istream& in) {
    std::vector<Shift> shifts;
    for (const Row& row : read_rows(in, "shifts", 5)) {
        Shift shift;
        shift.id = row.fields[0];
        if (!parse_date(row.fields[1], shift.day)) {
            fail("shifts", row.line, "date must be a real date formatted YYYY-MM-DD");
        }
        if (!parse_clock(row.fields[2], shift.start)) {
            fail("shifts", row.line, "start must be a time formatted HH:MM");
        }
        if (!parse_clock(row.fields[3], shift.end)) {
            fail("shifts", row.line, "end must be a time formatted HH:MM");
        }
        if (shift.end <= shift.start) {
            fail("shifts", row.line, "end must be after start");
        }
        shift.role = row.fields[4];
        shifts.push_back(shift);
    }
    return shifts;
}

std::vector<Request> parse_requests(std::istream& in) {
    std::vector<Request> requests;
    for (const Row& row : read_rows(in, "requests", 3)) {
        requests.push_back({row.fields[0], row.fields[1], row.fields[2]});
    }
    return requests;
}

Rules parse_rules(std::istream& in) {
    Rules rules;
    std::string text;
    int line = 0;
    while (std::getline(in, text)) {
        ++line;
        std::string content = trim(text);
        if (content.empty() || content[0] == '#') {
            continue;
        }
        std::size_t equals = content.find('=');
        if (equals == std::string::npos) {
            fail("rules", line, "expected key=value");
        }
        std::string key = trim(content.substr(0, equals));
        int value = 0;
        if (!parse_count(trim(content.substr(equals + 1)), value)) {
            fail("rules", line, "value must be a whole number");
        }
        if (key == "min_rest_minutes") {
            rules.min_rest_minutes = value;
        } else if (key == "overtime_after_minutes") {
            rules.overtime_after_minutes = value;
        } else if (key == "overtime_pct") {
            rules.overtime_pct = value;
        } else {
            fail("rules", line, "unknown key " + key);
        }
    }
    return rules;
}
