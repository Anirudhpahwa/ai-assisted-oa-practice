package com.example.roombooking.model;

import java.util.Locale;
import java.util.Optional;

public enum Role {
    USER, MANAGER;

    public static Optional<Role> parse(String raw) {
        try {
            return Optional.of(valueOf(raw.trim().toUpperCase(Locale.ROOT)));
        } catch (IllegalArgumentException e) {
            return Optional.empty();
        }
    }
}
