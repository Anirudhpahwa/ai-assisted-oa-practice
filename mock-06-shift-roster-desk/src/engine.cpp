#include "engine.h"

#include <algorithm>
#include <map>
#include <set>
#include <string>

#include "pay.h"
#include "timeutil.h"

namespace {

using Booked = std::vector<const Shift*>;

int absolute_start(const Shift& shift) {
    return shift.day * 1440 + shift.start;
}

int absolute_end(const Shift& shift) {
    return shift.day * 1440 + shift.end;
}

bool overlaps(const Shift& a, const Shift& b) {
    return absolute_start(a) < absolute_end(b) && absolute_start(b) < absolute_end(a);
}

// Minutes of rest between two shifts that do not overlap.
int rest_between(const Shift& a, const Shift& b) {
    return std::max(b.start - a.end, a.start - b.end);
}

int week_minutes(const Booked& booked, int day) {
    int total = 0;
    for (const Shift* shift : booked) {
        if (week_index(shift->day) == week_index(day)) {
            total += shift->minutes();
        }
    }
    return total;
}

// Returns the reason a request must be rejected, or an empty string when it can be approved.
std::string rejection_reason(const Staff* staff,
                             const Shift* shift,
                             const Booked& booked,
                             std::set<std::string>& filled,
                             const Rules& rules) {
    if (staff == nullptr) {
        return "UNKNOWN_STAFF";
    }
    if (shift == nullptr) {
        return "UNKNOWN_SHIFT";
    }
    if (shift->role != staff->role) {
        return "ROLE_MISMATCH";
    }
    if (!filled.insert(shift->id).second) {
        return "SHIFT_TAKEN";
    }
    for (const Shift* other : booked) {
        if (overlaps(*shift, *other)) {
            return "OVERLAP";
        }
    }
    for (const Shift* other : booked) {
        if (rest_between(*shift, *other) < rules.min_rest_minutes) {
            return "INSUFFICIENT_REST";
        }
    }
    if (week_minutes(booked, shift->day) + shift->minutes() > staff->max_weekly_minutes) {
        return "WEEKLY_LIMIT";
    }
    return "";
}

}  // namespace

std::vector<Decision> decide_all(const std::vector<Staff>& staff,
                                 const std::vector<Shift>& shifts,
                                 const std::vector<Request>& requests,
                                 const Rules& rules) {
    std::map<std::string, const Staff*> staff_by_id;
    for (const Staff& member : staff) {
        staff_by_id[member.id] = &member;
    }
    std::map<std::string, const Shift*> shift_by_id;
    for (const Shift& shift : shifts) {
        shift_by_id[shift.id] = &shift;
    }

    std::set<std::string> filled;
    std::map<std::string, Booked> booked;
    std::vector<Decision> decisions;

    for (const Request& request : requests) {
        Decision decision;
        decision.request_id = request.id;
        decision.staff_id = request.staff_id;
        decision.shift_id = request.shift_id;

        auto staff_it = staff_by_id.find(request.staff_id);
        auto shift_it = shift_by_id.find(request.shift_id);
        const Staff* member = staff_it == staff_by_id.end() ? nullptr : staff_it->second;
        const Shift* shift = shift_it == shift_by_id.end() ? nullptr : shift_it->second;

        Booked& mine = booked[request.staff_id];
        decision.reason = rejection_reason(member, shift, mine, filled, rules);
        decision.approved = decision.reason.empty();
        if (decision.approved) {
            int week_total = week_minutes(mine, shift->day) + shift->minutes();
            decision.minutes = shift->minutes();
            decision.pay_cents = shift_pay(member->hourly_rate_cents, week_total, shift->minutes(), rules);
            mine.push_back(shift);
        }
        decisions.push_back(decision);
    }
    return decisions;
}
