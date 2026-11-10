package com.example.roombooking.service;

import com.example.roombooking.common.ApiException;
import com.example.roombooking.dto.ListQuery;
import com.example.roombooking.dto.Requests.CreateBooking;
import com.example.roombooking.model.BookingStatus;
import java.time.Duration;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.format.DateTimeParseException;
import org.springframework.stereotype.Component;

@Component
public class BookingValidator {

    /** A create request that passed every check that does not need the database. */
    public record ValidBooking(Long roomId, String title, Instant start, Instant end, int attendees,
                               long minutes) {
    }

    private static ApiException bad(String message) {
        return new ApiException(400, message);
    }

    public ValidBooking create(CreateBooking request) {
        String title = request.title() == null ? "" : request.title().trim();
        if (title.length() < 3 || title.length() > 80) {
            throw bad("title must be 3 to 80 characters");
        }
        if (request.roomId() == null) {
            throw bad("roomId is required");
        }
        Instant start = instant(request.startsAt(), "startsAt");
        Instant end = instant(request.endsAt(), "endsAt");
        if (!end.isAfter(start)) {
            throw bad("endsAt must be after startsAt");
        }
        long seconds = Duration.between(start, end).getSeconds();
        if (seconds < 1800 || seconds > 28800 || seconds % 1800 != 0) {
            throw bad("duration must be 30 minutes to 8 hours in 30-minute steps");
        }
        if (request.attendees() == null || request.attendees() < 1) {
            throw bad("attendees must be a whole number of 1 or more");
        }
        return new ValidBooking(request.roomId(), title, start, end, request.attendees(), seconds / 60);
    }

    /** Returns the trimmed key, or null when there is none. */
    public String idempotencyKey(String raw) {
        String key = raw == null ? "" : raw.trim();
        if (key.length() > 64) {
            throw bad("Idempotency-Key must be at most 64 characters");
        }
        return key.isEmpty() ? null : key;
    }

    public ListQuery list(String roomId, String bookedBy, String status, String from, String to,
                          String page, String size) {
        Long room = blank(roomId) ? null : whole(roomId, "roomId must be a whole number");
        String who = blank(bookedBy) ? null : bookedBy.trim();
        BookingStatus wanted = blank(status) ? null : BookingStatus.parse(status)
                .orElseThrow(() -> bad("status must be CONFIRMED or CANCELLED"));
        Instant start = blank(from) ? null : instant(from, "from");
        Instant end = blank(to) ? null : instant(to, "to");
        if (start != null && end != null && !start.isBefore(end)) {
            throw bad("from must be before to");
        }
        int pageNumber = number(page, 0, 0, Integer.MAX_VALUE, "page must be zero or a positive integer");
        int pageSize = number(size, 20, 1, 100, "size must be an integer from 1 to 100");
        return new ListQuery(room, who, wanted, start, end, pageNumber, pageSize);
    }

    private static boolean blank(String value) {
        return value == null || value.isBlank();
    }

    private static Instant instant(String raw, String name) {
        try {
            if (blank(raw)) {
                throw bad(name + " must be a valid date-time");
            }
            return OffsetDateTime.parse(raw.trim()).toInstant();
        } catch (DateTimeParseException e) {
            throw bad(name + " must be a valid date-time");
        }
    }

    private static Long whole(String raw, String message) {
        if (!raw.trim().matches("\\d{1,18}")) {
            throw bad(message);
        }
        return Long.parseLong(raw.trim());
    }

    private static int number(String raw, int fallback, int min, int max, String message) {
        if (blank(raw)) {
            return fallback;
        }
        if (!raw.trim().matches("\\d{1,9}")) {
            throw bad(message);
        }
        int value = Integer.parseInt(raw.trim());
        if (value < min || value > max) {
            throw bad(message);
        }
        return value;
    }
}
