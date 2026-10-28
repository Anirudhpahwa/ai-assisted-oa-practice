#include <fstream>
#include <iostream>
#include <string>

#include "engine.h"
#include "parser.h"
#include "report.h"

namespace {

std::ifstream open_input(const std::string& dir, const std::string& name) {
    std::ifstream in(dir + "/" + name);
    if (!in) {
        throw std::runtime_error("cannot open " + dir + "/" + name);
    }
    return in;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "usage: roster <input_dir> <output_dir>\n";
        return 2;
    }
    std::string input_dir = argv[1];
    std::string output_dir = argv[2];
    try {
        std::ifstream staff_file = open_input(input_dir, "staff.csv");
        std::ifstream shifts_file = open_input(input_dir, "shifts.csv");
        std::ifstream requests_file = open_input(input_dir, "requests.csv");
        std::ifstream rules_file = open_input(input_dir, "rules.cfg");

        std::vector<Staff> staff = parse_staff(staff_file);
        std::vector<Shift> shifts = parse_shifts(shifts_file);
        std::vector<Request> requests = parse_requests(requests_file);
        Rules rules = parse_rules(rules_file);

        std::vector<Decision> decisions = decide_all(staff, shifts, requests, rules);
        std::ofstream(output_dir + "/results.csv") << format_results(decisions);
        std::ofstream(output_dir + "/summary.csv") << format_summary(summarize(staff, decisions));
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << "\n";
        return 1;
    }
    return 0;
}
