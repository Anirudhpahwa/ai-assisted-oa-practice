package com.example.roombooking.dto;

import com.example.roombooking.model.BookingStatus;
import java.time.Instant;

/** Parsed query string of GET /api/bookings. Null fields mean "no filter". */
public record ListQuery(Long roomId, String bookedBy, BookingStatus status, Instant from, Instant to,
                        int page, int size) {
}
