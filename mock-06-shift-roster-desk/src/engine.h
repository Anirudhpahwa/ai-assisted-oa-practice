#pragma once

#include <vector>

#include "model.h"

std::vector<Decision> decide_all(const std::vector<Staff>& staff,
                                 const std::vector<Shift>& shifts,
                                 const std::vector<Request>& requests,
                                 const Rules& rules);
