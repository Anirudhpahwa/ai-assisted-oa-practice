#pragma once

#include <stdexcept>
#include <string>

struct ParseError : std::runtime_error {
    using std::runtime_error::runtime_error;
};

struct Staff {
    std::string id;
    std::string name;
    std::string role;
    int max_weekly_minutes = 0;
    int hourly_rate_cents = 0;
};

struct Shift {
    std::string id;
    int day = 0;    // days since 1970-01-01
    int start = 0;  // minutes after midnight
    int end = 0;    // minutes after midnight
    std::string role;

    int minutes() const { return end - start; }
};

struct Request {
    std::string id;
    std::string staff_id;
    std::string shift_id;
};

struct Rules {
    int min_rest_minutes = 660;
    int overtime_after_minutes = 2400;
    int overtime_pct = 150;
};

struct Decision {
    std::string request_id;
    std::string staff_id;
    std::string shift_id;
    bool approved = false;
    std::string reason;  // empty when approved
    int minutes = 0;     // length of the shift when approved, otherwise 0
    int pay_cents = 0;   // pay for the shift when approved, otherwise 0
};

struct StaffSummary {
    std::string staff_id;
    std::string name;
    int shifts = 0;
    int minutes = 0;
    int pay_cents = 0;
};
