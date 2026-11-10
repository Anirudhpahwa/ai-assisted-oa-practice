package com.example.roombooking.model;

import java.util.Locale;
import java.util.Optional;

public enum BookingStatus {
    CONFIRMED, CANCELLED;

    public static Optional<BookingStatus> parse(String raw) {
        try {
            return Optional.of(valueOf(raw.trim().toUpperCase(Locale.ROOT)));
        } catch (IllegalArgumentException e) {
            return Optional.empty();
        }
    }
}
