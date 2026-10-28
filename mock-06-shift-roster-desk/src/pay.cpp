#include "pay.h"

#include <algorithm>

namespace {
// Pay is weighted in hundredths of the base rate, and an hour has 60 minutes.
const long long kMinutesTimesPercent = 60LL * 100LL;
}

int shift_pay(int hourly_rate_cents, int week_minutes_before, int shift_minutes, const Rules& rules) {
    int past_threshold = week_minutes_before + shift_minutes - rules.overtime_after_minutes;
    int overtime = std::min(shift_minutes, std::max(0, past_threshold));
    int regular = shift_minutes - overtime;
    long long weighted = static_cast<long long>(regular) * 100 + static_cast<long long>(overtime) * rules.overtime_pct;
    return static_cast<int>(weighted * hourly_rate_cents / kMinutesTimesPercent);
}
