package com.example.workorders.model;

import java.util.Locale;
import java.util.Optional;

public enum Status {
    OPEN, IN_PROGRESS, ON_HOLD, DONE, CANCELLED;

    public static Optional<Status> parse(String raw) {
        if (raw == null) {
            return Optional.empty();
        }
        try {
            return Optional.of(valueOf(raw.trim().toUpperCase(Locale.ROOT)));
        } catch (IllegalArgumentException e) {
            return Optional.empty();
        }
    }

    public boolean isClosed() {
        return this == DONE || this == CANCELLED;
    }
}
