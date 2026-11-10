package com.example.roombooking.service;

/** Money arithmetic for bookings. All amounts are whole cents, rounded half up. */
public final class PriceCalculator {

    private PriceCalculator() {
    }

    /** The price of {@code minutes} at an hourly rate. */
    public static long total(int hourlyRateCents, long minutes) {
        return hourlyRateCents * minutes / 60;
    }

    /** {@code percent} percent of an amount. */
    public static long percentOf(long cents, int percent) {
        return (cents * percent + 50) / 100;
    }
}
