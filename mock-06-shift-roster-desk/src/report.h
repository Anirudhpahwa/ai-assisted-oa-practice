#pragma once

#include <string>
#include <vector>

#include "model.h"

std::vector<StaffSummary> summarize(const std::vector<Staff>& staff, const std::vector<Decision>& decisions);
std::string format_results(const std::vector<Decision>& decisions);
std::string format_summary(const std::vector<StaffSummary>& summaries);
