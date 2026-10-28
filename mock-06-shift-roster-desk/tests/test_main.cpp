#include <functional>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "engine.h"
#include "model.h"
#include "parser.h"
#include "pay.h"
#include "report.h"
#include "timeutil.h"

struct Failure {
    std::string message;
};

template <typename A, typename B>
void expect_eq(const A& actual, const B& expected, int line) {
    if (!(actual == expected)) {
        std::ostringstream out;
        out << "line " << line << ": got [" << actual << "] expected [" << expected << "]";
        throw Failure{out.str()};
    }
}

#define EXPECT_EQ(actual, expected) expect_eq((actual), (expected), __LINE__)

template <typename Fn>
void expect_parse_error(Fn fn, const std::string& prefix, int line) {
    try {
        fn();
    } catch (const ParseError& error) {
        std::string message = error.what();
        if (message.compare(0, prefix.size(), prefix) != 0) {
            throw Failure{"line " + std::to_string(line) + ": got error [" + message + "] expected it to start with [" +
                          prefix + "]"};
        }
        return;
    }
    throw Failure{"line " + std::to_string(line) + ": expected a ParseError starting with [" + prefix + "]"};
}

#define EXPECT_PARSE_ERROR(call, prefix) expect_parse_error([&] { call; }, (prefix), __LINE__)

namespace {

const int kMonday = 20514;  // 2026-03-02

Staff make_staff(const std::string& id, const std::string& role, int max_weekly = 3000, int rate = 2000) {
    Staff member;
    member.id = id;
    member.name = "Name " + id;
    member.role = role;
    member.max_weekly_minutes = max_weekly;
    member.hourly_rate_cents = rate;
    return member;
}

Shift make_shift(const std::string& id, int day, int start, int end, const std::string& role = "cashier") {
    Shift shift;
    shift.id = id;
    shift.day = day;
    shift.start = start;
    shift.end = end;
    shift.role = role;
    return shift;
}

int hm(int hours, int minutes = 0) {
    return hours * 60 + minutes;
}

std::string verdict(const Decision& decision) {
    return decision.approved ? "APPROVED" : decision.reason;
}

void test_parse_inputs() {
    std::istringstream staff_in(
        "staff_id,name,role,max_weekly_minutes,hourly_rate_cents\r\n"
        "  s1 , Ana Lopez ,cashier, 2400 ,2000 \r\n"
        "\r\n"
        "s2,Ben,stock,1200,1500\r\n");
    std::vector<Staff> staff = parse_staff(staff_in);
    EXPECT_EQ(staff.size(), std::size_t(2));
    EXPECT_EQ(staff[0].id, std::string("s1"));
    EXPECT_EQ(staff[0].name, std::string("Ana Lopez"));
    EXPECT_EQ(staff[0].role, std::string("cashier"));
    EXPECT_EQ(staff[0].max_weekly_minutes, 2400);
    EXPECT_EQ(staff[0].hourly_rate_cents, 2000);
    EXPECT_EQ(staff[1].role, std::string("stock"));
    EXPECT_EQ(staff[1].hourly_rate_cents, 1500);

    std::istringstream shifts_in(
        "shift_id,date,start,end,role\n"
        "sh1,2026-03-02,08:00,16:00,cashier\n"
        " sh2 ,2026-03-03,22:00,23:30,stock \n");
    std::vector<Shift> shifts = parse_shifts(shifts_in);
    EXPECT_EQ(shifts.size(), std::size_t(2));
    EXPECT_EQ(shifts[0].id, std::string("sh1"));
    EXPECT_EQ(shifts[0].day, kMonday);
    EXPECT_EQ(shifts[0].start, 480);
    EXPECT_EQ(shifts[0].end, 960);
    EXPECT_EQ(shifts[0].minutes(), 480);
    EXPECT_EQ(shifts[1].id, std::string("sh2"));
    EXPECT_EQ(shifts[1].day, kMonday + 1);
    EXPECT_EQ(shifts[1].start, 1320);
    EXPECT_EQ(shifts[1].role, std::string("stock"));

    std::istringstream requests_in("request_id,staff_id,shift_id\r\nr1, s1 , sh1\r\n");
    std::vector<Request> requests = parse_requests(requests_in);
    EXPECT_EQ(requests.size(), std::size_t(1));
    EXPECT_EQ(requests[0].staff_id, std::string("s1"));
    EXPECT_EQ(requests[0].shift_id, std::string("sh1"));

    std::istringstream rules_in("# house rules\nmin_rest_minutes = 600\n\novertime_pct=125\r\n");
    Rules rules = parse_rules(rules_in);
    EXPECT_EQ(rules.min_rest_minutes, 600);
    EXPECT_EQ(rules.overtime_after_minutes, 2400);
    EXPECT_EQ(rules.overtime_pct, 125);

    EXPECT_EQ(days_from_civil(1970, 1, 1), 0);
    EXPECT_EQ(days_from_civil(2026, 3, 2), kMonday);

    std::istringstream bad_staff("h\ns1,Ana,cashier,2400,2000\ns2,Ben,stock,1200\n");
    EXPECT_PARSE_ERROR(parse_staff(bad_staff), "staff line 3:");
    std::istringstream bad_number("h\ns1,Ana,cashier,lots,2000\n");
    EXPECT_PARSE_ERROR(parse_staff(bad_number), "staff line 2:");
    std::istringstream bad_date("h\nsh1,2026-02-30,08:00,16:00,cashier\n");
    EXPECT_PARSE_ERROR(parse_shifts(bad_date), "shifts line 2:");
    std::istringstream bad_time("h\nsh1,2026-03-02,8:00,16:00,cashier\n");
    EXPECT_PARSE_ERROR(parse_shifts(bad_time), "shifts line 2:");
    std::istringstream backwards("h\nsh1,2026-03-02,16:00,08:00,cashier\n");
    EXPECT_PARSE_ERROR(parse_shifts(backwards), "shifts line 2:");
    std::istringstream bad_request("h\nr1,s1\n");
    EXPECT_PARSE_ERROR(parse_requests(bad_request), "requests line 2:");
    std::istringstream bad_key("# c\nsnack_break=15\n");
    EXPECT_PARSE_ERROR(parse_rules(bad_key), "rules line 2:");
    std::istringstream no_equals("min_rest_minutes 600\n");
    EXPECT_PARSE_ERROR(parse_rules(no_equals), "rules line 1:");
}

void test_basic_decisions() {
    std::vector<Staff> staff = {make_staff("s1", "cashier"), make_staff("s2", "cashier"), make_staff("s3", "stock")};
    std::vector<Shift> shifts = {
        make_shift("sh1", kMonday, hm(8), hm(16)),
        make_shift("sh3", kMonday, hm(8), hm(16), "stock"),
        make_shift("sh4", kMonday, hm(12), hm(20)),
    };
    std::vector<Request> requests = {
        {"r1", "s9", "sh1"}, {"r2", "s1", "sh9"}, {"r3", "s3", "sh1"}, {"r4", "s1", "sh1"},
        {"r5", "s2", "sh1"}, {"r6", "s1", "sh1"}, {"r7", "s1", "sh4"}, {"r8", "s2", "sh4"},
    };
    std::vector<Decision> decisions = decide_all(staff, shifts, requests, Rules());
    EXPECT_EQ(decisions.size(), std::size_t(8));
    EXPECT_EQ(verdict(decisions[0]), std::string("UNKNOWN_STAFF"));
    EXPECT_EQ(verdict(decisions[1]), std::string("UNKNOWN_SHIFT"));
    EXPECT_EQ(verdict(decisions[2]), std::string("ROLE_MISMATCH"));
    EXPECT_EQ(verdict(decisions[3]), std::string("APPROVED"));
    EXPECT_EQ(decisions[3].minutes, 480);
    EXPECT_EQ(decisions[3].pay_cents, 16000);
    EXPECT_EQ(verdict(decisions[4]), std::string("SHIFT_TAKEN"));
    EXPECT_EQ(verdict(decisions[5]), std::string("SHIFT_TAKEN"));
    EXPECT_EQ(decisions[5].minutes, 0);
    EXPECT_EQ(decisions[5].pay_cents, 0);
    EXPECT_EQ(verdict(decisions[6]), std::string("OVERLAP"));
    EXPECT_EQ(verdict(decisions[7]), std::string("APPROVED"));
    EXPECT_EQ(decisions[7].request_id, std::string("r8"));
    EXPECT_EQ(decisions[7].shift_id, std::string("sh4"));
}

void test_overlap_and_rest() {
    std::vector<Staff> staff = {make_staff("s1", "cashier", 5000)};
    int tuesday = kMonday + 1;
    std::vector<Shift> shifts = {
        make_shift("a", kMonday, hm(8), hm(16)),
        make_shift("b", kMonday, hm(14), hm(18)),
        make_shift("c", kMonday, hm(16), hm(20)),
        make_shift("f", tuesday, hm(2), hm(6)),
        make_shift("h", tuesday, hm(3), hm(9)),
        make_shift("i", tuesday, hm(17), hm(21)),
        make_shift("j", tuesday + 1, hm(7), hm(11)),
    };
    std::vector<Request> requests = {
        {"r1", "s1", "a"}, {"r2", "s1", "b"}, {"r3", "s1", "c"}, {"r4", "s1", "f"},
        {"r5", "s1", "h"}, {"r6", "s1", "i"}, {"r7", "s1", "j"},
    };
    std::vector<Decision> decisions = decide_all(staff, shifts, requests, Rules());
    EXPECT_EQ(verdict(decisions[0]), std::string("APPROVED"));
    EXPECT_EQ(verdict(decisions[1]), std::string("OVERLAP"));
    EXPECT_EQ(verdict(decisions[2]), std::string("INSUFFICIENT_REST"));
    EXPECT_EQ(verdict(decisions[3]), std::string("INSUFFICIENT_REST"));
    EXPECT_EQ(verdict(decisions[4]), std::string("APPROVED"));
    EXPECT_EQ(verdict(decisions[5]), std::string("INSUFFICIENT_REST"));
    EXPECT_EQ(verdict(decisions[6]), std::string("APPROVED"));
}

void test_weekly_limit() {
    std::vector<Staff> staff = {make_staff("s1", "cashier", 960)};
    int saturday = kMonday + 5;
    std::vector<Shift> shifts = {
        make_shift("sat1", saturday, hm(8), hm(16)),
        make_shift("sun1", saturday + 1, hm(8), hm(16)),
        make_shift("sat2", saturday, hm(16), hm(20)),
        make_shift("mon1", saturday + 2, hm(8), hm(16)),
        make_shift("mon2", saturday + 2, hm(16), hm(20)),
    };
    Rules rules;
    rules.min_rest_minutes = 0;
    std::vector<Request> requests = {
        {"r1", "s1", "sat1"}, {"r2", "s1", "sun1"}, {"r3", "s1", "sat2"}, {"r4", "s1", "mon1"}, {"r5", "s1", "mon2"},
    };
    std::vector<Decision> decisions = decide_all(staff, shifts, requests, rules);
    EXPECT_EQ(verdict(decisions[0]), std::string("APPROVED"));
    EXPECT_EQ(verdict(decisions[1]), std::string("APPROVED"));
    EXPECT_EQ(verdict(decisions[2]), std::string("WEEKLY_LIMIT"));
    EXPECT_EQ(verdict(decisions[3]), std::string("APPROVED"));
    EXPECT_EQ(verdict(decisions[4]), std::string("APPROVED"));

    EXPECT_EQ(week_index(kMonday), week_index(kMonday + 6));
    EXPECT_EQ(week_index(kMonday + 6) + 1, week_index(kMonday + 7));
}

void test_pay() {
    Rules rules;
    EXPECT_EQ(shift_pay(2000, 0, 480, rules), 16000);
    EXPECT_EQ(shift_pay(2000, 2400, 480, rules), 24000);
    EXPECT_EQ(shift_pay(2000, 2160, 480, rules), 20000);
    EXPECT_EQ(shift_pay(1999, 0, 45, rules), 1499);
    EXPECT_EQ(shift_pay(1501, 0, 30, rules), 751);

    std::vector<Staff> staff = {make_staff("s1", "cashier", 5000, 2000)};
    std::vector<Shift> shifts;
    std::vector<Request> requests;
    for (int i = 0; i < 6; ++i) {
        std::string id = "d" + std::to_string(i);
        shifts.push_back(make_shift(id, kMonday + i, hm(8), hm(16)));
        requests.push_back({"r" + std::to_string(i), "s1", id});
    }
    std::vector<Decision> decisions = decide_all(staff, shifts, requests, Rules());
    for (int i = 0; i < 5; ++i) {
        EXPECT_EQ(verdict(decisions[i]), std::string("APPROVED"));
        EXPECT_EQ(decisions[i].pay_cents, 16000);
    }
    EXPECT_EQ(verdict(decisions[5]), std::string("APPROVED"));
    EXPECT_EQ(decisions[5].pay_cents, 24000);
}

void test_summary_and_output() {
    std::vector<Staff> staff = {make_staff("s1", "cashier"), make_staff("s2", "cashier"), make_staff("s3", "cashier"),
                                make_staff("s4", "cashier")};
    std::vector<Decision> decisions;
    auto approved = [](const std::string& request, const std::string& staff_id, int minutes, int pay) {
        Decision decision;
        decision.request_id = request;
        decision.staff_id = staff_id;
        decision.shift_id = "x";
        decision.approved = true;
        decision.minutes = minutes;
        decision.pay_cents = pay;
        return decision;
    };
    Decision rejected;
    rejected.request_id = "r5";
    rejected.staff_id = "s4";
    rejected.shift_id = "x";
    rejected.reason = "OVERLAP";
    decisions.push_back(approved("r1", "s2", 240, 3000));
    decisions.push_back(approved("r2", "s1", 480, 4000));
    decisions.push_back(approved("r3", "s3", 600, 5000));
    decisions.push_back(approved("r4", "s2", 120, 1000));
    decisions.push_back(rejected);

    std::vector<StaffSummary> summaries = summarize(staff, decisions);
    EXPECT_EQ(summaries.size(), std::size_t(3));
    EXPECT_EQ(summaries[0].staff_id, std::string("s3"));
    EXPECT_EQ(summaries[1].staff_id, std::string("s1"));
    EXPECT_EQ(summaries[2].staff_id, std::string("s2"));
    EXPECT_EQ(summaries[2].shifts, 2);
    EXPECT_EQ(summaries[2].minutes, 360);
    EXPECT_EQ(summaries[2].pay_cents, 4000);
    EXPECT_EQ(summaries[2].name, std::string("Name s2"));

    EXPECT_EQ(format_summary(summaries),
              std::string("staff_id,name,shifts,minutes,pay_cents\n"
                          "s3,Name s3,1,600,5000\n"
                          "s1,Name s1,1,480,4000\n"
                          "s2,Name s2,2,360,4000\n"));
    EXPECT_EQ(format_results(decisions),
              std::string("request_id,decision,reason,pay_cents\n"
                          "r1,APPROVED,,3000\n"
                          "r2,APPROVED,,4000\n"
                          "r3,APPROVED,,5000\n"
                          "r4,APPROVED,,1000\n"
                          "r5,REJECTED,OVERLAP,0\n"));
}

}  // namespace

int main() {
    struct Case {
        const char* name;
        std::function<void()> run;
    };
    std::vector<Case> cases = {
        {"test_parse_inputs", test_parse_inputs},
        {"test_basic_decisions", test_basic_decisions},
        {"test_overlap_and_rest", test_overlap_and_rest},
        {"test_weekly_limit", test_weekly_limit},
        {"test_pay", test_pay},
        {"test_summary_and_output", test_summary_and_output},
    };
    int failed = 0;
    int passed = 0;
    for (const Case& test_case : cases) {
        try {
            test_case.run();
            std::cout << "PASSED " << test_case.name << "\n";
            ++passed;
        } catch (const Failure& failure) {
            std::cout << "FAILED " << test_case.name << ": " << failure.message << "\n";
            ++failed;
        } catch (const std::exception& error) {
            std::cout << "FAILED " << test_case.name << ": unexpected error " << error.what() << "\n";
            ++failed;
        }
    }
    std::cout << failed << " failed, " << passed << " passed\n";
    return failed == 0 ? 0 : 1;
}
