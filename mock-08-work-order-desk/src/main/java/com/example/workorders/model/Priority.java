package com.example.workorders.model;

import java.util.Locale;
import java.util.Optional;

/** Declared from most to least urgent; the database stores the position. */
public enum Priority {
    URGENT, HIGH, MEDIUM, LOW;

    public static Optional<Priority> parse(String raw) {
        if (raw == null) {
            return Optional.empty();
        }
        try {
            return Optional.of(valueOf(raw.trim().toUpperCase(Locale.ROOT)));
        } catch (IllegalArgumentException e) {
            return Optional.empty();
        }
    }
}
