package com.example.workorders.model;

import java.util.Locale;
import java.util.Optional;

public enum Role {
    TECHNICIAN, MANAGER;

    public static Optional<Role> parse(String raw) {
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
