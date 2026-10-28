#include "report.h"

#include <algorithm>
#include <map>

std::vector<StaffSummary> summarize(const std::vector<Staff>& staff, const std::vector<Decision>& decisions) {
    std::map<std::string, std::string> names;
    for (const Staff& member : staff) {
        names[member.id] = member.name;
    }

    std::map<std::string, StaffSummary> by_staff;
    for (const Decision& decision : decisions) {
        if (!decision.approved) {
            continue;
        }
        StaffSummary& row = by_staff[decision.staff_id];
        row.staff_id = decision.staff_id;
        row.name = names[decision.staff_id];
        row.shifts += 1;
        row.minutes += decision.minutes;
        row.pay_cents += decision.pay_cents;
    }

    std::vector<StaffSummary> summaries;
    for (const auto& entry : by_staff) {
        summaries.push_back(entry.second);
    }
    std::sort(summaries.begin(), summaries.end(), [](const StaffSummary& a, const StaffSummary& b) {
        if (a.pay_cents != b.pay_cents) {
            return a.pay_cents > b.pay_cents;
        }
        return a.staff_id > b.staff_id;
    });
    return summaries;
}

std::string format_results(const std::vector<Decision>& decisions) {
    std::string text = "request_id,decision,reason,pay_cents\n";
    for (const Decision& decision : decisions) {
        text += decision.request_id + "," + (decision.approved ? "APPROVED" : "REJECTED") + "," + decision.reason +
                "," + std::to_string(decision.pay_cents) + "\n";
    }
    return text;
}

std::string format_summary(const std::vector<StaffSummary>& summaries) {
    std::string text = "staff_id,name,shifts,minutes,pay_cents\n";
    for (const StaffSummary& row : summaries) {
        text += row.staff_id + "," + row.name + "," + std::to_string(row.shifts) + "," + std::to_string(row.minutes) +
                "," + std::to_string(row.pay_cents) + "\n";
    }
    return text;
}
