#pragma once

#include <istream>
#include <vector>

#include "model.h"

std::vector<Staff> parse_staff(std::istream& in);
std::vector<Shift> parse_shifts(std::istream& in);
std::vector<Request> parse_requests(std::istream& in);
Rules parse_rules(std::istream& in);
