package com.example.roombooking.service;

import java.time.Duration;
import org.springframework.stereotype.Component;

/** How much of the price is charged when a booking is cancelled. */
@Component
public class CancellationPolicy {

    private static final long FREE_HOURS = 24;
    private static final long LATE_HOURS = 3;

    public int feePercent(Duration untilStart) {
        if (untilStart.compareTo(Duration.ofHours(FREE_HOURS)) >= 0) {
            return 0;
        }
        if (untilStart.compareTo(Duration.ofHours(LATE_HOURS)) >= 0) {
            return 50;
        }
        return 100;
    }
}
